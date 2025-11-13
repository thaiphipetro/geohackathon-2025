"""
Test Well 7 Granite extraction with all fixes applied:
1. force_full_page_ocr = True
2. OCR page-by-page text for page detection
3. 2-page TOC extraction
4. parse_granite_multicolumn_table with validation
5. 60% confidence threshold
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.granite_toc_extractor import GraniteTOCExtractor
import fitz


def main():
    print("=" * 80)
    print("TESTING WELL 7 GRANITE EXTRACTION WITH ALL FIXES")
    print("=" * 80)

    # Well 7 PDF
    pdf_path = Path("Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf")

    if not pdf_path.exists():
        print(f"\nError: PDF not found: {pdf_path}")
        return

    # Get total pages
    doc = fitz.open(str(pdf_path))
    pdf_total_pages = len(doc)
    doc.close()

    print(f"\nPDF: {pdf_path.name}")
    print(f"Total pages: {pdf_total_pages}")
    print(f"TOC page: 3 (detected by OCR page text)")

    # Create Granite extractor
    print("\nInitializing Granite VLM extractor...")
    extractor = GraniteTOCExtractor()

    # Extract TOC
    print(f"\nExtracting TOC from page 3 (2-page extraction)...")
    toc_entries, confidence, method = extractor.extract_full_workflow(
        pdf_path,
        toc_page_num=3,
        pdf_total_pages=pdf_total_pages
    )

    # Display results
    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}")
    print(f"Method: {method}")
    print(f"Confidence: {confidence:.2f} (threshold: 0.60)")
    print(f"Total entries: {len(toc_entries)}")

    if len(toc_entries) == 0:
        print("\n[FAILED] No TOC entries extracted!")
        return

    print(f"\n{'='*80}")
    print("EXTRACTED TOC ENTRIES")
    print(f"{'='*80}")

    # Count entry types
    exact_count = sum(1 for e in toc_entries if isinstance(e['page'], int) and e['page'] > 0)
    range_count = sum(1 for e in toc_entries if isinstance(e['page'], str) and '-' in str(e['page']))
    unknown_count = sum(1 for e in toc_entries if e['page'] == 0)

    for entry in toc_entries:
        page_str = str(entry['page'])
        if entry['page'] == 0:
            status = "UNKNOWN"
        elif '-' in page_str:
            status = "RANGE"
        else:
            status = "EXACT"

        print(f"  {entry['number']:6s} {entry['title']:50s} {page_str:>8s} [{status}]")

    print(f"\n{'='*80}")
    print("STATISTICS")
    print(f"{'='*80}")
    print(f"Exact pages: {exact_count}")
    print(f"Range pages: {range_count}")
    print(f"Unknown pages: {unknown_count}")
    print(f"Confidence: {confidence:.2%}")

    # Compare with expected
    expected_pages = {
        '1': 5, '2': 6, '2.1': 7, '2.2': 8,
        '3': 9, '4': 10, '5': 12, '6': 13
    }

    print(f"\n{'='*80}")
    print("VALIDATION AGAINST EXPECTED VALUES")
    print(f"{'='*80}")

    correct = 0
    for entry in toc_entries:
        section = entry['number']
        page = entry['page']

        if section in expected_pages:
            expected = expected_pages[section]

            if isinstance(page, int) and page == expected:
                print(f"  {section:6s}: {page} == {expected} [CORRECT]")
                correct += 1
            elif isinstance(page, str) and '-' in page:
                lower, upper = map(int, page.split('-'))
                if lower <= expected <= upper:
                    print(f"  {section:6s}: {expected} in range {page} [CORRECT]")
                    correct += 1
                else:
                    print(f"  {section:6s}: {expected} NOT in range {page} [WRONG]")
            else:
                print(f"  {section:6s}: {page} != {expected} [WRONG]")

    accuracy = correct / len(expected_pages) * 100 if expected_pages else 0

    print(f"\n{'='*80}")
    print(f"ACCURACY: {correct}/{len(expected_pages)} = {accuracy:.1f}%")
    print(f"{'='*80}")

    # Check if it would pass the database builder threshold
    if confidence >= 0.6 and len(toc_entries) >= 3:
        print("\n[SUCCESS] Would be ACCEPTED by database builder (confidence >= 0.60)")
    else:
        print(f"\n[FAILED] Would be REJECTED by database builder (confidence {confidence:.2f} < 0.60)")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    main()
