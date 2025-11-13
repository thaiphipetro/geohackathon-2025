"""
Test Granite extraction on a single PDF with debug output
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))

from src.granite_toc_extractor import GraniteTOCExtractor
import fitz

# Import the detect_toc_page_number function
sys.path.insert(0, str(Path.cwd() / 'scripts'))
from build_multi_doc_toc_database_granite import detect_toc_page_number

# Test on Well 1 PDF
pdf_path = Path('Training data-shared with participants/Well 1/Well report/NLOG_GS_PUB_EOWR ADK-GT-01 SODM v1.1.pdf')

if not pdf_path.exists():
    print(f'ERROR: PDF not found: {pdf_path}')
    sys.exit(1)

print('='*80)
print('TESTING GRANITE ON WELL 1 (Native PDF)')
print('='*80)

# Get total pages
doc = fitz.open(str(pdf_path))
pdf_total_pages = len(doc)
doc.close()

print(f'PDF: {pdf_path.name}')
print(f'Total pages: {pdf_total_pages}')

# Detect TOC page using new function
toc_page_num = detect_toc_page_number(pdf_path, None, 0)
print(f'Detected TOC on page: {toc_page_num}')

# Create extractor
extractor = GraniteTOCExtractor()

print(f'Extracting TOC from page {toc_page_num}...')

toc_entries, confidence, method = extractor.extract_full_workflow(
    pdf_path,
    toc_page_num,
    pdf_total_pages
)

print('\n' + '='*80)
print('RESULTS')
print('='*80)
print(f'Method: {method}')
print(f'Confidence: {confidence:.2f}')
print(f'Total entries: {len(toc_entries)}')
print()

for entry in toc_entries:
    page_str = str(entry['page'])
    if entry['page'] == 0:
        status = 'UNKNOWN'
    elif '-' in page_str:
        status = 'RANGE'
    else:
        status = 'EXACT'

    print(f"  {entry['number']:6s} {entry['title']:50s} {page_str:>6s} [{status}]")

print('\n' + '='*80)
