"""Debug: Show lines 30-200 of Well 7 (where page 2 should be)"""
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

    print(f"\n{'='*80}")
    print(f"LINES 30-200 (PAGE 2 AREA):")
    print(f"{'='*80}\n")

    for i in range(30, min(200, len(lines))):
        line = lines[i]
        # Highlight important patterns
        prefix = "      "
        if '|' in line and '---' not in line:
            prefix = "[TBL]"
        elif line.strip().startswith('##'):
            prefix = "[HDR]"
        elif any(char.isdigit() for char in line) and '.' in line and len(line.strip()) < 80:
            prefix = "[NUM]"

        print(f"{prefix} {i:3}: {line[:120]}")

else:
    print("No EOWR file found")
