"""Fixed TOC extraction that works with actual well report formats"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter
import re
from collections import defaultdict

def extract_toc_from_markdown(text, debug=False):
    """
    Extract TOC from markdown text - handles multiple formats:
    - Table format with 4 columns: | section | title | title_dup | page |
    - Table format with 3 columns: | section+title | dup | page |
    - Plain text format: section title .... page
    """
    toc_entries = []
    lines = text.split('\n')

    # Find "Table of Contents" or similar heading
    toc_start = -1
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        toc_keywords = [
            'table of contents', 'contents', 'index', 'table des matieres',
            'inhoud', 'inhaltsverzeichnis'
        ]
        if any(kw in line_lower for kw in toc_keywords):
            toc_start = i
            if debug:
                print(f"[DEBUG] Found TOC heading at line {i}")
            break

    # If no explicit TOC heading, look for implicit TOC structure
    if toc_start < 0:
        for i in range(min(300, len(lines))):
            line = lines[i]
            if '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    first_col = parts[0].strip()
                    last_col = parts[-1].strip()
                    if re.match(r'^\d+\.?\d*$', first_col) and last_col.isdigit():
                        toc_start = i
                        if debug:
                            print(f"[DEBUG] Found implicit TOC at line {i}")
                        break

    if toc_start < 0:
        return []

    # Parse table rows after TOC start
    for i in range(toc_start + 1, min(toc_start + 200, len(lines))):
        line = lines[i]

        # Skip separator lines and empty lines
        if '---' in line or not line.strip():
            continue

        # Stop if we've left the TOC area
        if line.strip().startswith('##') and any(kw in line.upper() for kw in ['PART', 'CHAPTER']):
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

                if re.match(r'^\d+\.?\d*$', section_num) and page.isdigit():
                    if len(title) > 2:
                        toc_entries.append({
                            'number': section_num,
                            'title': title,
                            'page': int(page)
                        })

            # Format 2: 3 columns [section_num+title, dup, page]
            # Example: | 3.8.1 Horizontal Projection | 3.8.1 Horizontal Projection | 28 |
            elif len(parts) == 3:
                first_col = parts[0].strip()
                page = parts[2].strip()

                match = re.match(r'^(\d+\.\d+\.?\d*)\s+(.+)$', first_col)
                if match and page.isdigit():
                    section_num = match.group(1)
                    title = match.group(2).strip()
                    if len(title) > 2:
                        toc_entries.append({
                            'number': section_num,
                            'title': title,
                            'page': int(page)
                        })

            # Format 3: 2 columns [title, page] (for appendices)
            elif len(parts) == 2:
                title = parts[0].strip()
                page = parts[1].strip()

                if page.isdigit() and len(title) > 2:
                    toc_entries.append({
                        'number': title,
                        'title': title,
                        'page': int(page)
                    })

    return toc_entries


def analyze_well_report(pdf_path):
    """Parse a well report and extract its TOC"""
    print(f"\n{'='*80}")
    print(f"Analyzing: {pdf_path.name}")
    print(f"{'='*80}")

    try:
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        doc = result.document

        # Get first 20000 chars (covers first ~4 pages)
        text = doc.export_to_markdown()[:20000]

        # Extract TOC
        toc = extract_toc_from_markdown(text)

        if toc:
            print(f"\n[SUCCESS] Found {len(toc)} TOC entries\n")
            for entry in toc[:15]:
                print(f"  {entry['number']:10} {entry['title']:60} (page {entry['page']})")

            if len(toc) > 15:
                print(f"  ... and {len(toc) - 15} more entries")

            # Show key sections for parameter extraction
            print(f"\n[KEY SECTIONS FOR PARAMETER EXTRACTION]")
            key_count = 0
            for entry in toc:
                title_lower = entry['title'].lower()
                if any(kw in title_lower for kw in ['casing', 'completion', 'depth', 'trajectory',
                                                     'borehole', 'tubular', 'well data', 'technical summary',
                                                     'hole section', 'well construction']):
                    print(f"  >> {entry['number']:10} {entry['title']:60} (page {entry['page']})")
                    key_count += 1

            if key_count == 0:
                print("  (No key sections identified)")

            return toc
        else:
            print("\n[FAILED] NO TOC FOUND")
            print("  This may be due to:")
            print("  - Scanned image that OCR couldn't extract")
            print("  - Different TOC format not supported")
            print("  - No TOC in document")
            return []

    except Exception as e:
        print(f"\n[ERROR] {e}")
        return []


# Main analysis - test on all 8 wells
data_dir = Path(__file__).parent.parent / "Training data-shared with participants"

all_tocs = {}
all_section_titles = defaultdict(int)

print("\n" + "#"*80)
print("# TOC EXTRACTION ANALYSIS - ALL WELLS")
print("#"*80)

for well_num in range(1, 9):
    well_name = f"Well {well_num}"
    well_dir = data_dir / well_name / "Well report"

    if well_dir.exists():
        # Find EOWR files
        eowr_files = []
        for f in well_dir.rglob("*.pdf"):
            if any(kw in f.name.lower() for kw in ['eowr', 'final-well-report', 'final well report', 'end-of-well']):
                eowr_files.append(f)

        if eowr_files:
            print(f"\n{'#'*80}")
            print(f"# {well_name}")
            print(f"# Found {len(eowr_files)} EOWR file(s)")
            print(f"{'#'*80}")

            # Analyze first EOWR file
            toc = analyze_well_report(eowr_files[0])
            all_tocs[well_name] = toc

            # Count section titles for cross-well analysis
            for entry in toc:
                title_lower = entry['title'].lower()
                all_section_titles[title_lower] += 1

# Summary
print("\n" + "="*80)
print("SUMMARY - TOC EXTRACTION SUCCESS RATE")
print("="*80)

success_count = 0
for well_name, toc in all_tocs.items():
    status = "OK" if toc else "FAILED"
    count = len(toc) if toc else 0
    print(f"{well_name:15} {status:8} {count:3} entries")
    if toc:
        success_count += 1

print(f"\nSuccess Rate: {success_count}/{len(all_tocs)} wells ({100*success_count//len(all_tocs)}%)")

# Most common sections across wells
if all_section_titles:
    print("\n" + "="*80)
    print("MOST COMMON SECTIONS (across all wells)")
    print("="*80)
    sorted_sections = sorted(all_section_titles.items(), key=lambda x: x[1], reverse=True)
    for title, count in sorted_sections[:20]:
        print(f"  {count}x  {title}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
