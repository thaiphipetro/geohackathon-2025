# Repository Cleanup Plan

**Date:** 2025-11-08
**Purpose:** Organize repository, remove unnecessary files, improve maintainability

---

## Current Issues

1. **18 debug scripts** in `notebooks/` (temporary development files)
2. **Duplicate notebooks** (e.g., `01_data_exploration.ipynb` vs `01_data_exploration_v1.ipynb`)
3. **Jupyter checkpoints** (.ipynb_checkpoints/) tracked by git
4. **Session logs** consuming 212KB in `.claude/tasks/session-logs/`
5. **Old exploration outputs** (well_*_text.txt files)
6. **Multiple indexing logs** (can consolidate)
7. **Cache files** (__pycache__)
8. **Temporary files** (emoji_lines.txt)

**Total size to clean:** ~1.5MB (mostly notebooks/)

---

## Cleanup Strategy

### Phase 1: REMOVE - Delete Temporary/Debug Files ❌

**Debug Scripts (archive old, keep useful):**

**Keep these (move to scripts/):**
- `notebooks/debug_failing_wells.py` → `scripts/debug_failing_wells.py` ✅ **Useful for debugging indexing issues**

**Archive these (old development scripts):**
- `notebooks/debug_pymupdf_well1.py`
- `notebooks/debug_toc.py`
- `notebooks/debug_toc_structure.py`
- `notebooks/debug_well1_docling_markdown.py`
- `notebooks/debug_well2.py`
- `notebooks/debug_well2_docling.py`
- `notebooks/debug_well7_full_ocr.py`
- `notebooks/debug_well7_ocr.py`
- `notebooks/debug_well7_pymupdf.py`
- `notebooks/debug_well_7_images.py`
- `notebooks/debug_well_7_lines_30_200.py`
- `notebooks/debug_well_7_page_2.py`
- `notebooks/debug_well_7_structure.py`
- `notebooks/test_date_extraction.py`
- `notebooks/test_pymupdf_toc_parser.py`
- `notebooks/test_toc_well_5_7.py`
- `notebooks/test_toc_well_5_7_fixed.py`
- `notebooks/extract_toc_fixed.py`
- `notebooks/run_notebook.py`

**Duplicate/Old Notebooks:**
```bash
rm notebooks/01_data_exploration.ipynb  # Keep v1 (newer, cleaner version)
rm notebooks/.ipynb_checkpoints/*
```

**Temporary Files:**
```bash
rm emoji_lines.txt
rm SESSION_SUMMARY_2025-11-07.md
rm SESSION_SUMMARY_2025-11-08.md
```

**Old Exploration Outputs:**
```bash
rm outputs/exploration/well_1_docling_markdown.txt
rm outputs/exploration/well_1_pymupdf_text.txt
rm outputs/exploration/well_2_docling_markdown.txt
rm outputs/exploration/well_7_ocr_markdown.txt
rm outputs/exploration/well_5_table_metadata.json
```

**Old Logs (keep only latest):**
```bash
rm outputs/indexing_log.txt  # Keep indexing_log_fixed.txt
```

**Session Logs (archive or delete):**
```bash
# Option 1: Delete
rm -rf .claude/tasks/session-logs/

# Option 2: Archive
mkdir -p .archive/session-logs
mv .claude/tasks/session-logs/* .archive/session-logs/
```

**Cache Files:**
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

---

### Phase 2: ORGANIZE - Restructure Directories 📁

**Current Structure:**
```
notebooks/          # 1.4MB - Mix of notebooks and scripts
  ├── *.ipynb       # Jupyter notebooks (good)
  ├── *.py          # Python scripts (should be in scripts/)
  └── README.md
```

**Target Structure:**
```
notebooks/          # Notebooks only
  ├── 01_data_exploration_v1.ipynb
  ├── 02_toc_analysis_and_rag_integration.ipynb
  ├── 03_test_rag_system.ipynb
  ├── 04_interactive_rag_demo.ipynb
  ├── 05_test_summarization.ipynb
  ├── 06_sub_challenge_1_guide.ipynb
  └── README.md

scripts/            # All Python scripts
  ├── build_toc_database.py     # Move from notebooks/
  ├── analyze_all_tocs.py       # Move from notebooks/
  ├── debug_failing_wells.py    # Move from notebooks/
  ├── check_chromadb_status.py
  ├── index_all_wells.py
  ├── quick_explore.py
  ├── scan_all_wells_for_multi_pdf.py
  └── README.md

outputs/
  ├── exploration/              # TOC database and analysis
  ├── indexing_log_fixed.txt    # Latest indexing log
  ├── indexing_results.json     # Indexing summary
  └── README.md

.archive/                       # Optional: For historical reference
  ├── session-logs/
  ├── old-implementations/
  └── debug-scripts/
```

**Move Commands:**
```bash
# Move useful scripts from notebooks/ to scripts/
mv notebooks/build_toc_database.py scripts/
mv notebooks/analyze_all_tocs.py scripts/
mv notebooks/debug_failing_wells.py scripts/
```

---

### Phase 3: UPDATE - Improve .gitignore 🚫

**Add to .gitignore:**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project-specific
outputs/indexing_log*.txt
outputs/exploration/*.txt
emoji_lines.txt
SESSION_SUMMARY_*.md

# Docker
.docker/

# Temporary files
*.tmp
*.bak
*.orig

# Large data files (already in .gitignore but verify)
Training data-shared with participants/

# Archive folder
.archive/

# Session logs
.claude/tasks/session-logs/
```

---

### Phase 4: DOCUMENT - Update Documentation 📝

**Update README.md:**
- Add "Repository Structure" section
- Document what each directory contains
- Update setup instructions
- Add "Development Workflow" section

**Create scripts/README.md:**
```markdown
# Scripts

## Production Scripts
- `build_toc_database.py` - Build TOC database from well reports
- `index_all_wells.py` - Index all wells into ChromaDB
- `check_chromadb_status.py` - Verify indexed data

## Development Scripts
- `quick_explore.py` - Quick dataset scan
- `scan_all_wells_for_multi_pdf.py` - Find multi-PDF wells
- `debug_failing_wells.py` - Debug indexing failures

## Utility Scripts
- `add_second_well5_pdf.py` - Add second Well 5 PDF to TOC
- `remove_emojis_from_py_files.py` - Windows compatibility fix
```

**Create outputs/README.md:**
```markdown
# Outputs

## Essential Files
- `exploration/toc_database.json` - TOC database (9 wells)
- `indexing_results.json` - Latest indexing summary

## Analysis Files
- `exploration/TOC_ANALYSIS_SUMMARY.md` - TOC analysis report
- `exploration/toc_database_report.md` - TOC database report

## Logs
- `indexing_log_fixed.txt` - Latest indexing log (regenerated each run)
```

---

### Phase 5: VERIFY - Post-Cleanup Checks ✅

**Check Commands:**
```bash
# 1. Verify git status
git status

# 2. Check directory sizes
du -sh .claude src scripts notebooks outputs

# 3. Count files
find . -name "*.py" | wc -l
find . -name "*.ipynb" | wc -l

# 4. Verify no cache files
find . -name "__pycache__" -o -name ".ipynb_checkpoints"

# 5. Test imports
python -c "from src.rag_system import WellReportRAG; print('OK')"

# 6. Run tests
pytest tests/ -v
```

---

## Execution Order

**Safe cleanup (can run immediately):**
```bash
# 1. Remove cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null

# 2. Remove temporary files
rm emoji_lines.txt 2>/dev/null
rm SESSION_SUMMARY_*.md 2>/dev/null
```

**Review before deleting (verify not needed):**
```bash
# List files to remove
ls notebooks/debug_*.py
ls notebooks/test_*.py
ls outputs/exploration/*.txt
```

**Archive (recommended before deleting):**
```bash
# Create archive
mkdir -p .archive/{debug-scripts,session-logs,old-outputs}

# Move to archive
mv notebooks/debug_*.py .archive/debug-scripts/
mv notebooks/test_*.py .archive/debug-scripts/
mv .claude/tasks/session-logs/* .archive/session-logs/
mv outputs/exploration/*.txt .archive/old-outputs/
```

---

## Expected Results

**Before Cleanup:**
- Total files: ~80
- notebooks/: 1.4MB (26 files)
- .claude/: 212KB (includes session logs)
- Git status: Many untracked files

**After Cleanup:**
- Total files: ~35-40 (50% reduction)
- notebooks/: <500KB (6-7 notebooks only)
- .claude/: <100KB (no session logs)
- Git status: Clean, only essential files

**Benefits:**
- ✅ Easier navigation
- ✅ Faster git operations
- ✅ Clear project structure
- ✅ Better for collaboration
- ✅ Reduced repository size
- ✅ Easier to understand for new developers

---

## Rollback Plan

**If something goes wrong:**
```bash
# Restore from archive
cp -r .archive/debug-scripts/* notebooks/
cp -r .archive/session-logs/* .claude/tasks/session-logs/

# Or restore from git (if committed)
git checkout HEAD -- .
```

---

## Post-Cleanup Tasks

1. **Commit cleanup:**
   ```bash
   git add .
   git commit -m "chore: repository cleanup and reorganization

   - Remove 18 debug scripts from notebooks/
   - Remove duplicate notebooks and checkpoints
   - Remove temporary exploration outputs
   - Archive old session logs
   - Update .gitignore
   - Improve documentation
   "
   ```

2. **Update documentation:**
   - README.md with new structure
   - scripts/README.md
   - outputs/README.md

3. **Notify team:**
   - Share CLEANUP_PLAN.md
   - Update onboarding docs
   - Update CLAUDE.md if needed

---

## Notes

- **Do NOT delete:**
  - `src/` - Core system code
  - `outputs/exploration/toc_database.json` - Essential
  - `outputs/indexing_results.json` - Latest results
  - `.claude/tasks/*.md` - Implementation plans
  - Essential documentation files

- **Safe to delete:**
  - All `debug_*.py` files
  - All `.ipynb_checkpoints/`
  - Session logs (if archived)
  - Old exploration text dumps

- **Archive first (safer):**
  - Debug scripts (might need reference)
  - Session logs (historical context)
  - Old outputs (for comparison)
