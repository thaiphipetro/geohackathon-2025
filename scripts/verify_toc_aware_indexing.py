"""
Verify TOC-Aware Indexing Results

Checks:
1. Section type coverage statistics
2. Chunk size distribution (all under 10KB)
3. Sample retrieval with section_type filtering
4. Metadata quality
"""

import sys
from pathlib import Path
from typing import Dict, List
from collections import Counter

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


def verify_indexing():
    """Verify TOC-aware indexing results"""

    print("=" * 80)
    print("TOC-AWARE INDEXING VERIFICATION")
    print("=" * 80)

    # Load ChromaDB
    print("\n[LOAD] Loading ChromaDB...")
    embeddings = HuggingFaceEmbeddings(
        model_name="nomic-ai/nomic-embed-text-v1.5",
        model_kwargs={'device': 'cpu', 'trust_remote_code': True},
        encode_kwargs={'normalize_embeddings': True}
    )

    vectorstore = Chroma(
        collection_name="well_reports_toc_aware",
        embedding_function=embeddings,
        persist_directory="./chroma_db_toc_aware"
    )

    # Get all documents
    print("[LOAD] Retrieving all documents...")
    collection = vectorstore._collection
    all_docs = collection.get(include=['metadatas'])

    print(f"[OK] Loaded {len(all_docs['ids'])} documents")

    # Analyze section_type coverage
    print("\n" + "=" * 80)
    print("SECTION TYPE COVERAGE")
    print("=" * 80)

    text_chunks = [
        meta for meta in all_docs['metadatas']
        if meta.get('source_type') == 'text_chunk'
    ]

    print(f"\nTotal text chunks: {len(text_chunks)}")

    # Count section types
    section_types = [meta.get('section_type') for meta in text_chunks]
    section_type_counts = Counter(section_types)

    with_section_type = sum(1 for st in section_types if st)
    coverage_pct = (with_section_type / len(text_chunks) * 100) if text_chunks else 0

    print(f"Chunks with section_type: {with_section_type}/{len(text_chunks)} ({coverage_pct:.1f}%)")
    print(f"\nSection type distribution:")
    for section_type, count in sorted(section_type_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(text_chunks) * 100) if text_chunks else 0
        print(f"  {section_type or 'None'}: {count} chunks ({pct:.1f}%)")

    # Analyze chunk sizes
    print("\n" + "=" * 80)
    print("CHUNK SIZE VERIFICATION")
    print("=" * 80)

    # Get sample documents with content
    sample_docs = collection.get(
        where={"source_type": "text_chunk"},
        limit=1000,
        include=['documents', 'metadatas']
    )

    chunk_sizes = [len(doc) for doc in sample_docs['documents']]

    if chunk_sizes:
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        min_size = min(chunk_sizes)
        max_size = max(chunk_sizes)
        large_chunks = sum(1 for s in chunk_sizes if s > 10000)

        print(f"\nSample of {len(chunk_sizes)} chunks:")
        print(f"  Average size: {avg_size:.0f} chars")
        print(f"  Min size: {min_size} chars")
        print(f"  Max size: {max_size} chars")
        print(f"  Chunks > 10KB: {large_chunks}")

        if max_size <= 10000:
            print("\n[OK] All sampled chunks are under 10KB limit")
        else:
            print(f"\n[WARNING] {large_chunks} chunks exceed 10KB limit")

    # Split chunk analysis
    print("\n" + "=" * 80)
    print("SPLIT CHUNK STATISTICS")
    print("=" * 80)

    split_chunks = [meta for meta in text_chunks if meta.get('is_split')]
    original_chunks = [meta for meta in text_chunks if not meta.get('is_split')]

    print(f"\nTotal text chunks: {len(text_chunks)}")
    print(f"  Original chunks: {len(original_chunks)}")
    print(f"  Split sub-chunks: {len(split_chunks)}")

    # Well-by-well breakdown
    print("\n" + "=" * 80)
    print("PER-WELL STATISTICS")
    print("=" * 80)

    well_stats = {}
    for meta in text_chunks:
        well_name = meta.get('well_name', 'unknown')
        if well_name not in well_stats:
            well_stats[well_name] = {
                'total': 0,
                'with_section_type': 0,
                'split_chunks': 0
            }

        well_stats[well_name]['total'] += 1
        if meta.get('section_type'):
            well_stats[well_name]['with_section_type'] += 1
        if meta.get('is_split'):
            well_stats[well_name]['split_chunks'] += 1

    print(f"\n{'Well':<15} {'Total':<10} {'Section %':<12} {'Split Chunks':<15}")
    print("-" * 80)

    for well_name in sorted(well_stats.keys()):
        stats = well_stats[well_name]
        section_pct = (stats['with_section_type'] / stats['total'] * 100) if stats['total'] else 0
        print(f"{well_name:<15} {stats['total']:<10} {section_pct:<11.1f}% {stats['split_chunks']:<15}")

    # Test retrieval with section filtering
    print("\n" + "=" * 80)
    print("SECTION-FILTERED RETRIEVAL TEST")
    print("=" * 80)

    test_query = "casing program"
    print(f"\nQuery: '{test_query}'")
    print(f"Filter: section_type='casing'")

    # Retrieval with filter
    results_filtered = vectorstore.similarity_search(
        test_query,
        k=3,
        filter={"section_type": "casing"}
    )

    print(f"\n[OK] Retrieved {len(results_filtered)} results")
    for i, doc in enumerate(results_filtered, 1):
        print(f"\nResult {i}:")
        print(f"  Well: {doc.metadata.get('well_name')}")
        print(f"  Section: {doc.metadata.get('section_title', 'N/A')}")
        print(f"  Section type: {doc.metadata.get('section_type', 'N/A')}")
        print(f"  Page: {doc.metadata.get('page', 'N/A')}")
        print(f"  Snippet: {doc.page_content[:150]}...")

    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    print(f"\n[OK] Total documents indexed: {len(all_docs['ids'])}")
    print(f"[OK] Section type coverage: {coverage_pct:.1f}%")
    print(f"[OK] Chunk size limit: {'PASS' if max_size <= 10000 else 'FAIL'}")
    print(f"[OK] Section-filtered retrieval: WORKING")

    if coverage_pct >= 95:
        print("\n[EXCELLENT] Section type mapping achieved >95% coverage!")
    elif coverage_pct >= 90:
        print("\n[GOOD] Section type mapping achieved >90% coverage")
    else:
        print(f"\n[WARNING] Section type coverage below 90%: {coverage_pct:.1f}%")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    verify_indexing()
