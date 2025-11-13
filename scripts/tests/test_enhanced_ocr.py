"""
Test enhanced OCR settings on Well 7 EOWR
Try different combinations to see which works best for TOC extraction
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analyze_all_tocs import parse_first_n_pages, find_toc_boundaries
from robust_toc_extractor import RobustTOCExtractor

import tempfile
import os
import fitz
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption

pdf_path = Path("Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf")

print("="*80)
print("ENHANCED OCR TEST FOR WELL 7 EOWR")
print("="*80)

# Test configurations
configs = [
    {
        "name": "Default (baseline)",
        "images_scale": 1.0,
        "force_full_page_ocr": False,
        "do_picture_classification": False
    },
    {
        "name": "High resolution (2x scale)",
        "images_scale": 2.0,
        "force_full_page_ocr": False,
        "do_picture_classification": False
    },
    {
        "name": "Very high resolution (3x scale)",
        "images_scale": 3.0,
        "force_full_page_ocr": False,
        "do_picture_classification": False
    },
    {
        "name": "Force full page OCR",
        "images_scale": 1.0,
        "force_full_page_ocr": True,
        "do_picture_classification": False
    },
    {
        "name": "High resolution + force OCR",
        "images_scale": 2.0,
        "force_full_page_ocr": True,
        "do_picture_classification": False
    },
    {
        "name": "All enhancements (3x + force OCR + classification)",
        "images_scale": 3.0,
        "force_full_page_ocr": True,
        "do_picture_classification": True
    }
]

extractor = RobustTOCExtractor()

for config in configs:
    print(f"\n{'='*80}")
    print(f"TEST: {config['name']}")
    print(f"{'='*80}")
    print(f"  images_scale: {config['images_scale']}")
    print(f"  force_full_page_ocr: {config['force_full_page_ocr']}")
    print(f"  do_picture_classification: {config['do_picture_classification']}")

    # Extract first 10 pages with custom settings
    doc = fitz.open(str(pdf_path))
    pages_to_extract = min(10, len(doc))

    # Create temp PDF
    temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_path = temp_pdf.name
    temp_pdf.close()

    new_doc = fitz.open()
    for i in range(pages_to_extract):
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
    new_doc.save(temp_path)
    new_doc.close()
    doc.close()

    # Parse with custom Docling settings
    try:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.images_scale = config['images_scale']
        pipeline_options.ocr_options.force_full_page_ocr = config['force_full_page_ocr']
        pipeline_options.do_picture_classification = config['do_picture_classification']

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        print(f"\n  Processing PDF with enhanced OCR...")
        result = converter.convert(temp_path)
        docling_text = result.document.export_to_markdown()

        os.unlink(temp_path)

        # Try to find TOC
        lines = docling_text.split('\n')
        toc_start, toc_end = find_toc_boundaries(lines)

        if toc_start >= 0:
            toc_lines = lines[toc_start:toc_end]

            # Save TOC section for inspection
            if config['force_full_page_ocr']:
                toc_output_path = Path(f"outputs/well7_toc_force_ocr_scale{config['images_scale']}.txt")
                toc_output_path.parent.mkdir(exist_ok=True)
                with open(toc_output_path, 'w', encoding='utf-8') as f:
                    f.write(f"TOC Section (lines {toc_start} to {toc_end})\n")
                    f.write("="*80 + "\n\n")
                    for i, line in enumerate(toc_lines, toc_start):
                        f.write(f"{i:4d}: {line}\n")
                print(f"    Saved TOC to: {toc_output_path}")

            toc_entries, pattern = extractor.extract(toc_lines)

            print(f"\n  [SUCCESS] TOC found!")
            print(f"    Lines: {toc_start} to {toc_end} ({toc_end-toc_start} lines)")
            print(f"    Pattern: {pattern}")
            print(f"    Entries: {len(toc_entries)}")

            # Print first 15 lines of TOC for inspection
            print(f"\n    First 15 lines of TOC:")
            for i, line in enumerate(toc_lines[:15], toc_start):
                print(f"      {i:4d}: {line[:100]}")

            if len(toc_entries) >= 3:
                print(f"\n  First 5 entries:")
                for i, entry in enumerate(toc_entries[:5], 1):
                    print(f"    {i}. {entry.get('number', 'N/A'):5s} - {entry.get('title', 'Unknown'):50s} (page {entry.get('page', 0)})")
                if len(toc_entries) > 5:
                    print(f"    ... and {len(toc_entries) - 5} more")
            else:
                print(f"  [WARN] Only {len(toc_entries)} entries found (need >=3)")
        else:
            print(f"\n  [FAILED] No TOC found")

            # Check if "Contents" keyword exists
            has_contents = any('content' in line.lower() for line in lines[:200])
            if has_contents:
                print(f"  [INFO] 'Contents' keyword found but TOC boundary detection failed")
                print(f"  Showing lines with 'content':")
                for i, line in enumerate(lines[:200]):
                    if 'content' in line.lower():
                        print(f"    Line {i}: {line[:80]}")
            else:
                print(f"  [INFO] 'Contents' keyword not found in first 200 lines")

    except Exception as e:
        print(f"\n  [ERROR] Processing failed: {e}")
        import traceback
        traceback.print_exc()
        try:
            os.unlink(temp_path)
        except:
            pass

print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print(f"\nTested {len(configs)} configurations on Well 7 EOWR TOC extraction")
print(f"Check above results to see which configuration works best")
print(f"{'='*80}\n")
