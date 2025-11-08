# TOC Database Implementation Plan

**Goal:** Build a reliable TOC database for all 8 wells by reading first 4 pages of each EOWR report

**Problem Identified:** Current TOC parser is too rigid - only looks for markdown tables (`| section | title | page |`), missing plain text TOCs

---

## Phase 1: Fast EOWR Identification (10 minutes)

### Task 1.1: Scan Dataset
- Iterate through all 8 wells
- Find all PDF files matching EOWR patterns:
  - `*eowr*.pdf`
  - `*final-well-report*.pdf`
  - `*final well report*.pdf`
  - `*end-of-well*.pdf`

**Output:** Dictionary of `{well_name: [eowr_file_paths]}`

### Task 1.2: Quick Metadata Extraction
For each EOWR file:
- Get file size (bytes)
- Get file modification date (as backup)
- Count total pages (if available from PDF metadata)

**Output:** `{file_path: {size, mod_date, pages}}`

---

## Phase 2: Parse First 4 Pages Only (30 minutes)

### Task 2.1: Optimized Parsing Function
```python
def parse_first_4_pages(pdf_path):
    """
    Parse only first 4 pages - much faster than full document
    Returns: {text, lines, char_count}
    """
    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))
    full_text = result.document.export_to_markdown()

    # Estimate: ~2000-3000 chars per page
    # Take first 12,000 chars to ensure we get 4 pages
    first_4_pages = full_text[:12000]

    return {
        'text': first_4_pages,
        'lines': first_4_pages.split('\n'),
        'char_count': len(first_4_pages),
        'full_length': len(full_text)
    }
```

**Performance:** Should be same speed as full parse (Docling parses entire PDF), but we only analyze first 12K chars

---

## Phase 3: Flexible TOC Extraction (45 minutes)

### Task 3.1: Multi-Pattern TOC Parser

**Strategy:** Try multiple patterns in order until one succeeds

#### Pattern 1: Markdown Tables (current method)
```
| 1.1 | Section Name | Section Name | 5 |
```
**Indicators:**
- Lines with `|` character
- First column: section number `\d+\.?\d*`
- Last column: page number (digit)

#### Pattern 2: Plain Text with Dots
```
1.1 Section Name .................... 5
2.3 Another Section .............. 12
```
**Regex:** `^(\d+\.?\d*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$`

#### Pattern 3: Plain Text with Spacing
```
1.1    Section Name                    5
2.3    Another Section                12
```
**Regex:** `^(\d+\.?\d*)\s+(.+?)\s{3,}(\d+)\s*$`

#### Pattern 4: Tab-Separated
```
1.1	Section Name	5
2.3	Another Section	12
```
**Split by:** `\t` (tab character)

#### Pattern 5: OCR Artifacts (common issues)
```
1.1 Section Name  5
(multiple spaces instead of dots)
```
**Regex:** `^(\d+\.?\d*)\s+(.+?)\s{2,}(\d+)\s*$`

### Task 3.2: TOC Extraction Logic

```python
def extract_toc_flexible(lines):
    """
    Try multiple patterns to extract TOC
    Returns: [{number, title, page}] or []
    """
    # Step 1: Find TOC region (between "Contents" and first ## heading)
    toc_start, toc_end = find_toc_boundaries(lines)

    if toc_start < 0:
        return []

    toc_lines = lines[toc_start:toc_end]

    # Step 2: Try each pattern
    patterns = [
        extract_markdown_table_toc,
        extract_dotted_toc,
        extract_spaced_toc,
        extract_tab_separated_toc,
        extract_ocr_artifact_toc
    ]

    for pattern_func in patterns:
        toc = pattern_func(toc_lines)
        if len(toc) >= 3:  # At least 3 entries to be valid
            return toc

    return []
```

### Task 3.3: TOC Boundary Detection

```python
def find_toc_boundaries(lines):
    """
    Find start and end of TOC section
    """
    # Find start: line with keywords
    toc_keywords = [
        'table of contents', 'contents', 'index',
        'table des matieres', 'inhoud', 'inhaltsverzeichnis'
    ]

    start = -1
    for i, line in enumerate(lines[:100]):  # First 100 lines only
        if any(kw in line.lower() for kw in toc_keywords):
            start = i
            break

    # If no explicit heading, look for structure (multiple lines with numbers)
    if start < 0:
        start = find_implicit_toc_start(lines)

    # Find end: first ## heading after TOC, or max 150 lines
    end = min(start + 150, len(lines)) if start >= 0 else -1
    for i in range(start + 1, min(start + 150, len(lines))):
        if lines[i].strip().startswith('##') and not 'content' in lines[i].lower():
            end = i
            break

    return start, end
```

---

## Phase 4: Publication Date Extraction (15 minutes)

### Task 4.1: Context-Aware Date Finder

**Strategy:** Same as before, but ensure we search entire 4 pages

```python
def extract_publication_date(first_4_pages_text):
    """
    Find publication date using context keywords
    """
    context_keywords = [
        'publication date', 'date', 'published', 'issue date',
        'report date', 'approved', 'version', 'revision date'
    ]

    # Search line by line
    lines = first_4_pages_text.split('\n')
    for i, line in enumerate(lines):
        if any(kw in line.lower() for kw in context_keywords):
            # Search this line + next 2 lines for dates
            search_text = ' '.join(lines[i:i+3])
            dates = extract_dates_from_text(search_text)
            if dates:
                return max(dates)  # Most recent date

    return None
```

---

## Phase 5: EOWR Selection & TOC Database (15 minutes)

### Task 5.1: Select Best EOWR per Well

**Criteria (in order):**
1. Has valid TOC (≥3 entries) → keep
2. Newest publication date → prefer
3. Largest file size → prefer
4. Filename contains "final" → prefer

```python
def select_best_eowr(eowr_candidates):
    """
    Select the best EOWR from multiple candidates
    """
    scored = []
    for candidate in eowr_candidates:
        score = 0
        if candidate['toc'] and len(candidate['toc']) >= 3:
            score += 1000  # TOC is critical
        if candidate['pub_date']:
            score += candidate['pub_date'].year * 10
        score += candidate['file_size'] / 1000000  # MB
        if 'final' in candidate['filename'].lower():
            score += 100

        scored.append((score, candidate))

    return max(scored, key=lambda x: x[0])[1]
```

### Task 5.2: Build TOC Database

```python
toc_database = {
    'Well 1': {
        'eowr_file': 'path/to/file.pdf',
        'pub_date': datetime(2020, 7, 15),
        'file_size': 5234567,
        'toc': [
            {'number': '1.1', 'title': 'Preface', 'page': 3},
            {'number': '3.4', 'title': 'Casing Profile', 'page': 20},
            ...
        ],
        'key_sections': {
            'casing': [{'number': '3.4', 'page': 20}],
            'borehole': [{'number': '3.1', 'page': 20}],
            'depth': [{'number': '3.6', 'page': 22}]
        }
    },
    'Well 2': {...},
    ...
}
```

### Task 5.3: Save to JSON

```python
import json
output_path = 'outputs/exploration/toc_database.json'
with open(output_path, 'w') as f:
    json.dump(toc_database, f, indent=2, default=str)
```

---

## Phase 6: Validation & Analysis (10 minutes)

### Task 6.1: Generate Report

```markdown
# TOC Database Report

## Summary
- Total wells: 8
- Wells with TOC: X/8 (Y%)
- Wells without TOC: Z/8

## Per-Well Details

### Well 1 (ADK-GT-01)
- EOWR: filename.pdf
- Publication Date: 2020-07-15
- TOC Entries: 15
- Key Sections Found:
  - Casing Profile (page 20)
  - Borehole Data (page 18)

### Well 2 (HAG GT-01-02)
...
```

### Task 6.2: Verify Key Sections

For each well, check if we found:
- ✅ Casing/Completion sections
- ✅ Borehole/Depth sections
- ✅ Technical summary sections

---

## Implementation Script Structure

```python
# File: notebooks/build_toc_database.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter
import re
import datetime
import json
from collections import defaultdict

# Phase 1: Scan
def scan_all_eowr_files(data_dir):
    """Return {well_name: [eowr_paths]}"""
    pass

# Phase 2: Parse first 4 pages
def parse_first_4_pages(pdf_path):
    """Return {text, lines, metadata}"""
    pass

# Phase 3: Flexible TOC extraction
def extract_toc_flexible(lines):
    """Try multiple patterns, return best result"""
    pass

def extract_markdown_table_toc(lines):
    """Pattern 1: | section | title | page |"""
    pass

def extract_dotted_toc(lines):
    """Pattern 2: 1.1 Title .... 5"""
    pass

def extract_spaced_toc(lines):
    """Pattern 3: 1.1  Title     5"""
    pass

# Phase 4: Date extraction
def extract_publication_date(text):
    """Context-aware date finder"""
    pass

# Phase 5: Selection & Database
def select_best_eowr(candidates):
    """Score and select best EOWR"""
    pass

def build_toc_database(data_dir):
    """Main function - orchestrate all phases"""
    pass

# Phase 6: Reporting
def generate_report(toc_database):
    """Create markdown report"""
    pass

if __name__ == '__main__':
    data_dir = Path(__file__).parent.parent / "Training data-shared with participants"
    toc_db = build_toc_database(data_dir)

    # Save
    with open('outputs/exploration/toc_database.json', 'w') as f:
        json.dump(toc_db, f, indent=2, default=str)

    # Report
    report = generate_report(toc_db)
    with open('outputs/exploration/toc_database_report.md', 'w') as f:
        f.write(report)
```

---

## Expected Outcomes

### Success Criteria
- ✅ All 8 wells scanned
- ✅ TOC extracted for ≥6/8 wells (75%)
- ✅ Key sections identified for ≥6/8 wells
- ✅ JSON database created
- ✅ Validation report generated

### Deliverables
1. `notebooks/build_toc_database.py` - Main script
2. `outputs/exploration/toc_database.json` - Structured database
3. `outputs/exploration/toc_database_report.md` - Human-readable report
4. `outputs/exploration/well_X_first_4_pages.txt` - Debug outputs (optional)

---

## Timeline

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | EOWR Identification | 10 min | Pending |
| 2 | Parse First 4 Pages | 30 min | Pending |
| 3 | Flexible TOC Extraction | 45 min | Pending |
| 4 | Date Extraction | 15 min | Pending |
| 5 | Database Building | 15 min | Pending |
| 6 | Validation & Report | 10 min | Pending |
| **Total** | | **2 hours** | |

---

## Risk Mitigation

### Risk 1: OCR Still Can't Extract TOC
**Mitigation:** For wells with no TOC, extract all section headings (##) as fallback

### Risk 2: Date Extraction Fails
**Mitigation:** Use file size as primary selector, date as secondary

### Risk 3: Multiple TOC Formats Still Missed
**Mitigation:** Save first 4 pages as text files for manual review, iterate on patterns

---

## Next Steps After This Plan

1. **Review & Approve** this plan
2. **Implement** `build_toc_database.py`
3. **Run** on all 8 wells
4. **Review** results and iterate on patterns if needed
5. **Use** TOC database to extract casing tables (Sub-Challenge 2)

---

## Questions to Resolve

1. Should we cache the parsed first 4 pages to avoid re-parsing? (Yes - saves time)
2. What if a well has NO TOC at all? (Use section heading fallback)
3. Should we validate by manually checking Well 1 first? (Yes - good idea)

---

**Ready to implement?** Let me know if you want to:
- ✅ Proceed with implementation
- 🔄 Adjust the plan
- 🔍 Manually verify Well 1 first to confirm TOC is readable
