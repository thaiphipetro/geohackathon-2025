"""
Simple regex-based header detection for Well 7

Strategy:
1. Extract TOC titles into a list (no section numbers)
2. OCR the PDF page-by-page
3. Use regex to search for each title in OCR text
4. Map title -> page number
"""

import re
import sys
from pathlib import Path
import fitz  # PyMuPDF for fast text extraction

# Well 7 TOC - extract just the titles
TOC_TITLES = [
    "General Project data",
    "Well summary",
    "Directional plots",
    "Technical summary",
    "Drilling fluid summary",
    "Well schematic",
    "Geology",
    "HSE performance",
    "General",
    "Incident",
    "Drills/Emergency exercises, inspections & audits"
]

def extract_text_from_pdf(pdf_path: str, max_pages: int = 50) -> dict:
    """
    Extract text from each page using PyMuPDF (fast, no heavy OCR)

    Returns:
        {page_num: page_text}
    """
    doc = fitz.open(pdf_path)
    pages = {}

    for page_num in range(min(len(doc), max_pages)):
        page = doc[page_num]
        text = page.get_text()
        pages[page_num + 1] = text  # 1-indexed pages

    doc.close()
    return pages

def find_title_in_pages(title: str, pages: dict, use_fuzzy: bool = True) -> int:
    """
    Search for title in pages using regex

    Args:
        title: Section title to search for
        pages: Dict of {page_num: page_text}
        use_fuzzy: Allow minor variations (spaces, punctuation)

    Returns:
        Page number where title found, or 0 if not found
    """
    # Build regex pattern
    if use_fuzzy:
        # Replace spaces with \s+ to match any whitespace
        # Make punctuation optional
        pattern_str = re.escape(title)
        pattern_str = pattern_str.replace(r'\ ', r'\s+')  # Flexible spaces
        pattern_str = pattern_str.replace(r'\-', r'[\-\s]*')  # Optional hyphens
    else:
        pattern_str = re.escape(title)

    pattern = re.compile(pattern_str, re.IGNORECASE)

    # Search each page
    for page_num, page_text in sorted(pages.items()):
        if pattern.search(page_text):
            return page_num

    return 0

def detect_all_headers(pdf_path: str, titles: list) -> dict:
    """
    Detect page numbers for all titles

    Returns:
        {title: page_num}
    """
    print(f"Extracting text from PDF: {Path(pdf_path).name}")
    pages = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(pages)} pages")

    results = {}

    print("\nSearching for headers...")
    print("-"*80)

    for title in titles:
        page_num = find_title_in_pages(title, pages, use_fuzzy=True)
        results[title] = page_num

        status = "FOUND" if page_num > 0 else "NOT FOUND"
        print(f"{status:<12} '{title[:50]:<50}' -> page {page_num}")

    print("-"*80)

    return results

def build_corrected_toc(original_toc: list, detected_pages: dict) -> list:
    """
    Build corrected TOC by combining original structure with detected pages

    Args:
        original_toc: Original TOC with section numbers and titles
        detected_pages: {title: detected_page_num}

    Returns:
        Corrected TOC entries
    """
    corrected = []

    for entry in original_toc:
        title = entry['title']
        original_page = entry.get('page', 0)
        detected_page = detected_pages.get(title, 0)

        # Use detected page if found, otherwise keep original
        final_page = detected_page if detected_page > 0 else original_page

        corrected.append({
            'number': entry['number'],
            'title': title,
            'page': final_page,
            'original_page': original_page,
            'detected_page': detected_page,
            'source': 'detected' if detected_page > 0 else 'original'
        })

    return corrected


if __name__ == '__main__':
    # Well 7 original TOC with section numbers
    WELL7_TOC = [
        {"number": "1", "title": "General Project data", "page": 5},
        {"number": "2", "title": "Well summary", "page": 6},
        {"number": "2.1", "title": "Directional plots", "page": 7},
        {"number": "2.2", "title": "Technical summary", "page": 8},
        {"number": "3", "title": "Drilling fluid summary", "page": 9},
        {"number": "4", "title": "Well schematic", "page": 10},
        {"number": "5", "title": "Geology", "page": 12},
        {"number": "6", "title": "HSE performance", "page": 13},
        {"number": "6.1", "title": "General", "page": 14},
        {"number": "6.2", "title": "Incident", "page": 0},
        {"number": "6.3", "title": "Drills/Emergency exercises, inspections & audits", "page": 0},
    ]

    pdf_path = "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf"

    print("="*80)
    print("WELL 7 HEADER DETECTION - REGEX-BASED")
    print("="*80)
    print()

    # Detect headers
    detected_pages = detect_all_headers(pdf_path, TOC_TITLES)

    # Build corrected TOC
    corrected_toc = build_corrected_toc(WELL7_TOC, detected_pages)

    # Print comparison
    print("\n" + "="*80)
    print("COMPARISON: Original vs. Detected")
    print("="*80)
    print(f"{'Section':<8} {'Title':<40} {'Original':<10} {'Detected':<10} {'Status'}")
    print("-"*80)

    for entry in corrected_toc:
        section = entry['number']
        title = entry['title'][:38]
        orig_page = entry['original_page']
        detected_page = entry['detected_page']

        if orig_page == 0 and detected_page > 0:
            status = "FOUND!"
        elif orig_page > 0 and detected_page > 0 and orig_page != detected_page:
            status = "CORRECTED"
        elif detected_page == 0:
            status = "MISSING"
        else:
            status = "OK"

        print(f"{section:<8} {title:<40} {orig_page:<10} {detected_page:<10} {status}")

    print("-"*80)

    # Statistics
    found_count = sum(1 for e in corrected_toc if e['detected_page'] > 0)
    missing_filled = sum(1 for e in corrected_toc
                         if e['original_page'] == 0 and e['detected_page'] > 0)

    print(f"\nStatistics:")
    print(f"  Headers found: {found_count}/{len(corrected_toc)}")
    print(f"  Missing pages filled: {missing_filled}")
    print(f"  Detection rate: {100*found_count//len(corrected_toc)}%")

    # Save results
    import json
    output_path = Path("outputs/well7_headers_detected.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'detected_pages': detected_pages,
            'corrected_toc': corrected_toc
        }, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    print("="*80)
