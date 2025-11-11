"""
Check current Well 7 chunks in ChromaDB
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vector_store import TOCEnhancedVectorStore

print("="*80)
print("CHECKING WELL 7 CHUNKS IN CHROMADB")
print("="*80)

# Connect to ChromaDB
vector_store = TOCEnhancedVectorStore()

# Query for Well 7 chunks
collection = vector_store.collection

# Get all chunks for Well 7
results = collection.get(
    where={"well_name": "Well 7"},
    include=["metadatas"]
)

if not results['ids']:
    print("\n[INFO] No Well 7 chunks found in ChromaDB")
else:
    print(f"\n[INFO] Found {len(results['ids'])} Well 7 chunks:")
    print("-"*80)

    # Group by filename
    files = {}
    for i, chunk_id in enumerate(results['ids']):
        metadata = results['metadatas'][i]
        filename = metadata.get('filename', 'Unknown')
        chunk_type = metadata.get('chunk_type', 'text')
        has_section = 'section_number' in metadata

        if filename not in files:
            files[filename] = {'total': 0, 'with_toc': 0, 'without_toc': 0, 'types': {}}

        files[filename]['total'] += 1
        if has_section:
            files[filename]['with_toc'] += 1
        else:
            files[filename]['without_toc'] += 1

        if chunk_type not in files[filename]['types']:
            files[filename]['types'][chunk_type] = 0
        files[filename]['types'][chunk_type] += 1

    for filename, stats in files.items():
        print(f"\nFile: {filename}")
        print(f"  Total chunks: {stats['total']}")
        print(f"  With TOC metadata: {stats['with_toc']}")
        print(f"  Without TOC metadata: {stats['without_toc']}")
        print(f"  Chunk types: {stats['types']}")

    print("-"*80)
    print(f"\nTotal Well 7 chunks: {len(results['ids'])}")
    print(f"Chunks WITH TOC metadata: {sum(f['with_toc'] for f in files.values())}")
    print(f"Chunks WITHOUT TOC metadata: {sum(f['without_toc'] for f in files.values())}")

print("\n" + "="*80)
