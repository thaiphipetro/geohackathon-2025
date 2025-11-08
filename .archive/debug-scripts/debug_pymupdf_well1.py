"""Debug: See what PyMuPDF actually extracts from Well 1"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz  # PyMuPDF

# Open Well 1 EOWR
data_dir = Path(__file__).parent.parent / "Training data-shared with participants" / "Well 1"
well_reports_dir = data_dir / "Well report"

eowr_files = [f for f in well_reports_dir.rglob("*.pdf") if 'eowr' in f.name.lower()]
if eowr_files:
    test_pdf = eowr_files[0]
    print(f"Opening: {test_pdf.name}\n")

    doc = fitz.open(str(test_pdf))

    print(f"Total pages: {len(doc)}")
    print(f"\n{'='*80}")
    print(f"FIRST 4 PAGES TEXT (PyMuPDF extraction):")
    print(f"{'='*80}\n")

    full_text = ""
    for page_num in range(min(4, len(doc))):
        page_text = doc[page_num].get_text()
        full_text += f"\n{'='*80}\n"
        full_text += f"PAGE {page_num + 1}:\n"
        full_text += f"{'='*80}\n"
        full_text += page_text
        full_text += "\n"

    doc.close()

    # Print full text
    print(full_text[:8000])  # First 8000 chars

    # Save to file for detailed inspection
    output_file = Path(__file__).parent.parent / "outputs" / "exploration" / "well_1_pymupdf_text.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_text)

    print(f"\n{'='*80}")
    print(f"Full text saved to: {output_file}")
    print(f"Total characters extracted: {len(full_text)}")
    print(f"{'='*80}")

    # Look for "Contents" keyword
    lines = full_text.split('\n')
    print(f"\n{'='*80}")
    print(f"SEARCHING FOR 'CONTENTS' KEYWORD:")
    print(f"{'='*80}\n")

    for i, line in enumerate(lines):
        if 'content' in line.lower():
            print(f"Line {i}: {line}")
            # Show context: 5 lines before and 30 lines after
            print(f"\n[CONTEXT - 5 lines before to 30 lines after]:")
            for j in range(max(0, i-5), min(len(lines), i+30)):
                prefix = ">>>" if j == i else "   "
                print(f"{prefix} {j:3}: {lines[j][:120]}")
            break
    else:
        print("No 'contents' keyword found")
        print("\nShowing lines 50-150 (where TOC usually is):")
        for i in range(50, min(150, len(lines))):
            print(f"{i:3}: {lines[i][:120]}")

else:
    print("No EOWR file found")
