"""Debug: Show the actual TOC table structure in Well 5"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter

# Parse Well 5 Final-Well-Report
data_dir = Path(__file__).parent.parent / "Training data-shared with participants" / "Well 5"
well_reports_dir = data_dir / "Well report"

eowr_files = [f for f in well_reports_dir.rglob("*.pdf") if 'Final-Well-Report' in f.name]
if eowr_files:
    test_pdf = eowr_files[0]
    print(f"Parsing: {test_pdf.name}\n")

    converter = DocumentConverter()
    result = converter.convert(str(test_pdf))
    doc = result.document

    # Get text around TOC
    full_text = doc.export_to_markdown()
    lines = full_text.split('\n')

    # Find "Table of Contents" line
    toc_start = -1
    for i, line in enumerate(lines):
        if 'Table of Contents' in line:
            toc_start = i
            print(f"Found 'Table of Contents' at line {i}")
            break

    if toc_start >= 0:
        # Show 100 lines after TOC heading
        print(f"\n{'='*80}")
        print(f"100 LINES AFTER 'Table of Contents' HEADING:")
        print(f"{'='*80}\n")

        for i in range(toc_start, min(toc_start + 100, len(lines))):
            line = lines[i]
            # Highlight lines with table separators
            if '|' in line:
                print(f"[TABLE] Line {i}: {line}")
            else:
                print(f"        Line {i}: {line}")

        # Now show just the table rows
        print(f"\n{'='*80}")
        print(f"TABLE ROWS ONLY (with | character):")
        print(f"{'='*80}\n")

        for i in range(toc_start, min(toc_start + 100, len(lines))):
            line = lines[i]
            if '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                print(f"Line {i}: {len(parts)} columns")
                for j, part in enumerate(parts):
                    print(f"  Col {j}: '{part}'")
                print()

else:
    print("No EOWR file found")
