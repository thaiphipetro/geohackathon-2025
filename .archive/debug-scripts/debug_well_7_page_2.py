"""Debug: Find Contents section in Well 7 on page 2"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter

# Parse Well 7 EOWR
data_dir = Path(__file__).parent.parent / "Training data-shared with participants" / "Well 7"
well_reports_dir = data_dir / "Well report"

eowr_files = [f for f in well_reports_dir.rglob("*.pdf") if 'EOWR' in f.name or 'eowr' in f.name]
if eowr_files:
    test_pdf = eowr_files[0]
    print(f"Parsing: {test_pdf.name}\n")

    converter = DocumentConverter()
    result = converter.convert(str(test_pdf))
    doc = result.document

    # Get full text
    full_text = doc.export_to_markdown()
    lines = full_text.split('\n')

    print(f"Total document length: {len(full_text)} chars")
    print(f"Total lines: {len(lines)}")

    # Search for "Contents" or "content" anywhere
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
                print(f"{prefix} {j:3}: {lines[j]}")
            print()

else:
    print("No EOWR file found")
