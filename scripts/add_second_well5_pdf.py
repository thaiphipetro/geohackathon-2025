"""
Quick script to add the second Well 5 PDF to the TOC database
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'notebooks'))

# Import the functions from build_toc_database
from build_toc_database import parse_first_4_pages_smart, extract_toc_flexible, extract_publication_date, identify_key_sections

import json

print("="*80)
print("ADDING SECOND WELL 5 PDF TO TOC DATABASE")
print("="*80)

# Path to second PDF
data_dir = Path(__file__).parent.parent / "Training data-shared with participants"
pdf_path = data_dir / "Well 5" / "Well report" / "NLOG_GS_PUB_EOWR_SodM_NLW-GT-03-S1 v1.0_Redacted.pdf"

if not pdf_path.exists():
    print(f"\n[ERROR] PDF not found: {pdf_path}")
    sys.exit(1)

print(f"\nPDF: {pdf_path.name}")
print("Extracting TOC...")

# Parse first 4 pages (smart routing)
text, method, is_scanned = parse_first_4_pages_smart(pdf_path)

if not text:
    print(f"[ERROR] Failed to parse PDF")
    sys.exit(1)

print(f"[OK] Parsed with method: {method}")
print(f"[OK] Scanned: {'Yes' if is_scanned else 'No'}")

# Extract TOC
toc = extract_toc_flexible(text)
print(f"[OK] TOC entries found: {len(toc)}")

if len(toc) < 3:
    print(f"[WARNING] Not enough TOC entries (found {len(toc)}, expected >= 3)")
    print("Continuing anyway...")

# Extract publication date
pub_date = extract_publication_date(text)
if pub_date:
    print(f"[OK] Publication date: {pub_date.strftime('%Y-%m-%d')}")
else:
    print(f"[WARNING] Publication date not found")

# Get file size
file_size = pdf_path.stat().st_size
print(f"[OK] File size: {file_size/1024/1024:.1f} MB")

# Identify key sections
key_sections = identify_key_sections(toc) if toc else {}
key_count = sum(len(v) for v in key_sections.values())
print(f"[OK] Key sections found: {key_count}")

# Load existing database
toc_db_path = Path(__file__).parent.parent / "outputs" / "exploration" / "toc_database.json"
with open(toc_db_path, 'r') as f:
    toc_db = json.load(f)

print(f"\n[OK] Loaded existing database: {len(toc_db)} wells")

# Add as new well entry (Well 5 v1.0)
well_key = "Well 5 v1.0"
toc_db[well_key] = {
    'eowr_file': str(pdf_path),
    'filename': pdf_path.name,
    'file_size': file_size,
    'pub_date': pub_date.isoformat() if pub_date else None,
    'is_scanned': is_scanned,
    'parse_method': method,
    'toc': toc,
    'key_sections': key_sections
}

# Save updated database
with open(toc_db_path, 'w') as f:
    json.dump(toc_db, f, indent=2)

print(f"\n[OK] Added '{well_key}' to TOC database")
print(f"[OK] Total wells in database: {len(toc_db)}")
print(f"\n[OK] Saved to: {toc_db_path}")

print("\n" + "="*80)
print("DONE - Now you can index both PDFs!")
print("="*80)
print("\nNext steps:")
print("1. Re-run the notebook cell 5 to index Well 5")
print("2. Both PDFs should now be indexed")
print(f"   - Well 5: {toc_db['Well 5']['filename']}")
print(f"   - Well 5 v1.0: {toc_db[well_key]['filename']}")
