"""Test TOC extraction on Well 5 and Well 7 with FIXED parser"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter
import re

def extract_toc_from_markdown(text, debug=True):
    """Extract TOC from markdown text - FIXED to handle actual table format"""
    toc_entries = []
    lines = text.split('\n')

    if debug:
        print(f"\n[DEBUG] Total lines to search: {len(lines)}")

    # Find "Table of Contents" or "Contents" heading first
    # Try multiple variations
    toc_start = -1
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        # Check for various TOC heading formats
        toc_keywords = [
            'table of contents', 'contents', 'index', 'table des matieres',
            'inhoud', 'inhaltsverzeichnis'
        ]
        if any(kw in line_lower for kw in toc_keywords):
            toc_start = i
            if debug:
                print(f"[DEBUG] Found TOC heading at line {i}: '{line}'")
            break

    # If no explicit TOC heading, look for patterns that suggest a TOC structure
    # (multiple lines with section numbers and page numbers)
    if toc_start < 0:
        if debug:
            print("[DEBUG] No explicit TOC heading found, searching for TOC structure...")

        # Look for clusters of lines that look like TOC entries
        for i in range(min(300, len(lines))):
            line = lines[i]
            if '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                # Check if this looks like a TOC entry
                if len(parts) >= 2:
                    first_col = parts[0].strip()
                    last_col = parts[-1].strip()
                    # Section number in first col, page number in last col
                    if re.match(r'^\d+\.?\d*$', first_col) and last_col.isdigit():
                        toc_start = i
                        if debug:
                            print(f"[DEBUG] Found implicit TOC structure at line {i}")
                        break

    if toc_start < 0:
        if debug:
            print("[DEBUG] No TOC found")
        return []

    # Parse table rows after TOC heading
    # Stop when we hit a non-table line or reach 200 lines
    for i in range(toc_start + 1, min(toc_start + 200, len(lines))):
        line = lines[i]

        # Skip separator lines
        if '---' in line or not '|' in line:
            continue

        # Skip if we've left the TOC area (hit actual content)
        if line.strip().startswith('##') and 'PART' in line.upper():
            if debug:
                print(f"[DEBUG] Reached end of TOC at line {i}")
            break

        if '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]

            if len(parts) < 2:
                continue

            # Format 1: 4 columns [section_num, title, title_dup, page]
            # Example: | 1.1 | Preface | Preface | 3 |
            if len(parts) == 4:
                section_num = parts[0].strip()
                title = parts[1].strip()
                page = parts[3].strip()

                # Check if first column is a section number (1.1, 2.3, etc.)
                if re.match(r'^\d+\.?\d*$', section_num) and page.isdigit():
                    if len(title) > 2:
                        toc_entries.append({
                            'number': section_num,
                            'title': title,
                            'page': int(page),
                            'line': i
                        })
                        if debug and len(toc_entries) <= 5:
                            print(f"[DEBUG] Found entry (4-col): {section_num} -> {title} (page {page})")

            # Format 2: 3 columns [section_num+title, dup, page]
            # Example: | 3.8.1 Horizontal Projection | 3.8.1 Horizontal Projection | 28 |
            elif len(parts) == 3:
                first_col = parts[0].strip()
                page = parts[2].strip()

                # Try to extract section number and title from first column
                match = re.match(r'^(\d+\.\d+\.?\d*)\s+(.+)$', first_col)
                if match and page.isdigit():
                    section_num = match.group(1)
                    title = match.group(2).strip()
                    if len(title) > 2:
                        toc_entries.append({
                            'number': section_num,
                            'title': title,
                            'page': int(page),
                            'line': i
                        })
                        if debug and len(toc_entries) <= 5:
                            print(f"[DEBUG] Found entry (3-col): {section_num} -> {title} (page {page})")

            # Format 3: 2 columns [title, page] (for appendices, etc.)
            # Example: | Appendix 1 | 50 |
            elif len(parts) == 2:
                title = parts[0].strip()
                page = parts[1].strip()

                if page.isdigit() and len(title) > 2:
                    # Use title as section number for appendices
                    toc_entries.append({
                        'number': title,
                        'title': title,
                        'page': int(page),
                        'line': i
                    })
                    if debug and len(toc_entries) <= 5:
                        print(f"[DEBUG] Found entry (2-col): {title} (page {page})")

    return toc_entries


def analyze_well_report(pdf_path, search_chars=20000):
    """Parse a well report and extract its TOC"""
    print(f"\n{'='*80}")
    print(f"Analyzing: {pdf_path.name}")
    print(f"{'='*80}")

    try:
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        doc = result.document

        # Get first N characters (should cover first 4 pages)
        full_text = doc.export_to_markdown()
        text = full_text[:search_chars]

        print(f"\n[INFO] Document total length: {len(full_text)} chars")
        print(f"[INFO] Searching first {search_chars} chars")

        # Extract TOC
        toc = extract_toc_from_markdown(text, debug=True)

        if toc:
            print(f"\n[SUCCESS] Found {len(toc)} TOC entries:\n")
            for entry in toc[:20]:  # Show first 20
                print(f"  {entry['number']:10} {entry['title']:60} (page {entry['page']})")

            if len(toc) > 20:
                print(f"  ... and {len(toc) - 20} more entries")

            # Show key sections we care about (casing, completion, depth)
            print(f"\n[KEY SECTIONS]")
            for entry in toc:
                title_lower = entry['title'].lower()
                if any(kw in title_lower for kw in ['casing', 'completion', 'depth', 'trajectory', 'borehole', 'tubular', 'well data']):
                    print(f"  >> {entry['number']:10} {entry['title']:60} (page {entry['page']})")

            return toc
        else:
            print("\n[FAILED] NO TOC FOUND")
            return []

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return []


# Main test
data_dir = Path(__file__).parent.parent / "Training data-shared with participants"

test_wells = {
    'Well 5': 'NLW-GT-03',
    'Well 7': 'BRI-GT-01'
}

all_results = {}

for well_name, well_code in test_wells.items():
    well_dir = data_dir / well_name / "Well report"

    if well_dir.exists():
        # Find EOWR files
        eowr_files = []
        for f in well_dir.rglob("*.pdf"):
            if any(kw in f.name.lower() for kw in ['eowr', 'final-well-report', 'final well report']):
                eowr_files.append(f)

        if eowr_files:
            print(f"\n{'#'*80}")
            print(f"# {well_name} ({well_code})")
            print(f"# Found {len(eowr_files)} EOWR file(s)")
            print(f"{'#'*80}")

            # Analyze first EOWR file
            toc = analyze_well_report(eowr_files[0], search_chars=20000)
            all_results[well_name] = toc

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
for well_name, toc in all_results.items():
    status = f"OK - {len(toc)} entries" if toc else "FAILED - NO TOC FOUND"
    print(f"{well_name:15} {status}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
