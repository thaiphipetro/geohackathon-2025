"""Debug: Check what's in the image sections of Well 7"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption

# Parse Well 7 EOWR with aggressive OCR
data_dir = Path(__file__).parent.parent / "Training data-shared with participants" / "Well 7"
well_reports_dir = data_dir / "Well report"

eowr_files = [f for f in well_reports_dir.rglob("*.pdf") if 'EOWR' in f.name or 'eowr' in f.name]
if eowr_files:
    test_pdf = eowr_files[0]
    print(f"Parsing: {test_pdf.name}\n")

    # Try with OCR enabled
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    result = converter.convert(str(test_pdf))
    doc = result.document

    # Get full text
    full_text = doc.export_to_markdown()
    lines = full_text.split('\n')

    print(f"Total document length: {len(full_text)} chars")
    print(f"Total lines: {len(lines)}")

    # Show first 100 lines (before APPENDICES)
    print(f"\n{'='*80}")
    print(f"FIRST 100 LINES (before APPENDICES):")
    print(f"{'='*80}\n")

    for i in range(min(100, len(lines))):
        line = lines[i]
        if 'APPENDICES' in line.upper():
            print(f"\n[STOPPED AT LINE {i} - APPENDICES FOUND]")
            break

        prefix = "      "
        if '|' in line and '---' not in line:
            prefix = "[TBL]"
        elif 'image' in line.lower():
            prefix = "[IMG]"

        print(f"{prefix} {i:3}: {line[:120]}")

else:
    print("No EOWR file found")
