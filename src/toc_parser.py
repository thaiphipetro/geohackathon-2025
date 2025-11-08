"""
TOC-Enhanced Document Parser
Uses TOC database for page-targeted parsing (30-86x faster than full document)
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import fitz  # PyMuPDF
import tempfile
import os

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption


class TOCEnhancedParser:
    """
    Page-targeted PDF parser using TOC database

    Workflow:
        1. Load TOC database
        2. Query: "well depth" → section types: ['depth', 'borehole']
        3. TOC lookup → pages: [6, 20]
        4. Parse ONLY 2 pages (vs 100+ pages) → 30-86x faster
        5. Return text with section metadata

    Example:
        parser = TOCEnhancedParser('outputs/exploration/toc_database.json')
        pages = parser.get_section_pages('Well 5', ['depth', 'borehole'])
        result = parser.parse_targeted_pages(pdf_path, pages, 'Well 5')
    """

    def __init__(self, toc_db_path: str):
        """
        Initialize parser with TOC database

        Args:
            toc_db_path: Path to toc_database.json
        """
        self.toc_db_path = Path(toc_db_path)
        self.toc_db = self._load_toc_db()

    def _load_toc_db(self) -> Dict:
        """Load TOC database from JSON"""
        with open(self.toc_db_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_section_pages(self, well_name: str, section_types: List[str]) -> List[int]:
        """
        Get page numbers for specific section types

        Args:
            well_name: Well identifier (e.g., 'Well 5')
            section_types: List of section types (e.g., ['depth', 'borehole'])

        Returns:
            Sorted list of unique page numbers

        Example:
            >>> parser = TOCEnhancedParser('toc_database.json')
            >>> parser.get_section_pages('Well 5', ['depth', 'borehole'])
            [4, 6, 20, 22, 26, 28]
        """
        well_data = self.toc_db.get(well_name)
        if not well_data:
            raise ValueError(f"Well '{well_name}' not found in TOC database")

        pages = set()
        for section_type in section_types:
            sections = well_data['key_sections'].get(section_type, [])
            for sec in sections:
                pages.add(sec['page'])

        return sorted(pages)

    def get_section_metadata(self, well_name: str, section_types: List[str]) -> List[Dict]:
        """
        Get full metadata for sections

        Args:
            well_name: Well identifier
            section_types: List of section types

        Returns:
            List of section metadata dicts

        Example:
            >>> parser.get_section_metadata('Well 5', ['depth'])
            [
                {'number': '3.6', 'title': 'Directional drilling data', 'page': 22, 'type': 'depth'},
                {'number': '3.7', 'title': 'Directional drilling data', 'page': 26, 'type': 'depth'}
            ]
        """
        well_data = self.toc_db.get(well_name)
        if not well_data:
            return []

        metadata = []
        for section_type in section_types:
            sections = well_data['key_sections'].get(section_type, [])
            for sec in sections:
                metadata.append({
                    'number': sec['number'],
                    'title': sec['title'],
                    'page': sec['page'],
                    'type': section_type
                })

        return metadata

    def parse_targeted_pages(self,
                             pdf_path: str,
                             pages: List[int],
                             well_name: Optional[str] = None) -> Dict:
        """
        Parse only specific pages from PDF

        Optimization: Extract target pages to temp PDF, then parse with Docling
        This is 30-86x faster than parsing the full document

        Args:
            pdf_path: Path to PDF file
            pages: List of page numbers to parse (1-indexed)
            well_name: Optional well identifier for metadata

        Returns:
            Dict with:
                - text: Parsed markdown text
                - pages: List of parsed pages
                - well_name: Well identifier
                - parse_method: 'page_targeted'

        Example:
            >>> result = parser.parse_targeted_pages('report.pdf', [6, 20])
            >>> print(result['text'][:100])
        """
        if not pages:
            return {
                'text': '',
                'pages': [],
                'well_name': well_name,
                'parse_method': 'page_targeted'
            }

        # Step 1: Extract target pages to temp PDF
        doc = fitz.open(pdf_path)
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_path = temp_pdf.name
        temp_pdf.close()

        new_doc = fitz.open()
        for page_num in pages:
            # PDF pages are 0-indexed, TOC pages are 1-indexed
            if 0 < page_num <= len(doc):
                new_doc.insert_pdf(doc, from_page=page_num-1, to_page=page_num-1)

        new_doc.save(temp_path)
        new_doc.close()
        doc.close()

        # Step 2: Check if scanned (for OCR decision)
        is_scanned = self._is_scanned_pdf(pdf_path)

        # Step 3: Parse with Docling
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = is_scanned
        pipeline_options.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        result = converter.convert(temp_path)
        markdown = result.document.export_to_markdown()

        # Extract tables separately
        tables = result.document.tables if hasattr(result.document, 'tables') else []

        # Clean up temp file
        os.unlink(temp_path)

        return {
            'text': markdown,
            'tables': tables,
            'pages': pages,
            'well_name': well_name,
            'parse_method': 'page_targeted',
            'is_scanned': is_scanned,
        }

    def _is_scanned_pdf(self, pdf_path: str) -> bool:
        """
        Quick check if PDF is scanned image (no text layer)

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if scanned image, False if native PDF
        """
        doc = fitz.open(pdf_path)

        # Check first 3 pages
        for page_num in range(min(3, len(doc))):
            text = doc[page_num].get_text()
            if len(text.strip()) > 50:  # Has text content
                doc.close()
                return False

        doc.close()
        return True  # No text found → scanned image

    def get_well_pdf_path(self, well_name: str) -> Optional[str]:
        """
        Get PDF path from TOC database

        Args:
            well_name: Well identifier

        Returns:
            Path to PDF file, or None if not found
        """
        well_data = self.toc_db.get(well_name)
        if not well_data:
            return None

        return well_data.get('eowr_file')

    def list_available_wells(self) -> List[str]:
        """
        List all wells in TOC database

        Returns:
            List of well names
        """
        return list(self.toc_db.keys())


def main():
    """Test the TOC-enhanced parser"""
    # Setup paths
    toc_db_path = Path(__file__).parent.parent / 'outputs' / 'exploration' / 'toc_database.json'

    if not toc_db_path.exists():
        print(f"ERROR: TOC database not found at {toc_db_path}")
        print("Please run 'notebooks/build_toc_database.py' first")
        return

    # Initialize parser
    parser = TOCEnhancedParser(str(toc_db_path))

    print("="*80)
    print("TOC-ENHANCED PARSER - TEST")
    print("="*80)

    # List available wells
    wells = parser.list_available_wells()
    print(f"\nAvailable wells: {', '.join(wells)}")

    # Test with Well 5 (best quality)
    well_name = 'Well 5'
    section_types = ['depth', 'borehole']

    print(f"\nTest: Query '{well_name}' for sections {section_types}")

    # Get section pages
    pages = parser.get_section_pages(well_name, section_types)
    print(f"\nTarget pages: {pages}")
    print(f"Pages to parse: {len(pages)} (vs ~100+ pages in full document)")
    print(f"Speed improvement: ~{100//len(pages)}x faster")

    # Get section metadata
    metadata = parser.get_section_metadata(well_name, section_types)
    print(f"\nSections found: {len(metadata)}")
    for sec in metadata:
        print(f"  - {sec['number']:6} {sec['title']:50} (page {sec['page']}, type: {sec['type']})")

    # Get PDF path
    pdf_path = parser.get_well_pdf_path(well_name)
    if pdf_path and Path(pdf_path).exists():
        print(f"\nPDF path: {pdf_path}")
        print(f"Parsing {len(pages)} pages...")

        result = parser.parse_targeted_pages(pdf_path, pages, well_name)

        print(f"\nParsed successfully:")
        print(f"  - Text length: {len(result['text'])} chars")
        print(f"  - Scanned: {result['is_scanned']}")
        print(f"  - Method: {result['parse_method']}")
        print(f"\nFirst 500 chars:")
        print(result['text'][:500])
    else:
        print(f"\nPDF not found: {pdf_path}")


if __name__ == '__main__':
    main()
