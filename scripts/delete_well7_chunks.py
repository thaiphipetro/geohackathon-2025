"""
Delete all Well 7 chunks from ChromaDB
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vector_store import TOCEnhancedVectorStore

print("="*80)
print("DELETING WELL 7 CHUNKS FROM CHROMADB")
print("="*80)

# Connect to ChromaDB
vector_store = TOCEnhancedVectorStore()
collection = vector_store.collection

# Get all Well 7 chunk IDs
results = collection.get(
    where={"well_name": "Well 7"},
    include=[]
)

if not results['ids']:
    print("\n[INFO] No Well 7 chunks to delete")
else:
    chunk_count = len(results['ids'])
    print(f"\n[INFO] Found {chunk_count} Well 7 chunks")
    print(f"[ACTION] Deleting all Well 7 chunks...")

    # Delete all Well 7 chunks
    collection.delete(
        ids=results['ids']
    )

    print(f"[SUCCESS] Deleted {chunk_count} Well 7 chunks")

    # Verify deletion
    verify = collection.get(
        where={"well_name": "Well 7"},
        include=[]
    )

    if not verify['ids']:
        print(f"[OK] Verified: No Well 7 chunks remaining")
    else:
        print(f"[WARN] {len(verify['ids'])} chunks still remain!")

print("\n" + "="*80)
