"""
Test two-stage TOC extraction: LLM structure + OCR heading detection
"""

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from llm_toc_parser import LLMTOCParser

print("="*80)
print("TWO-STAGE TOC EXTRACTION TEST - WELL 7 EOWR")
print("="*80)
print("Stage 1: LLM extracts structure (section numbers + titles)")
print("Stage 2: OCR detects heading pages in actual PDF")
print("="*80)

pdf_path = "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf"

if not Path(pdf_path).exists():
    print(f"[ERROR] PDF not found: {pdf_path}")
    exit(1)

# STAGE 1: Extract structure using LLM
print("\n" + "="*80)
print("STAGE 1: LLM STRUCTURE EXTRACTION")
print("="*80)

print("\n[STEP 1.1] Extracting scrambled TOC with force_full_page_ocr...")
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True

converter = DocumentConverter(
    format_options={"pdf": PdfFormatOption(pipeline_options=pipeline_options)}
)

result = converter.convert(pdf_path)
raw_text = result.document.export_to_markdown()
lines = raw_text.split('\n')

# Find TOC boundaries
toc_start = -1
for i, line in enumerate(lines[:200]):
    if 'contents' in line.lower():
        toc_start = i
        break

if toc_start < 0:
    print("[ERROR] TOC not found")
    exit(1)

# Find precise TOC end (stop at next major heading or 70 lines max)
toc_end = toc_start + 70
for i in range(toc_start + 1, min(toc_start + 100, len(lines))):
    if lines[i].strip().startswith('##') and 'content' not in lines[i].lower():
        toc_end = i
        break

scrambled_toc = '\n'.join(lines[toc_start:toc_end])

print(f"[OK] Extracted {toc_end - toc_start} lines of scrambled TOC")

print("\n[STEP 1.2] Parsing structure with LLM (numbers + titles only)...")
parser = LLMTOCParser()
toc_entries, method = parser.parse_scrambled_toc(scrambled_toc)

if len(toc_entries) == 0:
    print("[ERROR] LLM failed to extract TOC structure")
    exit(1)

print(f"\n[SUCCESS] LLM extracted {len(toc_entries)} TOC entries")
print("\nExtracted structure:")
print("-"*80)
for entry in toc_entries:
    num = entry.get('number', '?')
    title = entry.get('title', 'Unknown')
    indent = "  " * (num.count('.'))
    print(f"{indent}{num:6s} {title}")
print("-"*80)

# STAGE 2: Detect heading pages using OCR
print("\n" + "="*80)
print("STAGE 2: OCR HEADING DETECTION")
print("="*80)

toc_with_pages = parser.detect_heading_pages(pdf_path, toc_entries)

# Display results
print("\n" + "="*80)
print("FINAL RESULTS (Structure + Pages)")
print("="*80)

for entry in toc_with_pages:
    num = entry.get('number', '?')
    title = entry.get('title', 'Unknown')
    page = entry.get('page', 0)
    indent = "  " * (num.count('.'))
    status = "OK" if page > 0 else "MISS"
    print(f"{indent}{num:6s} {title:45s} page {page:3d} [{status}]")

# Manual verification
print("\n" + "="*80)
print("MANUAL VERIFICATION (from PDF)")
print("="*80)

expected = {
    "1": 5,
    "2": 6,
    "2.1": 7,
    "2.2": 8,
    "3": 9,
    "4": 10,
    "5": 12,
    "6": 13,
}

print("\nComparison:")
print("-"*80)
print(f"{'Section':<8} {'Expected Page':<15} {'Detected Page':<15} {'Status':<10}")
print("-"*80)

errors = []
for section_num, expected_page in expected.items():
    entry = next((e for e in toc_with_pages if e.get('number') == section_num), None)

    if not entry:
        print(f"{section_num:<8} {expected_page:<15} {'MISSING':<15} {'ERROR':<10}")
        errors.append(f"Section {section_num} missing from output")
        continue

    detected_page = entry.get('page', 0)

    if detected_page == expected_page:
        status = "OK"
    else:
        status = "ERROR"
        errors.append(f"Section {section_num}: expected page {expected_page}, got {detected_page}")

    print(f"{section_num:<8} {expected_page:<15} {detected_page:<15} {status:<10}")

print("-"*80)

# Final summary
print("\n" + "="*80)
detected_count = sum(1 for e in toc_with_pages if e.get('page', 0) > 0)
total_count = len(toc_with_pages)
correct_count = len(expected) - len(errors)

print(f"RESULTS:")
print(f"  - Structure extracted: {total_count} sections")
print(f"  - Pages detected: {detected_count}/{total_count} ({100*detected_count//total_count if total_count > 0 else 0}%)")
print(f"  - Page accuracy: {correct_count}/{len(expected)} ({100*correct_count//len(expected) if len(expected) > 0 else 0}%)")
print("="*80)

if errors:
    print(f"\n{len(errors)} ERRORS:")
    for error in errors:
        print(f"  - {error}")
    exit(1)
else:
    print(f"\n[SUCCESS] All section pages correctly detected!")
    print("Two-stage approach is working!")
