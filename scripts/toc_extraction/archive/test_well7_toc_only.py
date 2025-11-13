"""
Quick test: Well 7 TOC extraction with LLM fallback
Tests only TOC extraction, not full indexing pipeline
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
from robust_toc_extractor import RobustTOCExtractor
from analyze_all_tocs import find_toc_boundaries
from llm_toc_parser import LLMTOCParser
import fitz

pdf_path = Path("Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf")

print("="*80)
print("WELL 7 TOC EXTRACTION TEST (LLM FALLBACK)")
print("="*80)
print(f"\nPDF: {pdf_path.name}")

# Initialize extractors
toc_extractor = RobustTOCExtractor()
llm_parser = LLMTOCParser()
print("[OK] Extractors ready")

# Configure Docling with enhanced OCR
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True  # Critical for scanned docs
pipeline_options.do_table_structure = False  # Skip tables for speed
pipeline_options.generate_picture_images = False  # Skip pictures for speed

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
print("[OK] Docling converter ready (enhanced OCR only)")

# Parse first 10 pages only (TOC is on page 3)
doc = fitz.open(str(pdf_path))
temp_pdf = Path("temp_well7_first10.pdf")
new_doc = fitz.open()
for i in range(min(10, len(doc))):
    new_doc.insert_pdf(doc, from_page=i, to_page=i)
new_doc.save(str(temp_pdf))
new_doc.close()
doc.close()

print(f"\n[1] Parsing first 10 pages with Docling...")
result = converter.convert(str(temp_pdf))
markdown = result.document.export_to_markdown()
print(f"  Extracted {len(markdown)} chars")

# Clean up temp file
temp_pdf.unlink()

# Try Docling TOC extraction
print(f"\n[2] Trying Docling TOC extraction...")
toc_sections = []
scrambled_toc_text = None

lines = markdown.split('\n')
toc_start, toc_end = find_toc_boundaries(lines)

if toc_start >= 0:
    print(f"  TOC found at lines {toc_start}-{toc_end}")
    toc_lines = lines[toc_start:toc_end]
    toc_entries, pattern = toc_extractor.extract(toc_lines)

    if len(toc_entries) >= 3:
        toc_sections = toc_entries
        print(f"  [SUCCESS] Docling: {len(toc_sections)} entries using {pattern}")
    else:
        print(f"  [WARN] Docling: TOC found but only {len(toc_entries)} entries (likely scrambled)")
        scrambled_toc_text = '\n'.join(toc_lines)
else:
    print(f"  [WARN] Docling: No TOC found")

# Try PyMuPDF fallback if needed
if not toc_sections:
    print(f"\n[3] Trying PyMuPDF fallback...")
    doc = fitz.open(str(pdf_path))
    raw_text = '\n'.join([doc[i].get_text() for i in range(min(10, len(doc)))])
    doc.close()

    raw_lines = raw_text.split('\n')
    toc_start, toc_end = find_toc_boundaries(raw_lines)

    if toc_start >= 0:
        print(f"  TOC found at lines {toc_start}-{toc_end}")
        toc_lines = raw_lines[toc_start:toc_end]
        toc_entries, pattern = toc_extractor.extract(toc_lines)

        if len(toc_entries) >= 3:
            toc_sections = toc_entries
            print(f"  [SUCCESS] PyMuPDF: {len(toc_sections)} entries using {pattern}")
        else:
            print(f"  [WARN] PyMuPDF: TOC found but only {len(toc_entries)} entries (likely scrambled)")
            if not scrambled_toc_text:
                scrambled_toc_text = '\n'.join(toc_lines)
    else:
        print(f"  [WARN] PyMuPDF: No TOC found")

# Try LLM fallback if we have scrambled text
if not toc_sections and scrambled_toc_text:
    print(f"\n[4] Trying LLM fallback (Tier 3)...")
    print(f"  Scrambled text length: {len(scrambled_toc_text)} chars")

    try:
        toc_entries, method = llm_parser.parse_scrambled_toc(scrambled_toc_text)
        if len(toc_entries) >= 3:
            # Validate: Check if ANY page is missing
            print(f"\n  [VALIDATION] Checking for missing pages...")

            missing_pages = sum(1 for e in toc_entries if e.get('page', 0) == 0)

            print(f"  Missing pages: {missing_pages}/{len(toc_entries)}")

            if missing_pages > 0:
                print(f"\n  [DECISION] Found {missing_pages} missing page(s)")
                print(f"  [FALLBACK] Extracting titles only (no section numbers or pages)")

                # Extract just titles for basic header detection
                # Filter out empty or very short titles
                toc_sections = [
                    {
                        'title': entry['title'].strip(),
                        'source': 'llm_titles_only',
                        'note': 'Section numbers and pages unreliable, titles only'
                    }
                    for entry in toc_entries
                    if entry.get('title', '').strip() and len(entry.get('title', '').strip()) > 2
                ]
            else:
                print(f"\n  [DECISION] All pages present - TOC quality acceptable")
                toc_sections = toc_entries

            print(f"  [SUCCESS] LLM: {len(toc_sections)} entries")
        else:
            print(f"  [WARN] LLM: Only {len(toc_entries)} entries")
    except Exception as e:
        print(f"  [ERROR] LLM fallback failed: {e}")

# Print results
print(f"\n{'='*80}")
print("RESULT")
print(f"{'='*80}")

if toc_sections:
    if toc_sections[0].get('source') == 'llm_titles_only':
        print(f"\n[TITLES ONLY MODE] Extracted {len(toc_sections)} section titles:")
        print("-"*80)
        for i, entry in enumerate(toc_sections, 1):
            title = entry.get('title', 'Unknown')
            print(f"{i:2d}. {title}")
        print("-"*80)
        print(f"\nNote: {toc_sections[0].get('note', 'N/A')}")
        print("These titles can be used for basic header detection during reindexing.")
        print("Section-aware chunking NOT recommended due to unreliable structure.")
    else:
        print(f"\n[SUCCESS] Extracted {len(toc_sections)} TOC entries:")
        print("-"*80)
        for i, entry in enumerate(toc_sections, 1):
            number = entry.get('number', 'N/A')
            title = entry.get('title', 'Unknown')
            page = entry.get('page', 0)
            print(f"{i:2d}. {number:5s} - {title:50s} (page {page})")
        print("-"*80)
else:
    print(f"\n[FAILED] No TOC extracted (tried Docling + PyMuPDF + LLM)")

print(f"\n{'='*80}\n")
