"""
Re-index all wells using TOC-enhanced chunking

This script:
1. Loads TOC analysis data (14 PDFs)
2. For each PDF:
   - Parse with TOC-enhanced parser
   - Create section-aware chunks
   - Add metadata from TOC
   - Index to ChromaDB
3. Reports results and statistics
"""

import sys
import json
import time
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vector_store import TOCEnhancedVectorStore
from embeddings import EmbeddingManager
from chunker import SectionAwareChunker
from table_chunker import TableChunker


class TOCEnhancedReIndexer:
    """Re-index all wells with TOC enhancement"""

    def __init__(self):
        print("="*80)
        print("INITIALIZING RE-INDEXING SYSTEM")
        print("="*80)

        self.vector_store = TOCEnhancedVectorStore()
        print("[OK] Vector store ready")

        self.embedding_manager = EmbeddingManager()
        print("[OK] Embedding manager ready")

        self.chunker = SectionAwareChunker(chunk_size=1000, overlap=200)
        print("[OK] Section-aware chunker ready")

        self.table_chunker = TableChunker()
        print("[OK] Table chunker ready")

        # Setup Docling with ALL advanced features for comprehensive extraction
        from docling.document_converter import DocumentConverter
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption
        from docling.datamodel.pipeline_options import TableFormerMode

        pipeline_options = PdfPipelineOptions()

        # 1. TABLEFORMER ACCURATE MODE - Extract ALL tables completely
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        pipeline_options.table_structure_options.do_cell_matching = False  # Better for merged cells

        # 2. ENHANCED OCR - Better for scanned documents
        pipeline_options.do_ocr = True

        # 3. PICTURE EXTRACTION - Extract diagrams and schematics
        pipeline_options.generate_picture_images = True
        pipeline_options.images_scale = 2.0  # Higher resolution (better VLM accuracy, actually faster!)
        pipeline_options.do_picture_classification = True

        # 4. PICTURE DESCRIPTION - SmolVLM-256M for diagram OCR and annotations
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

        # Load multi-document TOC database for section metadata
        toc_database_path = Path("outputs/exploration/toc_database_multi_doc_full.json")
        with open(toc_database_path, 'r') as f:
            toc_database = json.load(f)

        # Flatten to list format for compatibility with existing code
        self.toc_analysis = []
        for well_name, documents in toc_database.items():
            for doc in documents:
                pdf_data = {
                    'well': well_name,
                    'filename': doc['filename'],
                    'filepath': doc.get('filepath', ''),
                    'toc_entries': doc.get('toc', []),  # Map 'toc' to 'toc_entries'
                    'toc_lines': len(doc.get('toc', [])),
                    'pub_date': doc.get('pub_date'),
                    'key_sections': doc.get('key_sections', {})
                }
                self.toc_analysis.append(pdf_data)

        print(f"[OK] Loaded multi-document TOC database: {len(self.toc_analysis)} PDFs from {len(toc_database)} wells")

        self.results = {
            'timestamp': datetime.now().isoformat(),
            'total_pdfs': 0,
            'total_chunks': 0,
            'total_errors': 0,
            'wells': {},
            'errors': []
        }

    def _extract_pictures(self, doc, well_name, filename):
        """
        Extract pictures from document and save to filesystem
        Returns list of picture metadata for ChromaDB
        """
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
                    # Create safe filename from ref
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
                    # Classification (schematic, chart, photo, etc.)
                    if isinstance(annotation, PictureClassificationData):
                        if annotation.predicted_classes:
                            top_class = annotation.predicted_classes[0]
                            picture_data['classification'] = {
                                'type': top_class.class_name,
                                'confidence': top_class.confidence,
                            }

                    # VLM Description
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

    def get_pdf_path(self, well, filename, filepath_hint=None):
        """Find PDF path for a given well and filename"""
        # If filepath hint is provided from database, use it first
        if filepath_hint:
            hint_path = Path(filepath_hint)
            if hint_path.exists():
                return hint_path

        # Fallback: search common locations
        base_dir = Path("Training data-shared with participants")

        # Try common locations
        locations = [
            base_dir / well / "Well report" / "EOWR" / filename,
            base_dir / well / "Well report" / filename,
            base_dir / well / filename,
        ]

        for path in locations:
            if path.exists():
                return path

        return None

    def index_pdf(self, pdf_data):
        """Index a single PDF with TOC enhancement"""
        well = pdf_data['well']
        filename = pdf_data['filename']

        print(f"\n[{well}] Processing: {filename}")
        print(f"  TOC entries: {pdf_data.get('toc_lines', 0)}")

        # Find PDF path (with filepath hint from database)
        pdf_path = self.get_pdf_path(well, filename, filepath_hint=pdf_data.get('filepath'))

        if not pdf_path:
            print(f"  [ERROR] PDF not found")
            self.results['errors'].append({
                'well': well,
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

            # Extract pictures and save to filesystem
            pictures = self._extract_pictures(doc, well, filename)

            parse_time = time.time() - start_time
            print(f"  Parsed in {parse_time:.1f}s")
            print(f"  Extracted {len(tables)} tables, {len(pictures)} pictures")

            # Build TOC sections from TOC analysis data
            toc_sections = []
            if 'toc_entries' in pdf_data:
                for entry in pdf_data['toc_entries']:
                    toc_sections.append({
                        'section_number': entry.get('number', ''),
                        'title': entry.get('title', ''),
                        'page': entry.get('page', 0),
                        'type': entry.get('type', 'unknown')
                    })

            # Create section-aware chunks
            chunks = self.chunker.chunk_with_section_headers(
                text=markdown,
                toc_sections=toc_sections
            )

            # Add well and file metadata to each chunk
            for chunk in chunks:
                chunk['metadata']['well_name'] = well
                chunk['metadata']['filename'] = filename
                chunk['metadata']['filepath'] = str(pdf_path)

                # Add enriched metadata flags
                chunk['metadata']['has_tables'] = len(tables) > 0
                chunk['metadata']['has_pictures'] = len(pictures) > 0

            # Create picture-specific chunks for VLM descriptions
            picture_chunks = []
            for picture in pictures:
                if picture.get('description'):
                    # Create chunk with VLM description
                    picture_chunk = {
                        'text': f"Picture: {picture.get('caption', 'No caption')}\n\nDescription: {picture['description']}",
                        'metadata': {
                            'well_name': well,
                            'filename': filename,
                            'filepath': str(pdf_path),
                            'chunk_type': 'picture',
                            'picture_ref': picture['ref'],
                            'picture_path': picture.get('image_path'),
                            'picture_type': picture.get('classification', {}).get('type') if picture.get('classification') else None,
                            'has_handwriting': picture.get('contains_handwriting', False),
                            'has_text_labels': picture.get('contains_text_labels', False),
                            'section_number': None,
                            'section_title': None,
                            'section_type': 'visual',
                        }
                    }
                    picture_chunks.append(picture_chunk)

            # Create table chunks if tables exist
            table_chunks = []
            if tables:
                table_chunks = self.table_chunker.chunk_tables(
                    tables=tables,
                    doc_metadata={
                        'well_name': well,
                        'filename': filename
                    }
                )

            all_chunks = chunks + table_chunks + picture_chunks

            print(f"  Created {len(chunks)} text chunks, {len(table_chunks)} table chunks, {len(picture_chunks)} picture chunks")

            if not all_chunks:
                print(f"  [WARN] No chunks created")
                return {'status': 'success', 'chunks': 0, 'parse_time': parse_time}

            # Add embeddings to chunks
            texts = [chunk['text'] for chunk in all_chunks]
            embeddings = self.embedding_manager.embed_texts(texts)

            # Add embeddings to chunks (already in list format)
            for i, chunk in enumerate(all_chunks):
                chunk['embedding'] = embeddings[i]

            # Index to vector store
            indexed_count = self.vector_store.add_documents(
                chunks=all_chunks,
                well_name=well
            )

            print(f"  [OK] Indexed {indexed_count} chunks")

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
                'well': well,
                'file': filename,
                'error': str(e)
            })
            return {'status': 'error', 'error': str(e)}

    def reindex_all(self):
        """Re-index all PDFs from TOC analysis"""
        print("\n" + "="*80)
        print("RE-INDEXING ALL WELLS WITH TOC ENHANCEMENT")
        print("="*80)
        print(f"\nFound {len(self.toc_analysis)} PDFs with TOC data\n")

        # Index each PDF
        for pdf_data in tqdm(self.toc_analysis, desc="Indexing PDFs"):
            well = pdf_data['well']

            # Initialize well stats if needed
            if well not in self.results['wells']:
                self.results['wells'][well] = {
                    'pdfs': 0,
                    'chunks': 0,
                    'errors': 0
                }

            # Index the PDF
            result = self.index_pdf(pdf_data)

            # Update stats
            self.results['wells'][well]['pdfs'] += 1
            self.results['total_pdfs'] += 1

            if result['status'] == 'success':
                self.results['wells'][well]['chunks'] += result['chunks']
                self.results['total_chunks'] += result['chunks']
            else:
                self.results['wells'][well]['errors'] += 1
                self.results['total_errors'] += 1

        # Print summary
        self.print_summary()

        # Save results
        self.save_results()

    def print_summary(self):
        """Print indexing summary"""
        print("\n" + "="*80)
        print("RE-INDEXING COMPLETE")
        print("="*80)

        print(f"\nTotal PDFs indexed:  {self.results['total_pdfs']}")
        print(f"Total chunks created: {self.results['total_chunks']}")
        print(f"Total errors:        {self.results['total_errors']}")

        print("\nPer-Well Summary:")
        print("-"*80)
        for well, stats in sorted(self.results['wells'].items()):
            status = "[OK]" if stats['errors'] == 0 else "[WARN]"
            print(f"  {status} {well}: {stats['pdfs']} PDFs, {stats['chunks']} chunks")

        if self.results['errors']:
            print("\nErrors:")
            print("-"*80)
            for error in self.results['errors']:
                print(f"  [{error['well']}] {error['file']}: {error['error']}")

        print("="*80)

    def save_results(self):
        """Save results to JSON"""
        output_file = Path("outputs/reindexing_results.json")
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to: {output_file}")


if __name__ == '__main__':
    reindexer = TOCEnhancedReIndexer()
    reindexer.reindex_all()
