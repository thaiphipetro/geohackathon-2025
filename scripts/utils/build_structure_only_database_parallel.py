"""
Build Structure-Only TOC Database with Parallel Processing

Optimizations:
- Parse 5 pages instead of 10 (faster)
- Parallel processing with 6 workers (8 cores)
- Granite VLM only for scanned PDFs
- Structure only (no page numbers)

Input: 16 PDFs across 8 wells
Output: outputs/exploration/toc_database_structure_only.json
"""

import sys
from pathlib import Path
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import existing functions
from analyze_all_tocs import parse_first_n_pages, find_toc_boundaries
from robust_toc_extractor import RobustTOCExtractor
from build_toc_database import extract_publication_date  # Proven function, works for Well 7
from src.granite_toc_extractor import GraniteTOCExtractor


def detect_toc_page_simple(docling_text, toc_start):
    """
    Simple TOC page detection without side effects
    Estimate page number from line position
    """
    # Assumption: ~50 lines per page
    estimated_page = (toc_start // 50) + 1
    return max(1, min(estimated_page, 10))


def process_single_pdf(pdf_path_str, well_name):
    """
    Process a single PDF in parallel

    Args:
        pdf_path_str: String path to PDF (for multiprocessing serialization)
        well_name: Well name (e.g., "Well 1")

    Returns:
        (doc_info, status_msg) or (None, error_msg)
    """
    pdf_path = Path(pdf_path_str)
    pdf_name = pdf_path.name

    try:
        # Step 1: Parse first 5 pages (optimized from 10)
        docling_text, raw_text, is_scanned, error = parse_first_n_pages(pdf_path, num_pages=5)

        if error:
            return None, f"Parse error: {error}"

        # Step 2: Find TOC boundaries
        lines = docling_text.split('\n')
        toc_start, toc_end = find_toc_boundaries(lines)

        # Try PyMuPDF fallback if Docling fails
        if toc_start < 0:
            lines = raw_text.split('\n')
            toc_start, toc_end = find_toc_boundaries(lines)

        # AUTOMATIC FILTER: No TOC = supplementary report
        if toc_start < 0:
            return None, "No TOC found (supplementary report)"

        # Step 3: Route based on scan status
        if is_scanned:
            # SCANNED PDF: Use Granite VLM
            print(f"  [SCANNED] Using Granite VLM for scanned PDF")
            try:
                # Detect TOC page number (simple estimation)
                toc_page_num = detect_toc_page_simple(docling_text, toc_start)
                print(f"  [GRANITE] Attempting TOC extraction from page {toc_page_num}...")

                # Initialize Granite extractor
                granite_extractor = GraniteTOCExtractor()

                # Extract TOC page as image
                toc_page_pdf = granite_extractor.extract_toc_page_as_image(pdf_path, toc_page_num)

                # Run Granite VLM
                markdown, success = granite_extractor.extract_from_page(toc_page_pdf)

                # Cleanup temp file
                try:
                    toc_page_pdf.unlink()
                except Exception:
                    pass

                if success and markdown:
                    lines = markdown.split('\n')
                    parse_method = "Granite"
                    print(f"  [GRANITE] Success - extracted text from VLM")
                else:
                    # Granite failed, use text fallback
                    lines = docling_text.split('\n')[toc_start:toc_end]
                    parse_method = "Docling (Granite failed)"
                    print(f"  [FALLBACK] Granite failed, using Docling OCR")

            except Exception as e:
                # Granite error, use text fallback
                lines = docling_text.split('\n')[toc_start:toc_end]
                parse_method = f"Docling (Granite error: {str(e)[:50]})"
                print(f"  [FALLBACK] Granite error, using Docling OCR: {str(e)[:50]}")
        else:
            # NATIVE PDF: Use text extraction directly (NO GRANITE)
            lines = lines[toc_start:toc_end]
            parse_method = "Docling"
            print(f"  [NATIVE] Using Docling text extraction")

        # Step 4: Extract structure with RobustTOCExtractor
        extractor = RobustTOCExtractor()
        toc_entries, pattern = extractor.extract(lines, debug=False)

        if len(toc_entries) < 3:
            return None, f"Insufficient entries ({len(toc_entries)})"

        # Step 5: Structure only (strip page numbers)
        structure_only = []
        for entry in toc_entries:
            structure_only.append({
                'number': entry['number'],
                'title': entry['title']
                # NO PAGE NUMBER
            })

        # Step 6: Extract publication date from parsed text
        publication_date = extract_publication_date(docling_text) if docling_text else None

        # If not found in Docling, try PyMuPDF fallback
        if not publication_date and raw_text:
            publication_date = extract_publication_date(raw_text)

        # Step 7: Build document info
        doc_info = {
            'filename': pdf_name,
            'filepath': str(pdf_path),
            'well_name': well_name,
            'publication_date': publication_date.isoformat() if publication_date else None,
            'is_scanned': is_scanned,
            'parse_method': parse_method,
            'pattern': pattern,
            'toc': structure_only
        }

        status_msg = f"{parse_method} | {pattern} | {len(structure_only)} entries"
        return doc_info, status_msg

    except Exception as e:
        return None, f"Exception: {str(e)}"


def build_database_parallel():
    """
    Build structure-only TOC database with parallel processing
    """

    print("="*80)
    print("STRUCTURE-ONLY TOC DATABASE BUILDER (PARALLEL)")
    print("="*80)
    print()

    ALL_WELLS = ['Well 1', 'Well 2', 'Well 3', 'Well 4',
                 'Well 5', 'Well 6', 'Well 7', 'Well 8']

    data_dir = Path("Training data-shared with participants")

    # Collect all PDF paths
    all_pdf_tasks = []
    for well_name in ALL_WELLS:
        well_dir = data_dir / well_name / "Well report"

        if not well_dir.exists():
            print(f"[SKIP] {well_name} - directory not found")
            continue

        # Only scan top-level Well report/*.pdf (not recursive)
        pdf_files = list(well_dir.glob("*.pdf"))
        print(f"[FOUND] {well_name}: {len(pdf_files)} PDFs")

        for pdf_path in pdf_files:
            all_pdf_tasks.append((str(pdf_path), well_name))

    print(f"\nTotal PDFs found: {len(all_pdf_tasks)}")
    print(f"CPU cores available: {multiprocessing.cpu_count()}")

    # Use 6 workers (leave 2 cores for system)
    max_workers = min(6, multiprocessing.cpu_count() - 2)
    print(f"Using {max_workers} parallel workers")
    print(f"{'='*80}\n")

    # Process in parallel
    results = []
    errors = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_pdf = {
            executor.submit(process_single_pdf, pdf_path_str, well_name): (pdf_path_str, well_name)
            for pdf_path_str, well_name in all_pdf_tasks
        }

        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_pdf):
            pdf_path_str, well_name = future_to_pdf[future]
            pdf_name = Path(pdf_path_str).name
            completed += 1

            try:
                doc_info, status = future.result()

                if doc_info:
                    results.append(doc_info)
                    print(f"[{completed}/{len(all_pdf_tasks)}] OK   {well_name}/{pdf_name}")
                    print(f"             {status}")
                else:
                    errors.append((well_name, pdf_name, status))
                    print(f"[{completed}/{len(all_pdf_tasks)}] SKIP {well_name}/{pdf_name}")
                    print(f"             {status}")

            except Exception as e:
                errors.append((well_name, pdf_name, str(e)))
                print(f"[{completed}/{len(all_pdf_tasks)}] ERR  {well_name}/{pdf_name}")
                print(f"             {str(e)}")

    # Group by well
    database = {}
    for doc_info in results:
        well_name = doc_info.pop('well_name')
        if well_name not in database:
            database[well_name] = []
        database[well_name].append(doc_info)

    # Save database
    output_path = Path("outputs/exploration/toc_database_structure_only.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2)

    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total PDFs found:        {len(all_pdf_tasks)}")
    print(f"EOWRs processed:         {len(results)}")
    print(f"Supplementary skipped:   {len([e for e in errors if 'supplementary' in e[2].lower()])}")
    print(f"Errors:                  {len([e for e in errors if 'supplementary' not in e[2].lower()])}")

    # Breakdown by method
    methods = {}
    for doc_info in results:
        method = doc_info['parse_method']
        methods[method] = methods.get(method, 0) + 1

    print(f"\nParsing methods:")
    for method, count in sorted(methods.items()):
        print(f"  {method:30s}: {count} PDFs")

    # Per-well summary
    print(f"\nPer-well summary:")
    for well_name in sorted(database.keys()):
        docs = database[well_name]
        total_entries = sum(len(doc['toc']) for doc in docs)
        print(f"  {well_name:10s}: {len(docs)} documents, {total_entries} TOC entries")

    print(f"\nSaved to: {output_path}")
    print(f"{'='*80}")


if __name__ == "__main__":
    build_database_parallel()
