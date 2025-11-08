"""
Check ChromaDB status and show what's currently indexed
"""

import chromadb
from chromadb.config import Settings

print("="*80)
print("CHROMADB STATUS CHECK")
print("="*80)

# Connect to ChromaDB server
try:
    client = chromadb.HttpClient(host='localhost', port=8000)
    print("\n[OK] Connected to ChromaDB server at localhost:8000")
except Exception as e:
    print(f"\n[ERROR] Cannot connect to ChromaDB: {e}")
    print("Make sure ChromaDB container is running: docker-compose up -d chromadb")
    exit(1)

# List all collections
collections = client.list_collections()
print(f"\n[INFO] Collections: {len(collections)}")

if not collections:
    print("  No collections found - database is empty")
    print("\n[!] You need to run indexing first!")
    exit(0)

# Check each collection
for collection in collections:
    print(f"\n{'='*80}")
    print(f"Collection: {collection.name}")
    print(f"{'='*80}")

    # Get collection stats
    count = collection.count()
    print(f"  Total chunks: {count}")

    if count == 0:
        print("  [EMPTY] No documents indexed yet")
        continue

    # Sample some metadata to see what's indexed
    print("\n  Sampling metadata...")
    try:
        results = collection.get(limit=10, include=['metadatas'])

        # Extract unique well names
        well_names = set()
        document_names = set()
        chunk_types = set()

        for metadata in results['metadatas']:
            if 'well_name' in metadata:
                well_names.add(metadata['well_name'])
            if 'document_name' in metadata:
                document_names.add(metadata['document_name'])
            if 'chunk_type' in metadata:
                chunk_types.add(metadata['chunk_type'])

        print(f"\n  Wells indexed: {len(well_names)}")
        for well in sorted(well_names):
            print(f"    - {well}")

        print(f"\n  Documents indexed: {len(document_names)}")
        for doc in sorted(document_names):
            print(f"    - {doc}")

        print(f"\n  Chunk types: {', '.join(sorted(chunk_types))}")

    except Exception as e:
        print(f"  [WARNING] Could not sample metadata: {e}")

# Volume info
print("\n" + "="*80)
print("PERSISTENCE INFO")
print("="*80)
print("  Docker volume: hackathon_chroma_data")
print("  Data persists across container restarts")
print("  To backup: docker run --rm -v hackathon_chroma_data:/data -v $(pwd):/backup alpine tar czf /backup/chroma_backup.tar.gz /data")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
if count > 0:
    print(f"  [OK] {count} chunks indexed and persisted")
    print("  Data will be available even after restart")
else:
    print("  [!] No data indexed yet - run notebook to index PDFs")

print("="*80)
