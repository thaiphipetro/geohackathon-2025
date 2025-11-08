"""Debug: Process Well 7 with OCR on pages 1-10 to find TOC"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
import tempfile
import os

# Well 7
data_dir = Path(__file__).parent.parent / "Training data-shared with participants" / "Well 7"
well_reports_dir = data_dir / "Well report"

eowr_files = [f for f in well_reports_dir.rglob("*.pdf") if 'eowr' in f.name.lower()]
if eowr_files:
    test_pdf = eowr_files[0]
    print(f"Processing: {test_pdf.name}\n")

    # Extract first 10 pages to temp PDF
    doc = fitz.open(str(test_pdf))
    num_pages = min(10, len(doc))

    temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_path = temp_pdf.name
    temp_pdf.close()

    new_doc = fitz.open()
    for i in range(num_pages):
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
    new_doc.save(temp_path)
    new_doc.close()
    doc.close()

    print(f"Extracted {num_pages} pages to temp PDF\n")

    # Process with Docling + OCR
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    result = converter.convert(temp_path)
    markdown = result.document.export_to_markdown()

    # Clean up
    os.unlink(temp_path)

    print(f"Total OCR output length: {len(markdown)} chars\n")

    # Search for key markers
    lines = markdown.split('\n')

    # Find "Government notification"
    gov_idx = None
    for i, line in enumerate(lines):
        if 'government' in line.lower() and 'notification' in line.lower():
            gov_idx = i
            print(f"{'='*80}")
            print(f"FOUND 'Government notification' at line {i}: {line}")
            print(f"{'='*80}\n")
            # Show 50 lines after
            for j in range(i, min(i+50, len(lines))):
                print(f"{j:3}: {lines[j]}")
            break

    if not gov_idx:
        print("'Government notification' NOT FOUND\n")

        # Find APPENDICES
        for i, line in enumerate(lines):
            if 'appendices' in line.lower():
                print(f"{'='*80}")
                print(f"FOUND 'APPENDICES' at line {i}: {line}")
                print(f"{'='*80}\n")
                # Show 20 lines before and 10 after
                for j in range(max(0, i-20), min(i+10, len(lines))):
                    prefix = ">>> " if j == i else "    "
                    print(f"{prefix}{j:3}: {lines[j]}")
                break

else:
    print("No EOWR file found")
