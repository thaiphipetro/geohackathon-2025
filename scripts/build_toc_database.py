"""Build TOC Database for All Wells with Smart PDF Routing"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz  # PyMuPDF
from docling.document_converter import DocumentConverter
import re
import datetime
import json
from collections import defaultdict

print("="*80)
print("TOC DATABASE BUILDER")
print("="*80)


# ============================================================================
# PHASE 1: SCANNED PDF DETECTION
# ============================================================================

def is_scanned_pdf(pdf_path):
    """
    Quick check: is this a scanned image PDF?
    Returns: True if scanned, False if native PDF
    Takes: ~0.1 seconds (very fast)
    """
    try:
        doc = fitz.open(str(pdf_path))
        first_page = doc[0]
        text = first_page.get_text().strip()
        doc.close()

        # If first page has < 100 characters, it's likely scanned
        is_scanned = len(text) < 100
        return is_scanned
    except Exception as e:
        print(f"    [WARNING] Error detecting PDF type: {e}")
        return True  # Assume scanned if error, use Docling


# ============================================================================
# PHASE 2: SMART PDF PARSING
# ============================================================================

def parse_first_4_pages_smart(pdf_path):
    """
    OPTIMIZED: Extract first 4 pages with PyMuPDF, then process with Docling
    Returns: (text, method, is_scanned)
    """
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import PdfFormatOption
    import tempfile
    import os

    # Step 1: Quick scan detection
    is_scanned = is_scanned_pdf(pdf_path)

    # Step 2: Extract first 4 pages to temporary PDF
    try:
        doc = fitz.open(str(pdf_path))
        num_pages = min(4, len(doc))

        # Create temp PDF with first 4 pages only
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_path = temp_pdf.name
        temp_pdf.close()

        # Create new PDF with first 4 pages
        new_doc = fitz.open()
        for i in range(num_pages):
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
        new_doc.save(temp_path)
        new_doc.close()
        doc.close()

        print(f"    [EXTRACTED] First {num_pages} pages to temp PDF")
    except Exception as e:
        print(f"    [ERROR] Failed to extract pages: {e}")
        return "", 'error', is_scanned

    # Step 3: Process temp PDF with Docling
    if is_scanned:
        print(f"    [SCANNED] Using Docling with OCR")
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
    else:
        print(f"    [NATIVE] Using Docling without OCR")
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = True

    try:
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(temp_path)
        full_text = result.document.export_to_markdown()
        method = 'ocr' if is_scanned else 'fast_native'

        # Clean up temp file
        os.unlink(temp_path)

        return full_text, method, is_scanned
    except Exception as e:
        print(f"    [ERROR] Docling failed: {e}")
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass
        return "", 'error', is_scanned


# ============================================================================
# PHASE 3: FLEXIBLE TOC EXTRACTION
# ============================================================================

def find_toc_boundaries(lines):
    """Find start and end of TOC section"""
    toc_keywords = [
        'table of contents', 'contents', 'index',
        'table des matieres', 'inhoud', 'inhaltsverzeichnis'
    ]

    start = -1
    for i, line in enumerate(lines[:150]):
        line_lower = line.lower().strip()
        if any(kw in line_lower for kw in toc_keywords):
            start = i
            break

    # If no explicit heading, look for structure
    if start < 0:
        # Look for multiple lines with section numbers
        for i in range(min(150, len(lines))):
            # Check if next 5 lines have section numbers
            section_count = 0
            for j in range(i, min(i+5, len(lines))):
                if re.match(r'^\s*\d+\.?\d*\s+', lines[j]):
                    section_count += 1
            if section_count >= 3:
                start = i
                break

    if start < 0:
        return -1, -1

    # Find end
    end = min(start + 150, len(lines))
    for i in range(start + 1, min(start + 150, len(lines))):
        # Stop at first ## heading that's not TOC-related
        if lines[i].strip().startswith('##') and 'content' not in lines[i].lower():
            end = i
            break

    return start, end


def extract_markdown_table_toc(lines):
    """Pattern 1: Markdown tables | section | title | page |"""
    toc_entries = []

    for line in lines:
        if '|' not in line or '---' in line:
            continue

        parts = [p.strip() for p in line.split('|') if p.strip()]

        if len(parts) >= 2:
            # Try 4-column format: | 2.1 | Title | Title | 6 |
            if len(parts) == 4:
                section_num = parts[0].strip()
                title = parts[1].strip()
                page = parts[3].strip()

                if re.match(r'^\d+\.?\d*$', section_num) and page.isdigit():
                    if len(title) > 2:
                        toc_entries.append({
                            'number': section_num,
                            'title': title,
                            'page': int(page)
                        })

            # Try 3-column format: | 2.1 Title | dup | 6 |
            elif len(parts) == 3:
                first_col = parts[0].strip()
                second_col = parts[1].strip()
                third_col = parts[2].strip()

                # Pattern 1: Section number in first column, title in column 1
                match = re.match(r'^(\d+\.\d+\.?\d*)\s+(.+)$', first_col)
                if match and third_col.isdigit():
                    toc_entries.append({
                        'number': match.group(1),
                        'title': match.group(2).strip(),
                        'page': int(third_col)
                    })
                # Pattern 2: Malformed table - | 1.1 | 1.1 | Title...page |
                elif re.match(r'^\d+\.?\d*$', first_col):
                    # Extract page from third column which might be "Title...3" or just "3"
                    # Try: "Title...page" format
                    page_match = re.search(r'\.{2,}\s*(\d+)\s*$', third_col)
                    if page_match:
                        page = int(page_match.group(1))
                        title = re.sub(r'\s*\.{2,}\s*\d+\s*$', '', third_col).strip()
                        if len(title) > 2:
                            toc_entries.append({
                                'number': first_col,
                                'title': title,
                                'page': page
                            })
                    # Try: just page number
                    elif third_col.isdigit():
                        # Title might be in second column
                        if len(second_col) > 2 and not second_col.isdigit():
                            toc_entries.append({
                                'number': first_col,
                                'title': second_col,
                                'page': int(third_col)
                            })

            # Try 2-column format: | 2.1 | Title ........... 6 |
            elif len(parts) == 2:
                section_col = parts[0].strip()
                title_col = parts[1].strip()

                # Check if first column is a section number
                if re.match(r'^\d+\.?\d*$', section_col):
                    # Extract title and page from second column
                    # Format: "Title ............. 6"
                    page_match = re.search(r'\.{2,}\s*(\d+)\s*$', title_col)
                    if page_match:
                        page = int(page_match.group(1))
                        title = re.sub(r'\s*\.{2,}\s*\d+\s*$', '', title_col).strip()

                        if len(title) > 2:
                            toc_entries.append({
                                'number': section_col,
                                'title': title,
                                'page': page
                            })

    return toc_entries


def extract_dotted_toc(lines):
    """Pattern 2: Plain text with dots - 1.1 Title ........ 5"""
    toc_entries = []

    for line in lines:
        # Match: section_number + text + dots + page_number
        match = re.match(r'^(\d+\.?\d*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$', line.strip())
        if match:
            section_num, title, page = match.groups()
            if len(title.strip()) > 2:
                toc_entries.append({
                    'number': section_num,
                    'title': title.strip(),
                    'page': int(page)
                })

    return toc_entries


def extract_spaced_toc(lines):
    """Pattern 3: Spaced alignment - 1.1  Title     5"""
    toc_entries = []

    for line in lines:
        # Match: section_number + text + multiple spaces + page_number
        match = re.match(r'^(\d+\.?\d*)\s+(.+?)\s{3,}(\d+)\s*$', line.strip())
        if match:
            section_num, title, page = match.groups()
            if len(title.strip()) > 2:
                toc_entries.append({
                    'number': section_num,
                    'title': title.strip(),
                    'page': int(page)
                })

    return toc_entries


def extract_tab_separated_toc(lines):
    """Pattern 4: Tab-separated - 1.1\tTitle\t5"""
    toc_entries = []

    for line in lines:
        if '\t' not in line:
            continue

        parts = line.strip().split('\t')
        if len(parts) >= 3:
            section_num = parts[0].strip()
            title = parts[1].strip()
            page = parts[-1].strip()

            if re.match(r'^\d+\.?\d*$', section_num) and page.isdigit():
                if len(title) > 2:
                    toc_entries.append({
                        'number': section_num,
                        'title': title,
                        'page': int(page)
                    })

    return toc_entries


def extract_ocr_artifact_toc(lines):
    """Pattern 5: OCR artifacts - 1.1 Title  5 (just spaces, no dots)"""
    toc_entries = []

    for line in lines:
        # Match: section_number + text + 2+ spaces + single/double digit page
        match = re.match(r'^(\d+\.?\d*)\s+(.+?)\s{2,}(\d{1,3})\s*$', line.strip())
        if match:
            section_num, title, page = match.groups()
            # Filter out false positives (title too short or page too large)
            if len(title.strip()) > 3 and int(page) < 500:
                toc_entries.append({
                    'number': section_num,
                    'title': title.strip(),
                    'page': int(page)
                })

    return toc_entries


def extract_multiline_dotted_toc(lines):
    """Pattern 6: Multi-line format - Line 1: 1.1  Line 2: Title ........ 5"""
    toc_entries = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Check if this line is ONLY a section number
        if re.match(r'^\d+\.?\d*\s*$', line):
            section_num = line.strip()

            # Check next line for title with dots and page number
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                # Match title with dots leading to page number
                title_match = re.match(r'^(.+?)\s*\.{2,}\s*(\d+)\s*$', next_line)
                if title_match:
                    title, page = title_match.groups()

                    # Clean up title (remove trailing dots/spaces)
                    title = title.strip()

                    if len(title) > 2 and int(page) < 500:
                        toc_entries.append({
                            'number': section_num,
                            'title': title,
                            'page': int(page)
                        })
                        i += 2  # Skip both lines
                        continue

        i += 1

    return toc_entries


def extract_toc_flexible(text):
    """
    Try multiple patterns to extract TOC
    Returns: [{number, title, page}] or []
    """
    lines = text.split('\n')

    # Find TOC boundaries
    start, end = find_toc_boundaries(lines)

    if start < 0:
        return []

    toc_lines = lines[start:end]

    # Try each pattern in order
    patterns = [
        ('Markdown Table', extract_markdown_table_toc),
        ('Multi-line Dotted', extract_multiline_dotted_toc),
        ('Dotted Format', extract_dotted_toc),
        ('Spaced Format', extract_spaced_toc),
        ('Tab Separated', extract_tab_separated_toc),
        ('OCR Artifacts', extract_ocr_artifact_toc),
    ]

    for pattern_name, pattern_func in patterns:
        toc = pattern_func(toc_lines)
        if len(toc) >= 3:  # At least 3 entries to be valid
            print(f"    [TOC] Found {len(toc)} entries using {pattern_name}")
            return toc

    print(f"    [TOC] No valid TOC found (tried {len(patterns)} patterns)")
    return []


# ============================================================================
# PHASE 4: PUBLICATION DATE EXTRACTION
# ============================================================================

def extract_publication_date(text):
    """Extract publication date using context-aware search"""
    context_keywords = [
        'publication date', 'date', 'published', 'issue date',
        'report date', 'approved', 'version', 'revision date'
    ]

    lines = text.split('\n')
    found_dates = []

    for i, line in enumerate(lines):
        line_lower = line.lower()

        if any(keyword in line_lower for keyword in context_keywords):
            # Search this line + next 2 lines
            search_text = ' '.join(lines[i:i+3])

            # Pattern 1: Month/Year
            month_year_pattern = r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\s*[/\-]?\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)?\s*(\d{4})\b'
            matches = re.findall(month_year_pattern, search_text, re.IGNORECASE)
            for match in matches:
                try:
                    month = match[1] if match[1] else match[0]
                    year = match[2]
                    date_str = f"01 {month} {year}"
                    date_obj = datetime.datetime.strptime(date_str, '%d %B %Y')
                    if 2015 <= date_obj.year <= 2025:
                        found_dates.append(date_obj)
                except:
                    try:
                        date_str = f"01 {month} {year}"
                        date_obj = datetime.datetime.strptime(date_str, '%d %b %Y')
                        if 2015 <= date_obj.year <= 2025:
                            found_dates.append(date_obj)
                    except:
                        continue

            # Pattern 2: Full dates
            date_patterns = [
                r'\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})\b',
                r'\b(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b',
                r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b',
            ]

            for pattern in date_patterns:
                matches = re.findall(pattern, search_text, re.IGNORECASE)
                for match in matches:
                    for fmt in ['%d-%m-%Y', '%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d', '%d %B %Y', '%d %b %Y']:
                        try:
                            date_obj = datetime.datetime.strptime(match, fmt)
                            if 2015 <= date_obj.year <= 2025:
                                found_dates.append(date_obj)
                            break
                        except:
                            continue

    if found_dates:
        return max(found_dates)
    return None


# ============================================================================
# PHASE 5: EOWR SELECTION & DATABASE BUILDING
# ============================================================================

def scan_all_eowr_files(data_dir):
    """Scan all wells and find ALL PDF files in 'Well report' folders"""
    all_eowr = {}

    for well_num in range(1, 9):
        well_name = f"Well {well_num}"
        well_dir = data_dir / well_name / "Well report"

        if not well_dir.exists():
            continue

        # Get ALL PDFs in the Well report folder
        eowr_files = list(well_dir.rglob("*.pdf"))

        all_eowr[well_name] = eowr_files

    return all_eowr


def select_best_eowr(candidates):
    """
    Select the best EOWR from multiple candidates
    Scoring: TOC > Date > Size > Filename
    """
    if len(candidates) == 1:
        return candidates[0]

    scored = []
    for candidate in candidates:
        score = 0

        # Priority 1: Has valid TOC (critical)
        if candidate['toc'] and len(candidate['toc']) >= 3:
            score += 10000

        # Priority 2: Publication date (newer is better)
        if candidate['pub_date']:
            score += candidate['pub_date'].year * 10 + candidate['pub_date'].month

        # Priority 3: File size (larger is usually more complete)
        score += candidate['file_size'] / 1000000  # Convert to MB

        # Priority 4: Filename contains "final"
        if 'final' in candidate['filename'].lower():
            score += 100

        scored.append((score, candidate))

    return max(scored, key=lambda x: x[0])[1]


def identify_key_sections(toc):
    """Identify key sections from TOC for parameter extraction"""
    key_sections = {
        'casing': [],
        'borehole': [],
        'depth': [],
        'trajectory': [],
        'technical_summary': []
    }

    for entry in toc:
        title_lower = entry['title'].lower()

        if any(kw in title_lower for kw in ['casing', 'completion', 'tubular', 'well construction']):
            key_sections['casing'].append(entry)

        if any(kw in title_lower for kw in ['borehole', 'hole section', 'well data']):
            key_sections['borehole'].append(entry)

        if any(kw in title_lower for kw in ['depth', 'survey', 'directional']):
            key_sections['depth'].append(entry)

        if any(kw in title_lower for kw in ['trajectory', 'well path']):
            key_sections['trajectory'].append(entry)

        if any(kw in title_lower for kw in ['technical summary', 'well summary', 'summary']):
            key_sections['technical_summary'].append(entry)

    return key_sections


def build_toc_database(data_dir):
    """Main function - orchestrate all phases"""
    print("\n" + "#"*80)
    print("# PHASE 1: SCANNING FOR EOWR FILES")
    print("#"*80)

    all_eowr = scan_all_eowr_files(data_dir)

    total_files = sum(len(files) for files in all_eowr.values())
    print(f"\nFound {total_files} EOWR files across {len(all_eowr)} wells")

    print("\n" + "#"*80)
    print("# PHASE 2-4: PARSING AND ANALYSIS")
    print("#"*80)

    toc_database = {}

    for well_name, eowr_files in all_eowr.items():
        if not eowr_files:
            continue

        print(f"\n{'='*80}")
        print(f"{well_name}: {len(eowr_files)} EOWR file(s)")
        print(f"{'='*80}")

        candidates = []

        for eowr_file in eowr_files:
            print(f"\n  Analyzing: {eowr_file.name}")

            # Parse first 4 pages (smart routing)
            text, method, is_scanned = parse_first_4_pages_smart(eowr_file)

            if not text:
                print(f"    [SKIP] Failed to parse")
                continue

            # Extract TOC
            toc = extract_toc_flexible(text)

            # Extract publication date
            pub_date = extract_publication_date(text)
            if pub_date:
                print(f"    [DATE] {pub_date.strftime('%Y-%m-%d')}")
            else:
                print(f"    [DATE] Not found")

            # Get file size
            file_size = eowr_file.stat().st_size

            candidates.append({
                'file': eowr_file,
                'filename': eowr_file.name,
                'file_size': file_size,
                'is_scanned': is_scanned,
                'parse_method': method,
                'toc': toc,
                'pub_date': pub_date,
                'text_preview': text[:500]
            })

        # Select best EOWR
        if candidates:
            best = select_best_eowr(candidates)

            print(f"\n  [SELECTED] {best['filename']}")
            print(f"    - TOC entries: {len(best['toc'])}")
            print(f"    - Publication date: {best['pub_date'].strftime('%Y-%m-%d') if best['pub_date'] else 'N/A'}")
            print(f"    - File size: {best['file_size']/1024/1024:.1f} MB")
            print(f"    - Scanned: {'Yes' if best['is_scanned'] else 'No'}")

            # Identify key sections
            key_sections = identify_key_sections(best['toc']) if best['toc'] else {}

            # Count key sections found
            key_count = sum(len(v) for v in key_sections.values())
            if key_count > 0:
                print(f"    - Key sections found: {key_count}")

            toc_database[well_name] = {
                'eowr_file': str(best['file']),
                'filename': best['filename'],
                'file_size': best['file_size'],
                'pub_date': best['pub_date'].isoformat() if best['pub_date'] else None,
                'is_scanned': best['is_scanned'],
                'parse_method': best['parse_method'],
                'toc': best['toc'],
                'key_sections': key_sections
            }

    return toc_database


# ============================================================================
# PHASE 6: REPORTING
# ============================================================================

def generate_report(toc_database):
    """Generate markdown report"""
    report = []
    report.append("# TOC Database Report\n")
    report.append(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n")

    # Summary
    total_wells = len(toc_database)
    wells_with_toc = sum(1 for data in toc_database.values() if data['toc'])
    wells_scanned = sum(1 for data in toc_database.values() if data['is_scanned'])

    report.append("## Summary\n")
    report.append(f"- **Total wells analyzed:** {total_wells}\n")
    report.append(f"- **Wells with TOC:** {wells_with_toc}/{total_wells} ({100*wells_with_toc//total_wells if total_wells > 0 else 0}%)\n")
    report.append(f"- **Scanned PDFs:** {wells_scanned}/{total_wells}\n")
    report.append(f"- **Native PDFs:** {total_wells - wells_scanned}/{total_wells}\n")
    report.append("\n---\n")

    # Per-well details
    report.append("## Per-Well Details\n\n")

    for well_name in sorted(toc_database.keys()):
        data = toc_database[well_name]
        report.append(f"### {well_name}\n\n")
        report.append(f"- **File:** `{data['filename']}`\n")
        report.append(f"- **Publication Date:** {data['pub_date'] if data['pub_date'] else 'Not found'}\n")
        report.append(f"- **File Size:** {data['file_size']/1024/1024:.1f} MB\n")
        report.append(f"- **Type:** {'Scanned (OCR)' if data['is_scanned'] else 'Native PDF'}\n")
        report.append(f"- **TOC Entries:** {len(data['toc']) if data['toc'] else 0}\n")

        if data['toc']:
            report.append(f"\n**Table of Contents:**\n\n")
            for entry in data['toc'][:10]:
                report.append(f"- {entry['number']:6} {entry['title']:60} (page {entry['page']})\n")
            if len(data['toc']) > 10:
                report.append(f"- ... and {len(data['toc']) - 10} more entries\n")

            # Key sections
            key_sections = data.get('key_sections', {})
            key_count = sum(len(v) for v in key_sections.values())
            if key_count > 0:
                report.append(f"\n**Key Sections for Parameter Extraction:**\n\n")
                for category, sections in key_sections.items():
                    if sections:
                        report.append(f"- **{category.title()}:**\n")
                        for section in sections:
                            report.append(f"  - {section['number']} {section['title']} (page {section['page']})\n")
        else:
            report.append(f"\n**Status:** ❌ No TOC found\n")

        report.append("\n")

    return ''.join(report)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    data_dir = Path(__file__).parent.parent / "Training data-shared with participants"

    # Build database
    toc_db = build_toc_database(data_dir)

    # Save JSON
    output_json = Path(__file__).parent.parent / 'outputs' / 'exploration' / 'toc_database.json'
    output_json.parent.mkdir(parents=True, exist_ok=True)

    with open(output_json, 'w') as f:
        json.dump(toc_db, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"[OK] Database saved to: {output_json}")

    # Generate report
    report = generate_report(toc_db)
    output_report = Path(__file__).parent.parent / 'outputs' / 'exploration' / 'toc_database_report.md'

    with open(output_report, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"[OK] Report saved to: {output_report}")
    print("="*80)

    # Print summary
    total_wells = len(toc_db)
    wells_with_toc = sum(1 for data in toc_db.values() if data['toc'])

    print(f"\n[FINAL SUMMARY]")
    print(f"   Total wells: {total_wells}")
    print(f"   TOC extracted: {wells_with_toc}/{total_wells} ({100*wells_with_toc//total_wells if total_wells > 0 else 0}%)")
    print()
