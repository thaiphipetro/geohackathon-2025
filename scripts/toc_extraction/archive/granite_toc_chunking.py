"""
Granite TOC-Aware Chunking for Well 7
Compare with old chunking method
"""

import sys
import re
import time
from pathlib import Path
import fitz  # PyMuPDF

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from parse_granite_toc import parse_granite_multicolumn_table
from chunker import SectionAwareChunker


def extract_page_text(pdf_path, page_num):
    """
    Extract text from a specific page

    Args:
        pdf_path: Path to PDF
        page_num: 0-indexed page number

    Returns:
        Text from page
    """
    doc = fitz.open(str(pdf_path))
    if page_num < 0 or page_num >= len(doc):
        doc.close()
        return ""

    page = doc[page_num]
    text = page.get_text()
    doc.close()
    return text


def detect_section_in_text(text, section_numbers):
    """
    Detect which section numbers appear in text

    Args:
        text: Page text
        section_numbers: List of section numbers to search for (e.g., ["6.1", "6.2", "6.3"])

    Returns:
        Dict mapping section_number to first occurrence line number
    """
    lines = text.split('\n')
    detections = {}

    for section_num in section_numbers:
        # Escape dots for regex
        pattern = re.escape(section_num) + r'\s+'

        for line_idx, line in enumerate(lines):
            if re.search(pattern, line):
                if section_num not in detections:
                    detections[section_num] = line_idx
                    print(f"  [DETECT] Found section {section_num} at line {line_idx}: {line.strip()[:60]}")
                    break

    return detections


def refine_page_ranges(pdf_path, toc_entries, pdf_total_pages):
    """
    Refine page ranges by detecting section headers in page content

    For subsections with range notation (e.g., "13-14"), try to determine
    exact page by searching for section header in content.

    Args:
        pdf_path: Path to PDF
        toc_entries: TOC entries from Granite (with potential ranges)
        pdf_total_pages: Total pages in PDF

    Returns:
        Updated toc_entries with refined pages where possible
    """
    print("\n" + "="*80)
    print("REFINING PAGE RANGES WITH CONTENT DETECTION")
    print("="*80)

    # Find entries with range notation
    range_entries = [e for e in toc_entries if isinstance(e['page'], str) and '-' in e['page']]

    if not range_entries:
        print("\nNo range entries to refine")
        return toc_entries

    print(f"\nFound {len(range_entries)} entries with range notation:")
    for entry in range_entries:
        print(f"  - Section {entry['number']} '{entry['title']}': {entry['page']}")

    # Group by page range
    range_groups = {}
    for entry in range_entries:
        page_range = entry['page']
        if page_range not in range_groups:
            range_groups[page_range] = []
        range_groups[page_range].append(entry)

    # Process each range
    for page_range, entries in range_groups.items():
        print(f"\n[REFINING] Page range {page_range}")
        print(f"  Sections to detect: {[e['number'] for e in entries]}")

        # Parse range
        start_page, end_page = map(int, page_range.split('-'))

        # Extract text from all pages in range
        page_texts = {}
        for page_num in range(start_page, end_page + 1):
            # Convert document page to PDF page (0-indexed)
            pdf_page_idx = page_num - 1
            text = extract_page_text(pdf_path, pdf_page_idx)
            page_texts[page_num] = text
            print(f"  [EXTRACT] Page {page_num}: {len(text)} chars")

        # Detect sections in each page
        section_numbers = [e['number'] for e in entries]

        for page_num, text in page_texts.items():
            print(f"\n  [SCAN] Scanning page {page_num} for sections...")
            detections = detect_section_in_text(text, section_numbers)

            # Update entries where section was found
            for section_num in detections:
                entry = next(e for e in entries if e['number'] == section_num)
                print(f"  [REFINE] Section {section_num}: {page_range} → {page_num} (detected in content)")
                entry['page'] = page_num
                entry['refined'] = True

    return toc_entries


def chunk_with_granite_toc(pdf_path, toc_entries):
    """
    Create chunks using Granite TOC extraction

    Strategy:
        - For exact pages: Extract that page
        - For ranges: Extract all pages in range
        - Prepend section header to content
        - Create metadata with section info

    Note: TOC pages are document page numbers (matches page label in PDF)
          Need to convert to 0-indexed PDF pages

    Args:
        pdf_path: Path to PDF
        toc_entries: TOC entries from Granite

    Returns:
        List of chunks with metadata
    """
    print("\n" + "="*80)
    print("CREATING CHUNKS WITH GRANITE TOC")
    print("="*80)

    # Open PDF once
    doc = fitz.open(str(pdf_path))
    total_pdf_pages = len(doc)

    print(f"\nPDF total pages (0-indexed): {total_pdf_pages}")
    print(f"First page label: {doc[0].get_label()}")
    print(f"Page 4 label (TOC page): {doc[3].get_label() if len(doc) > 3 else 'N/A'}")

    chunks = []

    for entry in toc_entries:
        section_num = entry['number']
        title = entry['title']
        page = entry['page']

        print(f"\n[CHUNK] Section {section_num} '{title}' (page {page})")

        # Determine pages to extract
        if isinstance(page, str) and '-' in page:
            # Range notation
            start_page, end_page = map(int, page.split('-'))
            pages_to_extract = list(range(start_page, end_page + 1))
        elif isinstance(page, int):
            pages_to_extract = [page]
        else:
            print(f"  [SKIP] Invalid page: {page}")
            continue

        # Extract text from all pages
        # TOC page numbers are 1-indexed document pages, PDF is 0-indexed
        # Page 5 in TOC = PDF page index 4
        content_parts = []
        for doc_page_num in pages_to_extract:
            # Document page to PDF page index
            # Assuming TOC pages match PDF 0-indexed + 1
            pdf_page_idx = doc_page_num - 1

            if pdf_page_idx < 0 or pdf_page_idx >= total_pdf_pages:
                print(f"  [WARN] Page {doc_page_num} out of range (PDF has {total_pdf_pages} pages)")
                continue

            page = doc[pdf_page_idx]
            text = page.get_text()

            if text.strip():
                content_parts.append(f"[Page {doc_page_num}]\n{text}")
                print(f"  [EXTRACT] Page {doc_page_num} (PDF idx {pdf_page_idx}): {len(text)} chars")

        if not content_parts:
            print(f"  [SKIP] No content extracted")
            continue

        # Combine content
        content = '\n\n'.join(content_parts)

        # Create section header
        header = f"## {section_num} {title}"

        # Full chunk with header
        chunk_text = f"{header}\n\n{content}"

        chunk = {
            'text': chunk_text,
            'metadata': {
                'section_number': section_num,
                'section_title': title,
                'page': page,  # Keep original (int or range string)
                'chunk_source': 'granite_toc',
                'refined': entry.get('refined', False)
            }
        }

        chunks.append(chunk)

        print(f"  [OK] Created chunk: {len(chunk_text)} chars")

    doc.close()
    return chunks


def chunk_with_old_method(pdf_path, toc_entries):
    """
    Create chunks using old SectionAwareChunker method

    Args:
        pdf_path: Path to PDF
        toc_entries: TOC entries (for metadata)

    Returns:
        List of chunks with metadata
    """
    print("\n" + "="*80)
    print("CREATING CHUNKS WITH OLD METHOD")
    print("="*80)

    # Extract full document text
    print("\n[EXTRACT] Extracting full PDF text...")
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    full_text = ""
    for page_idx in range(total_pages):
        page_text = doc[page_idx].get_text()
        full_text += f"\n\n[Page {page_idx + 1}]\n{page_text}"
    doc.close()

    print(f"[OK] Extracted {len(full_text)} chars from {total_pages} pages")

    # Convert toc_entries to old format
    toc_sections = []
    for entry in toc_entries:
        # Extract numeric page (ignore ranges for old method)
        page = entry['page']
        if isinstance(page, str) and '-' in page:
            page = int(page.split('-')[0])  # Use first page of range

        toc_sections.append({
            'number': entry['number'],
            'title': entry['title'],
            'page': page,
            'type': None  # Would come from 11-category mapping
        })

    # Create chunker and chunk
    chunker = SectionAwareChunker(chunk_size=1000, overlap=200)
    chunks = chunker.chunk_with_section_headers(full_text, toc_sections)

    # Mark as old method
    for chunk in chunks:
        chunk['metadata']['chunk_source'] = 'old_method'

    print(f"\n[OK] Created {len(chunks)} chunks")

    return chunks


def compare_chunking_methods(granite_chunks, old_chunks):
    """Compare Granite TOC chunking vs old method"""
    print("\n" + "="*80)
    print("CHUNKING METHOD COMPARISON")
    print("="*80)

    print(f"\n{'Metric':<40} {'Granite TOC':<20} {'Old Method':<20}")
    print("-"*80)

    # Total chunks
    print(f"{'Total chunks':<40} {len(granite_chunks):<20} {len(old_chunks):<20}")

    # Average chunk size
    granite_avg = sum(len(c['text']) for c in granite_chunks) / len(granite_chunks) if granite_chunks else 0
    old_avg = sum(len(c['text']) for c in old_chunks) / len(old_chunks) if old_chunks else 0
    print(f"{'Average chunk size (chars)':<40} {int(granite_avg):<20} {int(old_avg):<20}")

    # Total content size
    granite_total = sum(len(c['text']) for c in granite_chunks)
    old_total = sum(len(c['text']) for c in old_chunks)
    print(f"{'Total content size (chars)':<40} {granite_total:<20} {old_total:<20}")

    # Sections covered
    granite_sections = set(c['metadata']['section_number'] for c in granite_chunks if c['metadata']['section_number'])
    old_sections = set(c['metadata']['section_number'] for c in old_chunks if c['metadata']['section_number'])
    print(f"{'Unique sections covered':<40} {len(granite_sections):<20} {len(old_sections):<20}")

    # Refined entries
    refined_count = sum(1 for c in granite_chunks if c['metadata'].get('refined'))
    print(f"{'Refined page ranges':<40} {refined_count:<20} {'N/A':<20}")

    print("\n" + "="*80)
    print("DETAILED SECTION COMPARISON")
    print("="*80)

    all_sections = sorted(granite_sections | old_sections, key=lambda x: [int(n) for n in x.split('.')])

    print(f"\n{'Section':<12} {'Granite Chunks':<18} {'Old Chunks':<18} {'Granite Page':<15}")
    print("-"*80)

    for section in all_sections:
        granite_count = sum(1 for c in granite_chunks if c['metadata']['section_number'] == section)
        old_count = sum(1 for c in old_chunks if c['metadata']['section_number'] == section)

        granite_page = next((c['metadata']['page'] for c in granite_chunks if c['metadata']['section_number'] == section), 'N/A')

        print(f"{section:<12} {granite_count:<18} {old_count:<18} {str(granite_page):<15}")


def main():
    """Test Granite TOC chunking on Well 7 and compare with old method"""

    print("="*80)
    print("GRANITE TOC CHUNKING - WELL 7 COMPARISON")
    print("="*80)

    # Paths
    pdf_path = Path("Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf")
    granite_toc_file = Path("outputs/granite_test/well7_correct_toc_granite.md")
    toc_page_pdf = Path("outputs/granite_test/well7_toc_page_only.pdf")

    if not pdf_path.exists():
        print(f"\nError: PDF not found: {pdf_path}")
        return

    if not granite_toc_file.exists():
        print(f"\nError: Granite TOC not found: {granite_toc_file}")
        return

    # Get PDF total pages
    doc = fitz.open(str(pdf_path))
    pdf_total_pages = len(doc)
    doc.close()

    print(f"\nPDF: {pdf_path.name}")
    print(f"Total pages: {pdf_total_pages}")

    # Load and parse Granite TOC
    print("\n[1/5] Loading Granite TOC extraction...")
    with open(granite_toc_file, 'r', encoding='utf-8') as f:
        granite_markdown = f.read()

    # Parse with validation
    toc_entries = parse_granite_multicolumn_table(
        granite_markdown,
        max_page_number=pdf_total_pages,
        toc_page_path=toc_page_pdf if toc_page_pdf.exists() else None,
        enable_retry=False  # Skip retry for faster testing
    )

    print(f"\n[OK] Parsed {len(toc_entries)} TOC entries")

    # Refine page ranges
    print("\n[2/5] Refining page ranges with content detection...")
    toc_entries = refine_page_ranges(pdf_path, toc_entries, pdf_total_pages)

    # Create chunks with Granite TOC
    print("\n[3/5] Creating chunks with Granite TOC method...")
    start = time.time()
    granite_chunks = chunk_with_granite_toc(pdf_path, toc_entries)
    granite_time = time.time() - start
    print(f"\n[OK] Granite chunking completed in {granite_time:.1f}s")

    # Create chunks with old method
    print("\n[4/5] Creating chunks with old method...")
    start = time.time()
    old_chunks = chunk_with_old_method(pdf_path, toc_entries)
    old_time = time.time() - start
    print(f"\n[OK] Old chunking completed in {old_time:.1f}s")

    # Compare
    print("\n[5/5] Comparing methods...")
    compare_chunking_methods(granite_chunks, old_chunks)

    # Show sample chunks
    print("\n" + "="*80)
    print("SAMPLE CHUNKS - SECTION 6.1")
    print("="*80)

    # Granite sample
    granite_sample = next((c for c in granite_chunks if c['metadata']['section_number'] == '6.1'), None)
    if granite_sample:
        print("\n[GRANITE TOC METHOD]")
        print(f"  Section: {granite_sample['metadata']['section_number']} - {granite_sample['metadata']['section_title']}")
        print(f"  Page: {granite_sample['metadata']['page']}")
        print(f"  Refined: {granite_sample['metadata'].get('refined', False)}")
        print(f"  Text ({len(granite_sample['text'])} chars):")
        print("  " + "-"*76)
        print("  " + granite_sample['text'][:500].replace('\n', '\n  '))
        print("  [...]")

    # Old method sample
    old_sample = next((c for c in old_chunks if c['metadata']['section_number'] == '6.1'), None)
    if old_sample:
        print("\n[OLD METHOD]")
        print(f"  Section: {old_sample['metadata']['section_number']} - {old_sample['metadata']['section_title']}")
        print(f"  Page: {old_sample['metadata']['page']}")
        print(f"  Text ({len(old_sample['text'])} chars):")
        print("  " + "-"*76)
        print("  " + old_sample['text'][:500].replace('\n', '\n  '))
        print("  [...]")

    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON")
    print("="*80)
    print(f"\nGranite TOC method: {granite_time:.1f}s")
    print(f"Old method: {old_time:.1f}s")
    print(f"Speedup: {old_time/granite_time:.1f}x" if granite_time > 0 else "N/A")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
