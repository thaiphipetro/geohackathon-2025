# Repository Cleanup Plan

**Status:** Planning
**Created:** 2025-11-12
**Goal:** Clean up repository structure, remove temporary files, and organize code for production readiness

---

## Current State Assessment

### Issues Identified:

1. **26 unorganized scripts** at `scripts/` root level (debug, test, experimental files)
2. **2 temporary test files** at project root (test_auto_discovery.py, test_pattern_categorization.py)
3. **1 temporary log file** (test_well7_pattern.log)
4. **1 image file** at root ("well 7 toc.png")
5. **10 deleted scripts** pending git commit
6. **Multiple untracked .claude/tasks/** files (planning documents)
7. **Organized toc_extraction/** folder structure (✅ already good)

### What's Working Well:

✅ **scripts/toc_extraction/** - Well organized with core/, tests/, archive/ subdirectories
✅ **src/toc_extraction/** - Clean module structure
✅ **.claude/tasks/toc_extraction/** - Organized documentation

---

## Cleanup Strategy

### Phase 1: Organize Root-Level Scripts (Priority: HIGH)

**Goal:** Move all 26 experimental/debug/test scripts from `scripts/` to appropriate locations

#### Category A: Debug Scripts (Move to `scripts/debug/`)
```
scripts/debug/
├── debug_docling_model.py
├── debug_page_content.py
├── debug_prov_structure.py
├── debug_well7_ocr.py
├── detect_well7_headers_regex.py
├── enhanced_well7_parser.py
├── extract_page3_only.py
└── README.md  # Explain these are debugging utilities
```

#### Category B: Test Scripts (Move to `scripts/tests/`)
```
scripts/tests/
├── test_demo_functionality.py
├── test_enhanced_ocr.py
├── test_improved_llm_prompt.py
├── test_page_number_extraction.py
├── test_reindex_results.py
├── test_well5_extraction.py
├── test_well7_ocr.py
└── README.md  # Explain these are experimental tests
```

#### Category C: Utility Scripts (Move to `scripts/utils/`)
```
scripts/utils/
├── add_new_documents.py
├── build_structure_only_database_parallel.py
├── compare_prompts.py
├── discover_well_documents.py
├── validate_well7_extraction.py
├── validate_well_inventory.py
└── README.md  # Explain these are utility scripts
```

#### Category D: Keep at Root (Production Scripts)
```
scripts/
├── quick_explore.py          # Main data exploration script
├── toc_extraction/           # Production TOC system (keep as-is)
├── debug/                    # New: debug scripts
├── tests/                    # New: experimental tests
├── utils/                    # New: utility scripts
└── README.md                 # Update with new structure
```

---

### Phase 2: Clean Up Root Directory (Priority: HIGH)

**Files to Remove:**
```bash
# Temporary test files
rm test_auto_discovery.py
rm test_pattern_categorization.py
rm test_well7_pattern.log

# Move image to documentation folder
mv "well 7 toc.png" .claude/tasks/toc_extraction/well-7-toc-example.png
```

**Files to Keep:**
- src/
- scripts/
- .claude/
- outputs/
- notebooks/
- venv/
- requirements.txt
- README.md
- CLAUDE.md
- START_HERE.md
- .gitignore

---

### Phase 3: Update Documentation (Priority: MEDIUM)

#### Update `scripts/README.md`
```markdown
# Scripts Directory

## Structure

```
scripts/
├── quick_explore.py          # Quick dataset scan (main utility)
├── toc_extraction/           # Production TOC extraction system
│   ├── core/                 # Production scripts
│   ├── tests/                # Integration tests
│   └── archive/              # Legacy scripts
├── debug/                    # Debugging utilities
├── tests/                    # Experimental test scripts
└── utils/                    # Utility scripts
```

## Usage

**Quick Data Exploration:**
```bash
python scripts/quick_explore.py
```

**TOC Extraction System:**
```bash
# Build complete TOC database
python scripts/toc_extraction/core/build_multi_doc_toc_database_granite.py

# Validate database
python scripts/toc_extraction/core/validate_toc_database.py
```

See `scripts/toc_extraction/README.md` for detailed TOC system documentation.

## Organization

- **quick_explore.py** - Production-ready data exploration
- **toc_extraction/** - Complete TOC extraction system (documented)
- **debug/** - Debugging and troubleshooting scripts (experimental)
- **tests/** - Experimental test scripts (not production)
- **utils/** - Utility scripts for specific tasks
```

#### Create `scripts/debug/README.md`
```markdown
# Debug Scripts

These are experimental debugging utilities used during development.
Not intended for production use.

## Scripts

- **debug_docling_model.py** - Debug Docling parsing issues
- **debug_page_content.py** - Inspect page content extraction
- **debug_prov_structure.py** - Debug provenance structures
- **debug_well7_ocr.py** - Debug Well 7 OCR extraction
- **detect_well7_headers_regex.py** - Test regex patterns for Well 7
- **enhanced_well7_parser.py** - Experimental Well 7 parser
- **extract_page3_only.py** - Extract single page for testing
```

#### Create `scripts/tests/README.md`
```markdown
# Experimental Test Scripts

These are one-off test scripts used during development.
Not part of the main test suite.

## Scripts

- **test_demo_functionality.py** - Demo system functionality test
- **test_enhanced_ocr.py** - Test enhanced OCR features
- **test_improved_llm_prompt.py** - Test LLM prompting strategies
- **test_page_number_extraction.py** - Test page number detection
- **test_reindex_results.py** - Test reindexing functionality
- **test_well5_extraction.py** - Test Well 5 extraction
- **test_well7_ocr.py** - Test Well 7 OCR pipeline

## Running Tests

These are experimental. For production tests, use:
```bash
python scripts/toc_extraction/tests/test_robust_extractor.py
python scripts/toc_extraction/tests/test_well7_granite_fixed.py
```
```

#### Create `scripts/utils/README.md`
```markdown
# Utility Scripts

Utility scripts for specific tasks and maintenance.

## Scripts

- **add_new_documents.py** - Add new documents to database
- **build_structure_only_database_parallel.py** - Build structure database
- **compare_prompts.py** - Compare different prompting strategies
- **discover_well_documents.py** - Discover well documents
- **validate_well7_extraction.py** - Validate Well 7 extraction
- **validate_well_inventory.py** - Validate well inventory
```

---

### Phase 4: Commit Deleted Files (Priority: HIGH)

**Files to commit as deleted:**
```bash
git rm scripts/add_well_with_toc.py
git rm scripts/analyze_all_tocs.py
git rm scripts/build_multi_doc_toc_database_full.py
git rm scripts/build_toc_database.py
git rm scripts/llm_toc_parser.py
git rm scripts/reindex_all_wells_with_toc.py
git rm scripts/robust_toc_extractor.py
git rm scripts/test_robust_extractor.py
git rm scripts/test_well7_toc_only.py
git rm scripts/test_with_fallback.py
```

**Commit message:**
```
refactor: move legacy TOC scripts to organized structure

- Moved core scripts to scripts/toc_extraction/core/
- Moved tests to scripts/toc_extraction/tests/
- Archived legacy scripts in scripts/toc_extraction/archive/
- Part of repository cleanup and reorganization
```

---

### Phase 5: Add New Files to Git (Priority: MEDIUM)

**Production code (add immediately):**
```bash
git add src/toc_extraction/
git add scripts/toc_extraction/core/
git add scripts/toc_extraction/tests/
git add scripts/toc_extraction/README.md
```

**Documentation (add after review):**
```bash
git add .claude/tasks/granite-toc-all-wells-comprehensive-plan.md
git add .claude/tasks/toc_extraction/
```

**Debug/Test scripts (add after organizing):**
```bash
git add scripts/debug/
git add scripts/tests/
git add scripts/utils/
git add scripts/README.md
```

---

### Phase 6: Update .gitignore (Priority: LOW)

**Add to .gitignore:**
```gitignore
# Temporary test files
test_*.py
test_*.log

# Debug outputs
debug_*.txt
debug_*.json

# Temporary images
*.png
!docs/**/*.png

# Log files
*.log
!outputs/logs/*.log
```

---

## Execution Plan

### Step-by-Step Checklist:

#### Immediate (Do Now):
- [ ] Create new directories: scripts/debug/, scripts/tests/, scripts/utils/
- [ ] Move 26 scripts to appropriate directories
- [ ] Remove temporary files (test_auto_discovery.py, etc.)
- [ ] Move "well 7 toc.png" to .claude/tasks/toc_extraction/
- [ ] Create README.md files for debug/, tests/, utils/
- [ ] Update scripts/README.md

#### Git Operations:
- [ ] Commit deleted files (10 files)
- [ ] Add organized scripts to git
- [ ] Add src/toc_extraction/ to git
- [ ] Add documentation to git
- [ ] Create consolidation commit

#### Verification:
- [ ] Run `scripts/toc_extraction/core/validate_toc_database.py`
- [ ] Verify all imports still work
- [ ] Check that main scripts are accessible

---

## Benefits

1. **Clear Organization**: Production code separated from experimental code
2. **Easy Navigation**: Logical folder structure
3. **Documentation**: Each folder has README explaining purpose
4. **Git Cleanliness**: No temporary files, clear history
5. **Maintainability**: Future developers can understand structure

---

## Timeline

**Total estimated time:** 45 minutes

- Phase 1 (Organize scripts): 15 min
- Phase 2 (Clean root): 5 min
- Phase 3 (Documentation): 15 min
- Phase 4 (Git deleted files): 2 min
- Phase 5 (Git new files): 5 min
- Phase 6 (Update .gitignore): 3 min

---

## Notes

- Keep `scripts/toc_extraction/` as-is (already well organized)
- Main production entry point: `scripts/toc_extraction/core/build_multi_doc_toc_database_granite.py`
- Secondary entry point: `scripts/quick_explore.py`
- All experimental code clearly marked in debug/, tests/, utils/
