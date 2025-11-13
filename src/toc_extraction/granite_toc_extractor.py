"""
Granite VLM-based TOC Extractor

Uses Granite-Docling-258M vision-language model to extract Table of Contents
from PDF pages. Works on both native and scanned PDFs by seeing TOC as an image.
"""

from pathlib import Path
import tempfile
from typing import Tuple, List, Dict, Optional

import fitz  # PyMuPDF
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.datamodel import vlm_model_specs


class GraniteTOCExtractor:
    """
    Extract Table of Contents using Granite-Docling-258M VLM

    Advantages over text-based extraction:
    - Vision-based: Sees TOC as image (not confused by formatting)
    - Works on scanned PDFs (Well 7 case)
    - Handles multi-column TOCs (dotted lines don't confuse)
    - Better boundary detection (sees visual layout)
    """

    def __init__(self):
        """Initialize Granite VLM converter"""
        # Configure Granite VLM pipeline
        self.pipeline_options = VlmPipelineOptions(
            vlm_options=vlm_model_specs.GRANITEDOCLING_TRANSFORMERS
        )

        # Create converter with Granite VLM
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=self.pipeline_options
                )
            }
        )

    def extract_toc_pages_as_pdf(
        self,
        pdf_path: Path,
        toc_page_num: int,
        num_pages: int = 2
    ) -> Path:
        """
        Extract TOC pages as standalone PDF (handles multi-page TOCs)

        Args:
            pdf_path: Path to source PDF
            toc_page_num: Starting document page number (1-indexed)
            num_pages: Number of consecutive pages to extract (default: 2)

        Returns:
            Path to temporary PDF containing TOC pages

        Example:
            TOC starts on page 3, spans 2 pages → toc_page_num=3, num_pages=2
            Extracts pages 3 and 4
        """
        doc = fitz.open(str(pdf_path))

        # Convert document page number (1-indexed) to PDF page index (0-indexed)
        start_idx = toc_page_num - 1
        end_idx = min(start_idx + num_pages - 1, len(doc) - 1)

        if start_idx < 0 or start_idx >= len(doc):
            doc.close()
            raise ValueError(
                f"TOC page {toc_page_num} out of range "
                f"(PDF has {len(doc)} pages)"
            )

        # Create temporary PDF with TOC pages
        temp_pdf = tempfile.NamedTemporaryFile(
            suffix='.pdf',
            delete=False,
            prefix='granite_toc_'
        )
        temp_path = temp_pdf.name
        temp_pdf.close()

        # Extract pages (handles both single and multi-page TOCs)
        toc_doc = fitz.open()
        toc_doc.insert_pdf(doc, from_page=start_idx, to_page=end_idx)
        toc_doc.save(temp_path)
        toc_doc.close()
        doc.close()

        print(f"    [GRANITE] Extracting {end_idx - start_idx + 1} page(s) starting from page {toc_page_num}")

        return Path(temp_path)

    def extract_from_page(self, toc_page_pdf_path: Path) -> Tuple[str, bool]:
        """
        Extract TOC using Granite VLM from single-page PDF

        Args:
            toc_page_pdf_path: Path to single-page TOC PDF

        Returns:
            (markdown_text, success) tuple
            - markdown_text: Granite's markdown output
            - success: True if extraction succeeded
        """
        try:
            result = self.converter.convert(str(toc_page_pdf_path))
            markdown = result.document.export_to_markdown()
            return markdown, True
        except Exception as e:
            print(f"    [ERROR] Granite extraction failed: {e}")
            return "", False

    def extract_full_workflow(
        self,
        pdf_path: Path,
        toc_page_num: int,
        pdf_total_pages: int
    ) -> Tuple[List[Dict], float, Optional[str]]:
        """
        Complete Granite TOC extraction workflow

        Steps:
        1. Extract TOC page as standalone PDF
        2. Run Granite VLM on TOC page
        3. Use RobustTOCExtractor (same as text-based method)
        4. Validate with 3-rule system + range notation

        Args:
            pdf_path: Path to source PDF
            toc_page_num: Document page number of TOC (1-indexed)
            pdf_total_pages: Total pages in PDF (for validation)

        Returns:
            (toc_entries, confidence, method) tuple
            - toc_entries: List of {number, title, page} dicts
            - confidence: 0.0-1.0 score (exact pages / total entries)
            - method: "Granite" if succeeded, None if failed
        """
        # Import parsing functions from parse_granite_toc (enhanced version with validation)
        try:
            import sys
            from pathlib import Path as P
            sys.path.insert(0, str(P(__file__).parent.parent / 'scripts'))
            from parse_granite_toc import parse_granite_multicolumn_table
        except ImportError as e:
            print(f"    [ERROR] Cannot import required modules: {e}")
            return [], 0.0, None

        # Step 1: Extract TOC pages (2 pages to handle multi-page TOCs)
        try:
            toc_page_pdf = self.extract_toc_pages_as_pdf(pdf_path, toc_page_num, num_pages=2)
        except Exception as e:
            print(f"    [ERROR] Failed to extract TOC pages: {e}")
            return [], 0.0, None

        # Step 2: Run Granite VLM
        markdown, success = self.extract_from_page(toc_page_pdf)

        # DEBUG: Save raw Granite output for analysis
        debug_dir = Path("outputs/debug")
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_path = debug_dir / f"granite_output_{pdf_path.stem}.md"
        try:
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"    [DEBUG] Saved Granite output to: {debug_path}")
        except Exception as e:
            print(f"    [DEBUG] Failed to save output: {e}")

        # Cleanup temp file
        try:
            toc_page_pdf.unlink()
        except Exception:
            pass

        if not success or not markdown:
            print("    [GRANITE] Extraction failed or empty output")
            return [], 0.0, None

        # Step 3: Parse using parse_granite_multicolumn_table (enhanced version with validation)
        try:
            # Use parse_granite_toc version (better validation + logging)
            # Extracts from column 2 (first page column: 5, 6, 7...)
            # enable_retry=False for speed (no Granite re-runs during bulk processing)
            toc_entries = parse_granite_multicolumn_table(
                markdown,
                max_page_number=pdf_total_pages,
                toc_page_path=None,      # No retry path needed
                enable_retry=False       # Fast mode: no Granite re-extraction
            )
            pattern = "Granite Multi-column Table (validated)"

            if toc_entries:
                print(f"    [GRANITE] Matched pattern: {pattern}")
        except Exception as e:
            print(f"    [ERROR] Failed to parse Granite output: {e}")
            return [], 0.0, None

        if len(toc_entries) < 3:
            print(f"    [GRANITE] Too few entries ({len(toc_entries)})")
            return [], 0.0, None

        # Step 4: Calculate confidence score
        # Note: parse_granite_multicolumn_table already did validation
        unknown_count = sum(1 for e in toc_entries if e['page'] == 0)
        range_count = sum(
            1 for e in toc_entries
            if isinstance(e['page'], str) and '-' in str(e['page'])
        )
        exact_count = len(toc_entries) - unknown_count - range_count

        confidence = exact_count / len(toc_entries) if toc_entries else 0.0

        print(f"    [GRANITE] Extracted {len(toc_entries)} entries:")
        print(f"      Exact: {exact_count}, Range: {range_count}, Unknown: {unknown_count}")
        print(f"      Confidence: {confidence:.2f}")

        return toc_entries, confidence, "Granite"


# Test function
def test_granite_extractor():
    """Test GraniteTOCExtractor on Well 7"""
    pdf_path = Path("Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf")

    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        return

    print("="*80)
    print("TESTING GRANITE TOC EXTRACTOR")
    print("="*80)

    # Get total pages
    doc = fitz.open(str(pdf_path))
    pdf_total_pages = len(doc)
    doc.close()

    print(f"\nPDF: {pdf_path.name}")
    print(f"Total pages: {pdf_total_pages}")

    # Create extractor
    extractor = GraniteTOCExtractor()

    # Extract TOC (page 3 for Well 7)
    toc_page_num = 3
    print(f"\nExtracting TOC from page {toc_page_num}...")

    toc_entries, confidence, method = extractor.extract_full_workflow(
        pdf_path,
        toc_page_num,
        pdf_total_pages
    )

    # Display results
    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}")
    print(f"Method: {method}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Total entries: {len(toc_entries)}\n")

    for entry in toc_entries:
        page_str = str(entry['page'])
        if entry['page'] == 0:
            status = "UNKNOWN"
        elif '-' in page_str:
            status = "RANGE"
        else:
            status = "EXACT"

        print(f"  {entry['number']:6s} {entry['title']:50s} {page_str:>6s} [{status}]")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    test_granite_extractor()
