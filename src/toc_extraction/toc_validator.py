"""
TOC Validation and Refinement

Provides validation logic for TOC entries extracted by Granite VLM or text-based methods.
Implements 3-rule validation system and range notation for uncertain pages.
"""

import re
from typing import List, Dict, Optional


def parse_granite_multicolumn_table(
    markdown_text: str,
    max_page_number: Optional[int] = None,
    enable_retry: bool = False
) -> List[Dict]:
    """
    Parse Granite's multi-column table format

    Granite outputs TOC as table with extra columns due to dotted lines:
    |   Contents | 1.                     |   2. |   3. |   4. |   5. |
    |        1   | General Project data   |    5 |    6 |    7 |    8 |

    We extract: section number (col 0), title (col 1), first page number (col 2)

    Args:
        markdown_text: Granite's markdown table output
        max_page_number: Maximum valid page number (PDF total pages)
        enable_retry: Not used (kept for compatibility)

    Returns:
        List of TOC entries: [{number, title, page, original_page}, ...]
    """
    lines = markdown_text.split('\n')
    toc_entries = []

    in_table = False
    for line in lines:
        # Check if this is a table row
        if '|' not in line:
            continue

        # Skip header and separator rows
        if 'Contents' in line or '---' in line:
            in_table = True
            continue

        if not in_table:
            continue

        # Split by |
        cols = [c.strip() for c in line.split('|')]

        # Remove empty first/last columns
        cols = [c for c in cols if c]

        # Handle different column formats:
        # - 6-column: | section | title | page1 | page2 | page3 | page4 |
        # - 3-column: | section | title | page |
        # - 2-column: | section | title | (no page)

        if len(cols) >= 3:
            # 3+ column format
            section_num = cols[0].strip()
            title = cols[1].strip()

            # Extract first page number from column 2
            try:
                page = int(cols[2].strip())
            except (ValueError, IndexError):
                page = 0

            # Only add if we have valid section number
            if section_num and any(c.isdigit() for c in section_num):
                toc_entries.append({
                    'number': section_num,
                    'title': title,
                    'page': page,
                    'original_page': page
                })

        elif len(cols) == 2:
            # 2-column format (no page numbers in table)
            section_num = cols[0].strip()
            title = cols[1].strip()

            # Try to extract page number from title if it ends with a number
            page = 0
            title_parts = title.rsplit(maxsplit=1)
            if len(title_parts) == 2:
                try:
                    page = int(title_parts[1])
                    title = title_parts[0]  # Remove page number from title
                except ValueError:
                    pass

            # Only add if we have valid section number
            if section_num and any(c.isdigit() for c in section_num):
                toc_entries.append({
                    'number': section_num,
                    'title': title,
                    'page': page,
                    'original_page': page
                })

    return toc_entries


def validate_and_refine_toc(
    toc_entries: List[Dict],
    pdf_total_pages: int
) -> List[Dict]:
    """
    Validate TOC entries and apply range notation for uncertain pages

    3-Rule Validation System:
    1. Page must not exceed PDF total pages (hallucination)
    2. Subsections must be >= parent section page (boundary violation)
    3. Subsections of last main section use range notation (no next boundary)

    Args:
        toc_entries: List of TOC entries from parse_granite_multicolumn_table()
        pdf_total_pages: Total pages in PDF

    Returns:
        Updated toc_entries with validated pages (may include range notation)
    """

    # Build main section boundaries map
    main_section_boundaries = {}
    for entry in toc_entries:
        section_num = entry['number']
        # Main sections are single digits or integers without dots
        if '.' not in section_num:
            main_section_boundaries[section_num] = entry['page']

    # Identify the last main section (highest number)
    last_main_section = None
    if main_section_boundaries:
        last_main_section = max(
            main_section_boundaries.keys(),
            key=lambda x: int(x)
        )

    # Validate entries
    for entry in toc_entries:
        section_num = entry['number']
        page = entry['page']
        is_hallucinated = False
        is_last_section_subsection = False

        # Special handling: ALL subsections of last main section use range notation
        # Reason: Granite has no "next section" boundary for validation
        if '.' in section_num and last_main_section:
            parent_num = section_num.split('.')[0]
            if parent_num == last_main_section:
                is_last_section_subsection = True

        # Rule 1: Check against PDF total pages
        if page > pdf_total_pages:
            is_hallucinated = True

        # Rule 2 & 3: For subsections, check parent section boundaries
        if '.' in section_num and not is_hallucinated and not is_last_section_subsection:
            parent_num = section_num.split('.')[0]

            if parent_num in main_section_boundaries:
                parent_page = main_section_boundaries[parent_num]

                # Subsection must be >= parent page
                if page < parent_page:
                    is_hallucinated = True

                # Find next main section to establish upper boundary
                parent_int = int(parent_num)
                next_section_num = str(parent_int + 1)

                if next_section_num in main_section_boundaries:
                    next_section_page = main_section_boundaries[next_section_num]
                    # Subsection must be < next main section
                    if page >= next_section_page:
                        is_hallucinated = True

        # Apply range notation for hallucinations or last section subsections
        if is_hallucinated or is_last_section_subsection:
            # Calculate valid range
            if '.' in section_num:
                parent_num = section_num.split('.')[0]
                parent_page = main_section_boundaries.get(parent_num, 0)

                # Find upper boundary (next main section or PDF end)
                parent_int = int(parent_num)
                next_section_num = str(parent_int + 1)

                if next_section_num in main_section_boundaries:
                    upper_bound = main_section_boundaries[next_section_num] - 1
                else:
                    # Last section, use PDF end
                    upper_bound = pdf_total_pages
            else:
                # Main section hallucinated (shouldn't happen)
                parent_page = 0
                upper_bound = pdf_total_pages

            # Set to range notation
            entry['page'] = f"{parent_page}-{upper_bound}"

    return toc_entries


def calculate_toc_confidence(toc_entries: List[Dict]) -> float:
    """
    Calculate confidence score for TOC extraction

    Confidence = (exact pages) / (total entries)
    Range pages and unknown pages reduce confidence

    Args:
        toc_entries: List of TOC entries

    Returns:
        Confidence score (0.0 to 1.0)
    """
    if not toc_entries:
        return 0.0

    unknown_count = sum(1 for e in toc_entries if e['page'] == 0)
    range_count = sum(
        1 for e in toc_entries
        if isinstance(e['page'], str) and '-' in str(e['page'])
    )
    exact_count = len(toc_entries) - unknown_count - range_count

    confidence = exact_count / len(toc_entries)
    return confidence


# Test function
def test_validator():
    """Test validation logic on sample TOC"""

    print("="*80)
    print("TESTING TOC VALIDATOR")
    print("="*80)

    # Sample TOC entries (Well 7 format)
    sample_toc = [
        {'number': '1', 'title': 'General Project data', 'page': 5, 'original_page': 5},
        {'number': '2', 'title': 'Well summary', 'page': 6, 'original_page': 6},
        {'number': '2.1', 'title': 'Directional plots', 'page': 7, 'original_page': 7},
        {'number': '2.2', 'title': 'Technical summary', 'page': 8, 'original_page': 8},
        {'number': '6', 'title': 'HSE performance', 'page': 13, 'original_page': 13},
        {'number': '6.1', 'title': 'General', 'page': 14, 'original_page': 14},  # Hallucinated
        {'number': '6.2', 'title': 'Incidents', 'page': 16, 'original_page': 16},  # Hallucinated
        {'number': '6.3', 'title': 'Drills', 'page': 17, 'original_page': 17},  # Hallucinated
    ]

    pdf_total_pages = 14

    print(f"\nPDF total pages: {pdf_total_pages}")
    print(f"TOC entries: {len(sample_toc)}")

    print("\n" + "-"*80)
    print("BEFORE VALIDATION")
    print("-"*80)
    for entry in sample_toc:
        print(f"  {entry['number']:5s} {entry['title']:40s} page {entry['page']}")

    # Validate
    validated_toc = validate_and_refine_toc(sample_toc, pdf_total_pages)

    print("\n" + "-"*80)
    print("AFTER VALIDATION")
    print("-"*80)
    for entry in validated_toc:
        page_str = str(entry['page'])
        if entry['page'] == 0:
            status = "UNKNOWN"
        elif '-' in page_str:
            status = "RANGE"
        else:
            status = "EXACT"

        print(f"  {entry['number']:5s} {entry['title']:40s} {page_str:>6s} [{status}]")

    # Calculate confidence
    confidence = calculate_toc_confidence(validated_toc)
    print(f"\n{'='*80}")
    print(f"Confidence: {confidence:.2f}")
    print(f"{'='*80}")


if __name__ == "__main__":
    test_validator()
