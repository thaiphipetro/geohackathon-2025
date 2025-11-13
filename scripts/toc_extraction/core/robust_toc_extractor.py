"""
Step 2: RobustTOCExtractor - Unified TOC Extraction System
Handles all TOC formats discovered in Step 1 analysis
"""

import re
from typing import List, Dict, Tuple, Optional


class RobustTOCExtractor:
    """
    Robust TOC extraction that handles multiple formats:
    - Markdown tables (2, 3, 4 columns)
    - Dotted format (1.1 Title ........ 5)
    - Multi-line format (section on one line, title+page on next)
    - Space-separated format (1.1 Title      5)
    """

    def __init__(self):
        self.debug = False

    def extract(self, toc_lines: List[str], debug: bool = False) -> Tuple[List[Dict], str]:
        """
        Main extraction method - tries all patterns hierarchically

        Returns:
            (entries, pattern_name) - List of TOC entries and which pattern matched
        """
        self.debug = debug

        # Step 1: Detect format type
        format_type = self._detect_format(toc_lines)

        if self.debug:
            print(f"\n[RobustTOCExtractor] Detected format: {format_type}")

        # Step 2: Use appropriate extractor
        if format_type == "table":
            entries = self._extract_table_adaptive(toc_lines)
            if len(entries) >= 3:
                return entries, "Adaptive Table"

        # Try non-table patterns
        patterns = [
            ("Multi-line Dotted", self._extract_multiline_dotted),
            ("Dotted Format", self._extract_dotted),
            ("Space-separated", self._extract_spaced),
        ]

        for pattern_name, pattern_func in patterns:
            entries = pattern_func(toc_lines)
            if len(entries) >= 3:
                if self.debug:
                    print(f"[RobustTOCExtractor] Matched pattern: {pattern_name}")
                return entries, pattern_name

        return [], None

    def _detect_format(self, lines: List[str]) -> str:
        """Detect if TOC uses table format or plain text"""
        table_lines = [l for l in lines if '|' in l and '---' not in l]

        if len(table_lines) >= 3:
            return "table"
        else:
            return "plain"

    # =========================================================================
    # TABLE EXTRACTORS
    # =========================================================================

    def _extract_table_adaptive(self, lines: List[str]) -> List[Dict]:
        """
        Adaptive table parser that intelligently detects column roles

        Algorithm:
        1. Find which column has section numbers
        2. Find which column has page numbers
        3. Find which column has titles (or title+page combined)
        4. Extract accordingly
        """
        toc_entries = []

        for line_num, line in enumerate(lines):
            if '|' not in line or '---' in line:
                continue

            parts = [p.strip() for p in line.split('|') if p.strip()]

            if len(parts) < 2:
                continue

            # Try to extract from this line
            entry = self._parse_table_line(parts)

            if entry:
                toc_entries.append(entry)

        return toc_entries

    def _parse_table_line(self, parts: List[str]) -> Optional[Dict]:
        """
        Parse a single table line intelligently

        Returns TOC entry dict or None if parsing fails
        """
        section_num = None
        title = None
        page = None

        # Step 1: Find section number (first column matching \d+\.?\d* or Appendix)
        appendix_col_with_title = None
        for col in parts:
            # Match numeric sections: 1, 1.1, 1.2.3
            if re.match(r'^\d+\.?\d*\.?\d*$', col):
                section_num = col
                break
            # Match Appendix entries: "Appendix 1", "A d ppen ix 1" (with OCR errors)
            appendix_match = re.search(r'(?:A\s*p*\s*d?\s*p*pen\s*d?ix|Appendix)\s+(\d+)', col, re.IGNORECASE)
            if appendix_match:
                section_num = f"Appendix {appendix_match.group(1)}"
                # Check if this column also contains the title (e.g., "Appendix 1, Detailed drilling program")
                if ',' in col:
                    appendix_col_with_title = col
                break

        if not section_num:
            return None  # Must have a section number

        # Step 2: Find title and page in remaining columns
        for col in parts:
            if col == section_num:
                continue  # Skip section number column
            # Also skip columns that contain the appendix pattern (e.g., "Appendix 1, Title...")
            if section_num.startswith("Appendix") and section_num in col:
                continue

            # Check if this column is JUST a page number
            if re.match(r'^\d{1,3}$', col):
                page_candidate = int(col)
                if page_candidate < 500:  # Reasonable page number
                    page = page_candidate
                    continue

            # Check if this column contains title + dots/underscores + page
            # Support both dots and underscores as separators
            dotted_match = re.search(r'[._]{2,}\s*(\d+)\s*$', col)
            if dotted_match:
                page_candidate = dotted_match.group(1)
                # Extract title (everything before the dots/underscores)
                title_candidate = col[:dotted_match.start()].strip()

                if len(title_candidate) > 1 and page_candidate.isdigit():
                    title = title_candidate
                    page = int(page_candidate)
                    break  # Found both in same column!

            # Check if this column is just a title
            if len(col) > 2 and not re.match(r'^\d+\.?\d*$', col):
                # Avoid columns that look like duplicates or metadata
                if col.lower() not in ['content', 'contents', 'page', 'section']:
                    if not title:  # Only take first title column
                        title = col

        # If we haven't found a title yet, try to extract from appendix column
        if not title and appendix_col_with_title:
            # Extract title after comma: "Appendix 1, Title" -> "Title"
            title_parts = appendix_col_with_title.split(',', 1)
            if len(title_parts) > 1:
                title = title_parts[1].strip()

        # Validate we have minimum required pieces (section_num + title)
        # Page is optional - some TOCs don't have pages, or we couldn't extract them
        if section_num and title:
            entry = {
                'number': section_num,
                'title': title,
                'page': page if page else 0
            }
            return entry

        return None

    # =========================================================================
    # NON-TABLE EXTRACTORS
    # =========================================================================

    def _extract_dotted(self, lines: List[str]) -> List[Dict]:
        """
        Extract from dotted format: 1.1 Title ........ 5
        """
        toc_entries = []

        for line in lines:
            # Match: section_number + title + dots + page
            match = re.match(r'^(\d+\.?\d*\.?\d*)\s+(.+?)\s*[._]{2,}\s*(\d+)\s*$', line.strip())

            if match:
                section_num, title, page = match.groups()

                if len(title.strip()) > 2 and int(page) < 500:
                    toc_entries.append({
                        'number': section_num,
                        'title': title.strip(),
                        'page': int(page)
                    })

        return toc_entries

    def _extract_spaced(self, lines: List[str]) -> List[Dict]:
        """
        Extract from space-separated format: 1.1  Title     5
        """
        toc_entries = []

        for line in lines:
            # Match: section_number + title + spaces + page
            match = re.match(r'^(\d+\.?\d*\.?\d*)\s+(.+?)\s{3,}(\d+)\s*$', line.strip())

            if match:
                section_num, title, page = match.groups()

                if len(title.strip()) > 2 and int(page) < 500:
                    toc_entries.append({
                        'number': section_num,
                        'title': title.strip(),
                        'page': int(page)
                    })

        return toc_entries

    def _extract_multiline_dotted(self, lines: List[str]) -> List[Dict]:
        """
        Extract from multi-line format:

        Line 1: 1.
        Line 2: (optional empty)
        Line 3: Title ........ 5
        """
        toc_entries = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Check if line is ONLY a section number
            if re.match(r'^\d+\.?\d*\.?\d*\s*$', line):
                section_num = line.strip()

                # Look ahead for title+page, skipping empty lines
                j = i + 1
                max_lookahead = min(i + 5, len(lines))
                found = False

                while j < max_lookahead:
                    next_line = lines[j].strip()

                    # Skip empty lines
                    if len(next_line) == 0:
                        j += 1
                        continue

                    # Check if this line has title + dots/underscores + page
                    title_match = re.match(r'^(.+?)\s*[._]{2,}\s*(\d+)\s*$', next_line)

                    if title_match:
                        title, page = title_match.groups()
                        title = title.strip()

                        if len(title) > 2 and int(page) < 500:
                            toc_entries.append({
                                'number': section_num,
                                'title': title,
                                'page': int(page)
                            })
                            i = j + 1  # Skip past this entry
                            found = True
                            break
                    else:
                        # Not a title+page line, stop looking
                        break

                    j += 1

                # If we didn't find a match, increment i
                if not found:
                    i += 1
            else:
                i += 1

        return toc_entries


def test_extractor():
    """Test the extractor on example TOC formats"""

    extractor = RobustTOCExtractor()

    # Test case 1: Markdown table (3-column)
    print("="*80)
    print("Test 1: Markdown Table (3-column)")
    print("="*80)

    table_lines = [
        "| 1 | Introduction | 3 |",
        "| 1.1 | Background | 4 |",
        "| 2 | Methodology | 10 |",
        "| 2.1 | Data Collection | 12 |",
    ]

    entries, pattern = extractor.extract(table_lines, debug=True)
    print(f"\nFound {len(entries)} entries using {pattern}")
    for e in entries:
        print(f"  {e['number']:6s} {e['title']:40s} (page {e['page']})")

    # Test case 2: Dotted format
    print("\n" + "="*80)
    print("Test 2: Dotted Format")
    print("="*80)

    dotted_lines = [
        "1      Introduction ........................... 3",
        "1.1    Background ............................. 4",
        "2      Methodology ............................ 10",
        "2.1    Data Collection ........................ 12",
    ]

    entries, pattern = extractor.extract(dotted_lines, debug=True)
    print(f"\nFound {len(entries)} entries using {pattern}")
    for e in entries:
        print(f"  {e['number']:6s} {e['title']:40s} (page {e['page']})")

    # Test case 3: Multi-line format
    print("\n" + "="*80)
    print("Test 3: Multi-line Format")
    print("="*80)

    multiline_lines = [
        "1.",
        "",
        "Introduction ........................... 3",
        "",
        "1.1",
        "",
        "Background ............................. 4",
        "",
        "2",
        "",
        "Methodology ............................ 10",
    ]

    entries, pattern = extractor.extract(multiline_lines, debug=True)
    print(f"\nFound {len(entries)} entries using {pattern}")
    for e in entries:
        print(f"  {e['number']:6s} {e['title']:40s} (page {e['page']})")

    print("\n" + "="*80)


if __name__ == '__main__':
    test_extractor()
