"""
Test TOC-aware indexer on Well 3 (has 311KB max chunk)

Validates:
1. TOC database loading
2. Section type mapping
3. Large chunk splitting (>10KB)
4. Metadata enrichment (section_type field)
5. Before/after chunk size statistics
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.simple_rag_indexer import SimpleRAGIndexer


def analyze_original_chunks(json_path: Path):
    """Analyze original chunks before TOC-aware processing"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunks = data.get('chunks', [])
    chunk_sizes = [len(c.get('text', '')) for c in chunks]

    return {
        'total_chunks': len(chunks),
        'avg_size': sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
        'min_size': min(chunk_sizes) if chunk_sizes else 0,
        'max_size': max(chunk_sizes) if chunk_sizes else 0,
        'large_chunks': sum(1 for s in chunk_sizes if s > 10000),
        'sizes': chunk_sizes
    }


def main():
    print("=" * 80)
    print("TEST: TOC-Aware Indexer on Well 3")
    print("=" * 80)

    # Find Well 3 JSON
    well_num = 3
    well_dir = project_root / "outputs" / "all_wells_comprehensive" / f"well_{well_num}"
    json_files = list(well_dir.glob("*_results.json"))

    if not json_files:
        print(f"[ERROR] No JSON results found in {well_dir}")
        return

    json_path = json_files[0]
    print(f"\n[LOAD] {json_path.name}")

    # Analyze original chunks
    print(f"\n[ANALYZE] Original chunks BEFORE TOC-aware processing:")
    original_stats = analyze_original_chunks(json_path)
    print(f"  Total chunks: {original_stats['total_chunks']}")
    print(f"  Avg size: {original_stats['avg_size']:.1f} chars")
    print(f"  Min size: {original_stats['min_size']} chars")
    print(f"  Max size: {original_stats['max_size']} chars")
    print(f"  Large chunks (>10KB): {original_stats['large_chunks']}")

    # Initialize indexer with TOC-aware chunking
    print(f"\n[INIT] Creating TOC-aware indexer...")
    indexer = SimpleRAGIndexer()

    # Load JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create documents with TOC-aware chunking
    print(f"\n[CONVERT] Creating documents with TOC-aware chunking...")
    documents = indexer.create_documents_from_json(
        data=data,
        well_name=f"well_{well_num}"
    )

    # Analyze new chunks
    text_docs = [d for d in documents if d.metadata['source_type'] == 'text_chunk']
    doc_sizes = [len(d.page_content) for d in text_docs]

    print(f"\n[STATS] AFTER TOC-aware processing:")
    print(f"  Total documents: {len(documents)}")
    print(f"  Text chunks: {len(text_docs)}")
    print(f"  Avg size: {sum(doc_sizes)/len(doc_sizes):.1f} chars")
    print(f"  Min size: {min(doc_sizes)} chars")
    print(f"  Max size: {max(doc_sizes)} chars")
    print(f"  Large chunks (>10KB): {sum(1 for s in doc_sizes if s > 10000)}")

    # Section type coverage
    with_section_type = sum(1 for d in text_docs if d.metadata.get('section_type'))
    print(f"\n[TOC MAPPING]")
    print(f"  Chunks with section_type: {with_section_type}/{len(text_docs)} ({with_section_type/len(text_docs)*100:.1f}%)")

    # Show section type distribution
    section_types = {}
    for doc in text_docs:
        stype = doc.metadata.get('section_type', 'unknown')
        section_types[stype] = section_types.get(stype, 0) + 1

    print(f"\n[SECTION TYPE DISTRIBUTION]")
    for stype, count in sorted(section_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {stype}: {count} chunks")

    # Show sample split chunks
    split_docs = [d for d in text_docs if d.metadata.get('is_split')]
    if split_docs:
        print(f"\n[SPLIT CHUNKS] Found {len(split_docs)} split chunks")
        print(f"  Example: chunk_index={split_docs[0].metadata['chunk_index']}, sub_chunks={sum(1 for d in text_docs if d.metadata['chunk_index'] == split_docs[0].metadata['chunk_index'])}")

    # Show sample documents with section type
    print(f"\n[SAMPLE] First 3 chunks with section_type:")
    count = 0
    for doc in text_docs:
        if doc.metadata.get('section_type'):
            count += 1
            print(f"\n  Chunk {count}:")
            print(f"    Section title: {doc.metadata.get('section_title', 'N/A')}")
            print(f"    Section type: {doc.metadata.get('section_type', 'N/A')}")
            print(f"    Page: {doc.metadata.get('page', 'N/A')}")
            print(f"    Size: {len(doc.page_content)} chars")
            print(f"    Is split: {doc.metadata.get('is_split', False)}")
            print(f"    Content preview: {doc.page_content[:100]}...")
            if count >= 3:
                break

    # Verification
    print(f"\n" + "=" * 80)
    print("VALIDATION")
    print("=" * 80)

    if max(doc_sizes) <= 10000:
        print("[OK] No chunks exceed 10KB limit")
    else:
        print(f"[WARNING] {sum(1 for s in doc_sizes if s > 10000)} chunks still exceed 10KB")

    if with_section_type > 0:
        print(f"[OK] {with_section_type/len(text_docs)*100:.1f}% of chunks have section_type mapped")
    else:
        print("[WARNING] No section_type mapping found")

    if original_stats['large_chunks'] > 0 and split_docs:
        print(f"[OK] Large chunks were split ({len(split_docs)} split chunks created)")
    elif original_stats['large_chunks'] == 0:
        print("[OK] No large chunks needed splitting")
    else:
        print("[WARNING] Large chunks detected but no splitting occurred")

    print(f"\n" + "=" * 80)
    print("[OK] Test complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
