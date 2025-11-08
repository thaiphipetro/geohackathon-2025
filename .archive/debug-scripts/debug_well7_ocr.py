"""Debug: Check Well 7's OCR output from Docling"""
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

    # Extract first 4 pages to temp PDF
    doc = fitz.open(str(test_pdf))
    num_pages = min(4, len(doc))

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
    pipeline_options.do_ocr = True  # Enable OCR for scanned image
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

    # Save to file
    output_file = Path(__file__).parent.parent / "outputs" / "exploration" / "well_7_ocr_markdown.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"Saved OCR markdown to: {output_file}")
    print(f"Total length: {len(markdown)} chars\n")

    # Print first 3000 chars to see structure
    print(f"{'='*80}")
    print(f"FIRST 3000 CHARS OF OCR OUTPUT:")
    print(f"{'='*80}\n")
    print(markdown[:3000])
    print("\n...")

    # Find and print Contents section
    lines = markdown.split('\n')
    for i, line in enumerate(lines):
        if 'content' in line.lower():
            print(f"\n{'='*80}")
            print(f"FOUND 'Contents' at line {i}: {line}")
            print(f"{'='*80}\n")
            # Show 40 lines after Contents
            for j in range(i, min(i+40, len(lines))):
                print(f"{j:3}: {lines[j]}")
            break

else:
    print("No EOWR file found")
