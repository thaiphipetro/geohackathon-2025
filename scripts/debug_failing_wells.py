"""Debug: Check TOC formats for Wells 2, 4, 7, 8"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz
import io
import sys

# Redirect stdout to handle Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data_dir = Path(__file__).parent.parent / "Training data-shared with participants"

failing_wells = {
    "Well 2": "NLOG_GS_PUB_HAG GT-01-02 CT Cleanout SodM EOWR v1.0.pdf",
    "Well 4": "NLOG_GS_PUB_EOWR NLW-GT-02 GRE workover SodM.pdf",
    "Well 8": "NLOG_GS_PUB_MSD-GT-01 EOWR_with_appendices_Redacted.pdf"
}

print("Debugging Wells 2, 4, 8 (native PDFs)")
print("Well 7 skipped - scanned image requiring OCR")

for well_name, filename in failing_wells.items():
    well_dir = data_dir / well_name / "Well report"
    pdf_files = [f for f in well_dir.rglob("*.pdf") if filename in f.name]

    if not pdf_files:
        print(f"\n{'='*80}")
        print(f"{well_name}: PDF not found")
        continue

    pdf_path = pdf_files[0]
    print(f"\n{'='*80}")
    print(f"{well_name}: {pdf_path.name}")
    print(f"{'='*80}\n")

    doc = fitz.open(str(pdf_path))

    # Read first 4 pages
    text = ""
    for page_num in range(min(4, len(doc))):
        text += doc[page_num].get_text() + "\n\n"
    doc.close()

    # Find Contents section
    lines = text.split('\n')
    found = False
    for i, line in enumerate(lines):
        if 'content' in line.lower() and 'table' not in line.lower():
            print(f"FOUND 'Contents' at line {i}: {line}")
            print(f"\n--- Next 40 lines after 'Contents' ---\n")
            for j in range(i+1, min(i+41, len(lines))):
                # Print with line numbers, handle special chars
                try:
                    print(f"{j:3}: {lines[j]}")
                except:
                    print(f"{j:3}: [Unicode error in line]")
            found = True
            break

    if not found:
        print("NO 'Contents' heading found in first 4 pages")
        print("\nFirst 100 lines of text:")
        for i in range(min(100, len(lines))):
            try:
                if lines[i].strip():
                    print(f"{i:3}: {lines[i]}")
            except:
                pass

print(f"\n{'='*80}")
print("Debug complete")
print(f"{'='*80}")
