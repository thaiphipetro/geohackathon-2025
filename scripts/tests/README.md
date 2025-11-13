# Experimental Test Scripts

One-off test scripts used during development. Not part of the main test suite.

## Scripts

- **test_demo_functionality.py** - Demo system functionality test
- **test_enhanced_ocr.py** - Test enhanced OCR features
- **test_improved_llm_prompt.py** - Test LLM prompting strategies
- **test_page_number_extraction.py** - Test page number detection
- **test_reindex_results.py** - Test reindexing functionality
- **test_well5_extraction.py** - Test Well 5 extraction
- **test_well7_ocr.py** - Test Well 7 OCR pipeline

## Usage

Run individual test scripts:

```bash
cd scripts/tests
python test_well5_extraction.py
```

## Production Tests

These are experimental tests. For production integration tests, use:

```bash
# TOC extraction tests
python scripts/toc_extraction/tests/test_robust_extractor.py
python scripts/toc_extraction/tests/test_well7_granite_fixed.py

# Validate TOC database
python scripts/toc_extraction/core/validate_toc_database.py
```

## Note

These scripts were created for specific development tasks and may not be maintained. They serve as reference implementations and exploratory code.
