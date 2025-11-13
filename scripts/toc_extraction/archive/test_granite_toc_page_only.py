"""
Test Granite-Docling on JUST the TOC page (page 2) to verify what it extracts
This will help us understand if the page number mismatch is due to:
1. Reading the actual TOC page incorrectly
2. Doing header detection throughout the document
"""

import sys
import time
from pathlib import Path
import fitz  # PyMuPDF

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def extract_toc_page_only():
    """Extract just page 2 (TOC page) and process with Granite"""

    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import PdfFormatOption
    from docling.pipeline.vlm_pipeline import VlmPipeline
    from docling.datamodel.pipeline_options import VlmPipelineOptions
    from docling.datamodel import vlm_model_specs
    from PIL import Image

    pdf_path = Path("Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf")
    output_dir = Path("outputs/granite_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("GRANITE-DOCLING: TOC PAGE ONLY TEST")
    print("="*80)

    # First, extract just page 2 (TOC page) as a separate PDF
    print("\n[1/4] Extracting TOC page (page 2) from PDF...")

    doc = fitz.open(str(pdf_path))
    print(f"  Total pages in PDF: {len(doc)}")

    # Create single-page PDF with just TOC
    toc_pdf_path = output_dir / "well7_toc_page_only.pdf"
    toc_doc = fitz.open()
    toc_doc.insert_pdf(doc, from_page=1, to_page=1)  # Page 2 (0-indexed as 1)
    toc_doc.save(str(toc_pdf_path))
    toc_doc.close()
    doc.close()

    print(f"  Saved TOC page to: {toc_pdf_path}")

    # Also save as image for visual verification
    doc = fitz.open(str(pdf_path))
    page = doc[1]  # Page 2
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale
    img_path = output_dir / "well7_toc_page_visual.png"
    pix.save(str(img_path))
    doc.close()
    print(f"  Saved TOC page image: {img_path}")

    # Now process with Granite-Docling
    print("\n[2/4] Processing TOC page with Granite-Docling...")
    print("  (This will take 2-3 minutes for 1 page)")

    pipeline_options = VlmPipelineOptions(
        vlm_options=vlm_model_specs.GRANITEDOCLING_TRANSFORMERS
    )

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=pipeline_options
            )
        }
    )

    start = time.time()
    result = converter.convert(str(toc_pdf_path))
    convert_time = time.time() - start

    markdown = result.document.export_to_markdown()

    print(f"\n[3/4] Conversion complete in {convert_time:.1f}s")
    print(f"  Markdown length: {len(markdown)} chars")

    # Save markdown
    markdown_file = output_dir / "well7_toc_page_granite_output.md"
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    print(f"  Saved markdown to: {markdown_file}")

    # Print markdown for inspection
    print("\n[4/4] Granite-Docling output from TOC page:")
    print("="*80)
    print(markdown)
    print("="*80)

    # Try to extract TOC entries
    print("\nAttempting to extract TOC entries from Granite output...")

    sys.path.insert(0, str(Path(__file__).parent))
    from robust_toc_extractor import RobustTOCExtractor
    from analyze_all_tocs import find_toc_boundaries

    lines = markdown.split('\n')
    toc_start, toc_end = find_toc_boundaries(lines)

    if toc_start >= 0:
        print(f"  TOC boundaries found: lines {toc_start}-{toc_end}")
        toc_lines = lines[toc_start:toc_end]

        print("\n  TOC lines:")
        for i, line in enumerate(toc_lines[:20], toc_start):
            print(f"    {i}: {line}")

        extractor = RobustTOCExtractor()
        toc_entries, pattern = extractor.extract(toc_lines)

        print(f"\n  Pattern: {pattern}")
        print(f"  Entries: {len(toc_entries)}")

        if toc_entries:
            print("\n  Extracted entries:")
            for i, entry in enumerate(toc_entries, 1):
                num = entry.get('number', 'N/A')
                title = entry.get('title', 'Unknown')
                page = entry.get('page', 0)
                print(f"    {i}. {num:5s} - {title:50s} (page {page})")
    else:
        print("  No TOC boundaries found in Granite output")

    # Now compare with ACTUAL TOC from screenshot
    print("\n" + "="*80)
    print("COMPARISON WITH ACTUAL TOC (from screenshot)")
    print("="*80)

    actual_toc = [
        ("1", "General Project data", 5),
        ("2", "Well summary", 6),
        ("2.1", "Directional plots", 7),
        ("2.2", "Technical summary", 8),
        ("3", "Drilling fluid summary", 9),
        ("4", "Geology", 10),
        ("5", "Well schematic", 12),
        ("6", "HSE performance", 13),
        ("6.1", "General", 13),
        ("6.2", "Incidents", 13),
        ("6.3", "Drills / Emergency exercises, inspections & audits", 13),
    ]

    print("\nActual TOC (from screenshot):")
    for i, (num, title, page) in enumerate(actual_toc, 1):
        print(f"  {i}. {num:5s} - {title:50s} (page {page})")

    if toc_entries:
        print("\n" + "-"*80)
        print("PAGE NUMBER COMPARISON:")
        print("-"*80)

        print(f"\n{'#':<4} {'Section':<8} {'Actual Page':<15} {'Granite Page':<15} {'Offset':<10} {'Match?'}")
        print("-"*80)

        for i, entry in enumerate(toc_entries[:len(actual_toc)]):
            granite_page = entry.get('page', 0)
            actual_entry = actual_toc[i] if i < len(actual_toc) else (None, None, 0)
            actual_page = actual_entry[2]
            offset = granite_page - actual_page
            match = "✓" if granite_page == actual_page else "✗"

            print(f"{i+1:<4} {entry.get('number', 'N/A'):<8} {actual_page:<15} {granite_page:<15} {offset:+d}{'':9} {match}")

        # Calculate accuracy
        correct = sum(1 for i, entry in enumerate(toc_entries[:len(actual_toc)])
                     if entry.get('page', 0) == actual_toc[i][2])
        accuracy = (correct / min(len(toc_entries), len(actual_toc)) * 100) if toc_entries else 0

        print(f"\nPage number accuracy: {accuracy:.1f}% ({correct}/{min(len(toc_entries), len(actual_toc))} correct)")

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)

    if toc_entries and toc_start >= 0:
        print("\n[INFO] Granite successfully extracted the TOC structure")
        print(f"  Entries: {len(toc_entries)}")
        print(f"  Pattern: {pattern}")

        if any(entry.get('page', 0) != actual_toc[i][2] for i, entry in enumerate(toc_entries[:len(actual_toc)])):
            print("\n[ISSUE] Page numbers do NOT match actual TOC")
            print("  This suggests Granite is:")
            print("  1. Reading the TOC page but extracting wrong page numbers")
            print("  2. Or doing document-wide header detection instead of reading the TOC table")
        else:
            print("\n[SUCCESS] Page numbers match actual TOC perfectly!")
    else:
        print("\n[FAIL] Could not extract TOC from Granite output")
        print("  Review the markdown output above to see what Granite extracted")

    print("\n" + "="*80)


if __name__ == "__main__":
    extract_toc_page_only()
