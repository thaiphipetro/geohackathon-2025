"""
Step 1: Data Collection & Format Analysis
Extract TOC sections from ALL 16 PDFs in Wells 1,2,3,4,5,6,8
"""

import sys
from pathlib import Path
import fitz
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
import re
import tempfile
import os
import json

project_root = Path(__file__).parent.parent
data_dir = project_root / "Training data-shared with participants"
output_dir = project_root / "outputs" / "toc_analysis"
output_dir.mkdir(parents=True, exist_ok=True)


def is_scanned_pdf(pdf_path):
    """Quick check if PDF is scanned"""
    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            return True
        first_page = doc[0]
        text = first_page.get_text()
        doc.close()
        return len(text.strip()) < 100
    except:
        return True


def parse_first_n_pages(pdf_path, num_pages=10):
    """
    Extract first N pages and parse with Docling + PyMuPDF fallback

    Returns:
        (docling_text, raw_text, is_scanned, error, page_texts)
        page_texts: dict {page_num: text} for each page (1-indexed)
    """
    is_scanned = is_scanned_pdf(pdf_path)

    # Extract raw text with PyMuPDF as fallback
    raw_text = ""
    try:
        doc = fitz.open(str(pdf_path))
        pages_to_extract = min(num_pages, len(doc))

        # Extract raw text from first N pages
        for i in range(pages_to_extract):
            raw_text += doc[i].get_text()

        # Create temp PDF for Docling
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_path = temp_pdf.name
        temp_pdf.close()

        # Copy pages
        new_doc = fitz.open()
        for i in range(pages_to_extract):
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
        new_doc.save(temp_path)
        new_doc.close()
        doc.close()

    except Exception as e:
        return "", raw_text, is_scanned, f"Failed to extract pages: {e}", {}

    # Parse with Docling
    try:
        if is_scanned:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options.force_full_page_ocr = True  # Critical for fully scanned PDFs
            pipeline_options.do_table_structure = True
        else:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False
            pipeline_options.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(temp_path)
        docling_text = result.document.export_to_markdown()

        # Extract page-by-page text for scanned PDFs
        page_texts = {}
        if is_scanned:
            # For scanned PDFs, extract each page's text from the document
            try:
                for page in result.document.pages.values():
                    page_num = page.page_no + 1  # Convert to 1-indexed
                    page_text = page.export_to_markdown()
                    page_texts[page_num] = page_text
            except (AttributeError, TypeError) as e:
                print(f"    [WARN] Could not extract page-by-page text: {e}")
                # Fallback: no page-by-page text available
                pass

        os.unlink(temp_path)
        return docling_text, raw_text, is_scanned, None, page_texts
    except Exception as e:
        try:
            os.unlink(temp_path)
        except:
            pass
        return "", raw_text, is_scanned, f"Docling failed: {e}", {}


def find_toc_boundaries(lines):
    """Find start and end of TOC section"""
    toc_keywords = [
        'table of contents', 'contents', 'content',  # Added singular "content"
        'index', 'table des matieres', 'inhoud', 'inhaltsverzeichnis'
    ]

    start = -1

    # Method 1: Look for explicit TOC heading
    for i, line in enumerate(lines[:200]):
        line_lower = line.lower().strip()
        # Check if line contains TOC keyword (with word boundaries)
        for kw in toc_keywords:
            if kw in line_lower:
                # Make sure it's not just part of another word
                if kw == 'content' or kw == 'contents':
                    # Accept "content", "contents", "## content", etc.
                    if re.search(r'\b' + kw, line_lower):
                        start = i
                        break
                else:
                    start = i
                    break
        if start >= 0:
            break

    # Method 2: Look for structure (multiple numbered lines)
    if start < 0:
        for i in range(min(200, len(lines))):
            section_count = 0
            for j in range(i, min(i+5, len(lines))):
                # Match lines starting with numbers like "1.1" or "1"
                if re.match(r'^\s*\d+\.?\d*\s+', lines[j]):
                    section_count += 1
            if section_count >= 3:
                start = i
                break

    if start < 0:
        return -1, -1

    # Find end
    end = min(start + 200, len(lines))
    for i in range(start + 1, min(start + 200, len(lines))):
        # End at next major heading that's not content-related
        if lines[i].strip().startswith('##'):
            line_lower = lines[i].lower()
            if not any(kw in line_lower for kw in ['content', 'contents', 'index']):
                end = i
                break

    return start, end


def analyze_toc_format(lines):
    """Analyze the format characteristics of a TOC section"""
    features = {
        'has_tables': False,
        'has_dots': False,
        'has_multiline': False,
        'table_column_counts': set(),
        'sample_lines': []
    }

    # Check for tables
    table_lines = [l for l in lines if '|' in l and '---' not in l]
    if table_lines:
        features['has_tables'] = True
        # Count columns in tables
        for line in table_lines[:5]:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                features['table_column_counts'].add(len(parts))

    # Check for dotted lines
    dotted_lines = [l for l in lines if '..' in l]
    if dotted_lines:
        features['has_dots'] = True

    # Check for multi-line format (section number on its own line)
    for i in range(len(lines) - 1):
        if re.match(r'^\d+\.?\d*\.?\d*\s*$', lines[i].strip()):
            features['has_multiline'] = True
            break

    # Sample lines (first 10 non-empty, non-header lines)
    count = 0
    for line in lines:
        if line.strip() and not line.strip().startswith('#') and '---' not in line:
            features['sample_lines'].append(line.strip())
            count += 1
            if count >= 10:
                break

    features['table_column_counts'] = list(features['table_column_counts'])
    return features


def main():
    """Analyze all TOC sections from all wells"""

    # Collect all PDFs from Wells 1,2,3,4,5,6,8
    target_wells = [1, 2, 3, 4, 5, 6, 8]
    all_pdfs = []

    for well_num in target_wells:
        well_name = f"Well {well_num}"
        well_dir = data_dir / well_name / "Well report"

        if not well_dir.exists():
            continue

        pdfs = list(well_dir.rglob("*.pdf"))
        for pdf in pdfs:
            all_pdfs.append({
                'well': well_name,
                'path': pdf,
                'filename': pdf.name
            })

    print("="*80)
    print("STEP 1: DATA COLLECTION & FORMAT ANALYSIS")
    print("="*80)
    print(f"\nTarget: {len(all_pdfs)} PDFs from Wells {target_wells}")
    print("\n" + "="*80)

    results = []
    toc_found_count = 0

    for i, pdf_info in enumerate(all_pdfs, 1):
        print(f"\n[{i}/{len(all_pdfs)}] {pdf_info['well']}: {pdf_info['filename']}")
        print("-"*80)

        # Parse PDF with both Docling and PyMuPDF
        docling_text, raw_text, is_scanned, error = parse_first_n_pages(pdf_info['path'], num_pages=10)

        if error:
            print(f"  ERROR: {error}")
            results.append({
                'well': pdf_info['well'],
                'filename': pdf_info['filename'],
                'has_toc_section': False,
                'error': error
            })
            continue

        # Try Docling text first
        text = docling_text
        source = "Docling"
        lines = text.split('\n')
        start, end = find_toc_boundaries(lines)

        # If Docling didn't find TOC, try PyMuPDF fallback
        if start < 0:
            print(f"  Docling: NO TOC FOUND")
            print(f"  Trying PyMuPDF fallback...")
            text = raw_text
            source = "PyMuPDF"
            lines = text.split('\n')
            start, end = find_toc_boundaries(lines)

        if start < 0:
            print(f"  NO TOC SECTION FOUND (tried both Docling and PyMuPDF)")
            results.append({
                'well': pdf_info['well'],
                'filename': pdf_info['filename'],
                'has_toc_section': False,
                'is_scanned': is_scanned
            })
            continue

        # TOC found!
        toc_found_count += 1
        toc_lines = lines[start:end]

        print(f"  TOC SECTION FOUND ({source}): lines {start} to {end} ({end-start} lines)")

        # Analyze format
        features = analyze_toc_format(toc_lines)

        print(f"  Features:")
        print(f"    - Has tables: {features['has_tables']}")
        if features['has_tables']:
            print(f"    - Table columns: {features['table_column_counts']}")
        print(f"    - Has dots: {features['has_dots']}")
        print(f"    - Has multiline: {features['has_multiline']}")
        print(f"    - Is scanned: {is_scanned}")

        # Save TOC section to file
        toc_filename = f"{pdf_info['well'].replace(' ', '_')}_{pdf_info['filename'].replace('.pdf', '')}_toc.txt"
        toc_file = output_dir / toc_filename

        with open(toc_file, 'w', encoding='utf-8') as f:
            f.write(f"TOC Section from: {pdf_info['well']} - {pdf_info['filename']}\n")
            f.write(f"Lines {start} to {end}\n")
            f.write("="*80 + "\n\n")
            for idx, line in enumerate(toc_lines):
                f.write(f"{start+idx:4d}: {line}\n")

        print(f"  Saved to: {toc_filename}")

        # Store result
        results.append({
            'well': pdf_info['well'],
            'filename': pdf_info['filename'],
            'has_toc_section': True,
            'toc_start': start,
            'toc_end': end,
            'toc_lines': end - start,
            'is_scanned': is_scanned,
            'source': source,  # Which method found the TOC
            'features': features,
            'toc_file': str(toc_file)
        })

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    print(f"\nTotal PDFs analyzed: {len(all_pdfs)}")
    print(f"TOC sections found: {toc_found_count}/{len(all_pdfs)} ({toc_found_count/len(all_pdfs)*100:.1f}%)")
    print(f"TOC sections NOT found: {len(all_pdfs)-toc_found_count}/{len(all_pdfs)}")

    # Breakdown by well
    print("\n" + "-"*80)
    print("BREAKDOWN BY WELL")
    print("-"*80)

    for well_num in target_wells:
        well_name = f"Well {well_num}"
        well_results = [r for r in results if r['well'] == well_name]

        if not well_results:
            continue

        well_toc_found = sum(1 for r in well_results if r['has_toc_section'])
        print(f"\n{well_name}: {well_toc_found}/{len(well_results)} PDFs have TOC sections")

        for r in well_results:
            if r['has_toc_section']:
                status = f"TOC ({r['toc_lines']} lines)"
            else:
                status = "No TOC"
            print(f"  {status:20s} - {r['filename']}")

    # Format analysis
    print("\n" + "-"*80)
    print("FORMAT PATTERNS DETECTED")
    print("-"*80)

    with_tables = sum(1 for r in results if r.get('has_toc_section') and r.get('features', {}).get('has_tables'))
    with_dots = sum(1 for r in results if r.get('has_toc_section') and r.get('features', {}).get('has_dots'))
    with_multiline = sum(1 for r in results if r.get('has_toc_section') and r.get('features', {}).get('has_multiline'))

    print(f"\nFormat distribution (out of {toc_found_count} TOCs found):")
    print(f"  Tables: {with_tables} PDFs")
    print(f"  Dots: {with_dots} PDFs")
    print(f"  Multi-line: {with_multiline} PDFs")

    # Save results to JSON
    output_json = output_dir / "toc_analysis_results.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\nAll TOC sections saved to: {output_dir}")
    print(f"Analysis results saved to: {output_json}")

    print("\n" + "="*80)


if __name__ == '__main__':
    main()
