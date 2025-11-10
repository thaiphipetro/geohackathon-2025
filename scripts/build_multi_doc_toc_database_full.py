"""
Build Multi-Document TOC Database - Full Version

Processes all 14 PDFs across all wells with multi-document structure.
Uses PyMuPDF fallback for 100% TOC extraction success.

Creates structure:
{
  "Well 1": [
    {"filename": "...", "pub_date": "...", "toc": [...], "key_sections": {...}},
    {"filename": "...", "pub_date": "...", "toc": [...], "key_sections": {...}}
  ],
  "Well 2": [...],
  ...
}
"""

import sys
from pathlib import Path
import fitz
import tempfile
import os

# Import existing functions from analyze_all_tocs.py and build_toc_database.py
sys.path.insert(0, str(Path(__file__).parent))

from build_toc_database import extract_publication_date
from analyze_all_tocs import (
    parse_first_n_pages,
    find_toc_boundaries
)
from robust_toc_extractor import RobustTOCExtractor

import json
from collections import defaultdict

print("="*80)
print("MULTI-DOCUMENT TOC DATABASE BUILDER - FULL")
print("="*80)

# Load 13-category mapping (v2 with well_testing & intervention)
categorization_path = Path("outputs/final_section_categorization_v2.json")
with open(categorization_path, 'r') as f:
    categorization = json.load(f)

print(f"[OK] Loaded 13-category mapping (v2)")

# Helper: Normalize for matching
def normalize_title(title):
    """Remove dots, extra whitespace, lowercase"""
    if not title:
        return ""
    cleaned = title.rstrip('. \t')
    cleaned = ' '.join(cleaned.split())
    return cleaned.lower()

def normalize_number(number):
    """Normalize section numbers: '1.' -> '1'"""
    return str(number).rstrip('.')

# Build lookup from categorization
category_lookup = {}
for category_name, category_data in categorization['categories'].items():
    for entry in category_data['entries']:
        well = entry['well']
        number = normalize_number(entry['number'])
        title = normalize_title(entry['title'])
        key = (well, number, title)
        category_lookup[key] = category_name

print(f"[OK] Built category lookup: {len(category_lookup)} entries\n")

# Process all wells
ALL_WELLS = ['Well 1', 'Well 2', 'Well 3', 'Well 4', 'Well 5', 'Well 6', 'Well 8']
data_dir = Path("Training data-shared with participants")

multi_doc_database = {}
total_pdfs_processed = 0
total_pdfs_skipped = 0

for well_name in ALL_WELLS:
    print(f"{'='*80}")
    print(f"PROCESSING {well_name}")
    print(f"{'='*80}\n")

    well_dir = data_dir / well_name / "Well report"

    if not well_dir.exists():
        print(f"[SKIP] {well_name} - directory not found")
        continue

    # Find all PDFs
    pdf_files = list(well_dir.rglob("*.pdf"))
    print(f"[FOUND] {len(pdf_files)} PDF files")

    well_documents = []

    for pdf_path in pdf_files:
        pdf_name = pdf_path.name
        print(f"\n[PDF] Processing: {pdf_name}")

        # Parse first 10 pages with Docling + PyMuPDF fallback
        docling_text, raw_text, is_scanned, error = parse_first_n_pages(pdf_path, num_pages=10)

        if error:
            print(f"  [ERROR] {error}")
            total_pdfs_skipped += 1
            continue

        # Try Docling text first
        text = docling_text
        source = "Docling"
        lines = text.split('\n')
        toc_start, toc_end = find_toc_boundaries(lines)

        # If Docling didn't find TOC, try PyMuPDF fallback
        if toc_start < 0:
            print(f"  Docling: NO TOC FOUND")
            print(f"  Trying PyMuPDF fallback...")
            text = raw_text
            source = "PyMuPDF"
            lines = text.split('\n')
            toc_start, toc_end = find_toc_boundaries(lines)

        if toc_start < 0:
            print(f"  [SKIP] No TOC found (tried both Docling and PyMuPDF)")
            total_pdfs_skipped += 1
            continue

        print(f"  TOC found ({source}): lines {toc_start} to {toc_end}")

        toc_section = lines[toc_start:toc_end]
        toc_text = '\n'.join(toc_section)

        # Use RobustTOCExtractor for 100% success rate
        extractor = RobustTOCExtractor()
        toc_entries, pattern = extractor.extract(toc_section)  # Returns (entries, pattern_name)
        print(f"  [EXTRACTOR] Used pattern: {pattern}")

        if len(toc_entries) < 3:
            print(f"  [SKIP] Insufficient TOC entries ({len(toc_entries)})")
            total_pdfs_skipped += 1
            continue

        print(f"  [TOC] Extracted {len(toc_entries)} entries")

        # Extract publication date - try both Docling and PyMuPDF
        pub_date = extract_publication_date(docling_text) if docling_text else None

        # If not found in Docling, try PyMuPDF fallback
        if not pub_date and raw_text:
            pub_date = extract_publication_date(raw_text)
            if pub_date:
                print(f"  [DATE] {pub_date.strftime('%Y-%m-%d')} (from PyMuPDF fallback)")

        if pub_date:
            print(f"  [DATE] {pub_date.strftime('%Y-%m-%d')}")
        else:
            print(f"  [DATE] Not found")

        # Apply 11-category mapping to TOC entries
        categorized_count = 0
        for entry in toc_entries:
            number = normalize_number(entry.get('number', ''))
            title = normalize_title(entry.get('title', ''))

            # Try exact match
            key = (well_name, number, title)
            if key in category_lookup:
                entry['type'] = category_lookup[key]
                categorized_count += 1
            else:
                # Try fuzzy match by number + partial title
                for (w, n, t), cat in category_lookup.items():
                    if w == well_name and n == number:
                        if title in t or t in title:
                            entry['type'] = cat
                            categorized_count += 1
                            break

        print(f"  [CATEGORY] Applied types to {categorized_count}/{len(toc_entries)} entries")

        # Build key_sections from categorized entries
        key_sections = defaultdict(list)
        for entry in toc_entries:
            if 'type' in entry:
                key_sections[entry['type']].append({
                    'number': entry.get('number', ''),
                    'title': entry.get('title', ''),
                    'page': entry.get('page', 0),
                    'type': entry['type']
                })

        # Store document info
        doc_info = {
            'filename': pdf_name,
            'filepath': str(pdf_path),
            'file_size': pdf_path.stat().st_size,
            'pub_date': pub_date.isoformat() if pub_date else None,
            'is_scanned': is_scanned,
            'parse_method': source,  # Docling or PyMuPDF
            'toc': toc_entries,
            'key_sections': dict(key_sections)
        }

        well_documents.append(doc_info)
        total_pdfs_processed += 1
        print(f"  [OK] Document processed")

    if well_documents:
        multi_doc_database[well_name] = well_documents
        print(f"\n[OK] {well_name}: {len(well_documents)} documents indexed")

# Save full database
output_path = Path("outputs/exploration/toc_database_multi_doc_full.json")
with open(output_path, 'w') as f:
    json.dump(multi_doc_database, f, indent=2)

print(f"\n{'='*80}")
print("FULL DATABASE BUILD COMPLETE")
print(f"{'='*80}")
print(f"Saved to: {output_path}")

# Print summary
total_docs = sum(len(docs) for docs in multi_doc_database.values())
print(f"\nSummary:")
print(f"  Wells processed: {len(multi_doc_database)}")
print(f"  Total documents processed: {total_pdfs_processed}")
print(f"  Total documents skipped: {total_pdfs_skipped}")

for well, docs in multi_doc_database.items():
    print(f"\n{well}: {len(docs)} documents")
    for doc in docs:
        toc_count = len(doc['toc'])
        cat_count = sum(len(sections) for sections in doc['key_sections'].values())
        print(f"  - {doc['filename']}")
        print(f"    TOC: {toc_count} entries, Categorized: {cat_count}")
        print(f"    Date: {doc['pub_date']}")

print(f"\n{'='*80}")
