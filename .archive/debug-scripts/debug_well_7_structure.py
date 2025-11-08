"""Debug: Show the structure of Well 7 EOWR to understand TOC format"""
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

    # Get text
    full_text = doc.export_to_markdown()
    lines = full_text.split('\n')

    print(f"Total document length: {len(full_text)} chars")
    print(f"Total lines: {len(lines)}")

    # Show first 150 lines
    print(f"\n{'='*80}")
    print(f"FIRST 150 LINES:")
    print(f"{'='*80}\n")

    for i in range(min(150, len(lines))):
        line = lines[i]
        # Highlight important patterns
        prefix = "      "
        if '|' in line:
            prefix = "[TBL]"
        elif any(kw in line.lower() for kw in ['content', 'index', 'toc', 'table']):
            prefix = "[TOC?]"
        elif line.strip().startswith('##'):
            prefix = "[HDR]"
        elif any(char.isdigit() for char in line) and '.' in line and len(line.strip()) < 50:
            prefix = "[NUM]"

        print(f"{prefix} {i:3}: {line[:100]}")

    # Look for specific patterns
    print(f"\n{'='*80}")
    print(f"LINES WITH 'CONTENT' OR 'INDEX':")
    print(f"{'='*80}\n")

    for i, line in enumerate(lines[:300]):
        if any(kw in line.lower() for kw in ['content', 'index', 'inhoud']):
            print(f"Line {i}: {line}")

    # Show table structures
    print(f"\n{'='*80}")
    print(f"TABLE STRUCTURES (first 30 tables):")
    print(f"{'='*80}\n")

    table_count = 0
    for i, line in enumerate(lines[:500]):
        if '|' in line and '---' not in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                table_count += 1
                if table_count <= 30:
                    print(f"Line {i}: {len(parts)} cols - {parts}")
                if table_count == 30:
                    print("\n... (showing first 30 tables only)")
                    break

else:
    print("No EOWR file found")
