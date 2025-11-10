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

        # Setup Docling for full PDF parsing
        from docling.document_converter import DocumentConverter
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        print("[OK] Docling converter ready")

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
            # Parse PDF with Docling
            start_time = time.time()

            result = self.converter.convert(str(pdf_path))
            markdown = result.document.export_to_markdown()
            tables = result.document.tables if hasattr(result.document, 'tables') else []

            parse_time = time.time() - start_time
            print(f"  Parsed in {parse_time:.1f}s")

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

            all_chunks = chunks + table_chunks

            print(f"  Created {len(chunks)} text chunks, {len(table_chunks)} table chunks")

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
