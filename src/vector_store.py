"""
TOC-Enhanced Vector Store
ChromaDB integration with metadata filtering for targeted retrieval
"""

from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings


class TOCEnhancedVectorStore:
    """
    Vector store for well reports with TOC-based metadata filtering

    Features:
        - Store chunks with section metadata (section_type, page, etc.)
        - Filter by section type during retrieval
        - Support multiple wells in single collection
        - Efficient metadata-based search

    Example:
        store = TOCEnhancedVectorStore()
        store.add_documents(chunks, well_name="Well 5")
        results = store.query_with_section_filter(
            query="What is the well depth?",
            well_name="Well 5",
            section_types=["depth", "borehole"],
            n_results=5
        )
    """

    def __init__(self,
                 collection_name: str = "well_reports",
                 chroma_host: str = None,
                 chroma_port: int = None,
                 persist_directory: str = None):
        """
        Initialize ChromaDB vector store

        Args:
            collection_name: Name of ChromaDB collection
            chroma_host: ChromaDB server host (None for local)
            chroma_port: ChromaDB server port (None for local)
            persist_directory: Directory for persistent storage
        """
        # Initialize ChromaDB client
        if chroma_host:
            # Connect to ChromaDB server (Docker setup)
            self.client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port or 8000
            )
            print(f"[OK] Connected to ChromaDB server at {chroma_host}:{chroma_port or 8000}")
        else:
            # Use local persistent storage
            self.client = chromadb.PersistentClient(
                path=persist_directory or "./chroma_db"
            )
            print(f"[OK] Using local ChromaDB at {persist_directory or './chroma_db'}")

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Geothermal well reports with TOC metadata"}
        )

        self.collection_name = collection_name
        print(f"[OK] Collection '{collection_name}' ready")

    def add_documents(self,
                     chunks: List[Dict],
                     well_name: str,
                     batch_size: int = 100) -> int:
        """
        Add document chunks to vector store

        Args:
            chunks: List of chunks with 'text', 'embedding', 'metadata'
                [{'text': '...', 'embedding': [...], 'metadata': {...}}, ...]
            well_name: Well identifier for filtering
            batch_size: Batch size for adding documents

        Returns:
            Number of chunks added
        """
        if not chunks:
            print("[WARN]  No chunks to add")
            return 0

        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            # Generate unique ID
            chunk_id = f"{well_name}_chunk_{i}"
            ids.append(chunk_id)

            # Extract embedding (should already be computed)
            if 'embedding' not in chunk:
                raise ValueError(f"Chunk {i} missing 'embedding' field")
            embeddings.append(chunk['embedding'])

            # Extract text
            documents.append(chunk['text'])

            # Build metadata
            metadata = {
                'well_name': well_name,
                'chunk_index': i,
                **chunk.get('metadata', {})
            }

            # ChromaDB requires all metadata values to be strings, ints, or floats
            # Convert None to empty string
            clean_metadata = {}
            for key, value in metadata.items():
                if value is None:
                    clean_metadata[key] = ""
                elif isinstance(value, (str, int, float)):
                    clean_metadata[key] = value
                else:
                    clean_metadata[key] = str(value)

            metadatas.append(clean_metadata)

        # Add to ChromaDB in batches
        total_added = 0
        for start_idx in range(0, len(ids), batch_size):
            end_idx = min(start_idx + batch_size, len(ids))

            self.collection.add(
                ids=ids[start_idx:end_idx],
                embeddings=embeddings[start_idx:end_idx],
                documents=documents[start_idx:end_idx],
                metadatas=metadatas[start_idx:end_idx]
            )

            total_added += (end_idx - start_idx)

        print(f"[OK] Added {total_added} chunks for {well_name}")
        return total_added

    def query_with_section_filter(self,
                                  query_embedding: List[float],
                                  well_name: str,
                                  section_types: Optional[List[str]] = None,
                                  n_results: int = 5) -> Dict:
        """
        Query with metadata filtering by section type

        Args:
            query_embedding: Query embedding vector
            well_name: Well to search in
            section_types: List of section types to filter by (e.g., ['depth', 'casing'])
                          None = search all sections
            n_results: Number of results to return

        Returns:
            {
                'documents': [...],     # Retrieved text chunks
                'metadatas': [...],     # Chunk metadata
                'distances': [...],     # Similarity distances
                'ids': [...]           # Chunk IDs
            }
        """
        # Build where clause for metadata filtering
        if section_types:
            # Combine well_name filter with section_type filter using $and
            where_clause = {
                "$and": [
                    {"well_name": well_name},
                    {"section_type": {"$in": section_types}}
                ]
            }
        else:
            # Only filter by well_name
            where_clause = {"well_name": well_name}

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=['documents', 'metadatas', 'distances']
        )

        # Return first result (we only sent one query)
        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'ids': results['ids'][0] if results['ids'] else []
        }

    def query_all_wells(self,
                       query_embedding: List[float],
                       section_types: Optional[List[str]] = None,
                       n_results: int = 5) -> Dict:
        """
        Query across all wells (no well_name filter)

        Args:
            query_embedding: Query embedding vector
            section_types: List of section types to filter by
            n_results: Number of results to return

        Returns:
            Same format as query_with_section_filter
        """
        where_clause = {}

        if section_types:
            where_clause["section_type"] = {"$in": section_types}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause if where_clause else None,
            include=['documents', 'metadatas', 'distances']
        )

        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'ids': results['ids'][0] if results['ids'] else []
        }

    def query_with_filters(self,
                          query_embedding: List[float],
                          well_name: Optional[str] = None,
                          section_types: Optional[List[str]] = None,
                          chunk_types: Optional[List[str]] = None,
                          document_names: Optional[List[str]] = None,
                          n_results: int = 10) -> Dict:
        """
        Flexible query with multiple filter types

        This is the most versatile query method, supporting filtering by:
        - well_name: Specific well
        - section_types: Section categories (depth, casing, etc.)
        - chunk_types: text vs table chunks
        - document_names: Specific source documents

        Args:
            query_embedding: Query embedding vector
            well_name: Well identifier (None = all wells)
            section_types: Section types to filter by
            chunk_types: Chunk types ('text', 'table')
            document_names: Document filenames to filter by
            n_results: Number of results to return

        Returns:
            {
                'documents': List[str],
                'metadatas': List[Dict],
                'distances': List[float],
                'ids': List[str]
            }

        Examples:
            # Get only table chunks from casing sections
            query_with_filters(emb, section_types=['casing'], chunk_types=['table'])

            # Get text chunks from specific document
            query_with_filters(emb, document_names=['Final-Well-Report.pdf'], chunk_types=['text'])

            # Get all chunks (text+tables) from Well 5, depth sections only
            query_with_filters(emb, well_name='Well 5', section_types=['depth'])
        """
        # Build filter conditions
        filters = []

        if well_name:
            filters.append({"well_name": well_name})

        if section_types:
            filters.append({"section_type": {"$in": section_types}})

        if chunk_types:
            filters.append({"chunk_type": {"$in": chunk_types}})

        if document_names:
            filters.append({"document_name": {"$in": document_names}})

        # Combine filters with $and operator
        if len(filters) > 1:
            where_clause = {"$and": filters}
        elif len(filters) == 1:
            where_clause = filters[0]
        else:
            where_clause = None  # No filters

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=['documents', 'metadatas', 'distances']
        )

        # Return first result (we only sent one query)
        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'ids': results['ids'][0] if results['ids'] else []
        }

    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            'collection_name': self.collection_name,
            'total_chunks': count,
            'metadata': self.collection.metadata
        }

    def delete_well(self, well_name: str) -> int:
        """
        Delete all chunks for a specific well

        Args:
            well_name: Well to delete

        Returns:
            Number of chunks deleted
        """
        # Get all IDs for this well
        results = self.collection.get(
            where={"well_name": well_name},
            include=[]
        )

        if results['ids']:
            self.collection.delete(ids=results['ids'])
            print(f"[OK] Deleted {len(results['ids'])} chunks for {well_name}")
            return len(results['ids'])

        print(f"[WARN]  No chunks found for {well_name}")
        return 0

    def reset_collection(self):
        """Delete entire collection (use with caution!)"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Geothermal well reports with TOC metadata"}
        )
        print(f"[WARN]  Collection '{self.collection_name}' reset")


def main():
    """Test the TOC-enhanced vector store"""
    import os

    print("="*80)
    print("TOC-ENHANCED VECTOR STORE - TEST")
    print("="*80)

    # Use Docker environment variables if available
    chroma_host = os.getenv('CHROMA_HOST', 'localhost')
    chroma_port = int(os.getenv('CHROMA_PORT', 8000))

    print(f"\nConnecting to ChromaDB at {chroma_host}:{chroma_port}...")

    try:
        # Initialize vector store
        store = TOCEnhancedVectorStore(
            collection_name="test_well_reports",
            chroma_host=chroma_host,
            chroma_port=chroma_port
        )

        # Create test chunks with embeddings
        test_chunks = [
            {
                'text': '## 2.1 Depths\n\nMeasured Depth: 2500 meters, True Vertical Depth: 2300 meters',
                'embedding': [0.1] * 768,  # Dummy 768-dim embedding
                'metadata': {
                    'section_number': '2.1',
                    'section_title': 'Depths',
                    'section_type': 'depth',
                    'page': 6,
                    'chunk_index': 0
                }
            },
            {
                'text': '## 2.2 Casing\n\nCasing: 13 3/8 inch to 500m, 9 5/8 inch to 1500m',
                'embedding': [0.2] * 768,  # Dummy embedding
                'metadata': {
                    'section_number': '2.2',
                    'section_title': 'Casing',
                    'section_type': 'casing',
                    'page': 6,
                    'chunk_index': 1
                }
            },
            {
                'text': '## 3.1 Trajectory\n\nKick-off point at 700 meters',
                'embedding': [0.3] * 768,  # Dummy embedding
                'metadata': {
                    'section_number': '3.1',
                    'section_title': 'Trajectory',
                    'section_type': 'trajectory',
                    'page': 10,
                    'chunk_index': 2
                }
            }
        ]

        # Add documents
        print("\n" + "-"*80)
        print("Adding test documents...")
        print("-"*80)
        num_added = store.add_documents(test_chunks, well_name="Test Well 5")

        # Get stats
        print("\n" + "-"*80)
        print("Collection Statistics:")
        print("-"*80)
        stats = store.get_collection_stats()
        print(f"  Collection: {stats['collection_name']}")
        print(f"  Total chunks: {stats['total_chunks']}")

        # Test query with section filter
        print("\n" + "-"*80)
        print("Test Query 1: Filter by section type 'depth'")
        print("-"*80)
        query_emb = [0.15] * 768  # Closer to depth chunk (0.1)

        results = store.query_with_section_filter(
            query_embedding=query_emb,
            well_name="Test Well 5",
            section_types=['depth'],
            n_results=5
        )

        print(f"Results: {len(results['documents'])} chunks")
        for i, (doc, meta, dist) in enumerate(zip(results['documents'],
                                                   results['metadatas'],
                                                   results['distances'])):
            print(f"\n  Result {i+1}:")
            print(f"    Section: {meta.get('section_number')} - {meta.get('section_title')}")
            print(f"    Type: {meta.get('section_type')}")
            print(f"    Page: {meta.get('page')}")
            print(f"    Distance: {dist:.4f}")
            print(f"    Text: {doc[:80]}...")

        # Test query without filter
        print("\n" + "-"*80)
        print("Test Query 2: No section filter (search all)")
        print("-"*80)

        results = store.query_with_section_filter(
            query_embedding=query_emb,
            well_name="Test Well 5",
            section_types=None,
            n_results=5
        )

        print(f"Results: {len(results['documents'])} chunks")

        # Clean up
        print("\n" + "-"*80)
        print("Cleanup: Deleting test data...")
        print("-"*80)
        store.delete_well("Test Well 5")

        print("\n" + "="*80)
        print("[OK] Vector store working correctly!")
        print("="*80)

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        print(f"\nMake sure ChromaDB is running on {chroma_host}:{chroma_port}")
        print("In Docker: docker-compose up -d chromadb")


if __name__ == '__main__':
    main()
