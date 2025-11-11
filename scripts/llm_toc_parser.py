"""
LLM-Based TOC Parser
Uses Ollama + Llama 3.2 3B to parse scrambled OCR text into structured TOC entries
"""

import re
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path


class LLMTOCParser:
    """
    Parse scrambled OCR text using LLM to reassemble section numbers, titles, and pages

    Designed for 2-column TOC layouts where OCR reads left-to-right, causing scrambled order.
    Uses Ollama + Llama 3.2 3B with structured prompting.
    """

    def __init__(self, ollama_model: str = "llama3.2:3b"):
        """
        Initialize LLM TOC parser

        Args:
            ollama_model: Ollama model to use (default: llama3.2:3b)
        """
        self.ollama_model = ollama_model
        self._verify_ollama()

    def _verify_ollama(self):
        """Verify Ollama is running and model is available"""
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if self.ollama_model not in result.stdout:
                raise RuntimeError(
                    f"Ollama model '{self.ollama_model}' not found. "
                    f"Run: ollama pull {self.ollama_model}"
                )

            print(f"  [OK] Ollama model '{self.ollama_model}' available")

        except FileNotFoundError:
            raise RuntimeError(
                "Ollama not found. Install from https://ollama.ai"
            )
        except Exception as e:
            print(f"  [WARN] Could not verify Ollama: {e}")

    def _query_ollama(self, prompt: str, temperature: float = 0.1) -> str:
        """
        Query Ollama with prompt

        Args:
            prompt: Text prompt for LLM
            temperature: Sampling temperature (0.1 for factual extraction)

        Returns:
            LLM response text
        """
        try:
            import subprocess

            # Build Ollama command
            cmd = [
                "ollama", "run", self.ollama_model,
                prompt
            ]

            # Run Ollama
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"Ollama error: {result.stderr}")

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise RuntimeError("Ollama query timeout (30s)")
        except Exception as e:
            raise RuntimeError(f"Ollama query failed: {e}")

    def _parse_llm_response(self, llm_output: str) -> List[Dict]:
        """
        Parse LLM output into structured TOC entries

        Expects JSON format:
        [
            {"number": "1", "title": "General Project data", "page": 5},
            {"number": "2", "title": "Well summary", "page": 6},
            ...
        ]

        Args:
            llm_output: LLM response text

        Returns:
            List of TOC entries [{'number': '1', 'title': '...', 'page': 5}, ...]
        """
        toc_entries = []

        # Try to extract JSON from LLM output
        # LLM might wrap JSON in markdown code blocks or add explanation text

        # Method 1: Look for JSON array in response
        json_match = re.search(r'\[\s*\{.*?\}\s*\]', llm_output, re.DOTALL)
        if json_match:
            try:
                toc_entries = json.loads(json_match.group(0))
                return toc_entries
            except json.JSONDecodeError:
                pass

        # Method 2: Look for markdown code block with JSON
        code_block_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', llm_output, re.DOTALL)
        if code_block_match:
            try:
                toc_entries = json.loads(code_block_match.group(1))
                return toc_entries
            except json.JSONDecodeError:
                pass

        # Method 3: Try to parse line-by-line format
        # "1. General Project data - page 5"
        for line in llm_output.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Pattern: "1. Title - page 5" or "1. Title (page 5)"
            match = re.match(
                r'^(\d+(?:\.\d+)*)\.\s+(.+?)\s*(?:-|page|\(page)\s*(\d+)',
                line,
                re.IGNORECASE
            )
            if match:
                number, title, page = match.groups()
                toc_entries.append({
                    'number': number.strip(),
                    'title': title.strip().rstrip('.)'),
                    'page': int(page)
                })
                continue

            # Pattern: "1. Title" (no page)
            match = re.match(r'^(\d+(?:\.\d+)*)\.\s+(.+)$', line)
            if match:
                number, title = match.groups()
                toc_entries.append({
                    'number': number.strip(),
                    'title': title.strip().rstrip('.)'),
                    'page': 0
                })

        return toc_entries

    def parse_scrambled_toc(self, scrambled_text: str) -> Tuple[List[Dict], str]:
        """
        Parse scrambled OCR text into structured TOC entries using LLM

        Args:
            scrambled_text: Raw OCR text with scrambled line order

        Returns:
            (toc_entries, method_name)
            toc_entries: List of dicts [{'number': '1', 'title': '...', 'page': 5}, ...]
            method_name: "LLM" for tracking
        """
        print(f"  [LLM] Parsing scrambled TOC text ({len(scrambled_text)} chars)...")

        # Original prompt: extract numbers, titles, AND pages
        prompt = f"""You are a document structure parser. The following text is a Table of Contents (TOC) extracted from a PDF using OCR, but the lines are scrambled due to a 2-column layout being read left-to-right.

Your task: Parse this scrambled text and extract the TOC entries in the correct order.

Scrambled TOC text:
{scrambled_text}

Instructions:
1. Match section numbers (1., 2., 2.1, 3., etc.) with their titles
2. Extract page numbers if present (often shown as dots like "..10" or "...12")
3. Return a JSON array of TOC entries in this exact format:
[
  {{"number": "1", "title": "General Project data", "page": 5}},
  {{"number": "2", "title": "Well summary", "page": 6}},
  {{"number": "2.1", "title": "Directional plots", "page": 8}},
  ...
]

Important:
- Preserve hierarchical numbering (1., 2., 2.1, 2.2, 3., etc.)
- Clean up titles (remove extra dots, spaces, HTML entities like &amp;)
- If page number is unclear, use 0
- Return ONLY the JSON array, no explanation text

JSON output:"""

        try:
            # Query LLM
            llm_output = self._query_ollama(prompt, temperature=0.1)

            print(f"  [LLM] Response ({len(llm_output)} chars)")

            # Parse LLM response
            toc_entries = self._parse_llm_response(llm_output)

            if len(toc_entries) >= 3:
                print(f"  [LLM] Extracted {len(toc_entries)} TOC entries")
                return toc_entries, "LLM"
            else:
                print(f"  [LLM] Insufficient TOC entries ({len(toc_entries)}) - need at least 3")
                return [], "LLM"

        except Exception as e:
            print(f"  [ERROR] LLM TOC parsing failed: {e}")
            import traceback
            traceback.print_exc()
            return [], "LLM"

    def detect_heading_pages(self, pdf_path: str, toc_entries: List[Dict]) -> List[Dict]:
        """
        Detect actual page numbers by searching for section headings in PDF using OCR

        Strategy:
        1. Use Docling OCR to extract text from each page (same as TOC extraction)
        2. For each TOC entry, search for section heading using fuzzy matching
        3. Return entries with detected page numbers

        Args:
            pdf_path: Path to PDF file
            toc_entries: TOC entries with structure (number + title) but no pages

        Returns:
            TOC entries with detected page numbers
        """
        print(f"\n  [INFO] Detecting heading pages using Docling OCR...")

        try:
            import re
            from difflib import SequenceMatcher
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions

            # Configure OCR (same as TOC extraction)
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options.force_full_page_ocr = True

            converter = DocumentConverter(
                format_options={"pdf": PdfFormatOption(pipeline_options=pipeline_options)}
            )

            print(f"  [INFO] Converting PDF with OCR for {len(toc_entries)} headings...")

            # Convert entire document
            result = converter.convert(pdf_path)

            # Extract text by page
            print(f"  [INFO] Extracting page-by-page text...")
            pages_text = {}

            # Get document text grouped by page
            for item in result.document.body:
                # Handle provenance - prov is a list of tuples (page, bbox)
                try:
                    if hasattr(item, 'prov') and item.prov and len(item.prov) > 0:
                        # prov is a list of (page_num, bbox) tuples
                        page_no = item.prov[0][0] if isinstance(item.prov[0], tuple) else item.prov[0].page
                    else:
                        page_no = 1
                except (AttributeError, IndexError, TypeError):
                    page_no = 1

                if page_no not in pages_text:
                    pages_text[page_no] = []

                # Get text from item
                if hasattr(item, 'text'):
                    pages_text[page_no].append(item.text)

            total_pages = len(pages_text)
            print(f"  [INFO] Extracted text from {total_pages} pages")

            # Search for each TOC entry
            for entry in toc_entries:
                section_num = entry.get('number', '')
                title = entry.get('title', '')

                if not title:
                    continue

                found_page = 0
                best_match_score = 0.7  # Minimum similarity threshold

                # Search through pages (first 50 pages only for efficiency)
                for page_num in sorted(pages_text.keys())[:50]:
                    page_text = '\n'.join(pages_text[page_num])

                    # Build search patterns
                    patterns = [
                        f"{section_num}\\s+{re.escape(title)}",  # "1. General Project data"
                        f"{section_num}\\.\\s+{re.escape(title)}",  # "1. General Project data"
                        re.escape(title),  # Just the title
                    ]

                    # Try exact pattern matching first
                    for pattern in patterns:
                        if re.search(pattern, page_text, re.IGNORECASE):
                            found_page = page_num
                            break

                    if found_page > 0:
                        break

                    # Fuzzy matching fallback
                    lines = page_text.split('\n')
                    for line in lines[:30]:  # Check first 30 lines of page
                        # Compare line with expected heading
                        expected = f"{section_num} {title}".lower()
                        actual = line.strip().lower()

                        similarity = SequenceMatcher(None, expected, actual).ratio()
                        if similarity > best_match_score:
                            found_page = page_num
                            best_match_score = similarity
                            break

                    if found_page > 0:
                        break

                if found_page > 0:
                    entry['page'] = found_page
                    print(f"    [OK] {section_num} '{title[:30]}...' -> page {found_page}")
                else:
                    print(f"    [MISS] {section_num} '{title[:30]}...' -> not found")
                    entry['page'] = 0

            # Count successful detections
            detected = sum(1 for e in toc_entries if e.get('page', 0) > 0)
            print(f"  [INFO] Detected {detected}/{len(toc_entries)} heading pages ({100*detected//len(toc_entries) if len(toc_entries) > 0 else 0}%)")

            return toc_entries

        except Exception as e:
            print(f"  [ERROR] Heading detection failed: {e}")
            import traceback
            traceback.print_exc()
            return toc_entries

    def validate_and_fix_page_numbers(self, pdf_path: str, toc_entries: List[Dict]) -> List[Dict]:
        """
        Validate TOC page numbers for logical consistency, fix suspicious ones with OCR

        Strategy:
        1. Check if page numbers make logical sense (no page 0, increasing order)
        2. Identify suspicious entries
        3. OCR only those specific pages to verify/correct

        Args:
            pdf_path: Path to PDF file
            toc_entries: TOC entries with potentially incorrect page numbers

        Returns:
            Updated TOC entries with corrected page numbers
        """
        print(f"\n  [INFO] Validating TOC page numbers for logical consistency...")

        # Step 1: Identify suspicious page numbers
        suspicious = self._find_suspicious_pages(toc_entries)

        if not suspicious:
            print(f"  [OK] All page numbers look reasonable")
            return toc_entries

        print(f"  [WARN] Found {len(suspicious)} suspicious page numbers:")
        for entry in suspicious:
            reason = entry.get('reason', 'unknown')
            print(f"    - Section {entry['number']} '{entry['title']}': page {entry['page']} ({reason})")

        # Step 2: Fix suspicious page numbers with targeted OCR
        print(f"\n  [INFO] Verifying suspicious page numbers with OCR...")
        corrected_entries = self._verify_pages_with_ocr(pdf_path, toc_entries, suspicious)

        return corrected_entries

    def _find_suspicious_pages(self, toc_entries: List[Dict]) -> List[Dict]:
        """
        Use LLM to identify suspicious page numbers and suggest search ranges

        Returns list of suspicious entries with 'reason' and 'search_range' fields
        """
        # Format TOC for LLM
        toc_text = "Table of Contents:\n"
        for i, entry in enumerate(toc_entries):
            num = entry.get('number', '')
            title = entry.get('title', '')
            page = entry.get('page', 0)
            toc_text += f"{i+1}. Section {num} '{title}': page {page}\n"

        prompt = f"""You are analyzing a Table of Contents to find suspicious page numbers.

{toc_text}

Task: Identify entries with incorrect or suspicious page numbers.

Rules:
1. Page numbers should generally increase (section 1 < section 2 < section 3)
2. Subsections should be near their parent (2.1 and 2.2 near section 2)
3. Page 0 means missing page number
4. Large gaps or backwards jumps are suspicious

For EACH suspicious entry, provide:
- section_number: The section number (e.g., "2.2")
- reason: Why it's suspicious
- expected_range: [min_page, max_page] where you expect to find it

Return JSON array:
[
  {{
    "section_number": "2.2",
    "reason": "page 0 (missing), should be between 2.1 (page 8) and section 3 (page 9)",
    "expected_range": [8, 9]
  }}
]

Return ONLY the JSON array, no other text."""

        try:
            # Query LLM
            llm_output = self._query_ollama(prompt, temperature=0.1)

            # Parse JSON response
            import json
            # Extract JSON from response (may have markdown markers)
            json_str = llm_output.strip()
            if '```' in json_str:
                json_str = json_str.split('```')[1]
                if json_str.startswith('json'):
                    json_str = json_str[4:]
            json_str = json_str.strip()

            suspicious_list = json.loads(json_str)

            # Match with actual entries
            suspicious = []
            for item in suspicious_list:
                section_num = item.get('section_number', '')
                for entry in toc_entries:
                    if entry.get('number') == section_num:
                        entry_copy = entry.copy()
                        entry_copy['reason'] = item.get('reason', 'unknown')
                        entry_copy['search_range'] = item.get('expected_range', [5, 15])
                        suspicious.append(entry_copy)
                        break

            return suspicious

        except Exception as e:
            print(f"  [WARN] LLM validation failed: {e}, falling back to simple rules")
            # Fallback to simple rule: page 0 is suspicious
            suspicious = []
            for i, entry in enumerate(toc_entries):
                if entry.get('page', 0) == 0:
                    entry_copy = entry.copy()
                    entry_copy['reason'] = 'missing page number (0)'
                    # Simple fallback range
                    if i > 0 and i < len(toc_entries) - 1:
                        prev_page = toc_entries[i-1].get('page', 5)
                        next_page = toc_entries[i+1].get('page', 15)
                        entry_copy['search_range'] = [prev_page, next_page]
                    else:
                        entry_copy['search_range'] = [5, 15]
                    suspicious.append(entry_copy)
            return suspicious

    def _verify_pages_with_ocr(self, pdf_path: str, toc_entries: List[Dict], suspicious: List[Dict]) -> List[Dict]:
        """
        Verify suspicious page numbers by OCRing specific pages

        Args:
            pdf_path: Path to PDF
            toc_entries: All TOC entries
            suspicious: List of suspicious entries to verify

        Returns:
            Updated TOC entries with corrected page numbers
        """
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions

        # Build map of suspicious entries
        suspicious_map = {entry['number']: entry for entry in suspicious}

        # Determine page range to OCR (use LLM-suggested ranges)
        pages_to_ocr = set()
        for entry in suspicious:
            search_range = entry.get('search_range', [5, 15])
            min_page, max_page = search_range
            # OCR the range suggested by LLM
            pages_to_ocr.update(range(min_page, max_page + 1))

        print(f"  [INFO] Will OCR {len(pages_to_ocr)} pages to verify: {sorted(pages_to_ocr)}")

        # Configure Docling with OCR
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options.force_full_page_ocr = True

        converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        # Parse PDF
        result = converter.convert(pdf_path)
        doc_model = result.document

        # Extract text from each page using document model
        pages = self._extract_pages_from_docling(doc_model)

        print(f"  [INFO] Extracted {len(pages)} pages from PDF")

        # Search for each suspicious section
        updated_entries = []
        for entry in toc_entries:
            if entry['number'] in suspicious_map:
                # This is suspicious, try to find correct page
                section_num = entry['number']
                section_title = entry['title']

                found_page = self._find_section_in_pages(section_num, section_title, pages)

                if found_page > 0:
                    entry['page'] = found_page
                    print(f"  [FIXED] Section {section_num} '{section_title}': corrected to page {found_page}")
                else:
                    print(f"  [WARN] Section {section_num} '{section_title}': could not find, keeping page {entry['page']}")

            updated_entries.append(entry)

        return updated_entries

    def _extract_pages_from_docling(self, doc_model) -> Dict[int, str]:
        """
        Extract text from each page using Docling's document model

        Args:
            doc_model: Docling Document object

        Returns:
            Dict mapping page number to text content
        """
        pages = {}

        # Get page count and extract text per page
        # Docling's document model has items with page numbers
        from collections import defaultdict
        page_items = defaultdict(list)

        # Group items by page number
        for item in doc_model.texts:
            page_no = getattr(item, 'page', 1)
            text = getattr(item, 'text', '')
            if text:
                page_items[page_no].append(text)

        # Combine text for each page
        for page_no, texts in page_items.items():
            pages[page_no] = '\n'.join(texts)

        # If no pages found, export entire document
        if not pages:
            pages[1] = doc_model.export_to_markdown()

        return pages

    def _split_docling_pages(self, doc_text: str) -> Dict[int, str]:
        """
        Split Docling markdown output by pages

        Docling markdown format uses page breaks
        """
        pages = {}

        # Split by page markers (Docling uses patterns like "---" or "Page X")
        # For now, use a simple heuristic: split by "---" or newline sequences
        current_page = 1
        current_content = []

        lines = doc_text.split('\n')
        for line in lines:
            # Detect page breaks (multiple dashes or explicit page markers)
            if line.strip() == '---' or line.strip().startswith('Page '):
                if current_content:
                    pages[current_page] = '\n'.join(current_content)
                    current_page += 1
                    current_content = []
            else:
                current_content.append(line)

        # Add last page
        if current_content:
            pages[current_page] = '\n'.join(current_content)

        # If no pages found, treat as single page
        if not pages:
            pages[1] = doc_text

        return pages

    def find_page_numbers(self, pdf_path: str, toc_entries: List[Dict]) -> List[Dict]:
        """
        Find actual page numbers by searching for section titles in PDF content

        Args:
            pdf_path: Path to PDF file
            toc_entries: TOC entries with potentially incorrect page numbers

        Returns:
            Updated TOC entries with corrected page numbers
        """
        print(f"\n  [INFO] Finding actual page numbers in PDF...")

        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.pipeline_options import PdfPipelineOptions

            # Configure with OCR
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options.force_full_page_ocr = True

            converter = DocumentConverter(
                format_options={
                    "pdf": PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            # Parse PDF
            result = converter.convert(pdf_path)
            doc_text = result.document.export_to_markdown()

            # Split into pages (Docling adds page markers)
            pages = self._split_by_pages(doc_text, pdf_path)

            print(f"  [INFO] Extracted {len(pages)} pages from PDF")

            # Find each section
            updated_entries = []
            for entry in toc_entries:
                section_num = entry.get('number', '')
                section_title = entry.get('title', '')

                # Search for section in pages
                found_page = self._find_section_in_pages(section_num, section_title, pages)

                if found_page > 0:
                    entry['page'] = found_page
                    print(f"  [FOUND] Section {section_num} '{section_title}' on page {found_page}")
                else:
                    print(f"  [WARN] Section {section_num} '{section_title}' not found, keeping page {entry.get('page', 0)}")

                updated_entries.append(entry)

            return updated_entries

        except Exception as e:
            print(f"  [ERROR] Page number extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return toc_entries

    def _split_by_pages(self, doc_text: str, pdf_path: str) -> Dict[int, str]:
        """Split document text by pages"""
        try:
            import pymupdf

            # Use PyMuPDF to extract page-by-page
            doc = pymupdf.open(pdf_path)
            pages = {}

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                pages[page_num + 1] = text

            doc.close()
            return pages

        except Exception as e:
            print(f"  [WARN] PyMuPDF page split failed: {e}")
            return {1: doc_text}

    def _find_section_in_pages(self, section_num: str, section_title: str, pages: Dict[int, str]) -> int:
        """
        Find which page contains the section

        Looks for patterns like:
        - "1 General Project data"
        - "1. General Project data"
        - "2.1 Directional plots"
        """
        # Normalize search title
        search_title = section_title.lower().strip()

        # Try multiple search patterns
        patterns = [
            f"{section_num}\\s+{re.escape(search_title)}",  # "1 Title"
            f"{section_num}\\.\\s+{re.escape(search_title)}",  # "1. Title"
            f"{section_num}\\s*{re.escape(search_title)}",  # "1Title"
            re.escape(search_title)  # Just the title
        ]

        # Search each page
        for page_num, page_text in sorted(pages.items()):
            page_lower = page_text.lower()

            for pattern in patterns:
                if re.search(pattern, page_lower):
                    return page_num

        # Not found
        return 0


if __name__ == '__main__':
    # Test on Well 7 scrambled OCR output
    from pathlib import Path

    print("="*80)
    print("LLM TOC PARSER TEST")
    print("="*80)

    # Load scrambled OCR output from Well 7
    toc_file = Path("outputs/well7_toc_force_ocr_scale1.0.txt")

    if not toc_file.exists():
        print(f"[ERROR] File not found: {toc_file}")
        print("Run 'python scripts/test_enhanced_ocr.py' first to generate this file")
        exit(1)

    with open(toc_file, 'r', encoding='utf-8') as f:
        scrambled_toc = f.read()

    print(f"\n[INPUT] Scrambled TOC from: {toc_file}")
    print(f"  Length: {len(scrambled_toc)} characters")
    print(f"  First 300 chars: {scrambled_toc[:300]}...")

    # Parse with LLM
    parser = LLMTOCParser()
    toc_entries, method = parser.parse_scrambled_toc(scrambled_toc)

    if len(toc_entries) >= 3:
        print(f"\n[SUCCESS] Extracted {len(toc_entries)} TOC entries using {method}:")
        print("-"*80)
        for i, entry in enumerate(toc_entries, 1):
            number = entry.get('number', 'N/A')
            title = entry.get('title', 'Unknown')
            page = entry.get('page', 0)
            print(f"{i:2d}. {number:5s} - {title:50s} (page {page})")
        print("-"*80)
    else:
        print(f"\n[FAILED] Only {len(toc_entries)} TOC entries found (need >=3)")

    print("\n" + "="*80)
