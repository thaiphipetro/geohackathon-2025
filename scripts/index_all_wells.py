"""
Index all 8 wells into ChromaDB
This will take ~30-60 minutes depending on document sizes
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rag_system import WellReportRAG
import json
import time

print("="*80)
print("INDEXING ALL WELLS")
print("="*80)

# Initialize RAG system
print("\nInitializing RAG system...")
rag = WellReportRAG()

# Get list of wells from TOC database
wells_to_index = []
for well_name in rag.toc_database.keys():
    # Extract base well name (e.g., "Well 5" from "Well 5 v1.0")
    base_well = well_name.split()[0] + " " + well_name.split()[1]
    if base_well not in wells_to_index:
        wells_to_index.append(base_well)

wells_to_index.sort()

print(f"\nWells to index: {len(wells_to_index)}")
for well in wells_to_index:
    print(f"  - {well}")

# Results tracking
results = {}
total_chunks = 0
total_pdfs = 0
start_time = time.time()

# Index each well
for i, well_name in enumerate(wells_to_index, 1):
    print(f"\n{'='*80}")
    print(f"INDEXING {well_name} ({i}/{len(wells_to_index)})")
    print(f"{'='*80}")

    well_start_time = time.time()

    try:
        # Index this well (will handle multiple PDFs if available)
        result = rag.index_well_reports(well_name, reindex=False)

        well_elapsed = time.time() - well_start_time

        # Track results
        results[well_name] = {
            'status': 'success',
            'pdfs_found': result['pdfs_found'],
            'pdfs_indexed': result['pdfs_indexed'],
            'pdfs_skipped': result['pdfs_skipped'],
            'total_chunks': result['total_chunks'],
            'elapsed_seconds': round(well_elapsed, 2)
        }

        total_chunks += result['total_chunks']
        total_pdfs += result['pdfs_indexed']

        print(f"\n[OK] {well_name} indexed in {well_elapsed:.1f}s")
        print(f"     PDFs: {result['pdfs_indexed']}, Chunks: {result['total_chunks']}")

    except Exception as e:
        well_elapsed = time.time() - well_start_time

        print(f"\n[ERROR] Failed to index {well_name}: {e}")

        results[well_name] = {
            'status': 'error',
            'error': str(e),
            'elapsed_seconds': round(well_elapsed, 2)
        }

    # Progress update
    elapsed_so_far = time.time() - start_time
    avg_time_per_well = elapsed_so_far / i
    remaining_wells = len(wells_to_index) - i
    estimated_remaining = avg_time_per_well * remaining_wells

    print(f"\nProgress: {i}/{len(wells_to_index)} wells ({100*i//len(wells_to_index)}%)")
    print(f"Elapsed: {elapsed_so_far/60:.1f} min | Estimated remaining: {estimated_remaining/60:.1f} min")

# Final summary
total_elapsed = time.time() - start_time

print("\n" + "="*80)
print("INDEXING COMPLETE")
print("="*80)

print(f"\nTotal time: {total_elapsed/60:.1f} minutes")
print(f"Total PDFs indexed: {total_pdfs}")
print(f"Total chunks indexed: {total_chunks}")

print(f"\nPer-well results:")
for well_name, result in results.items():
    if result['status'] == 'success':
        print(f"  [OK] {well_name}: {result['pdfs_indexed']} PDFs, {result['total_chunks']} chunks ({result['elapsed_seconds']}s)")
    else:
        print(f"  [ERROR] {well_name}: {result.get('error', 'Unknown error')}")

# Save results to file
output_file = Path(__file__).parent.parent / 'outputs' / 'indexing_results.json'
output_file.parent.mkdir(parents=True, exist_ok=True)

summary = {
    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    'total_elapsed_minutes': round(total_elapsed / 60, 2),
    'total_pdfs_indexed': total_pdfs,
    'total_chunks_indexed': total_chunks,
    'wells_indexed': len([r for r in results.values() if r['status'] == 'success']),
    'wells_failed': len([r for r in results.values() if r['status'] == 'error']),
    'results': results
}

with open(output_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n[OK] Results saved to: {output_file}")

# Final verification
print("\n" + "="*80)
print("VERIFYING INDEXED DATA")
print("="*80)

print("\nRun this command to verify:")
print("  python scripts/check_chromadb_status.py")

print("\n" + "="*80)
