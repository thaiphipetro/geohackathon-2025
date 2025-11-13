"""
Debug script: Show actual OCR output from Well 7 EOWR page 3

This will help us understand why find_toc_boundaries() is failing to detect TOC.
"""

import sys
from pathlib import Path
import fitz

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from analyze_all_tocs import parse_first_n_pages, find_toc_boundaries

# Well 7 EOWR path
pdf_path = Path("Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf")

print("="*80)
print("WELL 7 OCR DEBUG: What does OCR actually extract from page 3?")
print("="*80)

# Extract first 10 pages
print("\nExtracting first 10 pages with Docling + PyMuPDF...")
docling_text, raw_text, is_scanned, error = parse_first_n_pages(pdf_path, num_pages=10)

if error:
    print(f"ERROR: {error}")
    sys.exit(1)

print(f"Scanned document: {is_scanned}")

# Try Docling first
print("\n" + "="*80)
print("DOCLING OUTPUT")
print("="*80)

docling_lines = docling_text.split('\n')
print(f"Total lines extracted: {len(docling_lines)}")

# Show lines 50-150 (page 3 is likely here)
print("\nShowing lines 50-150 (where page 3 TOC should be):")
print("-"*80)
for i in range(50, min(150, len(docling_lines))):
    line = docling_lines[i]
    if line.strip():
        print(f"{i:4d}: {line}")

# Try find_toc_boundaries on Docling
toc_start_docling, toc_end_docling = find_toc_boundaries(docling_lines)
print(f"\nDocling find_toc_boundaries result: start={toc_start_docling}, end={toc_end_docling}")

# Try PyMuPDF
print("\n" + "="*80)
print("PYMUPDF OUTPUT")
print("="*80)

raw_lines = raw_text.split('\n')
print(f"Total lines extracted: {len(raw_lines)}")

# Show lines 50-150
print("\nShowing lines 50-150 (where page 3 TOC should be):")
print("-"*80)
for i in range(50, min(150, len(raw_lines))):
    line = raw_lines[i]
    if line.strip():
        print(f"{i:4d}: {line}")

# Try find_toc_boundaries on PyMuPDF
toc_start_pymupdf, toc_end_pymupdf = find_toc_boundaries(raw_lines)
print(f"\nPyMuPDF find_toc_boundaries result: start={toc_start_pymupdf}, end={toc_end_pymupdf}")

# Search for "contents" keyword manually
print("\n" + "="*80)
print("MANUAL KEYWORD SEARCH")
print("="*80)

print("\nSearching Docling output for 'contents' (case-insensitive):")
for i, line in enumerate(docling_lines[:200]):
    if 'content' in line.lower():
        print(f"  Line {i}: {line}")

print("\nSearching PyMuPDF output for 'contents' (case-insensitive):")
for i, line in enumerate(raw_lines[:200]):
    if 'content' in line.lower():
        print(f"  Line {i}: {line}")

# Search for numbered lines (1, 1.1, etc.)
print("\n" + "="*80)
print("SEARCHING FOR NUMBERED LINES")
print("="*80)

import re

print("\nSearching Docling output for numbered lines like '1.', '1.1', etc.:")
for i, line in enumerate(docling_lines[:200]):
    if re.match(r'^\s*\d+\.?\d*\s+', line):
        print(f"  Line {i}: {line}")

print("\nSearching PyMuPDF output for numbered lines:")
for i, line in enumerate(raw_lines[:200]):
    if re.match(r'^\s*\d+\.?\d*\s+', line):
        print(f"  Line {i}: {line}")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

if toc_start_docling >= 0:
    print("\nDocling: TOC FOUND")
elif toc_start_pymupdf >= 0:
    print("\nPyMuPDF: TOC FOUND")
else:
    print("\nBOTH FAILED: No TOC detected by find_toc_boundaries()")
    print("\nPossible reasons:")
    print("  1. OCR quality too poor - 'Contents' keyword not recognized")
    print("  2. Numbered section lines not extracted cleanly")
    print("  3. Need alternative TOC detection method (visual/pattern-based)")

print("="*80)
