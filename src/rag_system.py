"""
RAG System for Geothermal Well Reports
Complete pipeline: Query → Intent → TOC → Parse → Chunk → Embed → Retrieve → LLM
"""

import os
import json
import glob
from typing import List, Dict, Optional
import ollama

from query_intent import QueryIntentMapper
from toc_parser import TOCEnhancedParser
from chunker import SectionAwareChunker
from table_chunker import TableChunker
from embeddings import EmbeddingManager
from vector_store import TOCEnhancedVectorStore


class WellReportRAG:
    """
    TOC-enhanced RAG system for well reports

    Architecture:
        1. Query Intent Mapper: "well depth" → ['depth', 'borehole']
        2. TOC Database Lookup: Get pages [6, 20] for those sections
        3. Page-Targeted Parser: Parse ONLY 2 pages (25x faster)
        4. Section-Aware Chunker: Prepend "Section 2.1 Depths\n\n..."
        5. Nomic Embeddings: Generate 768-dim vectors
        6. ChromaDB: Store with metadata {section: '2.1', type: 'depth'}
        7. Retrieval: where={'section_type': {'$in': ['depth']}}
        8. Ollama LLM: Generate answer with citations

    Example:
        rag = WellReportRAG()
        rag.index_well("Well 5", toc_sections)
        answer = rag.query("What is the well depth?", well_name="Well 5")
    """

    def __init__(self,
                 toc_database_path: str = "outputs/exploration/toc_database.json",
                 data_dir: str = None,
                 chroma_host: str = None,
                 chroma_port: int = None,
                 ollama_host: str = None,
                 model_name: str = "llama3.2:3b"):
        """
        Initialize RAG system

        Args:
            toc_database_path: Path to TOC database JSON
            data_dir: Directory containing well data
            chroma_host: ChromaDB server host
            chroma_port: ChromaDB server port
            ollama_host: Ollama server host
            model_name: Ollama model name
        """
        print("="*80)
        print("INITIALIZING RAG SYSTEM")
        print("="*80)

        # Load TOC database
        print(f"\n[LOAD] Loading TOC database from {toc_database_path}...")
        with open(toc_database_path, 'r') as f:
            self.toc_database = json.load(f)
        print(f"[OK] Loaded TOC database: {len(self.toc_database)} wells")

        # Auto-detect data directory (Docker vs local)
        if data_dir is None:
            # Check if we're in Docker
            if os.path.exists('/app/data'):
                data_dir = '/app/data'
                print(f"[OK] Detected Docker environment: data_dir = {data_dir}")
            else:
                data_dir = 'Training data-shared with participants'
                print(f"[OK] Detected local environment: data_dir = {data_dir}")

        self.data_dir = data_dir

        # Initialize components
        print("\n[INIT] Initializing components...")

        self.intent_mapper = QueryIntentMapper()
        print("[OK] Query intent mapper ready")

        self.parser = TOCEnhancedParser(toc_database_path)
        print("[OK] TOC-enhanced parser ready")

        self.chunker = SectionAwareChunker(chunk_size=1000, overlap=200)
        print("[OK] Section-aware chunker ready")

        self.table_chunker = TableChunker()
        print("[OK] Table chunker ready")

        self.embedding_manager = EmbeddingManager()
        print("[OK] Embedding manager ready")

        # Use environment variables if not provided
        chroma_host = chroma_host or os.getenv('CHROMA_HOST', 'localhost')
        chroma_port = chroma_port or int(os.getenv('CHROMA_PORT', 8000))

        self.vector_store = TOCEnhancedVectorStore(
            collection_name="well_reports",
            chroma_host=chroma_host,
            chroma_port=chroma_port
        )
        print("[OK] Vector store ready")

        # Ollama setup
        self.ollama_host = ollama_host or os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.model_name = model_name

        # Set Ollama client host if needed
        if self.ollama_host:
            os.environ['OLLAMA_HOST'] = self.ollama_host

        print(f"[OK] Ollama configured: {self.ollama_host} (model: {model_name})")

        print("\n" + "="*80)
        print("[OK] RAG SYSTEM READY")
        print("="*80)

    def index_well(self, well_name: str, reindex: bool = False) -> Dict:
        """
        Index a well's EOWR document

        Args:
            well_name: Well identifier (e.g., "Well 5")
            reindex: If True, delete existing chunks before reindexing

        Returns:
            {
                'well_name': str,
                'chunks_indexed': int,
                'sections_parsed': int,
                'pages_processed': List[int]
            }
        """
        print(f"\n{'='*80}")
        print(f"INDEXING {well_name}")
        print(f"{'='*80}")

        # Get TOC entry for this well
        if well_name not in self.toc_database:
            raise ValueError(f"Well '{well_name}' not found in TOC database")

        well_data = self.toc_database[well_name]

        # Build TOC sections with type information from key_sections
        toc_sections = []
        section_to_type = {}  # Map section number -> type

        # First, build mapping from key_sections
        if 'key_sections' in well_data:
            for section_type, sections in well_data['key_sections'].items():
                for section in sections:
                    section_to_type[section['number']] = section_type

        # Now enrich toc entries with type information
        for entry in well_data['toc']:
            enriched_entry = entry.copy()
            if entry['number'] in section_to_type:
                enriched_entry['type'] = section_to_type[entry['number']]
            toc_sections.append(enriched_entry)

        # Get PDF path - try multiple locations
        pdf_filename = well_data['filename']

        # Try with EOWR subdirectory first
        pdf_path = os.path.join(self.data_dir, well_name, "Well report", "EOWR", pdf_filename)

        # If not found, try directly in "Well report" (Docker environment)
        if not os.path.exists(pdf_path):
            pdf_path = os.path.join(self.data_dir, well_name, "Well report", pdf_filename)

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found. Tried:\n  - {os.path.join(self.data_dir, well_name, 'Well report', 'EOWR', pdf_filename)}\n  - {os.path.join(self.data_dir, well_name, 'Well report', pdf_filename)}")

        print(f"[FILE] PDF: {pdf_filename}")
        print(f" TOC entries: {len(toc_sections)}")

        # Delete existing chunks if reindexing
        if reindex:
            print(f"\n  Reindexing: deleting existing chunks...")
            self.vector_store.delete_well(well_name)

        # Get all unique pages from TOC
        all_pages = sorted(set([section['page'] for section in toc_sections]))
        print(f"\n[FILE] Target pages: {all_pages[:10]}{'...' if len(all_pages) > 10 else ''} ({len(all_pages)} pages)")

        # Parse targeted pages
        print(f"\n Parsing {len(all_pages)} pages...")
        parsed = self.parser.parse_targeted_pages(pdf_path, all_pages, well_name)

        # Chunk with section headers (text chunks)
        print(f"\n  Chunking text with section context...")
        text_chunks = self.chunker.chunk_with_section_headers(parsed['text'], toc_sections)
        print(f"[OK] Created {len(text_chunks)} text chunks")

        # Add document metadata to text chunks
        doc_metadata = {
            'well_name': well_name,
            'document_name': os.path.basename(pdf_path)
        }
        for chunk in text_chunks:
            chunk['metadata'].update(doc_metadata)
            chunk['metadata']['chunk_type'] = 'text'  # Mark as text chunk

        # Chunk tables separately
        print(f"\n[STATS] Chunking tables...")
        table_chunks = []
        if 'tables' in parsed and parsed['tables']:
            # Group tables by section (approximate based on page number)
            for table in parsed['tables']:
                # Find matching section for this table
                matching_section = None
                if hasattr(table, 'page'):
                    for section in toc_sections:
                        if section.get('page') == table.page:
                            matching_section = section
                            break

                # Chunk this table
                table_chunk_list = self.table_chunker.chunk_tables(
                    tables=[table],
                    section_info=matching_section,
                    doc_metadata=doc_metadata
                )
                table_chunks.extend(table_chunk_list)

            print(f"[OK] Created {len(table_chunks)} table chunks from {len(parsed['tables'])} tables")
        else:
            print(f"[INFO]  No tables found in document")

        # Combine text and table chunks
        chunks = text_chunks + table_chunks
        print(f"[OK] Total chunks: {len(chunks)} ({len(text_chunks)} text + {len(table_chunks)} tables)")

        # Generate embeddings
        print(f"\n[EMBED] Generating embeddings...")
        chunks_with_embeddings = self.embedding_manager.embed_chunks(chunks)
        print(f"[OK] Embeddings generated")

        # Add to vector store
        print(f"\n[SAVE] Adding to vector store...")
        num_added = self.vector_store.add_documents(chunks_with_embeddings, well_name)

        print(f"\n{'='*80}")
        print(f"[OK] {well_name} INDEXED: {num_added} chunks")
        print(f"{'='*80}")

        return {
            'well_name': well_name,
            'chunks_indexed': num_added,
            'sections_parsed': len(toc_sections),
            'pages_processed': all_pages
        }

    def query(self,
             query: str,
             well_name: Optional[str] = None,
             n_results: int = 5,
             temperature: float = 0.1) -> Dict:
        """
        Query the RAG system

        Args:
            query: Natural language query
            well_name: Well to search (None = search all wells)
            n_results: Number of context chunks to retrieve
            temperature: LLM temperature (0.1 = factual, 0.7 = creative)

        Returns:
            {
                'query': str,
                'answer': str,
                'sources': [{'section': ..., 'page': ..., 'text': ...}],
                'well_name': str,
                'section_types_used': List[str]
            }
        """
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print(f"{'='*80}")

        # Step 1: Map query to section types
        print("\n[TARGET] Mapping query to section types...")
        section_types = self.intent_mapper.get_section_types(query)
        print(f"[OK] Target sections: {', '.join(section_types)}")

        # Step 2: Generate query embedding
        print("\n[EMBED] Generating query embedding...")
        query_embedding = self.embedding_manager.embed_text(query)

        # Step 3: Retrieve relevant chunks
        print(f"\n Retrieving top {n_results} chunks...")
        if well_name:
            results = self.vector_store.query_with_section_filter(
                query_embedding=query_embedding,
                well_name=well_name,
                section_types=section_types,
                n_results=n_results
            )
        else:
            results = self.vector_store.query_all_wells(
                query_embedding=query_embedding,
                section_types=section_types,
                n_results=n_results
            )

        print(f"[OK] Retrieved {len(results['documents'])} chunks")

        if not results['documents']:
            print("[WARN]  No relevant chunks found")
            return {
                'query': query,
                'answer': "I couldn't find any relevant information to answer this query.",
                'sources': [],
                'well_name': well_name,
                'section_types_used': section_types
            }

        # Step 4: Build context from retrieved chunks
        context_parts = []
        sources = []

        for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
            section_num = meta.get('section_number', 'N/A')
            section_title = meta.get('section_title', 'N/A')
            page = meta.get('page', 'N/A')
            well = meta.get('well_name', 'N/A')

            context_parts.append(f"[Source {i+1}] Section {section_num} ({section_title}) - Page {page} - {well}\n{doc}\n")

            sources.append({
                'source_index': i + 1,
                'section_number': section_num,
                'section_title': section_title,
                'page': page,
                'well_name': well,
                'text': doc[:200] + '...' if len(doc) > 200 else doc
            })

        context = "\n---\n".join(context_parts)

        # Step 5: Generate answer with Ollama
        print(f"\n[LLM] Generating answer with {self.model_name}...")

        prompt = f"""You are an expert geothermal engineer analyzing well completion reports.

Answer the following question based ONLY on the provided context. Be factual and precise.

IMPORTANT: Always cite your sources using [Source X] notation.

Question: {query}

Context:
{context}

Answer (with citations):"""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': 'You are a factual geothermal engineering assistant. Always cite sources.'},
                    {'role': 'user', 'content': prompt}
                ],
                options={
                    'temperature': temperature,
                    'num_predict': 500
                }
            )

            answer = response['message']['content'].strip()
            print(f"[OK] Answer generated ({len(answer)} chars)")

        except Exception as e:
            print(f"[ERROR] Ollama error: {e}")
            answer = f"Error generating answer: {e}"

        print(f"\n{'='*80}")
        print(f"[OK] QUERY COMPLETE")
        print(f"{'='*80}")

        return {
            'query': query,
            'answer': answer,
            'sources': sources,
            'well_name': well_name or 'all wells',
            'section_types_used': section_types
        }

    def get_indexed_wells(self) -> List[str]:
        """Get list of wells available in TOC database"""
        return list(self.toc_database.keys())

    def index_well_reports(self, well_name: str, reindex: bool = False) -> Dict:
        """
        Scan and index all PDFs in Well report/ folder

        This method:
        1. Scans Well report/ folder for all PDFs
        2. For each PDF, checks if TOC exists in database
        3. Indexes PDFs with TOC using index_well()
        4. Reports PDFs without TOC

        Args:
            well_name: Well identifier (e.g., "Well 5")
            reindex: If True, delete existing chunks before reindexing

        Returns:
            {
                'well_name': str,
                'pdfs_found': int,
                'pdfs_indexed': int,
                'pdfs_skipped': List[str],  # PDFs without TOC
                'total_chunks': int
            }
        """
        print(f"\n{'='*80}")
        print(f"INDEXING ALL PDFs IN {well_name}/Well report/")
        print(f"{'='*80}")

        # Scan for PDFs
        report_dir = os.path.join(self.data_dir, well_name, "Well report")
        if not os.path.exists(report_dir):
            raise FileNotFoundError(f"Well report directory not found: {report_dir}")

        # Find all PDFs (recursively)
        pdf_pattern = os.path.join(report_dir, "**", "*.pdf")
        pdf_files = glob.glob(pdf_pattern, recursive=True)

        print(f"\n[DIR] Scanning: {report_dir}")
        print(f"[FILE] Found {len(pdf_files)} PDF files")

        # List found PDFs
        for pdf in pdf_files:
            rel_path = os.path.relpath(pdf, report_dir)
            print(f"  • {rel_path}")

        # Find all TOC entries for this well (could be multiple versions)
        # e.g., "Well 5" and "Well 5 v1.0"
        well_entries = {}
        for db_key, db_data in self.toc_database.items():
            if db_key == well_name or db_key.startswith(f"{well_name} "):
                well_entries[db_key] = db_data

        if not well_entries:
            print(f"\n[WARN]  Warning: No TOC entries found for {well_name}")
            print(f"   Only PDFs with TOC entries can be indexed")
            return {
                'well_name': well_name,
                'pdfs_found': len(pdf_files),
                'pdfs_indexed': 0,
                'pdfs_skipped': [os.path.basename(p) for p in pdf_files],
                'total_chunks': 0
            }

        print(f"\n[LOAD] Found {len(well_entries)} TOC entries for {well_name}:")
        for entry_key in well_entries.keys():
            print(f"  • {entry_key}: {well_entries[entry_key]['filename']}")

        # Collect all TOC-indexed filenames
        toc_filenames = {data['filename'] for data in well_entries.values()}

        # Index all PDFs with TOC entries
        pdfs_indexed = 0
        pdfs_skipped = []
        total_chunks = 0
        indexed_files = set()

        for pdf_path in pdf_files:
            pdf_name = os.path.basename(pdf_path)

            # Check if this PDF has a TOC entry
            matching_entry = None
            for entry_key, entry_data in well_entries.items():
                if entry_data['filename'] in pdf_path:
                    matching_entry = entry_key
                    break

            if matching_entry:
                print(f"\n[OK] Found TOC-indexed PDF: {pdf_name}")
                print(f"   Using TOC entry: {matching_entry}")

                # Index using existing method (with the TOC database key)
                try:
                    result = self.index_well(matching_entry, reindex=reindex)
                    pdfs_indexed += 1
                    total_chunks += result['chunks_indexed']
                    indexed_files.add(pdf_name)
                except Exception as e:
                    print(f"[ERROR] Failed to index {pdf_name}: {e}")
                    pdfs_skipped.append(pdf_name)
            else:
                # PDF doesn't have TOC entry
                pdfs_skipped.append(pdf_name)
                print(f"\n[INFO]  Skipped (no TOC): {pdf_name}")
                print(f"   To index this PDF, add its TOC to the TOC database")

        print(f"\n{'='*80}")
        print(f"[OK] INDEXING COMPLETE")
        print(f"   PDFs found: {len(pdf_files)}")
        print(f"   PDFs indexed: {pdfs_indexed}")
        print(f"   PDFs skipped: {len(pdfs_skipped)}")
        print(f"   Total chunks: {total_chunks}")
        print(f"{'='*80}")

        return {
            'well_name': well_name,
            'pdfs_found': len(pdf_files),
            'pdfs_indexed': pdfs_indexed,
            'pdfs_skipped': pdfs_skipped,
            'total_chunks': total_chunks
        }


def main():
    """Test the RAG system"""
    import sys

    # Initialize RAG system
    rag = WellReportRAG()

    # Check available wells
    wells = rag.get_indexed_wells()
    print(f"\n Available wells: {', '.join(wells)}")

    # Index Well 5 (best quality)
    print(f"\n{'='*80}")
    print("TEST: Indexing Well 5")
    print(f"{'='*80}")

    try:
        result = rag.index_well("Well 5", reindex=True)
        print(f"\n[OK] Indexing successful:")
        print(f"   Chunks: {result['chunks_indexed']}")
        print(f"   Sections: {result['sections_parsed']}")
        print(f"   Pages: {len(result['pages_processed'])}")

    except Exception as e:
        print(f"\n[ERROR] Indexing failed: {e}")
        sys.exit(1)

    # Test query
    print(f"\n{'='*80}")
    print("TEST: Querying RAG system")
    print(f"{'='*80}")

    test_queries = [
        "What is the measured depth of the well?",
        "What is the casing inner diameter?",
    ]

    for query in test_queries:
        try:
            result = rag.query(query, well_name="Well 5", n_results=3)

            print(f"\n" + "-"*80)
            print(f"Query: {result['query']}")
            print(f"Section types: {', '.join(result['section_types_used'])}")
            print(f"\nAnswer:\n{result['answer']}")
            print(f"\nSources ({len(result['sources'])}):")
            for source in result['sources']:
                print(f"  [{source['source_index']}] Section {source['section_number']} - {source['section_title']} (Page {source['page']})")

        except Exception as e:
            print(f"\n[ERROR] Query failed: {e}")

    print(f"\n{'='*80}")
    print("[OK] RAG SYSTEM TEST COMPLETE")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
