"""
Scan all wells to identify:
1. Wells with multiple PDFs
2. Which PDFs are scanned vs native
3. Which PDFs already have TOC entries
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'notebooks'))

from build_toc_database import is_scanned_pdf
import json

print("="*80)
print("SCANNING ALL WELLS FOR MULTI-PDF CANDIDATES")
print("="*80)

# Load existing TOC database
toc_db_path = Path(__file__).parent.parent / "outputs" / "exploration" / "toc_database.json"
with open(toc_db_path, 'r') as f:
    toc_db = json.load(f)

# Get all TOC-indexed filenames
toc_indexed_files = {}
for well_key, well_data in toc_db.items():
    filename = well_data['filename']
    toc_indexed_files[filename] = well_key

print(f"\nCurrent TOC database: {len(toc_db)} entries")
print("TOC-indexed files:")
for filename, well_key in toc_indexed_files.items():
    print(f"  • {well_key}: {filename}")

# Scan all wells
data_dir = Path(__file__).parent.parent / "Training data-shared with participants"

results = {}

for well_num in range(1, 9):
    well_name = f"Well {well_num}"
    well_report_dir = data_dir / well_name / "Well report"

    if not well_report_dir.exists():
        print(f"\n{well_name}: Well report/ folder not found")
        continue

    # Find all PDFs
    pdf_files = list(well_report_dir.rglob("*.pdf"))

    if not pdf_files:
        print(f"\n{well_name}: No PDFs found")
        continue

    print(f"\n{'='*80}")
    print(f"{well_name}: {len(pdf_files)} PDF(s)")
    print(f"{'='*80}")

    pdf_info = []

    for pdf_path in pdf_files:
        pdf_name = pdf_path.name
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)

        # Check if scanned
        is_scanned = is_scanned_pdf(pdf_path)

        # Check if already indexed
        has_toc = pdf_name in toc_indexed_files
        toc_entry = toc_indexed_files.get(pdf_name, "N/A")

        pdf_info.append({
            'name': pdf_name,
            'path': pdf_path,
            'size_mb': file_size_mb,
            'is_scanned': is_scanned,
            'has_toc': has_toc,
            'toc_entry': toc_entry
        })

        status = "[INDEXED]" if has_toc else "[NOT INDEXED]"
        scan_type = "[SCANNED]" if is_scanned else "[NATIVE]"

        print(f"  {status:15} | {scan_type:10} | {file_size_mb:>6.1f} MB | {pdf_name}")
        if has_toc:
            print(f"           TOC entry: {toc_entry}")

    results[well_name] = {
        'total_pdfs': len(pdf_files),
        'indexed_pdfs': sum(1 for p in pdf_info if p['has_toc']),
        'unindexed_pdfs': sum(1 for p in pdf_info if not p['has_toc']),
        'scanned_pdfs': sum(1 for p in pdf_info if p['is_scanned']),
        'native_pdfs': sum(1 for p in pdf_info if not p['is_scanned']),
        'pdf_info': pdf_info
    }

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

for well_name, data in results.items():
    print(f"\n{well_name}:")
    print(f"  Total PDFs: {data['total_pdfs']}")
    print(f"  Indexed: {data['indexed_pdfs']}, Unindexed: {data['unindexed_pdfs']}")
    print(f"  Native: {data['native_pdfs']}, Scanned: {data['scanned_pdfs']}")

    if data['unindexed_pdfs'] > 0:
        print(f"  [!] {data['unindexed_pdfs']} PDF(s) need TOC extraction")

# Recommendations
print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)

print("\nWells with multiple PDFs that need TOC extraction:")
for well_name, data in results.items():
    if data['unindexed_pdfs'] > 0:
        unindexed = [p for p in data['pdf_info'] if not p['has_toc']]

        # Prioritize native PDFs (faster processing)
        native_unindexed = [p for p in unindexed if not p['is_scanned']]
        scanned_unindexed = [p for p in unindexed if p['is_scanned']]

        if native_unindexed:
            print(f"\n{well_name} - NATIVE PDFs (recommended):")
            for pdf in native_unindexed:
                print(f"  • {pdf['name']} ({pdf['size_mb']:.1f} MB)")

        if scanned_unindexed:
            print(f"\n{well_name} - SCANNED PDFs (slower, OCR required):")
            for pdf in scanned_unindexed:
                print(f"  • {pdf['name']} ({pdf['size_mb']:.1f} MB)")

print("\n" + "="*80)
print("Next steps:")
print("1. Run build_toc_database.py to extract TOC from all unindexed PDFs")
print("2. Or manually add specific PDFs using add_second_well5_pdf.py as template")
print("="*80)
