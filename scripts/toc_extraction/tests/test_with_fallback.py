"""
Test RobustTOCExtractor with PyMuPDF Fallback
Specifically tests the failed PDF: Well 4 NLOG_GS_PUB_EOWR NLW-GT-02 GRE workover SodM.pdf
"""

import sys
from pathlib import Path
import fitz
import tempfile
import os
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
import re

sys.path.insert(0, str(Path(__file__).parent))
from robust_toc_extractor import RobustTOCExtractor

project_root = Path(__file__).parent.parent
data_dir = project_root / "Training data-shared with participants"


def is_scanned_pdf(pdf_path):
    """Quick check if PDF is scanned"""
    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            return True
        first_page = doc[0]
        text = first_page.get_text()
        doc.close()
        return len(text.strip()) < 100
    except:
        return True


def parse_with_fallback(pdf_path, num_pages=10):
    """
    Parse PDF with Docling + PyMuPDF fallback

    Returns: (docling_text, raw_text, is_scanned, error)
    """
    is_scanned = is_scanned_pdf(pdf_path)

    # Extract raw text with PyMuPDF
    raw_text = ""
    try:
        doc = fitz.open(str(pdf_path))
        pages_to_extract = min(num_pages, len(doc))

        # Extract raw text from first N pages
        for i in range(pages_to_extract):
            raw_text += doc[i].get_text()

        # Create temp PDF for Docling
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_path = temp_pdf.name
        temp_pdf.close()

        # Copy pages
        new_doc = fitz.open()
        for i in range(pages_to_extract):
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
        new_doc.save(temp_path)
        new_doc.close()
        doc.close()

    except Exception as e:
        return "", raw_text, is_scanned, f"Failed to extract pages: {e}"

    # Parse with Docling
    try:
        if is_scanned:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.do_table_structure = True
        else:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False
            pipeline_options.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(temp_path)
        docling_text = result.document.export_to_markdown()

        os.unlink(temp_path)
        return docling_text, raw_text, is_scanned, None
    except Exception as e:
        try:
            os.unlink(temp_path)
        except:
            pass
        return "", raw_text, is_scanned, f"Docling failed: {e}"


def find_toc_boundaries(lines):
    """Find start and end of TOC section"""
    toc_keywords = [
        'table of contents', 'contents', 'content',
        'index', 'table des matieres', 'inhoud', 'inhaltsverzeichnis'
    ]

    start = -1

    # Method 1: Look for explicit TOC heading
    for i, line in enumerate(lines[:200]):
        line_lower = line.lower().strip()
        for kw in toc_keywords:
            if kw in line_lower:
                if kw == 'content' or kw == 'contents':
                    if re.search(r'\b' + kw, line_lower):
                        start = i
                        break
                else:
                    start = i
                    break
        if start >= 0:
            break

    # Method 2: Look for structure (multiple numbered lines)
    if start < 0:
        for i in range(min(200, len(lines))):
            section_count = 0
            for j in range(i, min(i+5, len(lines))):
                if re.match(r'^\s*\d+\.?\d*\s+', lines[j]):
                    section_count += 1
            if section_count >= 3:
                start = i
                break

    if start < 0:
        return -1, -1

    # Find end
    end = min(start + 200, len(lines))
    for i in range(start + 1, min(start + 200, len(lines))):
        if lines[i].strip().startswith('##'):
            line_lower = lines[i].lower()
            if not any(kw in line_lower for kw in ['content', 'contents', 'index']):
                end = i
                break

    return start, end


def main():
    """Test the fallback on Well 4's failed PDF"""

    pdf_path = data_dir / "Well 4" / "Well report" / "NLOG_GS_PUB_EOWR NLW-GT-02 GRE workover SodM.pdf"

    if not pdf_path.exists():
        print(f"ERROR: PDF not found at {pdf_path}")
        return

    print("="*80)
    print("TEST: PyMuPDF FALLBACK FOR FAILED PDF")
    print("="*80)
    print(f"\nTesting: {pdf_path.name}")
    print("\n" + "="*80)

    # Parse with fallback
    print("\nStep 1: Parsing PDF with Docling + PyMuPDF...")
    docling_text, raw_text, is_scanned, error = parse_with_fallback(pdf_path, num_pages=10)

    if error:
        print(f"  ERROR: {error}")
        return

    print(f"  Docling text: {len(docling_text)} characters")
    print(f"  PyMuPDF text: {len(raw_text)} characters")
    print(f"  Is scanned: {is_scanned}")

    # Initialize extractor
    extractor = RobustTOCExtractor()

    # Try Docling text first
    print("\nStep 2: Try extraction with Docling text...")
    lines = docling_text.split('\n')
    start, end = find_toc_boundaries(lines)

    if start >= 0:
        print(f"  TOC boundaries found: lines {start} to {end}")
        toc_lines = lines[start:end]
        entries, pattern = extractor.extract(toc_lines, debug=False)
        print(f"  Extracted {len(entries)} entries using {pattern}")
    else:
        print(f"  No TOC boundaries found")
        entries = []
        pattern = None

    # If Docling failed, try PyMuPDF
    if len(entries) == 0:
        print("\nStep 3: Docling failed, trying PyMuPDF fallback...")
        lines = raw_text.split('\n')
        start, end = find_toc_boundaries(lines)

        if start >= 0:
            print(f"  TOC boundaries found: lines {start} to {end}")
            toc_lines = lines[start:end]
            entries, pattern = extractor.extract(toc_lines, debug=False)
            print(f"  Extracted {len(entries)} entries using {pattern}")
        else:
            print(f"  No TOC boundaries found in raw text either")

    # Output results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    if len(entries) > 0:
        print(f"\n[SUCCESS] Extracted {len(entries)} TOC entries using {pattern}")
        print(f"\nALL ENTRIES:")
        print("-"*80)
        for i, entry in enumerate(entries, 1):
            print(f"{i:2d}. [{entry['number']:6s}] {entry['title']:60s} (page {entry['page']:3d})")
    else:
        print("\n[FAILED] Could not extract TOC entries")

    print("\n" + "="*80)


if __name__ == '__main__':
    main()
