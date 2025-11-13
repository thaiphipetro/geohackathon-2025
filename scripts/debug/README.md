# Debug Scripts

Experimental debugging utilities used during development. Not intended for production use.

## Scripts

- **debug_docling_model.py** - Debug Docling parsing issues
- **debug_page_content.py** - Inspect page content extraction
- **debug_prov_structure.py** - Debug provenance structures
- **debug_well7_ocr.py** - Debug Well 7 OCR extraction
- **detect_well7_headers_regex.py** - Test regex patterns for Well 7
- **enhanced_well7_parser.py** - Experimental Well 7 parser
- **extract_page3_only.py** - Extract single page for testing

## Usage

These scripts are standalone debugging tools. Run them directly from this directory:

```bash
cd scripts/debug
python debug_docling_model.py
```

## Note

These are experimental scripts for troubleshooting specific issues. For production TOC extraction, use:
```bash
python scripts/toc_extraction/core/build_multi_doc_toc_database_granite.py
```
