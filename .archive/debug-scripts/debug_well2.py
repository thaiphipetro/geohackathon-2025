"""Debug: Check Well 2's TOC format"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz

# Well 2
data_dir = Path(__file__).parent.parent / "Training data-shared with participants" / "Well 2"
well_reports_dir = data_dir / "Well report"

eowr_files = [f for f in well_reports_dir.rglob("*.pdf") if 'eowr' in f.name.lower()]
if eowr_files:
    test_pdf = eowr_files[0]
    print(f"Processing: {test_pdf.name}\n")

    doc = fitz.open(str(test_pdf))
    text = ""
    for page_num in range(min(4, len(doc))):
        print(f"================================================================================")
        print(f"PAGE {page_num + 1}:")
        print(f"================================================================================")
        page_text = doc[page_num].get_text()
        print(page_text[:1500])  # First 1500 chars
        print("\n")
        text += page_text + "\n\n"
    doc.close()

    # Search for "Contents" line
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'content' in line.lower() or 'table of content' in line.lower():
            print(f"\n{'='*80}")
            print(f"FOUND 'CONTENTS' at line {i}")
            print(f"{'='*80}\n")
            # Show 30 lines after Contents
            for j in range(i, min(i+30, len(lines))):
                print(f"{j:3}: {lines[j]}")
            break

else:
    print("No EOWR file found")
