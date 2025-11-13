"""
Debug: Check what's actually on page 7 of Well 7 EOWR
"""

import pymupdf
from pathlib import Path

pdf_path = "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf"

if not Path(pdf_path).exists():
    print(f"[ERROR] PDF not found: {pdf_path}")
    exit(1)

doc = pymupdf.open(pdf_path)

# Check pages 6-9 (0-indexed: 5-8)
for page_num in range(5, 9):
    page = doc[page_num]
    text = page.get_text()

    print("="*80)
    print(f"PAGE {page_num + 1}")
    print("="*80)
    print(text[:500])  # First 500 chars
    print("...")
    print(text[-200:])  # Last 200 chars
    print()

doc.close()
