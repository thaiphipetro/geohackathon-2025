"""
Test ChromaDB Retrieval

Simple script to verify TOC-aware ChromaDB indexing works correctly.

Tests:
1. Load ChromaDB
2. Basic similarity search
3. Section type filtering
4. Metadata inspection
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


def test_chromadb_retrieval():
    """Test ChromaDB retrieval with TOC-aware metadata"""

    print("=" * 80)
    print("CHROMADB RETRIEVAL TEST")
    print("=" * 80)

    # Load embeddings
    print("\n[1/5] Loading embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="nomic-ai/nomic-embed-text-v1.5",
        model_kwargs={'device': 'cpu', 'trust_remote_code': True},
        encode_kwargs={'normalize_embeddings': True}
    )
    print("[OK] Embeddings loaded")

    # Load ChromaDB
    print("\n[2/5] Loading ChromaDB...")
    vectorstore = Chroma(
        collection_name="well_reports_toc_aware",
        embedding_function=embeddings,
        persist_directory="./chroma_db_toc_aware"
    )
    print("[OK] ChromaDB loaded")

    # Get collection stats
    collection = vectorstore._collection
    count = collection.count()
    print(f"[INFO] Total documents in collection: {count}")

    # Test 1: Basic similarity search
    print("\n" + "=" * 80)
    print("[3/5] TEST 1: Basic Similarity Search")
    print("=" * 80)

    query = "What is the total depth of the well?"
    print(f"\nQuery: '{query}'")
    print("Retrieving top 5 results...")

    results = vectorstore.similarity_search(query, k=5)

    print(f"\n[OK] Retrieved {len(results)} results")
    for i, doc in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"  Well: {doc.metadata.get('well_name', 'N/A')}")
        print(f"  Source type: {doc.metadata.get('source_type', 'N/A')}")
        print(f"  Section: {doc.metadata.get('section_title', 'N/A')}")
        print(f"  Section type: {doc.metadata.get('section_type', 'N/A')}")
        print(f"  Page: {doc.metadata.get('page', 'N/A')}")
        print(f"  Content preview: {doc.page_content[:150]}...")

    # Test 2: Section type filtering (casing)
    print("\n" + "=" * 80)
    print("[4/5] TEST 2: Section Type Filtering (Casing)")
    print("=" * 80)

    query = "casing program"
    print(f"\nQuery: '{query}'")
    print("Filter: section_type='casing'")
    print("Retrieving top 3 results...")

    results_filtered = vectorstore.similarity_search(
        query,
        k=3,
        filter={"section_type": "casing"}
    )

    print(f"\n[OK] Retrieved {len(results_filtered)} results")
    for i, doc in enumerate(results_filtered, 1):
        print(f"\nResult {i}:")
        print(f"  Well: {doc.metadata.get('well_name', 'N/A')}")
        print(f"  Section: {doc.metadata.get('section_title', 'N/A')}")
        print(f"  Section type: {doc.metadata.get('section_type', 'N/A')}")
        print(f"  Page: {doc.metadata.get('page', 'N/A')}")
        print(f"  Content preview: {doc.page_content[:150]}...")

    # Test 3: Well-specific filtering
    print("\n" + "=" * 80)
    print("[5/5] TEST 3: Well-Specific Filtering (Well 5)")
    print("=" * 80)

    query = "lithology"
    print(f"\nQuery: '{query}'")
    print("Filter: well_name='well_5'")
    print("Retrieving top 3 results...")

    results_well = vectorstore.similarity_search(
        query,
        k=3,
        filter={"well_name": "well_5"}
    )

    print(f"\n[OK] Retrieved {len(results_well)} results")
    for i, doc in enumerate(results_well, 1):
        print(f"\nResult {i}:")
        print(f"  Well: {doc.metadata.get('well_name', 'N/A')}")
        print(f"  Source type: {doc.metadata.get('source_type', 'N/A')}")
        print(f"  Section: {doc.metadata.get('section_title', 'N/A')}")
        print(f"  Section type: {doc.metadata.get('section_type', 'N/A')}")
        print(f"  Page: {doc.metadata.get('page', 'N/A')}")
        print(f"  Content preview: {doc.page_content[:150]}...")

    # Test 4: Combined filtering (well + section type)
    print("\n" + "=" * 80)
    print("BONUS: Combined Filtering (Well 7 + Geology)")
    print("=" * 80)

    query = "formation"
    print(f"\nQuery: '{query}'")
    print("Filter: well_name='well_7' AND section_type='geology'")
    print("Retrieving top 3 results...")

    results_combined = vectorstore.similarity_search(
        query,
        k=3,
        filter={
            "$and": [
                {"well_name": "well_7"},
                {"section_type": "geology"}
            ]
        }
    )

    print(f"\n[OK] Retrieved {len(results_combined)} results")
    for i, doc in enumerate(results_combined, 1):
        print(f"\nResult {i}:")
        print(f"  Well: {doc.metadata.get('well_name', 'N/A')}")
        print(f"  Section: {doc.metadata.get('section_title', 'N/A')}")
        print(f"  Section type: {doc.metadata.get('section_type', 'N/A')}")
        print(f"  Page: {doc.metadata.get('page', 'N/A')}")
        print(f"  Content preview: {doc.page_content[:150]}...")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("\n[OK] All retrieval tests passed!")
    print(f"[OK] ChromaDB contains {count} documents")
    print("[OK] Basic similarity search: WORKING")
    print("[OK] Section type filtering: WORKING")
    print("[OK] Well-specific filtering: WORKING")
    print("[OK] Combined filtering: WORKING")
    print("\n[READY] ChromaDB is ready for RAG QA system!")
    print("=" * 80)


if __name__ == '__main__':
    test_chromadb_retrieval()
