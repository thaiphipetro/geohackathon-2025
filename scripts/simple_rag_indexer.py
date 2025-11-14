"""
Simple RAG Indexer - Index Comprehensive Parser Results to ChromaDB

Reads JSON results from parse_all_wells_comprehensive.py and indexes:
1. Text chunks (hierarchical)
2. Tables (as markdown)
3. Pictures with raw OCR text (no LLM processing)

Usage:
    python scripts/simple_rag_indexer.py
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional
import time
import re

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# LangChain imports
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


class SimpleRAGIndexer:
    """Simple indexer for comprehensive parser results"""

    def __init__(
        self,
        embedding_model: str = "nomic-ai/nomic-embed-text-v1.5",
        collection_name: str = "well_reports_toc_aware",
        chroma_persist_dir: str = "./chroma_db_toc_aware",
        toc_database_path: Optional[str] = None
    ):
        """Initialize indexer with embeddings, vector store, and TOC database"""
        print(f"[INIT] Loading embeddings: {embedding_model}")

        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu', 'trust_remote_code': True},
            encode_kwargs={'normalize_embeddings': True}
        )

        print(f"[INIT] Creating ChromaDB at: {chroma_persist_dir}")
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=chroma_persist_dir
        )

        # Load TOC database for section type mapping
        if toc_database_path is None:
            toc_database_path = str(project_root / "outputs" / "exploration" / "toc_database_multi_doc_full.json")

        print(f"[INIT] Loading TOC database: {toc_database_path}")
        self.toc_database = self._load_toc_database(toc_database_path)
        print(f"[INIT] TOC database loaded with {sum(len(docs) for docs in self.toc_database.values())} PDFs across {len(self.toc_database)} wells")

        # Size limit for chunks (10KB = 10,000 chars)
        self.max_chunk_size = 10000

    def _load_toc_database(self, toc_path: str) -> Dict:
        """Load TOC database from JSON"""
        try:
            with open(toc_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Failed to load TOC database: {e}")
            return {}

    def _map_heading_to_section_type(self, pdf_filename: str, heading: str, page: Optional[int] = None) -> Optional[str]:
        """
        Map a heading to its section type using TOC database with intelligent fallbacks

        Args:
            pdf_filename: PDF filename to look up in TOC database
            heading: Section heading from chunk metadata
            page: Optional page number for more precise matching

        Returns:
            Section type (e.g., 'casing', 'survey', 'lithology') or None
        """
        if not heading or not self.toc_database:
            return None

        # Find matching document in TOC database
        matched_doc = None
        for well_name, documents in self.toc_database.items():
            for doc in documents:
                if doc['filename'] == pdf_filename:
                    matched_doc = doc
                    break
            if matched_doc:
                break

        if not matched_doc:
            return None

        toc_entries = matched_doc.get('toc', [])

        # Strategy 1: Direct fuzzy match (original method)
        for toc_entry in toc_entries:
            # Match by heading (fuzzy match - lowercase and strip)
            if heading.lower().strip() in toc_entry['title'].lower().strip() or \
               toc_entry['title'].lower().strip() in heading.lower().strip():
                # If page provided, verify it matches
                if page is not None and toc_entry.get('page') is not None:
                    if abs(page - toc_entry['page']) <= 1:  # Allow 1 page difference
                        return toc_entry.get('type')
                else:
                    return toc_entry.get('type')

        # Strategy 2: Number prefix matching (e.g., "2.1" inherits from "2")
        # Extract leading number from heading
        heading_match = re.match(r'^(\d+(?:\.\d+)?)\s+', heading)
        if heading_match:
            heading_number = heading_match.group(1)
            # Find TOC entry with matching or parent number
            for toc_entry in toc_entries:
                toc_match = re.match(r'^(\d+(?:\.\d+)?)', toc_entry.get('number', ''))
                if toc_match:
                    toc_number = toc_match.group(1)
                    # Check if heading number starts with TOC number
                    if heading_number.startswith(toc_number):
                        return toc_entry.get('type')

        # Strategy 3: Page-based inference (find section containing this page)
        if page is not None:
            # Sort TOC entries by page
            sorted_toc = sorted(
                [e for e in toc_entries if e.get('page') is not None],
                key=lambda x: x['page']
            )
            # Find the section this page belongs to
            for i, toc_entry in enumerate(sorted_toc):
                start_page = toc_entry['page']
                # Determine end page (start of next section or +50 pages)
                end_page = sorted_toc[i+1]['page'] if i+1 < len(sorted_toc) else start_page + 50
                if start_page <= page < end_page:
                    return toc_entry.get('type')

        # Strategy 4: Keyword-based inference
        heading_lower = heading.lower()
        keyword_map = {
            'casing': ['casing', 'cement', 'tubular', 'liner'],
            'geology': ['geology', 'lithology', 'formation', 'reservoir', 'stratigraphy'],
            'drilling_operations': ['drilling', 'mud', 'fluid', 'circulation', 'bit'],
            'completion': ['completion', 'perforation', 'production', 'testing'],
            'survey': ['survey', 'trajectory', 'directional', 'inclination'],
            'well_identification': ['well data', 'location', 'coordinates', 'operator'],
            'appendices': ['appendix', 'appendices', 'attachment']
        }

        for section_type, keywords in keyword_map.items():
            if any(kw in heading_lower for kw in keywords):
                return section_type

        return None

    def _split_large_chunk(self, text: str, max_size: int = 10000) -> List[str]:
        """
        Split large chunks while preserving semantic boundaries

        Splits at:
        1. Double newlines (paragraphs)
        2. Single newlines (sentences)
        3. Periods (last resort)

        Args:
            text: Text to split
            max_size: Maximum chunk size in characters

        Returns:
            List of text chunks
        """
        if len(text) <= max_size:
            return [text]

        chunks = []
        remaining = text

        while len(remaining) > max_size:
            # Try to split at paragraph boundary
            split_pos = remaining[:max_size].rfind('\n\n')

            if split_pos == -1:
                # Try to split at sentence boundary (newline)
                split_pos = remaining[:max_size].rfind('\n')

            if split_pos == -1:
                # Try to split at period + space
                split_pos = remaining[:max_size].rfind('. ')
                if split_pos != -1:
                    split_pos += 1  # Include the period

            if split_pos == -1:
                # Last resort: split at max_size
                split_pos = max_size

            # Extract chunk and update remaining
            chunk = remaining[:split_pos].strip()
            if chunk:
                chunks.append(chunk)
            remaining = remaining[split_pos:].strip()

        # Add final chunk
        if remaining:
            chunks.append(remaining)

        return chunks

    def load_well_json(self, json_path: Path) -> Dict:
        """Load comprehensive parser JSON"""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_documents_from_json(self, data: Dict, well_name: str) -> List[Document]:
        """
        Convert JSON to LangChain Documents with TOC-aware chunking

        Creates 3 types of documents:
        1. Text chunks (from hierarchical chunker) with section type mapping and size control
        2. Tables (markdown format)
        3. Pictures with raw OCR text

        Features:
        - Maps section titles to section types using TOC database
        - Splits oversized chunks (>10KB) while preserving semantic boundaries
        - Adds section_type metadata for filtering
        """
        documents = []
        pdf_filename = data.get('filename', 'unknown')
        split_stats = {'total_chunks': 0, 'split_chunks': 0, 'original_large': 0}

        # 1. Text chunks with TOC-aware chunking
        for i, chunk in enumerate(data.get('chunks', [])):
            # Extract section title from headings
            meta = chunk.get('meta', {})
            headings = meta.get('headings', [])
            section_title = headings[0] if headings else ''

            # Extract page number
            page_no = None
            if meta.get('doc_items'):
                try:
                    page_no = meta['doc_items'][0]['prov'][0]['page_no']
                except (KeyError, IndexError):
                    pass

            # Map heading to section type using TOC database
            section_type = self._map_heading_to_section_type(pdf_filename, section_title, page_no)

            # Get chunk text
            chunk_text = chunk.get('text', '')
            split_stats['total_chunks'] += 1

            # Check if chunk is too large and split if needed
            if len(chunk_text) > self.max_chunk_size:
                split_stats['original_large'] += 1
                sub_chunks = self._split_large_chunk(chunk_text, self.max_chunk_size)
                split_stats['split_chunks'] += len(sub_chunks)

                # Create document for each sub-chunk
                for sub_idx, sub_chunk in enumerate(sub_chunks):
                    doc = Document(
                        page_content=sub_chunk,
                        metadata={
                            'source_type': 'text_chunk',
                            'well_name': well_name,
                            'pdf_filename': pdf_filename,
                            'chunk_index': i,
                            'sub_chunk_index': sub_idx,
                            'section_title': section_title,
                            'section_type': section_type,
                            'page': page_no,
                            'is_split': True
                        }
                    )
                    documents.append(doc)
            else:
                # Original chunk is within size limit
                doc = Document(
                    page_content=chunk_text,
                    metadata={
                        'source_type': 'text_chunk',
                        'well_name': well_name,
                        'pdf_filename': pdf_filename,
                        'chunk_index': i,
                        'section_title': section_title,
                        'section_type': section_type,
                        'page': page_no,
                        'is_split': False
                    }
                )
                documents.append(doc)

        # Print split statistics
        if split_stats['original_large'] > 0:
            print(f"[SPLIT] {split_stats['original_large']} large chunks split into {split_stats['split_chunks']} sub-chunks")

        # 2. Tables (as markdown)
        for table in data.get('tables', []):
            markdown = table.get('markdown', '')
            if not markdown:
                continue

            doc = Document(
                page_content=markdown,
                metadata={
                    'source_type': 'table',
                    'well_name': well_name,
                    'pdf_filename': pdf_filename,
                    'table_ref': table.get('ref', ''),
                    'num_rows': table.get('num_rows', 0),
                    'num_cols': table.get('num_cols', 0),
                    'page': table.get('page', None)
                }
            )
            documents.append(doc)

        # 3. Pictures with raw OCR text (no LLM processing!)
        for picture in data.get('pictures', []):
            ocr_text = picture.get('ocr_text', '')
            if not ocr_text or len(ocr_text) < 10:
                continue  # Skip empty OCR

            doc = Document(
                page_content=ocr_text,
                metadata={
                    'source_type': 'picture_ocr',
                    'well_name': well_name,
                    'pdf_filename': pdf_filename,
                    'picture_ref': picture.get('ref', ''),
                    'file_size_kb': picture.get('file_size_kb', 0),
                    'page': picture.get('page', None),
                    'width': picture.get('width', None),
                    'height': picture.get('height', None)
                }
            )
            documents.append(doc)

        return documents

    def index_well(self, well_num: int) -> Dict:
        """Index a single well"""
        print(f"\n[WELL {well_num}] Processing...")

        well_dir = project_root / "outputs" / "all_wells_comprehensive" / f"well_{well_num}"

        if not well_dir.exists():
            print(f"[SKIP] Directory not found: {well_dir}")
            return {'success': False, 'error': 'Directory not found'}

        # Find JSON file
        json_files = list(well_dir.glob("*_results.json"))

        if not json_files:
            print(f"[SKIP] No JSON results found in {well_dir}")
            return {'success': False, 'error': 'No JSON results'}

        json_path = json_files[0]
        print(f"[LOAD] {json_path.name}")

        # Load JSON
        data = self.load_well_json(json_path)

        # Create documents
        documents = self.create_documents_from_json(
            data=data,
            well_name=f"well_{well_num}"
        )

        print(f"[CONVERT] Created {len(documents)} documents")
        print(f"  - Text chunks: {sum(1 for d in documents if d.metadata['source_type'] == 'text_chunk')}")
        print(f"  - Tables: {sum(1 for d in documents if d.metadata['source_type'] == 'table')}")
        print(f"  - Pictures with OCR: {sum(1 for d in documents if d.metadata['source_type'] == 'picture_ocr')}")

        # Index to ChromaDB in batches
        batch_size = 100
        indexed = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            self.vectorstore.add_documents(batch)
            indexed += len(batch)
            print(f"[INDEX] {indexed}/{len(documents)} documents")

        return {
            'success': True,
            'num_documents': len(documents),
            'num_text_chunks': sum(1 for d in documents if d.metadata['source_type'] == 'text_chunk'),
            'num_tables': sum(1 for d in documents if d.metadata['source_type'] == 'table'),
            'num_pictures': sum(1 for d in documents if d.metadata['source_type'] == 'picture_ocr')
        }

    def index_all_wells(self) -> Dict:
        """Index all 8 wells"""
        print("=" * 80)
        print("SIMPLE RAG INDEXING - Raw OCR Approach")
        print("=" * 80)

        start_time = time.time()
        stats = {
            'total_documents': 0,
            'total_text_chunks': 0,
            'total_tables': 0,
            'total_pictures': 0,
            'wells_processed': 0,
            'wells_skipped': 0
        }

        for well_num in range(1, 9):
            result = self.index_well(well_num)

            if result.get('success'):
                stats['wells_processed'] += 1
                stats['total_documents'] += result.get('num_documents', 0)
                stats['total_text_chunks'] += result.get('num_text_chunks', 0)
                stats['total_tables'] += result.get('num_tables', 0)
                stats['total_pictures'] += result.get('num_pictures', 0)
            else:
                stats['wells_skipped'] += 1

        elapsed = time.time() - start_time

        print("\n" + "=" * 80)
        print("INDEXING COMPLETE")
        print("=" * 80)
        print(f"Processing time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        print(f"Wells processed: {stats['wells_processed']}/8")
        print(f"Total documents indexed: {stats['total_documents']}")
        print(f"  - Text chunks: {stats['total_text_chunks']}")
        print(f"  - Tables: {stats['total_tables']}")
        print(f"  - Pictures with raw OCR: {stats['total_pictures']}")

        return stats


def main():
    """Index all comprehensive parser results"""
    indexer = SimpleRAGIndexer()
    stats = indexer.index_all_wells()

    # Save stats
    output_file = project_root / "outputs" / "rag_indexing_stats.json"
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"\n[SAVED] Statistics: {output_file}")
    print("\nReady for RAG queries!")


if __name__ == '__main__':
    main()
