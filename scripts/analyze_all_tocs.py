"""Analyze Table of Contents from multiple well reports"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter
import re
from collections import defaultdict

def extract_toc_from_markdown(text):
    """Extract TOC from markdown text"""
    toc_entries = []
    lines = text.split('\n')

    # Look for table-based TOC format
    for line in lines:
        if '|' in line and any(char.isdigit() for char in line):
            parts = [p.strip() for p in line.split('|') if p.strip()]

            if len(parts) >= 2:
                first_col = parts[0].strip()

                if re.match(r'^\d+\.?[\d\.]*$', first_col):
                    last_col = parts[-1].strip()

                    # Extract title and page
                    page_match = re.search(r'\.{2,}\s*(\d+)\s*$', last_col)
                    if page_match:
                        page_num = int(page_match.group(1))
                        title = re.sub(r'\.{2,}\s*\d+\s*$', '', last_col).strip()

                        if title and len(title) > 2:
                            toc_entries.append({
                                'number': first_col,
                                'title': title,
                                'page': page_num
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

        # Get first 8000 chars (should cover TOC)
        text = doc.export_to_markdown()[:8000]

        # Extract TOC
        toc = extract_toc_from_markdown(text)

        if toc:
            print(f"\nFound {len(toc)} TOC entries:\n")
            for entry in toc[:15]:  # Show first 15
                print(f"  {entry['number']:6} {entry['title']:60} (page {entry['page']})")

            if len(toc) > 15:
                print(f"  ... and {len(toc) - 15} more entries")

            return toc
        else:
            print("[NO TOC FOUND]")
            return []

    except Exception as e:
        print(f"[ERROR] {e}")
        return []

# Main analysis
data_dir = Path(__file__).parent.parent / "Training data-shared with participants"

# Analyze multiple wells
target_wells = ['Well 1', 'Well 2', 'Well 5', 'Well 7']
all_tocs = {}
all_section_titles = defaultdict(int)

for well_name in target_wells:
    well_dir = data_dir / well_name / "Well report"

    if well_dir.exists():
        # Find EOWR files
        eowr_files = []
        for f in well_dir.rglob("*.pdf"):
            if any(kw in f.name.lower() for kw in ['eowr', 'final-well-report']):
                eowr_files.append(f)

        if eowr_files:
            # Analyze first EOWR file
            toc = analyze_well_report(eowr_files[0])
            all_tocs[well_name] = toc

            # Count section titles
            for entry in toc:
                title_lower = entry['title'].lower()
                all_section_titles[title_lower] += 1

# Analysis Summary
print("\n" + "="*80)
print("CROSS-WELL TOC ANALYSIS")
print("="*80)

print("\n1. MOST COMMON SECTION TITLES (across all wells):")
print("-" * 80)
sorted_sections = sorted(all_section_titles.items(), key=lambda x: x[1], reverse=True)
for title, count in sorted_sections[:30]:
    print(f"  {count}x  {title}")

# Categorize sections
print("\n2. SECTION CATEGORIZATION:")
print("-" * 80)

casing_related = []
depth_trajectory = []
technical_summary = []
operational = []
geology = []
administrative = []
other = []

for title, count in sorted_sections:
    title_lower = title.lower()

    if any(kw in title_lower for kw in ['casing', 'completion', 'tubular', 'wellbore schematic', 'well construction']):
        casing_related.append((title, count))
    elif any(kw in title_lower for kw in ['depth', 'trajectory', 'survey']):
        depth_trajectory.append((title, count))
    elif any(kw in title_lower for kw in ['technical summary', 'well summary', 'summary']):
        technical_summary.append((title, count))
    elif any(kw in title_lower for kw in ['drilling', 'operational', 'operation', 'rig']):
        operational.append((title, count))
    elif any(kw in title_lower for kw in ['geology', 'lithology', 'formation', 'geolog']):
        geology.append((title, count))
    elif any(kw in title_lower for kw in ['project', 'organisation', 'organization', 'approval', 'revision', 'abbreviation', 'definition']):
        administrative.append((title, count))
    else:
        other.append((title, count))

print("\nA. CASING/COMPLETION RELATED (HIGH PRIORITY):")
for title, count in casing_related:
    print(f"  {count}x  {title}")

print("\nB. DEPTH/TRAJECTORY (MEDIUM-HIGH PRIORITY):")
for title, count in depth_trajectory:
    print(f"  {count}x  {title}")

print("\nC. TECHNICAL SUMMARY (MEDIUM-HIGH PRIORITY):")
for title, count in technical_summary:
    print(f"  {count}x  {title}")

print("\nD. OPERATIONAL/DRILLING (MEDIUM PRIORITY):")
for title, count in operational[:10]:
    print(f"  {count}x  {title}")

print("\nE. GEOLOGY (LOW PRIORITY):")
for title, count in geology[:10]:
    print(f"  {count}x  {title}")

print("\nF. ADMINISTRATIVE (LOW PRIORITY):")
for title, count in administrative[:10]:
    print(f"  {count}x  {title}")

print("\nG. OTHER:")
for title, count in other[:10]:
    print(f"  {count}x  {title}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
