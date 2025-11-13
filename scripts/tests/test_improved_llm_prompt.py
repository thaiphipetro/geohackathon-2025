"""
Test improved LLM prompt on Well 7 scrambled TOC
Compare results with manual verification
"""

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent))
from llm_toc_parser import LLMTOCParser

print("="*80)
print("TESTING IMPROVED LLM PROMPT - WELL 7 EOWR")
print("="*80)

pdf_path = "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf"

if not Path(pdf_path).exists():
    print(f"[ERROR] PDF not found: {pdf_path}")
    exit(1)

# Step 1: Extract scrambled TOC using force OCR
print("\n[STEP 1] Extracting scrambled TOC with force_full_page_ocr...")

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True

converter = DocumentConverter(
    format_options={
        "pdf": PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert(pdf_path)
raw_text = result.document.export_to_markdown()

# Extract TOC section (we know from previous test it's around line 72-142)
lines = raw_text.split('\n')

# Find Contents keyword
toc_start = -1
for i, line in enumerate(lines[:200]):
    if 'contents' in line.lower():
        toc_start = i
        break

if toc_start < 0:
    print("[ERROR] TOC not found")
    exit(1)

toc_end = min(toc_start + 200, len(lines))
for i in range(toc_start + 1, min(toc_start + 200, len(lines))):
    if lines[i].strip().startswith('##'):
        if 'content' not in lines[i].lower():
            toc_end = i
            break

scrambled_toc = '\n'.join(lines[toc_start:toc_end])

print(f"[OK] Extracted {toc_end - toc_start} lines of scrambled TOC")
print(f"\nFirst 500 chars of scrambled text:")
print("-"*80)
print(scrambled_toc[:500])
print("...")
print("-"*80)

# Step 2: Parse with improved LLM prompt
print("\n[STEP 2] Parsing with improved LLM prompt...")
print("(This will take ~10-15 seconds with Llama 3.2 3B)")

parser = LLMTOCParser()

# Monkey patch to capture LLM output
original_query = parser._query_ollama
llm_raw_output = None

def capture_query(prompt, temperature=0.1):
    global llm_raw_output
    result = original_query(prompt, temperature)
    llm_raw_output = result
    return result

parser._query_ollama = capture_query

toc_entries, method = parser.parse_scrambled_toc(scrambled_toc)

# Show raw LLM output
if llm_raw_output:
    print("\n" + "="*80)
    print("RAW LLM OUTPUT (for debugging):")
    print("="*80)
    print(llm_raw_output)
    print("="*80)

# Step 3: Display results
print("\n" + "="*80)
print("RESULTS")
print("="*80)

if len(toc_entries) == 0:
    print("[ERROR] LLM failed to extract any TOC entries")
    exit(1)

print(f"\n[SUCCESS] Extracted {len(toc_entries)} TOC entries\n")

# Pretty print results
print("Extracted TOC Entries:")
print("-"*80)
for entry in toc_entries:
    num = entry.get('number', '?')
    title = entry.get('title', 'Unknown')
    page = entry.get('page', 0)
    indent = "  " * (num.count('.'))
    print(f"{indent}{num:6s} {title:45s} page {page}")

# Step 4: Compare with manual verification
print("\n" + "="*80)
print("MANUAL VERIFICATION (from PDF)")
print("="*80)

expected = {
    "1": {"title": "General Project data", "page": 5},
    "2": {"title": "Well summary", "page": 6},
    "2.1": {"title": "Directional plots", "page": 7},  # Was wrong (8) with old prompt
    "2.2": {"title": "Technical summary", "page": 8},  # Was wrong (0) with old prompt
    "3": {"title": "Drilling fluid summary", "page": 9},
    "4": {"title": "Well schematic", "page": 10},
    "5": {"title": "Geology", "page": 12},
    "6": {"title": "HSE performance", "page": 13},
}

print("\nComparison:")
print("-"*80)
print(f"{'Section':<8} {'Expected Page':<15} {'LLM Page':<12} {'Status':<10}")
print("-"*80)

errors = []
for section_num, expected_data in expected.items():
    # Find matching entry
    llm_entry = next((e for e in toc_entries if e['number'] == section_num), None)

    if not llm_entry:
        print(f"{section_num:<8} {expected_data['page']:<15} {'MISSING':<12} {'ERROR':<10}")
        errors.append(f"Section {section_num} missing from LLM output")
        continue

    llm_page = llm_entry['page']
    expected_page = expected_data['page']

    if llm_page == expected_page:
        status = "OK"
    else:
        status = "ERROR"
        errors.append(f"Section {section_num}: expected page {expected_page}, got {llm_page}")

    print(f"{section_num:<8} {expected_page:<15} {llm_page:<12} {status:<10}")

print("-"*80)

# Final summary
print("\n" + "="*80)
if errors:
    print(f"RESULT: {len(errors)} ERRORS FOUND")
    print("="*80)
    for error in errors:
        print(f"  - {error}")
    exit(1)
else:
    print("RESULT: ALL PAGE NUMBERS CORRECT!")
    print("="*80)
    print("[SUCCESS] Improved prompt successfully fixed page number errors")
    print("  - Section 2.1 (Directional plots): Correctly identified as page 7")
    print("  - Section 2.2 (Technical summary): Correctly identified as page 8")
