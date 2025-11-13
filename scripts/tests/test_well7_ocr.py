"""
Test Well 7 OCR Quality
Check if scanned documents are readable with current Docling setup
"""

import sys
from pathlib import Path
import time

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption

print("="*80)
print("TESTING WELL 7 OCR QUALITY")
print("="*80)

# Setup Docling with OCR
print("\n[SETUP] Initializing Docling with OCR...")
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
print("[OK] Docling ready")

# Test PDFs from Well 7
well7_dir = project_root / "Training data-shared with participants" / "Well 7"
test_pdfs = [
    well7_dir / "Well report" / "EOWR" / "NLOG_GS_PUB_EOWR BRI GT-01 SodM V1.0.pdf",
    well7_dir / "Technical log" / "NLOG_GS_PUB_Appendix I_Lithology log BRI-GT-01.pdf",
]

for pdf_path in test_pdfs:
    if not pdf_path.exists():
        print(f"\n[SKIP] {pdf_path.name} - not found")
        continue

    print(f"\n{'='*80}")
    print(f"Testing: {pdf_path.name}")
    print(f"Size: {pdf_path.stat().st_size / 1024:.1f} KB")
    print(f"{'='*80}")

    # Parse
    start = time.time()
    try:
        result = converter.convert(str(pdf_path))
        parse_time = time.time() - start

        # Get text
        markdown = result.document.export_to_markdown()
        tables = result.document.tables if hasattr(result.document, 'tables') else []

        # Stats
        text_length = len(markdown)
        word_count = len(markdown.split())
        line_count = len(markdown.split('\n'))
        table_count = len(tables)

        print(f"\n[RESULTS]")
        print(f"  Parse time: {parse_time:.1f}s")
        print(f"  Text extracted: {text_length:,} chars")
        print(f"  Word count: {word_count:,} words")
        print(f"  Line count: {line_count:,} lines")
        print(f"  Tables found: {table_count}")

        # Sample text
        print(f"\n[SAMPLE TEXT - First 500 chars]")
        print("-" * 80)
        print(markdown[:500])
        print("-" * 80)

        # Check for OCR warnings
        if text_length < 100:
            print("\n[WARNING] Very little text extracted - possible OCR failure")
        elif word_count < 20:
            print("\n[WARNING] Low word count - possible scanned image with poor OCR")
        else:
            print(f"\n[OK] OCR appears successful")

        # Check tables
        if table_count > 0:
            print(f"\n[TABLE SAMPLE - First table]")
            print("-" * 80)
            first_table = tables[0]
            print(f"Table has {len(first_table.data)} rows")
            for i, row in enumerate(first_table.data[:3]):
                print(f"Row {i}: {row}")
            print("-" * 80)

    except Exception as e:
        parse_time = time.time() - start
        print(f"\n[ERROR] Failed to parse: {e}")
        print(f"  Time before error: {parse_time:.1f}s")

print("\n" + "="*80)
print("WELL 7 OCR TEST COMPLETE")
print("="*80)
