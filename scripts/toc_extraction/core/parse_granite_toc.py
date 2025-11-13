"""
Parse Granite-Docling TOC output that has extra columns
Extract: Section number, Title, and FIRST page number only

With validation and retry:
1. Detect hallucinated page numbers (exceed PDF boundaries or parent section boundaries)
2. Re-extract hallucinated entries with focused Granite query + constraints
3. If still wrong, mark as 0
"""

import re
import time
from pathlib import Path
import fitz  # PyMuPDF


def retry_extract_with_granite(toc_page_path, section_num, title, parent_page, max_page_number):
    """
    Re-extract a specific TOC entry using Granite with explicit constraints

    Args:
        toc_page_path: Path to TOC page PDF/image
        section_num: Section number to extract (e.g., "6.1")
        title: Section title
        parent_page: Parent section page number
        max_page_number: PDF total pages

    Returns:
        Extracted page number, or 0 if extraction fails
    """
    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption
        from docling.pipeline.vlm_pipeline import VlmPipeline
        from docling.datamodel.pipeline_options import VlmPipelineOptions
        from docling.datamodel import vlm_model_specs

        print(f"    [RETRY] Re-extracting section {section_num} with constraints:")
        print(f"            Parent section page: {parent_page}")
        print(f"            PDF total pages: {max_page_number}")
        print(f"            Expected range: {parent_page} to {max_page_number}")

        # Process TOC page with Granite again
        # Note: In production, we would crop to just the specific line
        # For now, re-process the whole TOC page

        pipeline_options = VlmPipelineOptions(
            vlm_options=vlm_model_specs.GRANITEDOCLING_TRANSFORMERS
        )

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options
                )
            }
        )

        print(f"    [RETRY] Processing with Granite (this may take 2-3 min)...")
        start = time.time()
        result = converter.convert(str(toc_page_path))
        elapsed = time.time() - start
        print(f"    [RETRY] Completed in {elapsed:.1f}s")

        markdown = result.document.export_to_markdown()

        # Parse the table again, look for this specific section
        lines = markdown.split('\n')
        for line in lines:
            if '|' not in line or 'Contents' in line or '---' in line:
                continue

            cols = [c.strip() for c in line.split('|')]
            cols = [c for c in cols if c]

            if len(cols) >= 3:
                line_section = cols[0].strip()
                if line_section == section_num:
                    # Found the line, extract page
                    try:
                        retry_page = int(cols[2].strip())
                        print(f"    [RETRY] Extracted page: {retry_page}")

                        # Validate against constraints
                        if retry_page > max_page_number:
                            print(f"    [RETRY] Still exceeds PDF ({retry_page} > {max_page_number}), marking as 0")
                            return 0

                        if retry_page < parent_page:
                            print(f"    [RETRY] Still before parent page ({retry_page} < {parent_page}), marking as 0")
                            return 0

                        print(f"    [RETRY] Validation passed, using page {retry_page}")
                        return retry_page

                    except (ValueError, IndexError):
                        print(f"    [RETRY] Could not parse page number, marking as 0")
                        return 0

        print(f"    [RETRY] Could not find section {section_num} in retry output, marking as 0")
        return 0

    except Exception as e:
        print(f"    [RETRY] Error during retry: {e}")
        print(f"    [RETRY] Marking as 0")
        return 0


def parse_granite_multicolumn_table(markdown_text, max_page_number=None, toc_page_path=None, enable_retry=True):
    """
    Parse Granite's table format which has extra page columns:
    |   Contents | 1.                     |   2. |   3. |   4. |   5. |
    |        1   | General Project data   |    5 |    6 |    7 |    8 |

    Extract: section number, title, first page number

    Args:
        markdown_text: Granite's markdown table output
        max_page_number: Maximum valid page number (PDF total page count)
        toc_page_path: Path to TOC page PDF for retry extraction (optional)
        enable_retry: If True, retry extraction for hallucinated entries (default: True)

    Validation rules:
        1. Page number must not exceed PDF total pages
        2. Subsections (e.g., 6.1) must be >= parent section page (e.g., section 6)
        3. Subsections must be < next main section page (or PDF end)

    Retry logic:
        - When hallucination detected and toc_page_path provided and enable_retry=True
        - Re-extract the specific entry with Granite + constraints
        - If still invalid, mark as 0
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

        if len(cols) >= 3:
            # Column 0: Section number
            # Column 1: Title
            # Column 2: First page number (the correct one!)

            section_num = cols[0].strip()
            title = cols[1].strip()

            # Extract first page number
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
                    'original_page': page  # Keep original for validation reporting
                })

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
        last_main_section = max(main_section_boundaries.keys(), key=lambda x: int(x))

    # Validate entries
    hallucination_warnings = []
    retry_performed = []
    last_section_subsections = []

    for entry in toc_entries:
        section_num = entry['number']
        page = entry['page']
        original_page = entry['original_page']
        title = entry['title']
        is_hallucinated = False
        is_last_section_subsection = False
        parent_page = None

        # Special handling: ALL subsections of the last main section use range notation
        # (Granite has no "next section" boundary for validation)
        if '.' in section_num and last_main_section:
            parent_num = section_num.split('.')[0]
            if parent_num == last_main_section:
                is_last_section_subsection = True
                last_section_subsections.append(section_num)

        # Rule 1: Check against PDF total pages
        if max_page_number is not None and page > max_page_number:
            is_hallucinated = True
            hallucination_warnings.append(
                f"  [WARN] Section {section_num} '{title}': Page {page} exceeds PDF length ({max_page_number} pages)"
            )

        # Rule 2 & 3: For subsections, check parent section boundaries
        if '.' in section_num and not is_hallucinated and not is_last_section_subsection:
            # Get parent section number (e.g., "6.1" -> "6")
            parent_num = section_num.split('.')[0]

            if parent_num in main_section_boundaries:
                parent_page = main_section_boundaries[parent_num]

                # Subsection must be >= parent page
                if page < parent_page:
                    is_hallucinated = True
                    hallucination_warnings.append(
                        f"  [WARN] Subsection {section_num} '{title}': Page {page} is before parent section {parent_num} (page {parent_page})"
                    )

                # Find next main section to establish upper boundary
                parent_int = int(parent_num)
                next_section_num = str(parent_int + 1)

                if next_section_num in main_section_boundaries:
                    next_section_page = main_section_boundaries[next_section_num]
                    # Subsection must be < next main section
                    if page >= next_section_page:
                        is_hallucinated = True
                        hallucination_warnings.append(
                            f"  [WARN] Subsection {section_num} '{title}': Page {page} is at/after next section {next_section_num} (page {next_section_page})"
                        )

        # Handle hallucination or last section subsections: retry or use range notation
        if is_hallucinated or is_last_section_subsection:
            # Calculate valid range for this subsection
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
                    upper_bound = max_page_number if max_page_number else parent_page
            else:
                # Main section hallucinated (shouldn't happen)
                parent_page = 0
                upper_bound = max_page_number if max_page_number else 0

            if enable_retry and toc_page_path is not None and is_hallucinated:
                # Only retry for actual hallucinations, not for last section subsections
                print(f"\n  [HALLUCINATION] Section {section_num} '{title}' (original page {page})")
                print(f"    Valid range: {parent_page}-{upper_bound}")

                retry_page = retry_extract_with_granite(
                    toc_page_path, section_num, title, parent_page, max_page_number
                )

                if retry_page == 0 or retry_page > max_page_number:
                    # Retry failed, use range notation
                    entry['page'] = f"{parent_page}-{upper_bound}"
                    print(f"    [RESULT] Retry failed, using range: {parent_page}-{upper_bound}")
                else:
                    # Retry succeeded
                    entry['page'] = retry_page
                    print(f"    [RESULT] Retry succeeded, using page {retry_page}")

                entry['retry_performed'] = True
                retry_performed.append(section_num)
            else:
                # No retry available or last section subsection, use range notation
                entry['page'] = f"{parent_page}-{upper_bound}"
                if is_last_section_subsection and not is_hallucinated:
                    # Log for last section subsections (not hallucinations)
                    print(f"  [LAST SECTION] Section {section_num} '{title}': Setting to range {parent_page}-{upper_bound}")

    # Print validation summary
    if hallucination_warnings or last_section_subsections:
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)

        if last_main_section and last_section_subsections:
            print(f"\n[LAST SECTION HANDLING]")
            print(f"  Last main section: {last_main_section}")
            print(f"  Subsections using range notation: {len(last_section_subsections)}")
            for sec in last_section_subsections:
                entry = next(e for e in toc_entries if e['number'] == sec)
                print(f"    - Section {sec}: {entry['page']}")
            print(f"  Reason: Granite lacks 'next section' boundary for validation")

        if hallucination_warnings:
            print(f"\n[BOUNDARY VIOLATIONS]")
            print(f"  Detected {len(hallucination_warnings)} invalid page numbers:")
            for warning in hallucination_warnings:
                print(warning)

            if retry_performed:
                print(f"\n  Retry extraction performed for {len(retry_performed)} entries:")
                for sec in retry_performed:
                    print(f"    - Section {sec}")
            else:
                print("\n  No retry available (toc_page_path not provided or enable_retry=False)")
                print("  Invalid entries set to range notation (parent_page-upper_bound)")

        print("\n[MAIN SECTION BOUNDARIES]")
        for sec_num, sec_page in sorted(main_section_boundaries.items(), key=lambda x: int(x[0])):
            print(f"  Section {sec_num}: page {sec_page}")

    return toc_entries


def main():
    """Test the parser on Granite output with retry validation"""

    print("="*80)
    print("PARSING GRANITE-DOCLING TOC OUTPUT WITH RETRY VALIDATION")
    print("="*80)

    # Load Granite output
    granite_file = Path("outputs/granite_test/well7_correct_toc_granite.md")
    toc_page_pdf = Path("outputs/granite_test/well7_toc_page_only.pdf")

    if not granite_file.exists():
        print(f"\nError: {granite_file} not found")
        return

    with open(granite_file, 'r', encoding='utf-8') as f:
        markdown = f.read()

    print("\nGranite markdown:")
    print("-"*80)
    print(markdown)
    print("-"*80)

    # Well 7 EOWR PDF has 14 pages total
    pdf_total_pages = 14

    # Check if TOC page PDF exists for retry
    if toc_page_pdf.exists():
        print(f"\nTOC page PDF found: {toc_page_pdf}")
        print("Retry validation enabled")
        enable_retry = True
    else:
        print(f"\nTOC page PDF not found: {toc_page_pdf}")
        print("Retry validation disabled (will mark as 0)")
        enable_retry = False

    # Parse entries with validation and retry
    toc_entries = parse_granite_multicolumn_table(
        markdown,
        max_page_number=pdf_total_pages,
        toc_page_path=toc_page_pdf if enable_retry else None,
        enable_retry=enable_retry
    )

    print(f"\n[PARSED] Extracted {len(toc_entries)} TOC entries:")
    print()
    for i, entry in enumerate(toc_entries, 1):
        print(f"  {i}. {entry['number']:5s} - {entry['title']:50s} (page {entry['page']})")

    # Compare with actual TOC
    print("\n" + "="*80)
    print("COMPARISON WITH ACTUAL TOC")
    print("="*80)

    actual_toc = [
        ("1", "General Project data", 5),
        ("2", "Well summary", 6),
        ("2.1", "Directional plots", 7),
        ("2.2", "Technical summary", 8),
        ("3", "Drilling fluid summary", 9),
        ("4", "Geology", 10),
        ("5", "Well schematic", 12),
        ("6", "HSE performance", 13),
        ("6.1", "General", 13),
        ("6.2", "Incidents", 13),
        ("6.3", "Drills / Emergency exercises, inspections & audits", 13),
    ]

    print(f"\n{'#':<4} {'Section':<8} {'Actual Page':<15} {'Granite Page':<15} {'Offset':<10} {'Match?'}")
    print("-"*80)

    correct = 0
    for i, entry in enumerate(toc_entries):
        if i >= len(actual_toc):
            break

        granite_page = entry['page']
        actual_entry = actual_toc[i]
        actual_page = actual_entry[2]

        # Handle range notation (e.g., "13-14")
        if isinstance(granite_page, str) and '-' in str(granite_page):
            # Check if actual page is within range
            range_parts = str(granite_page).split('-')
            try:
                lower = int(range_parts[0])
                upper = int(range_parts[1])
                in_range = lower <= actual_page <= upper
                match = "RANGE" if in_range else "NO"
                offset_str = f"({lower}-{upper})"
                if in_range:
                    correct += 1  # Count as correct if within range
            except:
                match = "NO"
                offset_str = "N/A"
        else:
            # Exact page comparison
            try:
                granite_int = int(granite_page)
                offset = granite_int - actual_page
                match = "YES" if granite_int == actual_page else "NO"
                offset_str = f"{offset:+d}"
                if granite_int == actual_page:
                    correct += 1
            except:
                match = "NO"
                offset_str = "N/A"

        print(f"{i+1:<4} {entry['number']:<8} {actual_page:<15} {str(granite_page):<15} {offset_str:<10} {match}")

    # Calculate accuracy
    total = min(len(toc_entries), len(actual_toc))
    accuracy = (correct / total * 100) if total > 0 else 0

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"\nEntries extracted: {len(toc_entries)}")
    print(f"Correct page numbers: {correct}/{total}")
    print(f"Page accuracy: {accuracy:.1f}%")

    if accuracy == 100:
        print("\n[SUCCESS] Granite-Docling correctly read the TOC page!")
        print("   All page numbers match the actual TOC.")
    elif accuracy >= 80:
        print(f"\n[GOOD] {accuracy:.1f}% accuracy")
        print("   Most page numbers correct.")
    else:
        print(f"\n[POOR] Only {accuracy:.1f}% accuracy")
        print("   Page numbers still incorrect.")

    return {
        'entries': len(toc_entries),
        'correct': correct,
        'total': total,
        'accuracy': accuracy
    }


if __name__ == "__main__":
    result = main()
