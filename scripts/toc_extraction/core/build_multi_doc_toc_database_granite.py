"""
Build Multi-Document TOC Database with Smart Routing

Routes PDFs based on document type:
- SCANNED PDFs: Use Granite VLM (vision-based, ~25s per PDF)
- NATIVE PDFs: Use text-based extraction (Docling + PyMuPDF, ~7s per PDF)

Output: outputs/exploration/toc_database_multi_doc_granite.json
"""

import sys
from pathlib import Path
import fitz
import json
from collections import defaultdict
import threading
import time
import datetime
import re
import logging

# Add src/ and scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # Project root
sys.path.insert(0, str(Path(__file__).parent.parent / 'archive'))  # archive folder
sys.path.insert(0, str(Path(__file__).parent))  # core folder

# Import existing functions
from build_toc_database import extract_publication_date  # From archive
from analyze_all_tocs import parse_first_n_pages, find_toc_boundaries  # From core
from robust_toc_extractor import RobustTOCExtractor  # From core

# Import Granite modules
from src.toc_extraction.granite_toc_extractor import GraniteTOCExtractor

# Configure logging
log_dir = Path(__file__).parent.parent / "outputs" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"database_builder_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

logger.info("="*80)
logger.info("MULTI-DOCUMENT TOC DATABASE BUILDER - SMART ROUTING")
logger.info("="*80)
logger.info("Scanned PDFs  -> Granite VLM extraction")
logger.info("Native PDFs   -> Text-based extraction")
logger.info(f"Log file: {log_file}")
logger.info("="*80)

print("="*80)
print("MULTI-DOCUMENT TOC DATABASE BUILDER - SMART ROUTING")
print("="*80)
print("Scanned PDFs  -> Granite VLM extraction")
print("Native PDFs   -> Text-based extraction")
print(f"Log file: {log_file}")
print("="*80)

# Load 13-category mapping
categorization_path = Path("outputs/final_section_categorization_v2.json")
with open(categorization_path, 'r') as f:
    categorization = json.load(f)

print(f"[OK] Loaded 13-category mapping")

# Helper functions
def normalize_title(title):
    """Remove dots, extra whitespace, lowercase"""
    if not title:
        return ""
    cleaned = title.rstrip('. \t')
    cleaned = ' '.join(cleaned.split())
    return cleaned.lower()

def normalize_number(number):
    """Normalize section numbers: '1.' -> '1'"""
    return str(number).rstrip('.')

def categorize_by_title_pattern(title, number):
    """
    Intelligent fallback: Categorize based on title patterns
    Used when well is not in the lookup file (e.g., new wells)
    """
    title_lower = title.lower()

    # Project Admin
    if any(keyword in title_lower for keyword in [
        'project data', 'project details', 'organization', 'management',
        'signature', 'signing', 'executive summary', 'preface', 'introducing',
        'objectives', 'duties', 'responsibilities', 'contractor'
    ]):
        return 'project_admin'

    # Well Identification
    if any(keyword in title_lower for keyword in [
        'well data', 'basic well', 'general well', 'well name', 'well location'
    ]):
        return 'well_identification'

    # Technical Summary
    if any(keyword in title_lower for keyword in [
        'well summary', 'technical summary', 'summary of operations',
        'operations summary', 'operational summary', 'operations review'
    ]):
        return 'technical_summary'

    # Directional
    if any(keyword in title_lower for keyword in [
        'directional', 'trajectory', 'deviation', 'survey', 'well path',
        'horizontal projection', 'vertical projection', 'drilling rate'
    ]):
        return 'directional'

    # Borehole
    if any(keyword in title_lower for keyword in [
        'borehole', 'hole section', 'depths', 'depth reference',
        'measured depth', 'true vertical depth'
    ]):
        return 'borehole'

    # Casing
    if any(keyword in title_lower for keyword in [
        'casing', 'cementing', 'cement', 'tubing', 'liner'
    ]):
        return 'casing'

    # Drilling Operations
    if any(keyword in title_lower for keyword in [
        'drilling fluid', 'mud properties', 'drilling rig', 'bit run',
        'non productive time', 'npt'
    ]):
        return 'drilling_operations'

    # Geology
    if any(keyword in title_lower for keyword in [
        'geology', 'geological', 'stratigraphic', 'litholog',
        'cutting samples', 'hydrocarbon', 'fault'
    ]):
        return 'geology'

    # Completion
    if any(keyword in title_lower for keyword in [
        'completion', 'well status', 'well schematic', 'wellhead',
        'christmas tree', 'well barrier', 'suspension'
    ]):
        return 'completion'

    # HSE (including generic subsections like "6.1 General" under HSE parent)
    if any(keyword in title_lower for keyword in [
        'hse', 'safety', 'incident', 'drill', 'emergency', 'audit', 'inspection', 'performance'
    ]) or (title_lower == 'general' and number.count('.') > 0):  # Generic subsection
        return 'hse'

    # Well Testing
    if any(keyword in title_lower for keyword in [
        'well test', 'production test', 'fit test', 'pressure test'
    ]):
        return 'well_testing'

    # Intervention
    if any(keyword in title_lower for keyword in [
        'perforating', 'tcp', 'workover', 'intervention', 'toolstring'
    ]):
        return 'intervention'

    # Appendices
    if any(keyword in title_lower for keyword in [
        'appendix', 'appendices', 'attachment', 'dvd'
    ]):
        return 'appendices'

    # Default: None (will not be categorized)
    return None

# Build lookup from categorization
category_lookup = {}
for category_name, category_data in categorization['categories'].items():
    for entry in category_data['entries']:
        well = entry['well']
        number = normalize_number(entry['number'])
        title = normalize_title(entry['title'])
        key = (well, number, title)
        category_lookup[key] = category_name

print(f"[OK] Built category lookup: {len(category_lookup)} entries\n")


# Timeout handler (Windows-compatible)
class TimeoutError(Exception):
    pass

class GraniteExtractionThread(threading.Thread):
    """Thread wrapper for Granite extraction with timeout support"""
    def __init__(self, extractor, pdf_path, toc_page_num, pdf_total_pages):
        super().__init__()
        self.extractor = extractor
        self.pdf_path = pdf_path
        self.toc_page_num = toc_page_num
        self.pdf_total_pages = pdf_total_pages
        self.result = None
        self.exception = None

    def run(self):
        try:
            self.result = self.extractor.extract_full_workflow(
                self.pdf_path, self.toc_page_num, self.pdf_total_pages
            )
        except Exception as e:
            self.exception = e


def extract_date_with_granite(pdf_path):
    """
    Extract publication date using Granite VLM (for scanned documents)

    DISABLED: Granite VLM date extraction has import errors.
    Using text-based fallback instead.

    Args:
        pdf_path: Path to PDF

    Returns:
        datetime object or None
    """
    print(f"  [GRANITE-DATE] DISABLED - Using text-based fallback")
    return None

    # DISABLED CODE BELOW (import error: granite_vlm_picture_description)
    """
    try:
        # Extract first page as image
        doc = fitz.open(str(pdf_path))
        first_page = doc[0]

        # Render page to image
        pix = first_page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better quality
        img_bytes = pix.tobytes("png")

        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        doc.close()

        # Use Docling VLM pipeline to extract text from image
        from docling.document_converter import DocumentConverter
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False  # Not needed for single page

        # Use Granite VLM
        from docling.datamodel.pipeline_options import granite_vlm_picture_description
        pipeline_options.do_picture_description = True
        pipeline_options.picture_description_options = granite_vlm_picture_description
        pipeline_options.picture_description_options.prompt = (
            "Extract the publication date from this document cover page. "
            "Look for 'Date:', 'Publication Date:', 'Report Date:', 'Approved:', or similar labels. "
            "Return the date in format: DD Month YYYY (e.g., 27 November 2015)"
        )

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        # Convert first page
        result = converter.convert(pdf_path)

        # Extract text from VLM description
        vlm_text = ""
        for element in result.document.iterate_items():
            if hasattr(element, 'text'):
                vlm_text += element.text + "\n"

        # Clean up temp file
        import os
        os.unlink(tmp_path)

        # Parse date from VLM output
        if vlm_text:
            print(f"  [GRANITE-DATE] VLM output: {vlm_text[:100]}...")
            date_obj = extract_publication_date(vlm_text)
            if date_obj:
                print(f"  [GRANITE-DATE] Extracted: {date_obj.strftime('%Y-%m-%d')}")
                return date_obj

        print(f"  [GRANITE-DATE] No date found in VLM output")
        return None

    except Exception as e:
        print(f"  [GRANITE-DATE] ERROR: {e}")
        return None
    """


def detect_toc_page_number(pdf_path, parsed_text, toc_start_line, is_scanned=False, page_texts=None):
    """
    Detect which page contains TOC

    Args:
        pdf_path: Path to PDF
        parsed_text: Docling parsed text (not used)
        toc_start_line: Line number where TOC starts (not used)
        is_scanned: Whether PDF is scanned
        page_texts: Dict of {page_num: ocr_text} for scanned PDFs

    Returns:
        Page number (1-indexed) or -1 if not found
    """
    toc_keywords = ['table of contents', 'contents', 'content']

    # For scanned PDFs: Use OCR'd page texts (avoid PyMuPDF which returns empty)
    if is_scanned and page_texts:
        print(f"    [TOC-PAGE] Searching {len(page_texts)} OCR'd pages...")

        for page_num in sorted(page_texts.keys()):
            text = page_texts[page_num].lower()

            # Check for TOC keywords
            has_keyword = any(keyword in text for keyword in toc_keywords)

            if has_keyword:
                # Verify it looks like a TOC (has numbered entries)
                has_numbers = False
                for num in range(1, 6):  # Check for numbers 1-5
                    if f'\n{num}' in text or f'{num}.' in text or f' {num} ' in text:
                        has_numbers = True
                        break

                if has_numbers:
                    print(f"    [TOC-PAGE] Found on page {page_num} (OCR)")
                    return page_num

        # If not found, default to page 3 (common TOC location)
        print(f"    [TOC-PAGE] Not found in OCR, defaulting to page 3")
        return 3

    # For native PDFs: Use fast PyMuPDF text search
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        print(f"  [ERROR] Cannot open PDF for TOC page detection: {e}")
        return -1

    # Search first 10 pages
    for page_num in range(min(10, len(doc))):
        page = doc[page_num]
        text = page.get_text().lower()

        # Check for TOC keywords
        has_keyword = any(keyword in text for keyword in toc_keywords)

        if has_keyword:
            # Verify it looks like a TOC (has numbered entries)
            has_numbers = False
            for num in range(1, 5):  # Check for numbers 1-4
                if f'\n{num} ' in text or f'\n{num}.' in text or f' {num} ' in text:
                    has_numbers = True
                    break

            if has_numbers:
                doc.close()
                return page_num + 1  # Convert to 1-indexed

    doc.close()

    # Fallback: Use line-based estimation
    estimated_page = (toc_start_line // 50) + 1
    estimated_page = max(1, min(estimated_page, 10))
    return estimated_page


def extract_toc_with_granite(pdf_path, well_name, pdf_name):
    """
    Extract TOC using Granite VLM (for scanned documents)

    Returns:
        (toc_entries, confidence, parse_method, is_scanned) tuple
    """
    print(f"  [GRANITE] Starting VLM extraction...")

    # Get PDF info
    try:
        doc = fitz.open(str(pdf_path))
        pdf_total_pages = len(doc)
        doc.close()
    except Exception as e:
        print(f"  [ERROR] Cannot open PDF: {e}")
        return [], 0.0, None, False

    # Parse first 5 pages to detect TOC page
    docling_text, raw_text, is_scanned, error, page_texts = parse_first_n_pages(pdf_path, num_pages=5)

    if error:
        print(f"  [ERROR] {error}")
        return [], 0.0, None, is_scanned

    # Find TOC boundaries
    lines = docling_text.split('\n')
    toc_start, toc_end = find_toc_boundaries(lines)

    # If Docling failed, try PyMuPDF
    if toc_start < 0:
        lines = raw_text.split('\n')
        toc_start, toc_end = find_toc_boundaries(lines)

    if toc_start < 0:
        print(f"  [GRANITE] No TOC boundaries found")
        return [], 0.0, None, is_scanned

    # Detect TOC page number (use OCR page texts for scanned PDFs)
    toc_page_num = detect_toc_page_number(pdf_path, docling_text, toc_start, is_scanned, page_texts)
    print(f"  [GRANITE] TOC detected on page {toc_page_num}")

    # Initialize Granite extractor
    granite_extractor = GraniteTOCExtractor()

    # Run Granite extraction with 60s timeout (Windows-compatible)
    thread = GraniteExtractionThread(granite_extractor, pdf_path, toc_page_num, pdf_total_pages)
    thread.start()
    thread.join(timeout=60)  # Wait up to 60 seconds

    if thread.is_alive():
        # Timeout occurred
        print(f"  [GRANITE] TIMEOUT after 60s")
        return [], 0.0, None, is_scanned

    if thread.exception:
        # Exception occurred during extraction
        print(f"  [GRANITE] ERROR: {thread.exception}")
        return [], 0.0, None, is_scanned

    if thread.result:
        # Successful extraction
        toc_entries, confidence, method = thread.result

        if method == "Granite":
            print(f"  [GRANITE] Confidence: {confidence:.2f}")
            return toc_entries, confidence, "Granite", is_scanned
        else:
            print(f"  [GRANITE] Extraction failed")
            return [], 0.0, None, is_scanned
    else:
        # No result
        print(f"  [GRANITE] No result returned")
        return [], 0.0, None, is_scanned


def extract_toc_text_fallback(pdf_path, well_name, pdf_name):
    """
    Extract TOC using text-based methods (for native PDFs or Granite fallback)

    Returns:
        (toc_entries, parse_method, is_scanned) tuple
    """
    print(f"  [TEXT] Starting text-based extraction...")

    # Parse first 5 pages
    docling_text, raw_text, is_scanned, error, page_texts = parse_first_n_pages(pdf_path, num_pages=5)

    if error:
        print(f"  [ERROR] {error}")
        return [], None, is_scanned

    # Try Docling text first
    text = docling_text
    source = "Docling"
    lines = text.split('\n')
    toc_start, toc_end = find_toc_boundaries(lines)

    # PyMuPDF fallback
    if toc_start < 0:
        print(f"  [DOCLING] No TOC found, trying PyMuPDF...")
        text = raw_text
        source = "PyMuPDF"
        lines = text.split('\n')
        toc_start, toc_end = find_toc_boundaries(lines)

    if toc_start < 0:
        print(f"  [SKIP] No TOC found in Docling or PyMuPDF")
        return [], None, is_scanned

    print(f"  [TOC] Found using {source}: lines {toc_start} to {toc_end}")

    # Extract TOC
    toc_section = lines[toc_start:toc_end]
    extractor = RobustTOCExtractor()
    toc_entries, pattern = extractor.extract(toc_section)

    if len(toc_entries) < 3:
        print(f"  [SKIP] Insufficient TOC entries ({len(toc_entries)})")
        return [], None, is_scanned

    print(f"  [OK] Extracted {len(toc_entries)} entries using {pattern}")

    return toc_entries, source, is_scanned


# Auto-discover all well folders
data_dir = Path("Training data-shared with participants")

if not data_dir.exists():
    print(f"[ERROR] Data directory not found: {data_dir}")
    sys.exit(1)

# Find all directories that contain a "Well report" or "Well Report" subfolder
ALL_WELLS = []
for item in data_dir.iterdir():
    if item.is_dir():
        # Check for "Well report" (case-insensitive)
        well_report_dir = None
        for subdir in item.iterdir():
            if subdir.is_dir() and subdir.name.lower() == "well report":
                well_report_dir = subdir
                break

        if well_report_dir:
            ALL_WELLS.append(item.name)

ALL_WELLS = sorted(ALL_WELLS)  # Sort for consistent ordering

print(f"[AUTO-DISCOVERY] Found {len(ALL_WELLS)} wells with 'Well report' folders:")
for well in ALL_WELLS:
    print(f"  - {well}")
print()

multi_doc_database = {}
total_pdfs_processed = 0
total_pdfs_skipped = 0

# Statistics
stats = {
    'total_pdfs': 0,
    'scanned_pdfs': 0,
    'native_pdfs': 0,
    'granite_success': 0,
    'text_fallback': 0,
    'failed': 0,
    'total_exact_pages': 0,
    'total_range_pages': 0,
    'total_unknown_pages': 0,
    'pdfs_by_method': {
        'Granite': [],
        'Docling': [],
        'PyMuPDF': []
    }
}

for well_name in ALL_WELLS:
    print(f"\n{'='*80}")
    print(f"PROCESSING {well_name}")
    print(f"{'='*80}")

    well_dir = data_dir / well_name / "Well report"

    if not well_dir.exists():
        print(f"[SKIP] {well_name} - directory not found")
        continue

    # Find all PDFs
    pdf_files = list(well_dir.rglob("*.pdf"))
    print(f"[FOUND] {len(pdf_files)} PDF files")

    well_documents = []

    for pdf_path in pdf_files:
        pdf_name = pdf_path.name
        print(f"\n{'='*80}")
        print(f"[PDF] {pdf_name}")
        print(f"{'='*80}")

        # STEP 1: Check if PDF is scanned or native
        print(f"  [CHECK] Detecting document type...")
        docling_text, raw_text, is_scanned, error, page_texts = parse_first_n_pages(pdf_path, num_pages=5)

        if error:
            print(f"  [ERROR] {error}")
            total_pdfs_skipped += 1
            stats['failed'] += 1
            continue

        if is_scanned:
            print(f"  [SCANNED] Document is scanned - using Granite VLM")
            stats['scanned_pdfs'] += 1
        else:
            print(f"  [NATIVE] Document is native PDF - using text extraction")
            stats['native_pdfs'] += 1

        # STEP 2: Route based on document type
        toc_entries = []
        parse_method = None
        confidence = 0.0

        if is_scanned:
            # Route to Granite VLM for scanned documents
            toc_entries, confidence, parse_method, _ = extract_toc_with_granite(
                pdf_path, well_name, pdf_name
            )

            # Check if Granite succeeded (lower threshold for scanned PDFs: 0.6 vs 0.7)
            # Scanned PDFs have more subsections with range notation, so confidence naturally lower
            if parse_method == "Granite" and confidence >= 0.6 and len(toc_entries) >= 3:
                print(f"  [RESULT] Using Granite (confidence: {confidence:.2f})")
                stats['granite_success'] += 1
                stats['pdfs_by_method']['Granite'].append(pdf_name)

                # Show entries
                for entry in toc_entries:
                    page_str = str(entry['page'])
                    if entry['page'] == 0:
                        status = "UNKNOWN"
                        stats['total_unknown_pages'] += 1
                    elif '-' in page_str:
                        status = "RANGE"
                        stats['total_range_pages'] += 1
                    else:
                        status = "EXACT"
                        stats['total_exact_pages'] += 1

                    print(f"    {entry['number']:6s} {entry['title']:50s} {page_str:>6s} [{status}]")
            else:
                # Granite failed, fall back to text-based
                print(f"  [FALLBACK] Granite failed (confidence: {confidence:.2f}), using text-based")
                toc_entries, parse_method, _ = extract_toc_text_fallback(
                    pdf_path, well_name, pdf_name
                )
        else:
            # Route directly to text-based extraction for native PDFs
            toc_entries, parse_method, _ = extract_toc_text_fallback(
                pdf_path, well_name, pdf_name
            )

        # Check if extraction succeeded
        if not toc_entries or len(toc_entries) < 3:
            print(f"  [SKIP] Failed to extract TOC")
            total_pdfs_skipped += 1
            stats['failed'] += 1
            continue

        # If using text-based method, update stats
        if parse_method != "Granite":
            print(f"  [RESULT] Using {parse_method}")
            stats['text_fallback'] += 1
            stats['pdfs_by_method'][parse_method].append(pdf_name)

            # Count pages for text-based entries
            for entry in toc_entries:
                if entry['page'] == 0:
                    stats['total_unknown_pages'] += 1
                else:
                    stats['total_exact_pages'] += 1

        # Extract publication date
        pub_date = None

        if is_scanned:
            # For scanned PDFs: Try Granite VLM first (better for images)
            pub_date = extract_date_with_granite(pdf_path)

            # Fallback to text-based if Granite fails
            if not pub_date:
                print(f"  [DATE] Granite failed, trying text-based extraction...")
                docling_text, raw_text, _, _, _ = parse_first_n_pages(pdf_path, num_pages=5)
                pub_date = extract_publication_date(docling_text) if docling_text else None
                if not pub_date and raw_text:
                    pub_date = extract_publication_date(raw_text)
        else:
            # For native PDFs: Use text-based extraction (faster)
            docling_text, raw_text, _, _, _ = parse_first_n_pages(pdf_path, num_pages=5)
            pub_date = extract_publication_date(docling_text) if docling_text else None
            if not pub_date and raw_text:
                pub_date = extract_publication_date(raw_text)

        if pub_date:
            print(f"  [DATE] {pub_date.strftime('%Y-%m-%d')}")
        else:
            print(f"  [DATE] Not found")

        # Apply category mapping
        categorized_count = 0
        fallback_count = 0
        for entry in toc_entries:
            number = normalize_number(entry.get('number', ''))
            title = normalize_title(entry.get('title', ''))
            original_title = entry.get('title', '')

            # Strategy 1: Exact match in lookup
            key = (well_name, number, title)
            if key in category_lookup:
                entry['type'] = category_lookup[key]
                categorized_count += 1
                continue

            # Strategy 2: Fuzzy match in lookup (same well, same number)
            matched = False
            for (w, n, t), cat in category_lookup.items():
                if w == well_name and n == number:
                    if title in t or t in title:
                        entry['type'] = cat
                        categorized_count += 1
                        matched = True
                        break

            if matched:
                continue

            # Strategy 3: Pattern-based fallback (for new wells or missing entries)
            category = categorize_by_title_pattern(original_title, number)
            if category:
                entry['type'] = category
                categorized_count += 1
                fallback_count += 1

        if fallback_count > 0:
            print(f"  [CATEGORY] Applied types to {categorized_count}/{len(toc_entries)} entries ({fallback_count} via pattern fallback)")
        else:
            print(f"  [CATEGORY] Applied types to {categorized_count}/{len(toc_entries)} entries")

        # Build key_sections
        key_sections = defaultdict(list)
        for entry in toc_entries:
            if 'type' in entry:
                key_sections[entry['type']].append({
                    'number': entry.get('number', ''),
                    'title': entry.get('title', ''),
                    'page': entry.get('page', 0),
                    'type': entry['type']
                })

        # Get file size
        file_size = pdf_path.stat().st_size

        # Store document info
        doc_info = {
            'filename': pdf_name,
            'filepath': str(pdf_path),
            'file_size': file_size,
            'pub_date': pub_date.isoformat() if pub_date else None,
            'is_scanned': is_scanned,
            'parse_method': parse_method,
            'toc': toc_entries,
            'key_sections': dict(key_sections)
        }

        well_documents.append(doc_info)
        total_pdfs_processed += 1
        stats['total_pdfs'] += 1

        print(f"  [OK] Document processed")

    if well_documents:
        multi_doc_database[well_name] = well_documents
        print(f"\n[OK] {well_name}: {len(well_documents)} documents indexed")

# Save database
output_path = Path("outputs/exploration/toc_database_multi_doc_granite.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w') as f:
    json.dump(multi_doc_database, f, indent=2)

print(f"\n{'='*80}")
print("DATABASE BUILD COMPLETE")
print(f"{'='*80}")
print(f"Saved to: {output_path}")

# Print final statistics
print(f"\n{'='*80}")
print("FINAL STATISTICS")
print(f"{'='*80}")
print(f"\nTotal PDFs processed: {stats['total_pdfs']}")
print(f"Total PDFs skipped: {total_pdfs_skipped}")

print(f"\nDocument Types:")
print(f"  Scanned PDFs:   {stats['scanned_pdfs']}")
print(f"  Native PDFs:    {stats['native_pdfs']}")

print(f"\nExtraction Methods:")
print(f"  Granite VLM:    {stats['granite_success']}")
print(f"  Text fallback:  {stats['text_fallback']}")
print(f"  Failed:         {stats['failed']}")

print(f"\nPage Quality:")
print(f"  Exact pages:    {stats['total_exact_pages']}")
print(f"  Range pages:    {stats['total_range_pages']}")
print(f"  Unknown pages:  {stats['total_unknown_pages']}")

total_entries = stats['total_exact_pages'] + stats['total_range_pages'] + stats['total_unknown_pages']
if total_entries > 0:
    known_pages = stats['total_exact_pages'] + stats['total_range_pages']
    accuracy = (known_pages / total_entries) * 100
    print(f"\nAccuracy: {accuracy:.1f}% ({known_pages}/{total_entries} known pages)")

# Per-well summary
print(f"\n{'='*80}")
print("PER-WELL SUMMARY")
print(f"{'='*80}")

for well_name in sorted(multi_doc_database.keys()):
    docs = multi_doc_database[well_name]
    print(f"\n{well_name}: {len(docs)} documents")
    for doc in docs:
        toc_count = len(doc['toc'])
        method = doc['parse_method']
        print(f"  - {doc['filename']}")
        print(f"    Method: {method}, TOC: {toc_count} entries, Date: {doc['pub_date']}")

print(f"\n{'='*80}")
