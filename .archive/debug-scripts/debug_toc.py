"""Debug: See what the TOC actually looks like in the PDF"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter

# Parse Well 5 EOWR
data_dir = Path(__file__).parent.parent / "Training data-shared with participants" / "Well 5"
well_reports_dir = data_dir / "Well report"

eowr_files = list(well_reports_dir.rglob("*EOWR*.pdf"))
if eowr_files:
    test_pdf = eowr_files[0]
    print(f"Parsing: {test_pdf.name}\n")

    converter = DocumentConverter()
    result = converter.convert(str(test_pdf))
    doc = result.document

    # Get full text
    full_text = doc.export_to_markdown()

    # Show first 5000 characters (should include TOC)
    print("="*80)
    print("FIRST 5000 CHARACTERS OF DOCUMENT:")
    print("="*80)
    print(full_text[:5000])
    print("="*80)

    # Look for lines that might be TOC entries
    print("\nLINES CONTAINING NUMBERS AND DOTS (possible TOC):")
    print("="*80)
    lines = full_text[:5000].split('\n')
    for i, line in enumerate(lines):
        # Look for lines with numbers and dots
        if '.' in line and any(char.isdigit() for char in line):
            print(f"Line {i}: {line}")

else:
    print("No EOWR file found")
