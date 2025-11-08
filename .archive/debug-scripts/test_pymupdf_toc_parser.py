"""Test: Parse TOC from PyMuPDF multi-line format"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz
import re

def extract_pymupdf_multiline_toc(text):
    """
    Parse TOC from PyMuPDF multi-line format:
    - Line 1: TITLE ...................
    - Line 2: PAGE_NUMBER

    OR

    - Line 1: SECTION_NUMBER
    - Line 2: TITLE ...................
    """
    lines = text.split('\n')

    # Find "Contents" heading
    toc_start = -1
    for i, line in enumerate(lines):
        if line.strip().lower() in ['contents', 'table of contents']:
            toc_start = i
            break

    if toc_start < 0:
        return []

    toc_entries = []
    i = toc_start + 1

    while i < min(toc_start + 200, len(lines)):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Stop at next section (Page X:)
        if line.startswith('Page ') or line.startswith('PAGE '):
            break

        # Pattern 1: Line with dots (title line)
        # Example: "GLOSSARY .............................."
        if '.' in line and line.count('.') >= 5:
            title = re.sub(r'\.{2,}.*$', '', line).strip()

            # Check next line for page number
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.isdigit():
                    page = int(next_line)

                    # Check if there's a section number on prev line
                    if i > toc_start + 1:
                        prev_line = lines[i - 1].strip()
                        if re.match(r'^\d+\.?\d*$', prev_line):
                            section_num = prev_line
                        else:
                            section_num = ""
                    else:
                        section_num = ""

                    if title and len(title) > 2:
                        toc_entries.append({
                            'number': section_num if section_num else title,
                            'title': title,
                            'page': page
                        })

                    i += 2  # Skip title + page number
                    continue

        # Pattern 2: Standalone section number
        # Example: "2.1"
        if re.match(r'^\d+\.?\d*$', line):
            section_num = line

            # Check next line for title
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                # Title might have dots
                if next_line and len(next_line) > 2:
                    title = re.sub(r'\.{2,}.*$', '', next_line).strip()

                    # Page number might be on line after title
                    page = None
                    if i + 2 < len(lines):
                        page_line = lines[i + 2].strip()
                        if page_line.isdigit():
                            page = int(page_line)

                    if title:
                        toc_entries.append({
                            'number': section_num,
                            'title': title,
                            'page': page if page else 0
                        })

                    i += 3 if page else 2
                    continue

        i += 1

    return toc_entries


# Test on Well 1
data_dir = Path(__file__).parent.parent / "Training data-shared with participants" / "Well 1"
well_reports_dir = data_dir / "Well report"

eowr_files = [f for f in well_reports_dir.rglob("*.pdf") if 'eowr' in f.name.lower()]
if eowr_files:
    test_pdf = eowr_files[0]
    print(f"Testing: {test_pdf.name}\n")

    doc = fitz.open(str(test_pdf))
    text = ""
    for page_num in range(min(4, len(doc))):
        text += doc[page_num].get_text() + "\n\n"
    doc.close()

    # Extract TOC
    toc = extract_pymupdf_multiline_toc(text)

    if toc:
        print(f"SUCCESS! Found {len(toc)} TOC entries:\n")
        for entry in toc:
            print(f"  {entry['number']:10} {entry['title']:50} (page {entry['page']})")
    else:
        print("FAILED - No TOC found")

else:
    print("No EOWR file found")
