"""
Add new well to database WITH TOC metadata (no re-index required)

This script combines:
- TOC extraction (RobustTOCExtractor)
- Section-aware chunking (SectionAwareChunker with TOC)
- Multi-modal extraction (text + tables + pictures)
- Incremental indexing (append to existing ChromaDB)

Usage:
    # Add single PDF with TOC extraction
    python scripts/add_well_with_toc.py --pdf "Well 7/Well report/EOWR.pdf" --well "Well 7"

    # Add entire well folder with TOC extraction for all PDFs
    python scripts/add_well_with_toc.py --well-folder "Training data-shared with participants/Well 7"
"""

import sys
import json
import time
import argparse
import fitz
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vector_store import TOCEnhancedVectorStore
from embeddings import EmbeddingManager
from chunker import SectionAwareChunker
from table_chunker import TableChunker


class TOCEnhancedIncrementalIndexer:
    """Add new documents with TOC extraction and full multi-modal features"""

    def __init__(self):
        print("="*80)
        print("TOC-ENHANCED INCREMENTAL INDEXING")
        print("="*80)

        # Connect to EXISTING vector store (does not delete existing data)
        self.vector_store = TOCEnhancedVectorStore()
        print("[OK] Connected to existing vector store")

        self.embedding_manager = EmbeddingManager()
        print("[OK] Embedding manager ready")

        self.chunker = SectionAwareChunker(chunk_size=1000, overlap=200)
        print("[OK] Section-aware chunker ready")

        self.table_chunker = TableChunker()
        print("[OK] Table chunker ready")

        # Setup Docling with ALL advanced features (same as comprehensive reindex)
        from docling.document_converter import DocumentConverter
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption
        from docling.datamodel.pipeline_options import TableFormerMode

        pipeline_options = PdfPipelineOptions()

        # TableFormer ACCURATE mode
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        pipeline_options.table_structure_options.do_cell_matching = False

        # Enhanced OCR with force_full_page_ocr for scanned documents
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options.force_full_page_ocr = True  # Critical for scanned TOCs

        # Picture extraction
        pipeline_options.generate_picture_images = True
        pipeline_options.images_scale = 2.0  # Optimal (proven 20% faster)
        pipeline_options.do_picture_classification = True

        # SmolVLM for picture descriptions
        from docling.datamodel.pipeline_options import smolvlm_picture_description

        pipeline_options.do_picture_description = True
        pipeline_options.picture_description_options = smolvlm_picture_description
        pipeline_options.picture_description_options.prompt = (
            "Describe this diagram or figure in detail. "
            "Include all visible text, labels, measurements, annotations, and handwritten notes. "
            "Mention axes, legends, and any technical information shown."
        )

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        print("[OK] Docling converter ready (TableFormer ACCURATE + SmolVLM-256M + Enhanced OCR)")

        # Load TOC extractor
        sys.path.insert(0, str(Path(__file__).parent))
        from robust_toc_extractor import RobustTOCExtractor
        from analyze_all_tocs import find_toc_boundaries
        from llm_toc_parser import LLMTOCParser
        self.toc_extractor = RobustTOCExtractor()
        self.llm_toc_parser = LLMTOCParser()
        self.find_toc_boundaries = find_toc_boundaries
        print("[OK] TOC extractor ready (RobustTOCExtractor + LLM fallback)")

        self.results = {
            'timestamp': datetime.now().isoformat(),
            'added_pdfs': 0,
            'added_chunks': 0,
            'errors': []
        }

    def _extract_text_pymupdf(self, pdf_path, num_pages=10):
        """Extract raw text from PDF using PyMuPDF for TOC fallback"""
        try:
            doc = fitz.open(str(pdf_path))
            text_parts = []
            for page_num in range(min(num_pages, len(doc))):
                page = doc[page_num]
                text_parts.append(page.get_text())
            doc.close()
            return '\n'.join(text_parts)
        except Exception as e:
            print(f"  [ERROR] PyMuPDF extraction failed: {e}")
            return None

    def _extract_pictures(self, doc, well_name, filename):
        """Extract pictures from document and save to filesystem"""
        from docling_core.types.doc.document import (
            PictureItem,
            PictureDescriptionData,
            PictureClassificationData,
        )

        pictures = []
        output_dir = Path(f"outputs/well_pictures/{well_name}")
        output_dir.mkdir(parents=True, exist_ok=True)

        for item, level in doc.iterate_items():
            if isinstance(item, PictureItem):
                picture_data = {
                    'ref': str(item.self_ref),
                    'caption': item.caption_text(doc=doc),
                    'image_path': None,
                    'width': None,
                    'height': None,
                    'page': None,
                    'classification': None,
                    'description': None,
                    'contains_handwriting': False,
                    'contains_text_labels': False,
                }

                # Save picture image
                if hasattr(item, 'image') and item.image:
                    image_filename = f"{filename.replace('.pdf', '')}_{item.self_ref.replace('#/', '').replace('/', '_')}.png"
                    image_path = output_dir / image_filename

                    try:
                        pil_image = item.get_image(doc)
                        pil_image.save(str(image_path))
                        picture_data['image_path'] = str(image_path)
                        picture_data['width'] = pil_image.width
                        picture_data['height'] = pil_image.height
                    except Exception as e:
                        print(f"    [WARN] Could not save image {item.self_ref}: {e}")

                # Extract annotations
                for annotation in item.annotations:
                    if isinstance(annotation, PictureClassificationData):
                        if annotation.predicted_classes:
                            top_class = annotation.predicted_classes[0]
                            picture_data['classification'] = {
                                'type': top_class.class_name,
                                'confidence': top_class.confidence,
                            }

                    elif isinstance(annotation, PictureDescriptionData):
                        description_text = annotation.text
                        picture_data['description'] = description_text

                        # Detect handwriting
                        handwriting_keywords = [
                            'handwritten', 'handwriting', 'hand-written',
                            'written by hand', 'manuscript', 'written note'
                        ]
                        picture_data['contains_handwriting'] = any(
                            keyword in description_text.lower()
                            for keyword in handwriting_keywords
                        )

                        # Detect text labels
                        label_keywords = [
                            'label', 'annotation', 'text', 'caption',
                            'measurement', 'depth', 'meter', 'foot'
                        ]
                        picture_data['contains_text_labels'] = any(
                            keyword in description_text.lower()
                            for keyword in label_keywords
                        )

                pictures.append(picture_data)

        return pictures

    def add_single_pdf(self, pdf_path, well_name):
        """
        Add a single PDF with TOC extraction and full features

        Args:
            pdf_path: Path to PDF file
            well_name: Well identifier (e.g., "Well 7")

        Returns:
            Dict with status and chunk count
        """
        pdf_path = Path(pdf_path)
        filename = pdf_path.name

        print(f"\n[{well_name}] Adding: {filename}")

        if not pdf_path.exists():
            print(f"  [ERROR] PDF not found: {pdf_path}")
            self.results['errors'].append({
                'well': well_name,
                'file': filename,
                'error': 'File not found'
            })
            return {'status': 'error', 'error': 'File not found'}

        try:
            # Parse PDF with Docling (comprehensive extraction)
            start_time = time.time()

            result = self.converter.convert(str(pdf_path))
            doc = result.document
            markdown = doc.export_to_markdown()
            tables = doc.tables if hasattr(doc, 'tables') else []

            # Extract pictures
            pictures = self._extract_pictures(doc, well_name, filename)

            parse_time = time.time() - start_time
            print(f"  Parsed in {parse_time:.1f}s")
            print(f"  Extracted {len(tables)} tables, {len(pictures)} pictures")

            # EXTRACT TOC with Docling markdown first, PyMuPDF fallback, LLM fallback
            print(f"  Extracting TOC...")
            toc_sections = []
            toc_source = None
            scrambled_toc_text = None  # Store TOC text if found but scrambled

            # Try Docling markdown first
            lines = markdown.split('\n')
            toc_start, toc_end = self.find_toc_boundaries(lines)

            if toc_start >= 0:
                toc_lines = lines[toc_start:toc_end]
                toc_entries, pattern = self.toc_extractor.extract(toc_lines)

                if len(toc_entries) >= 3:
                    toc_sections = toc_entries
                    toc_source = "Docling"
                    print(f"  [OK] Extracted {len(toc_sections)} TOC sections from Docling using {pattern}")
                    for i, toc in enumerate(toc_sections[:5], 1):
                        print(f"    {i}. {toc.get('number', 'N/A')} - {toc.get('title', 'Unknown')}")
                    if len(toc_sections) > 5:
                        print(f"    ... and {len(toc_sections) - 5} more")
                else:
                    # TOC found but parsing failed (likely scrambled) - save for LLM
                    print(f"  [WARN] Docling: TOC found but parsing failed ({len(toc_entries)} entries) - likely scrambled")
                    scrambled_toc_text = '\n'.join(toc_lines)

            # If Docling didn't find TOC, try PyMuPDF fallback
            if not toc_sections:
                if toc_start < 0:  # Only if Docling didn't find TOC at all
                    print(f"  Docling: NO TOC FOUND")
                print(f"  Trying PyMuPDF fallback...")

                raw_text = self._extract_text_pymupdf(pdf_path, num_pages=10)
                if raw_text:
                    raw_lines = raw_text.split('\n')
                    toc_start, toc_end = self.find_toc_boundaries(raw_lines)

                    if toc_start >= 0:
                        toc_lines = raw_lines[toc_start:toc_end]
                        toc_entries, pattern = self.toc_extractor.extract(toc_lines)

                        if len(toc_entries) >= 3:
                            toc_sections = toc_entries
                            toc_source = "PyMuPDF"
                            print(f"  [OK] Extracted {len(toc_sections)} TOC sections from PyMuPDF using {pattern}")
                            for i, toc in enumerate(toc_sections[:5], 1):
                                print(f"    {i}. {toc.get('number', 'N/A')} - {toc.get('title', 'Unknown')}")
                            if len(toc_sections) > 5:
                                print(f"    ... and {len(toc_sections) - 5} more")
                        else:
                            # TOC found but parsing failed (likely scrambled) - save for LLM
                            print(f"  [WARN] PyMuPDF: TOC found but parsing failed ({len(toc_entries)} entries) - likely scrambled")
                            if not scrambled_toc_text:  # Only if Docling didn't provide scrambled text
                                scrambled_toc_text = '\n'.join(toc_lines)
                    else:
                        print(f"  [WARN] PyMuPDF: No TOC found")

            # If we have scrambled TOC text but no parsed entries, try LLM fallback
            titles_only_mode = False
            section_titles = []

            if not toc_sections and scrambled_toc_text:
                print(f"  Trying LLM fallback to parse scrambled TOC...")
                try:
                    toc_entries, method = self.llm_toc_parser.parse_scrambled_toc(scrambled_toc_text)
                    if len(toc_entries) >= 3:
                        # Validate TOC quality - check for missing pages
                        print(f"  [VALIDATION] Checking TOC quality...")
                        missing_pages = sum(1 for e in toc_entries if e.get('page', 0) == 0)
                        print(f"  Missing pages: {missing_pages}/{len(toc_entries)}")

                        if missing_pages > 0:
                            # Use titles-only mode
                            print(f"  [DECISION] Found {missing_pages} missing page(s) - using titles-only mode")
                            titles_only_mode = True
                            section_titles = [
                                entry['title'].strip()
                                for entry in toc_entries
                                if entry.get('title', '').strip() and len(entry.get('title', '').strip()) > 2
                            ]
                            print(f"  [OK] Extracted {len(section_titles)} section titles")
                            for i, title in enumerate(section_titles[:5], 1):
                                print(f"    {i}. {title}")
                            if len(section_titles) > 5:
                                print(f"    ... and {len(section_titles) - 5} more")
                        else:
                            # TOC quality acceptable
                            toc_sections = toc_entries
                            toc_source = "LLM"
                            print(f"  [OK] Extracted {len(toc_sections)} TOC sections from LLM")
                            for i, toc in enumerate(toc_sections[:5], 1):
                                print(f"    {i}. {toc.get('number', 'N/A')} - {toc.get('title', 'Unknown')}")
                            if len(toc_sections) > 5:
                                print(f"    ... and {len(toc_sections) - 5} more")
                    else:
                        print(f"  [WARN] LLM: Only {len(toc_entries)} entries extracted")
                except Exception as e:
                    print(f"  [ERROR] LLM fallback failed: {e}")

            if not toc_sections and not titles_only_mode:
                print(f"  [WARN] No TOC found (tried Docling + PyMuPDF + LLM) - will use hierarchical chunking")

            # Choose chunking strategy based on TOC quality
            if titles_only_mode:
                # Use hierarchical chunking (no TOC required)
                print(f"  Creating hierarchical chunks (titles-only mode)...")
                from docling_core.transforms.chunker import HierarchicalChunker
                from transformers import AutoTokenizer

                tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
                hierarchical_chunker = HierarchicalChunker(tokenizer=tokenizer)

                chunk_iter = hierarchical_chunker.chunk(dl_doc=doc)
                chunks = []
                for chunk in chunk_iter:
                    chunks.append({
                        'text': chunk.text,
                        'metadata': {
                            'chunk_strategy': 'hierarchical_no_toc',
                            'has_toc': False,
                            'toc_quality': 'titles_only',
                        }
                    })
            else:
                # Use section-aware chunking WITH TOC
                print(f"  Creating section-aware chunks with TOC...")
                chunks = self.chunker.chunk_with_section_headers(
                    text=markdown,
                    toc_sections=toc_sections  # Pass extracted TOC!
                )

            # Add well and file metadata
            for chunk in chunks:
                chunk['metadata']['well_name'] = well_name
                chunk['metadata']['filename'] = filename
                chunk['metadata']['filepath'] = str(pdf_path)
                chunk['metadata']['has_tables'] = len(tables) > 0
                chunk['metadata']['has_pictures'] = len(pictures) > 0

                # Add section titles if in titles-only mode
                if titles_only_mode and section_titles:
                    chunk['metadata']['section_titles'] = ','.join(section_titles)
                    chunk['metadata']['section_count'] = len(section_titles)

            # Create picture chunks
            picture_chunks = []
            for picture in pictures:
                if picture.get('description'):
                    picture_chunk = {
                        'text': f"Picture: {picture.get('caption', 'No caption')}\n\nDescription: {picture['description']}",
                        'metadata': {
                            'well_name': well_name,
                            'filename': filename,
                            'filepath': str(pdf_path),
                            'chunk_type': 'picture',
                            'picture_ref': picture['ref'],
                            'picture_path': picture.get('image_path'),
                            'picture_type': picture.get('classification', {}).get('type') if picture.get('classification') else None,
                            'has_handwriting': picture.get('contains_handwriting', False),
                            'has_text_labels': picture.get('contains_text_labels', False),
                            'section_type': 'visual',
                        }
                    }
                    picture_chunks.append(picture_chunk)

            # Create table chunks
            table_chunks = []
            if tables:
                table_chunks = self.table_chunker.chunk_tables(
                    tables=tables,
                    doc_metadata={
                        'well_name': well_name,
                        'filename': filename
                    }
                )

            all_chunks = chunks + table_chunks + picture_chunks

            print(f"  Created {len(chunks)} text chunks, {len(table_chunks)} table chunks, {len(picture_chunks)} picture chunks")

            if not all_chunks:
                print(f"  [WARN] No chunks created")
                return {'status': 'success', 'chunks': 0, 'parse_time': parse_time}

            # Add embeddings
            texts = [chunk['text'] for chunk in all_chunks]
            embeddings = self.embedding_manager.embed_texts(texts)

            for i, chunk in enumerate(all_chunks):
                chunk['embedding'] = embeddings[i]

            # Add to EXISTING vector store (appends, doesn't replace)
            indexed_count = self.vector_store.add_documents(
                chunks=all_chunks,
                well_name=well_name
            )

            print(f"  [OK] Added {indexed_count} chunks to database")

            # Update results
            self.results['added_pdfs'] += 1
            self.results['added_chunks'] += indexed_count

            return {
                'status': 'success',
                'chunks': indexed_count,
                'parse_time': parse_time,
                'toc_sections': len(toc_sections)
            }

        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

            self.results['errors'].append({
                'well': well_name,
                'file': filename,
                'error': str(e)
            })
            return {'status': 'error', 'error': str(e)}

    def add_well_folder(self, well_folder_path):
        """
        Add all PDFs from a well folder with TOC extraction

        Args:
            well_folder_path: Path to well folder (e.g., "Training data-shared with participants/Well 7")

        Returns:
            Dict with summary statistics
        """
        well_folder = Path(well_folder_path)
        well_name = well_folder.name

        print(f"\n{'='*80}")
        print(f"ADDING NEW WELL: {well_name}")
        print(f"{'='*80}")

        if not well_folder.exists():
            print(f"[ERROR] Folder not found: {well_folder}")
            return {'status': 'error', 'error': 'Folder not found'}

        # Find all PDFs in well folder
        pdfs = list(well_folder.rglob("*.pdf"))

        if not pdfs:
            print(f"[WARN] No PDFs found in {well_folder}")
            return {'status': 'success', 'pdfs': 0, 'chunks': 0}

        print(f"Found {len(pdfs)} PDFs to add\n")

        total_chunks = 0
        errors = 0

        for pdf in pdfs:
            result = self.add_single_pdf(pdf, well_name)
            if result['status'] == 'success':
                total_chunks += result['chunks']
            else:
                errors += 1

        print(f"\n{'='*80}")
        print(f"WELL {well_name} COMPLETE")
        print(f"{'='*80}")
        print(f"  PDFs added: {len(pdfs) - errors}")
        print(f"  Total chunks: {total_chunks}")
        print(f"  Errors: {errors}")

        return {
            'status': 'success',
            'pdfs': len(pdfs) - errors,
            'chunks': total_chunks,
            'errors': errors
        }

    def save_results(self):
        """Save results to JSON"""
        output_file = Path("outputs/toc_enhanced_incremental_indexing_results.json")
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Add new documents with TOC extraction")
    parser.add_argument('--pdf', help="Path to a single PDF to add")
    parser.add_argument('--well', help="Well name (required with --pdf)")
    parser.add_argument('--well-folder', help="Path to well folder to add all PDFs")

    args = parser.parse_args()

    indexer = TOCEnhancedIncrementalIndexer()

    if args.pdf:
        if not args.well:
            print("[ERROR] --well is required when using --pdf")
            sys.exit(1)

        indexer.add_single_pdf(args.pdf, args.well)
        indexer.save_results()

    elif args.well_folder:
        indexer.add_well_folder(args.well_folder)
        indexer.save_results()

    else:
        parser.print_help()
        sys.exit(1)

    print("\n" + "="*80)
    print("TOC-ENHANCED INCREMENTAL INDEXING COMPLETE")
    print("="*80)
    print(f"  Total PDFs added: {indexer.results['added_pdfs']}")
    print(f"  Total chunks added: {indexer.results['added_chunks']}")
    print(f"  Total errors: {len(indexer.results['errors'])}")
    print("="*80)


if __name__ == '__main__':
    main()
