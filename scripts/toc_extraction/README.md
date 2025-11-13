# TOC Extraction System

**Automated Table of Contents extraction from well report PDFs with smart routing:**
- **Scanned PDFs** → Granite VLM (vision-based)
- **Native PDFs** → Text-based extraction (Docling + PyMuPDF)

**Status:** ✅ Production-ready (BETA quality)
**Well 7 Status:** ✅ Fixed and indexed successfully

---

## Quick Start

### Build Database
```bash
cd "C:\Users\Thai Phi\Downloads\Hackathon"
source venv/Scripts/activate
python scripts/toc_extraction/core/build_multi_doc_toc_database_granite.py
```

**Output:** `outputs/exploration/toc_database_multi_doc_granite.json`
**Runtime:** ~10-15 minutes for all 16 PDFs

### Validate Database
```bash
python scripts/toc_extraction/core/validate_toc_database.py
```

**Expected:** `[VALID] DATABASE IS VALID - No issues found`

### Test Well 7
```bash
python scripts/toc_extraction/tests/test_well7_granite_fixed.py
```

**Expected:** 73% confidence, 100% accuracy

---

## Folder Structure

```
toc_extraction/
├── core/                    # Production-ready scripts
│   ├── build_multi_doc_toc_database_granite.py  ⭐ Main database builder
│   ├── analyze_all_tocs.py                      Parse PDFs with OCR
│   ├── robust_toc_extractor.py                  Core TOC extractor
│   ├── parse_granite_toc.py                     Enhanced Granite parser
│   └── validate_toc_database.py                 Database validation
│
├── tests/                   # Test scripts
│   ├── test_well7_granite_fixed.py              Well 7 complete test
│   ├── test_granite_toc_standalone.py           Granite standalone test
│   ├── test_robust_extractor.py                 Extractor tests
│   └── test_with_fallback.py                    Fallback demo
│
└── archive/                 # Old/experimental scripts
    ├── build_toc_database.py                    Old version (replaced)
    ├── build_multi_doc_toc_database_full.py     Old version (replaced)
    └── ... (10+ legacy scripts)
```

---

## Core Scripts

### 1. build_multi_doc_toc_database_granite.py
**Purpose:** Main database builder with smart routing and auto-discovery
**Input:** Auto-discovers all folders with `Well report/` subfolder in `Training data-shared with participants/`
**Output:** `outputs/exploration/toc_database_multi_doc_granite.json`
**Features:**
- **Auto-discovery:** Automatically finds all well folders (e.g., "Well 1", "Beaver A 1H", "9")
- **Pattern-based categorization:** Works with any well, no manual configuration needed
- Smart routing (scanned → Granite, native → text)
- Comprehensive logging to `outputs/logs/database_builder_*.log`
- Error handling with fallbacks
- 13-category section mapping

**Folder Structure Required:**
```
Training data-shared with participants/
├── Well 1/
│   └── Well report/        ← Must have this subfolder
│       └── *.pdf
├── Beaver A 1H/           ← Any folder name works
│   └── Well report/        ← Case-insensitive
│       └── *.pdf
└── 9/                     ← Even numeric names work
    └── Well Report/        ← "Well Report" or "well report"
        └── *.pdf
```

**Usage:**
```bash
python scripts/toc_extraction/core/build_multi_doc_toc_database_granite.py
```

**Scalability:** Works with any number of wells - just add more folders with `Well report/` subfolder!

### 2. analyze_all_tocs.py
**Purpose:** Parse PDFs with OCR support
**Key Features:**
- `force_full_page_ocr = True` for scanned PDFs
- Page-by-page OCR text extraction
- TOC boundary detection
- PyMuPDF fallback

**Used by:** `build_multi_doc_toc_database_granite.py`

### 3. robust_toc_extractor.py
**Purpose:** Core TOC extraction logic
**Features:**
- Hierarchical pattern matching
- Adaptive table parsing
- Handles multiple TOC formats (tables, dotted, multi-line)

**Used by:** Text-based extraction path

### 4. parse_granite_toc.py
**Purpose:** Enhanced Granite parser with validation
**Features:**
- Correct column selection (column 2, not last column)
- 3-rule validation system
- Range notation for uncertain pages
- Boundary violation detection

**Used by:** Granite VLM extraction path

### 5. validate_toc_database.py
**Purpose:** Database quality validation
**Checks:**
- All PDFs have entries
- No negative page numbers
- Valid dates
- No duplicates
- Page numbers within bounds

**Usage:**
```bash
python scripts/toc_extraction/core/validate_toc_database.py
```

---

## Test Scripts

### test_well7_granite_fixed.py
**Purpose:** Complete integration test for Well 7
**Runtime:** ~50 seconds
**Expected:** 73% confidence, 100% accuracy (8/8 main sections)

### test_granite_toc_standalone.py
**Purpose:** Standalone Granite VLM test
**Usage:** Test Granite extraction on specific PDF

### test_robust_extractor.py
**Purpose:** Validate TOC extraction on 14 PDFs
**Expected:** 100% success rate

### test_with_fallback.py
**Purpose:** Demonstrate PyMuPDF fallback
**Usage:** Show fallback when Docling corrupts TOC

---

## Well 7 Fixes (2025-11-12)

All 6 critical fixes for scanned PDF support:

1. ✅ **Force Full Page OCR** (`analyze_all_tocs.py:73`)
2. ✅ **Page-by-Page OCR Text** (`analyze_all_tocs.py:94-106`)
3. ✅ **OCR-Based Page Detection** (`build_multi_doc_toc_database_granite.py:180-254`)
4. ✅ **2-Page TOC Extraction** (`src/toc_extraction/granite_toc_extractor.py:48-100`)
5. ✅ **Correct Column Selection** (`src/toc_extraction/granite_toc_extractor.py:190-203`)
6. ✅ **60% Confidence Threshold** (`build_multi_doc_toc_database_granite.py:462`)

**Result:** Well 7 successfully indexed with 11 TOC entries, 73% confidence

---

## Database Quality

**Current Stats (from validation):**
- Wells: 8
- Documents: 15 (1 scanned, 14 native)
- TOC Entries: 218
- Exact pages: 188 (86.2%)
- Range pages: 3 (1.4%)
- Unknown pages: 27 (12.4%)
- **Accuracy: 87.6%**

**Parse Methods:**
- Granite: 1 document (Well 7)
- Docling: 14 documents

**Status:** ✅ VALID - No integrity issues

---

## Source Modules

Located in `src/toc_extraction/`:

### granite_toc_extractor.py
**Purpose:** Granite VLM wrapper class
**Key Methods:**
- `extract_toc_pages_as_pdf()` - Extract 2 consecutive TOC pages
- `extract_from_page()` - Run Granite VLM on TOC page
- `extract_full_workflow()` - Complete extraction + validation

### toc_validator.py
**Purpose:** Validation functions
**Key Functions:**
- `parse_granite_multicolumn_table()` - Basic Granite parser
- `validate_and_refine_toc()` - 3-rule validation
- `calculate_toc_confidence()` - Confidence scoring

**Note:** Enhanced version in `scripts/toc_extraction/core/parse_granite_toc.py`

---

## Documentation

Located in `.claude/tasks/toc_extraction/`:

### database-builder-detailed-design.md
**Contents:**
- Complete workflow documentation
- All 6 Well 7 fixes with code snippets
- Scripts & files reference
- How to run commands
- Output file locations

---

## Archive

Old/experimental scripts moved to `archive/`:
- `build_toc_database.py` - Original single-doc builder
- `build_multi_doc_toc_database_full.py` - Pre-Granite version
- `test_two_stage_toc.py` - Two-stage TOC experiment
- `llm_toc_parser.py` - LLM-based parser (abandoned)
- And 10+ other legacy scripts

**Reason for archival:** Replaced by production-ready core scripts

---

## Known Limitations

1. **Unknown Pages:** 12.4% of pages are unknown (target: <5%)
2. **Granite Date Extraction:** Disabled due to import errors (using text fallback)
3. **Single Scanned PDF:** Only tested on Well 7 (need more scanned PDFs)
4. **No Timeout Handling:** Granite can hang on large PDFs
5. **No Progress Indicators:** Long operations show no progress

---

## Next Steps

**For RAG System:**
- Use `outputs/exploration/toc_database_multi_doc_granite.json`
- TOC structure provides natural chunking boundaries
- 13-category mapping enables semantic search

**For Improvements:**
- Add progress indicators (tqdm)
- Add timeout handling
- Reduce unknown pages <5%
- Add unit tests

---

## Contact

For issues or questions:
- Check `.claude/tasks/toc_extraction/database-builder-detailed-design.md`
- Review test scripts in `tests/`
- Run validation: `python scripts/toc_extraction/core/validate_toc_database.py`
