"""
Test TOC boundary detection with force OCR
See exactly what the OCR produces and why boundaries might fail
"""

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from pathlib import Path
import re


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
        # Check if line contains TOC keyword (with word boundaries)
        for kw in toc_keywords:
            if kw in line_lower:
                # Make sure it's not just part of another word
                if kw == 'content' or kw == 'contents':
                    # Accept "content", "contents", "## content", etc.
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
                # Match lines starting with numbers like "1.1" or "1"
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
        # End at next major heading that's not content-related
        if lines[i].strip().startswith('##'):
            line_lower = lines[i].lower()
            if not any(kw in line_lower for kw in ['content', 'contents', 'index']):
                end = i
                break

    return start, end

pdf_path = "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf"

if not Path(pdf_path).exists():
    print(f"[ERROR] PDF not found: {pdf_path}")
    exit(1)

print("="*80)
print("TOC BOUNDARY DETECTION TEST - WELL 7 EOWR")
print("="*80)

# Configure with force OCR
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True

converter = DocumentConverter(
    format_options={
        "pdf": PdfFormatOption(pipeline_options=pipeline_options)
    }
)

print("\n[INFO] Converting PDF with force_full_page_ocr=True...")
result = converter.convert(pdf_path)
raw_text = result.document.export_to_markdown()

print(f"[INFO] Extracted {len(raw_text)} characters")

# Show first 2000 characters
print("\n" + "="*80)
print("FIRST 2000 CHARACTERS OF OCR OUTPUT:")
print("="*80)
print(raw_text[:2000])
print("...")

# Try to find TOC boundaries
print("\n" + "="*80)
print("SEARCHING FOR TOC BOUNDARIES...")
print("="*80)

# Convert text to lines for boundary detection
lines = raw_text.split('\n')
print(f"[INFO] Text split into {len(lines)} lines")

toc_start, toc_end = find_toc_boundaries(lines)

if toc_start >= 0:
    print(f"[SUCCESS] TOC boundaries found!")
    print(f"  Start: line {toc_start}")
    print(f"  End: line {toc_end}")

    toc_lines = lines[toc_start:toc_end]

    print(f"\n[INFO] Extracted {len(toc_lines)} lines")
    print("\n" + "-"*80)
    print("TOC SECTION CONTENT:")
    print("-"*80)
    for i, line in enumerate(toc_lines[:50], toc_start):  # Show first 50 lines
        print(f"{i:4d}: {line}")
    if len(toc_lines) > 50:
        print(f"... ({len(toc_lines)-50} more lines)")
else:
    print(f"[FAILED] TOC boundaries NOT found")
    print(f"  toc_start: {toc_start}")
    print(f"  toc_end: {toc_end}")

    # Search for keywords manually
    print("\n" + "-"*80)
    print("MANUAL KEYWORD SEARCH:")
    print("-"*80)

    keywords = ["table of contents", "contents", "content", "index"]

    for keyword in keywords:
        found_lines = []
        for i, line in enumerate(lines[:500]):  # Check first 500 lines
            if keyword in line.lower():
                found_lines.append((i, line))

        if found_lines:
            print(f"\n[FOUND] Keyword '{keyword}' in {len(found_lines)} lines:")
            for i, line in found_lines[:5]:  # Show first 5 matches
                print(f"  Line {i}: {line.strip()}")
        else:
            print(f"[NOT FOUND] Keyword '{keyword}'")

print("\n" + "="*80)
