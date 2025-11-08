"""Debug: Check Well 7's PyMuPDF plain text extraction"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz

# Well 7
data_dir = Path(__file__).parent.parent / "Training data-shared with participants" / "Well 7"
well_reports_dir = data_dir / "Well report"

eowr_files = [f for f in well_reports_dir.rglob("*.pdf") if 'eowr' in f.name.lower()]
if eowr_files:
    test_pdf = eowr_files[0]
    print(f"Processing: {test_pdf.name}\n")

    doc = fitz.open(str(test_pdf))

    # Check first 4 pages
    for page_num in range(min(4, len(doc))):
        print(f"{'='*80}")
        print(f"PAGE {page_num + 1} - PyMuPDF Text Extraction:")
        print(f"{'='*80}")
        page_text = doc[page_num].get_text()
        print(f"Length: {len(page_text)} chars")
        print(page_text[:1500] if page_text else "[NO TEXT EXTRACTED]")
        print("\n")

    doc.close()

    # Now check for "Government notification" and "APPENDICES" markers
    doc = fitz.open(str(test_pdf))
    text = ""
    for page_num in range(min(4, len(doc))):
        text += doc[page_num].get_text() + "\n\n"
    doc.close()

    lines = text.split('\n')

    # Find Government notification
    gov_idx = None
    app_idx = None

    for i, line in enumerate(lines):
        if 'government' in line.lower() and 'notification' in line.lower():
            gov_idx = i
            print(f"{'='*80}")
            print(f"FOUND 'Government notification' at line {i}: {line}")
            print(f"{'='*80}\n")
        if 'appendices' in line.lower() or 'appendix' in line.lower():
            if app_idx is None:  # First occurrence
                app_idx = i
                print(f"{'='*80}")
                print(f"FOUND 'APPENDICES' at line {i}: {line}")
                print(f"{'='*80}\n")

    # Extract content between markers
    if gov_idx is not None and app_idx is not None:
        print(f"{'='*80}")
        print(f"CONTENT BETWEEN 'Government notification' (line {gov_idx}) and 'APPENDICES' (line {app_idx}):")
        print(f"{'='*80}\n")
        for i in range(gov_idx, min(app_idx, gov_idx + 50)):
            print(f"{i:3}: {lines[i]}")
    else:
        print(f"\nCouldn't find both markers:")
        print(f"  Government notification: {'FOUND' if gov_idx else 'NOT FOUND'}")
        print(f"  APPENDICES: {'FOUND' if app_idx else 'NOT FOUND'}")

else:
    print("No EOWR file found")
