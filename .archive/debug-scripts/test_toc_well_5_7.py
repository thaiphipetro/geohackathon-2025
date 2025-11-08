"""Test TOC extraction on Well 5 and Well 7 with detailed debugging"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter
import re

def extract_toc_from_markdown(text, debug=True):
    """Extract TOC from markdown text with detailed debugging"""
    toc_entries = []
    lines = text.split('\n')

    if debug:
        print(f"\n[DEBUG] Total lines to search: {len(lines)}")
        print(f"[DEBUG] Total characters: {len(text)}")

    # Pattern 1: Table-based TOC format
    # Format: |   1. | Project Details ........... 5   |
    table_pattern_count = 0
    for i, line in enumerate(lines):
        if '|' in line and any(char.isdigit() for char in line):
            table_pattern_count += 1
            parts = [p.strip() for p in line.split('|') if p.strip()]

            if len(parts) >= 2:
                first_col = parts[0].strip()

                # Check if it looks like a section number (1., 1.1, 2.2, etc.)
                if re.match(r'^\d+\.?[\d\.]*$', first_col):
                    last_col = parts[-1].strip()

                    # Extract title and page from "Title ........ 5" format
                    page_match = re.search(r'\.{2,}\s*(\d+)\s*$', last_col)
                    if page_match:
                        page_num = int(page_match.group(1))
                        title = re.sub(r'\.{2,}\s*\d+\s*$', '', last_col).strip()

                        if title and len(title) > 2:
                            if debug and len(toc_entries) < 5:
                                print(f"[DEBUG] Found TOC entry at line {i}: '{first_col}' -> '{title}' (page {page_num})")
                            toc_entries.append({
                                'number': first_col,
                                'title': title,
                                'page': page_num,
                                'line': i
                            })

    if debug:
        print(f"[DEBUG] Lines with table pattern (|...): {table_pattern_count}")

    # Pattern 2: Plain text format (without tables)
    # Format: "1.2 Title ........... 5" or "1.2  Title  5"
    if not toc_entries:
        if debug:
            print("[DEBUG] No table-based TOC found. Trying plain text format...")

        for i, line in enumerate(lines):
            line = line.strip()
            # Look for lines starting with section numbers
            match = re.match(r'^(\d+\.?[\d\.]*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$', line)
            if not match:
                # Try alternate format without dots: "1.2  Title  5"
                match = re.match(r'^(\d+\.?[\d\.]*)\s+(.+?)\s+(\d+)\s*$', line)

            if match:
                section_num, title, page_num = match.groups()
                if len(title.strip()) > 2:
                    if debug and len(toc_entries) < 5:
                        print(f"[DEBUG] Found TOC entry at line {i}: '{section_num}' -> '{title}' (page {page_num})")
                    toc_entries.append({
                        'number': section_num,
                        'title': title.strip(),
                        'page': int(page_num),
                        'line': i
                    })

    # Pattern 3: Look for "Contents" or "Table of Contents" heading
    toc_heading_line = -1
    for i, line in enumerate(lines[:200]):  # Check first 200 lines
        line_lower = line.lower().strip()
        if line_lower in ['contents', 'table of contents', 'table of content'] or \
           line_lower.startswith('table of contents') or \
           line_lower.startswith('contents'):
            toc_heading_line = i
            if debug:
                print(f"[DEBUG] Found TOC heading at line {i}: '{line}'")
            break

    # If we found a TOC heading but no entries, show the lines after it
    if toc_heading_line >= 0 and not toc_entries:
        if debug:
            print(f"\n[DEBUG] TOC heading found but no entries extracted. Lines after heading:")
            for i in range(toc_heading_line + 1, min(toc_heading_line + 30, len(lines))):
                print(f"  Line {i}: {lines[i][:100]}")

    return toc_entries


def analyze_well_report(pdf_path, search_chars=20000):
    """Parse a well report and extract its TOC with detailed debugging"""
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
        print(f"[INFO] Searching first {search_chars} chars (~first 4 pages)")

        # Show a sample of what the text looks like
        print(f"\n[SAMPLE] First 500 characters:")
        print("-" * 80)
        print(text[:500])
        print("-" * 80)

        # Extract TOC
        toc = extract_toc_from_markdown(text, debug=True)

        if toc:
            print(f"\n[SUCCESS] Found {len(toc)} TOC entries:\n")
            for entry in toc[:15]:  # Show first 15
                print(f"  {entry['number']:6} {entry['title']:60} (page {entry['page']}, line {entry.get('line', '?')})")

            if len(toc) > 15:
                print(f"  ... and {len(toc) - 15} more entries")

            return toc
        else:
            print("\n[FAILED] NO TOC FOUND")
            print("\n[DEBUG] Searching for 'content' keyword in text...")
            for i, line in enumerate(text.split('\n')[:300]):
                if 'content' in line.lower():
                    print(f"  Line {i}: {line[:100]}")
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

            # Analyze first EOWR file with 20,000 character search
            analyze_well_report(eowr_files[0], search_chars=20000)
        else:
            print(f"\n[WARNING] No EOWR files found for {well_name}")
    else:
        print(f"\n[WARNING] Well directory not found: {well_dir}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
