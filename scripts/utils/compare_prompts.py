"""
Compare original vs improved LLM prompts for TOC parsing
"""

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from pathlib import Path
import subprocess
import re
import json

pdf_path = "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf"

# Extract scrambled TOC
print("="*80)
print("EXTRACTING SCRAMBLED TOC")
print("="*80)

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True

converter = DocumentConverter(
    format_options={"pdf": PdfFormatOption(pipeline_options=pipeline_options)}
)

result = converter.convert(pdf_path)
raw_text = result.document.export_to_markdown()
lines = raw_text.split('\n')

# Find TOC
toc_start = -1
for i, line in enumerate(lines[:200]):
    if 'contents' in line.lower():
        toc_start = i
        break

toc_end = min(toc_start + 200, len(lines))
scrambled_toc = '\n'.join(lines[toc_start:toc_end])

print(f"Extracted {toc_end - toc_start} lines")

# Test prompts
def query_ollama(prompt):
    cmd = ["ollama", "run", "llama3.2:3b", prompt]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout.strip()

def parse_json_response(output):
    """Extract JSON array from LLM output"""
    # Try to find JSON array
    json_match = re.search(r'\[\s*\{.*?\}\s*\]', output, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass
    return []

# ORIGINAL PROMPT (that got 11 entries)
original_prompt = f"""You are a document structure parser. The following text is a Table of Contents (TOC) extracted from a PDF using OCR, but the lines are scrambled due to a 2-column layout being read left-to-right.

Your task: Parse this scrambled text and extract the TOC entries in the correct order.

Scrambled TOC text:
{scrambled_toc}

Instructions:
1. Match section numbers (1., 2., 2.1, 3., etc.) with their titles
2. Extract page numbers if present (often shown as dots like "..10" or "...12")
3. Return a JSON array of TOC entries in this exact format:
[
  {{"number": "1", "title": "General Project data", "page": 5}},
  {{"number": "2", "title": "Well summary", "page": 6}},
  {{"number": "2.1", "title": "Directional plots", "page": 8}},
  ...
]

Important:
- Preserve hierarchical numbering (1., 2., 2.1, 2.2, 3., etc.)
- Clean up titles (remove extra dots, spaces, HTML entities like &amp;)
- If page number is unclear, use 0
- Return ONLY the JSON array, no explanation text

JSON output:"""

# IMPROVED PROMPT (balanced)
improved_prompt = f"""Parse this scrambled Table of Contents from a scanned PDF. The OCR read a 2-column layout left-to-right, so section numbers, titles, and page numbers are scattered across many lines.

SCRAMBLED TEXT:
{scrambled_toc}

EXAMPLE (how to parse scrambled format):
Input:
Contents
1.
General Project data
2.
Well summary.......
2.1
Directional plots.....
5
6
7

Output:
[
  {{"number": "1", "title": "General Project data", "page": 5}},
  {{"number": "2", "title": "Well summary", "page": 6}},
  {{"number": "2.1", "title": "Directional plots", "page": 7}}
]

INSTRUCTIONS:
1. Match section numbers (1., 2.1, etc.) with their titles (may be 3-10 lines apart)
2. Extract page numbers (look for dots like "..5" or standalone digits)
3. Clean titles (remove extra dots, spaces, HTML entities like &amp;)
4. Ensure logical structure (page numbers should generally increase, subsections under parents)

CRITICAL OUTPUT REQUIREMENTS:
- Return ONLY pure JSON array format
- Use double quotes for all strings
- NO JavaScript syntax (no "let", no variable declarations)
- NO markdown code blocks
- NO explanations or commentary
- Start response with [ and end with ]

JSON array:"""

# Test both prompts
print("\n" + "="*80)
print("TEST 1: ORIGINAL PROMPT")
print("="*80)
print("Querying Ollama...")
original_output = query_ollama(original_prompt)
original_entries = parse_json_response(original_output)

print(f"\nRaw output length: {len(original_output)} chars")
print(f"Parsed entries: {len(original_entries)}")
if len(original_entries) > 0:
    print("\nFirst 3 entries:")
    for entry in original_entries[:3]:
        print(f"  {entry.get('number')}: {entry.get('title')} (page {entry.get('page')})")

print("\n" + "="*80)
print("TEST 2: IMPROVED PROMPT")
print("="*80)
print("Querying Ollama...")
improved_output = query_ollama(improved_prompt)
improved_entries = parse_json_response(improved_output)

print(f"\nRaw output length: {len(improved_output)} chars")
print(f"Parsed entries: {len(improved_entries)}")
if len(improved_entries) > 0:
    print("\nFirst 3 entries:")
    for entry in improved_entries[:3]:
        print(f"  {entry.get('number')}: {entry.get('title')} (page {entry.get('page')})")

# Comparison
print("\n" + "="*80)
print("COMPARISON")
print("="*80)

expected = {
    "1": {"title": "General Project data", "page": 5},
    "2": {"title": "Well summary", "page": 6},
    "2.1": {"title": "Directional plots", "page": 7},
    "2.2": {"title": "Technical summary", "page": 8},
    "3": {"title": "Drilling fluid summary", "page": 9},
}

def score_entries(entries):
    correct = 0
    total = len(expected)
    for section_num, expected_data in expected.items():
        entry = next((e for e in entries if e.get('number') == section_num), None)
        if entry and entry.get('page') == expected_data['page']:
            correct += 1
    return correct, total

original_score = score_entries(original_entries)
improved_score = score_entries(improved_entries)

print(f"\nOriginal Prompt:")
print(f"  - Entries extracted: {len(original_entries)}")
print(f"  - Page accuracy: {original_score[0]}/{original_score[1]} ({100*original_score[0]//original_score[1] if original_score[1] > 0 else 0}%)")

print(f"\nImproved Prompt:")
print(f"  - Entries extracted: {len(improved_entries)}")
print(f"  - Page accuracy: {improved_score[0]}/{improved_score[1]} ({100*improved_score[0]//improved_score[1] if improved_score[1] > 0 else 0}%)")

print("\n" + "="*80)
if improved_score[0] > original_score[0]:
    print("WINNER: Improved Prompt")
elif original_score[0] > improved_score[0]:
    print("WINNER: Original Prompt")
else:
    print("TIE")
print("="*80)
