"""Test date extraction on Well 5 EOWR files"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import datetime
import re
from docling.document_converter import DocumentConverter

def extract_publication_date(pdf_path):
    """Extract publication date from first 2 pages using context-aware search"""
    try:
        temp_converter = DocumentConverter()
        result = temp_converter.convert(str(pdf_path))

        # Get text and limit to first ~3000 characters (roughly first 2 pages)
        full_text = result.document.export_to_markdown()
        text = full_text[:3000]

        print(f"\n{'='*80}")
        print(f"Testing: {pdf_path.name}")
        print(f"{'='*80}")

        # Define context keywords that indicate a date nearby
        context_keywords = [
            'publication date', 'date', 'published', 'issue date',
            'report date', 'approved', 'version', 'revision date'
        ]

        # Split text into lines for context search
        lines = text.split('\n')
        found_dates = []

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Check if line contains context keywords
            has_context = any(keyword in line_lower for keyword in context_keywords)

            if has_context:
                # Look at this line and next 2 lines (dates might be on next line)
                search_text = ' '.join(lines[i:i+3])

                print(f"\n[FOUND CONTEXT] Line {i}: {line[:100]}...")
                print(f"  Search area: {search_text[:150]}...")

                # Pattern 1: Month/Year formats like "July / August 2020" or "July 2020"
                month_year_pattern = r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\s*[/\-]?\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)?\s*(\d{4})\b'
                matches = re.findall(month_year_pattern, search_text, re.IGNORECASE)
                for match in matches:
                    print(f"  [MATCHED MONTH/YEAR] {match}")
                    try:
                        # Use the last month mentioned (e.g., "August" in "July / August 2020")
                        month = match[1] if match[1] else match[0]
                        year = match[2]
                        date_str = f"01 {month} {year}"
                        date_obj = datetime.datetime.strptime(date_str, '%d %B %Y')
                        if 2015 <= date_obj.year <= 2025:
                            found_dates.append(date_obj)
                            print(f"  [PARSED] → {date_obj.strftime('%Y-%m-%d')}")
                    except:
                        try:
                            date_str = f"01 {month} {year}"
                            date_obj = datetime.datetime.strptime(date_str, '%d %b %Y')
                            if 2015 <= date_obj.year <= 2025:
                                found_dates.append(date_obj)
                                print(f"  [PARSED] → {date_obj.strftime('%Y-%m-%d')}")
                        except:
                            continue

                # Pattern 2: Full dates like "DD-MM-YYYY" or "19 October 2020"
                date_patterns = [
                    r'\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})\b',
                    r'\b(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b',
                    r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b',
                ]

                for pattern in date_patterns:
                    matches = re.findall(pattern, search_text, re.IGNORECASE)
                    for match in matches:
                        print(f"  [MATCHED FULL DATE] {match}")
                        try:
                            for fmt in ['%d-%m-%Y', '%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d', '%d %B %Y', '%d %b %Y']:
                                try:
                                    date_obj = datetime.datetime.strptime(match, fmt)
                                    if 2015 <= date_obj.year <= 2025:
                                        found_dates.append(date_obj)
                                        print(f"  [PARSED] → {date_obj.strftime('%Y-%m-%d')}")
                                    break
                                except:
                                    continue
                        except:
                            continue

        if found_dates:
            result_date = max(found_dates)
            print(f"\n[FINAL RESULT] Most recent date: {result_date.strftime('%Y-%m-%d')}")
            return result_date
        else:
            print(f"\n[NO DATE FOUND]")
            return None

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

# Test on Well 5 EOWR files
data_dir = Path(__file__).parent.parent / "Training data-shared with participants" / "Well 5"
well_reports_dir = data_dir / "Well report"

if well_reports_dir.exists():
    eowr_files = []
    for f in well_reports_dir.rglob("*.pdf"):
        if any(keyword in f.name.lower() for keyword in ['eowr', 'final-well-report', 'final well report']):
            eowr_files.append(f)

    print(f"Found {len(eowr_files)} EOWR files in Well 5:")
    for f in eowr_files:
        print(f"  - {f.name}")

    # Test date extraction on each
    for pdf_file in eowr_files:
        extract_publication_date(pdf_file)
else:
    print(f"Well reports directory not found: {well_reports_dir}")
