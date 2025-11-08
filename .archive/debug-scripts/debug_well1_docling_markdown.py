"""Debug: Save Docling's markdown output from Well 1 to see TOC format"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption

# Well 1
data_dir = Path(__file__).parent.parent / "Training data-shared with participants" / "Well 1"
well_reports_dir = data_dir / "Well report"

eowr_files = [f for f in well_reports_dir.rglob("*.pdf") if 'eowr' in f.name.lower()]
if eowr_files:
    test_pdf = eowr_files[0]
    print(f"Processing: {test_pdf.name}\n")

    # Use Docling without OCR (same as in build script)
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    result = converter.convert(str(test_pdf))
    full_text = result.document.export_to_markdown()

    # Save first 4 pages (~12000 chars)
    first_4_pages = full_text[:12000]

    output_file = Path(__file__).parent.parent / "outputs" / "exploration" / "well_1_docling_markdown.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(first_4_pages)

    print(f"Saved first 12000 chars to: {output_file}")
    print(f"Total document length: {len(full_text)} chars")

    # Print first 2000 chars to console
    print(f"\n{'='*80}")
    print("FIRST 2000 CHARACTERS:")
    print(f"{'='*80}\n")
    print(first_4_pages[:2000])

    # Search for "Contents" line
    lines = first_4_pages.split('\n')
    for i, line in enumerate(lines):
        if 'content' in line.lower():
            print(f"\n{'='*80}")
            print(f"FOUND 'CONTENTS' at line {i}")
            print(f"{'='*80}\n")
            # Show 50 lines after Contents
            for j in range(i, min(i+50, len(lines))):
                print(f"{j:3}: {lines[j]}")
            break

else:
    print("No EOWR file found")
