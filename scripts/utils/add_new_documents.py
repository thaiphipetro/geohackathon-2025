"""
Add new documents to existing ChromaDB without re-indexing everything

Usage:
    # Add a single PDF
    python scripts/add_new_documents.py --pdf "Well 5/New_Report.pdf" --well "Well 5"

    # Add an entire new well
    python scripts/add_new_documents.py --well-folder "Training data-shared with participants/Well 9"

    # Add multiple PDFs
    python scripts/add_new_documents.py --pdf-list pdfs_to_add.txt
"""

import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vector_store import TOCEnhancedVectorStore
from embeddings import EmbeddingManager
from chunker import SectionAwareChunker
from table_chunker import TableChunker


class IncrementalIndexer:
    """Add new documents to existing ChromaDB without full re-index"""

    def __init__(self):
        print("="*80)
        print("INCREMENTAL INDEXING - ADD NEW DOCUMENTS")
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

        # Setup Docling with ALL advanced features
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

        # Enhanced OCR
        pipeline_options.do_ocr = True

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

        self.results = {
            'timestamp': datetime.now().isoformat(),
            'added_pdfs': 0,
            'added_chunks': 0,
            'errors': []
        }

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
        Add a single PDF to existing database

        Args:
            pdf_path: Path to PDF file
            well_name: Well identifier (e.g., "Well 5")

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

            # Create section-aware chunks (without TOC for now)
            chunks = self.chunker.chunk_with_section_headers(
                text=markdown,
                toc_sections=[]  # No TOC required for incremental adding
            )

            # Add well and file metadata
            for chunk in chunks:
                chunk['metadata']['well_name'] = well_name
                chunk['metadata']['filename'] = filename
                chunk['metadata']['filepath'] = str(pdf_path)
                chunk['metadata']['has_tables'] = len(tables) > 0
                chunk['metadata']['has_pictures'] = len(pictures) > 0

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
                'parse_time': parse_time
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
        Add all PDFs from a well folder to existing database

        Args:
            well_folder_path: Path to well folder (e.g., "Training data-shared with participants/Well 9")

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
        output_file = Path("outputs/incremental_indexing_results.json")
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Add new documents to existing ChromaDB")
    parser.add_argument('--pdf', help="Path to a single PDF to add")
    parser.add_argument('--well', help="Well name (required with --pdf)")
    parser.add_argument('--well-folder', help="Path to well folder to add all PDFs")
    parser.add_argument('--pdf-list', help="Path to text file with list of PDFs to add")

    args = parser.parse_args()

    indexer = IncrementalIndexer()

    if args.pdf:
        if not args.well:
            print("[ERROR] --well is required when using --pdf")
            sys.exit(1)

        indexer.add_single_pdf(args.pdf, args.well)
        indexer.save_results()

    elif args.well_folder:
        indexer.add_well_folder(args.well_folder)
        indexer.save_results()

    elif args.pdf_list:
        # Read list of PDFs from file
        with open(args.pdf_list, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Format: pdf_path,well_name
                parts = line.split(',')
                if len(parts) == 2:
                    pdf_path, well_name = parts
                    indexer.add_single_pdf(pdf_path.strip(), well_name.strip())

        indexer.save_results()

    else:
        parser.print_help()
        sys.exit(1)

    print("\n" + "="*80)
    print("INCREMENTAL INDEXING COMPLETE")
    print("="*80)
    print(f"  Total PDFs added: {indexer.results['added_pdfs']}")
    print(f"  Total chunks added: {indexer.results['added_chunks']}")
    print(f"  Total errors: {len(indexer.results['errors'])}")
    print("="*80)


if __name__ == '__main__':
    main()
