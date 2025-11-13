"""
Test page number extraction for Well 7 EOWR
Validates that find_page_numbers() correctly identifies section locations
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from llm_toc_parser import LLMTOCParser

print("="*80)
print("PAGE NUMBER EXTRACTION TEST - WELL 7 EOWR")
print("="*80)

# Initialize parser
parser = LLMTOCParser()

# Well 7 EOWR path
pdf_path = "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf"

if not Path(pdf_path).exists():
    print(f"[ERROR] PDF not found: {pdf_path}")
    exit(1)

# Test entries with incorrect page numbers (from LLM inference)
test_entries = [
    {"number": "1", "title": "General Project data", "page": 5},
    {"number": "2", "title": "Well summary", "page": 6},
    {"number": "2.1", "title": "Directional plots", "page": 8},  # WRONG: should be 7
    {"number": "2.2", "title": "Technical summary", "page": 0},  # WRONG: should be 8
    {"number": "3", "title": "Drilling fluid summary", "page": 9},
    {"number": "4", "title": "Well schematic", "page": 10},
    {"number": "5", "title": "Geology", "page": 12},
    {"number": "6", "title": "HSE performance", "page": 13},
]

print(f"\n[INFO] Testing smart page number validation on {len(test_entries)} entries...")
print("-"*80)

# Validate and fix page numbers (smart approach - only OCR suspicious pages)
corrected_entries = parser.validate_and_fix_page_numbers(pdf_path, test_entries)

print("\n" + "="*80)
print("RESULTS COMPARISON")
print("="*80)

# Expected correct values (manually verified)
expected = {
    "2.1": 7,  # Directional plots
    "2.2": 8,  # Technical summary
}

errors = []
for entry in corrected_entries:
    section_num = entry['number']
    original_page = next((e['page'] for e in test_entries if e['number'] == section_num), 0)
    corrected_page = entry['page']

    status = "OK"
    if section_num in expected:
        if corrected_page == expected[section_num]:
            status = "CORRECTED"
        else:
            status = "ERROR"
            errors.append(f"Section {section_num}: expected page {expected[section_num]}, got {corrected_page}")

    print(f"{section_num:5s} {entry['title']:40s} | Original: {original_page:2d} -> Corrected: {corrected_page:2d} [{status}]")

print("="*80)

if errors:
    print(f"\n[ERROR] {len(errors)} page number errors:")
    for error in errors:
        print(f"  - {error}")
    exit(1)
else:
    print(f"\n[SUCCESS] All page numbers correctly identified!")
    print("[INFO] Page number extraction is working as expected")
