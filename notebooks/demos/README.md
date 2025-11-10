# Demo Notebooks

Educational Jupyter notebooks that demonstrate the TOC extraction, categorization, and database building workflow.

## Key Feature: Sandboxed Environment

All demo notebooks use the **isolated sandbox** at `notebooks/sandbox/` to prevent interference with the production RAG system.

- ✅ Separate ChromaDB (`notebooks/sandbox/chroma_db/`)
- ✅ Separate outputs (`notebooks/sandbox/outputs/`)
- ✅ Read-only access to training data
- ✅ Safe experimentation without breaking production

## Notebooks

### 00_complete_walkthrough.ipynb
**End-to-end workflow for new users**

Complete walkthrough from setup to working RAG system:
1. Environment setup and verification
2. Install and configure Ollama
3. Extract publication dates from PDFs
4. Extract TOC entries with robust extractor
5. Categorize TOCs with 13-category system
6. Build multi-document TOC database
7. Index documents in ChromaDB
8. Query RAG system and verify results

**Who should use:** New users setting up the system for the first time

---

### 07_publication_date_extraction.ipynb
**Demonstrate PyMuPDF fallback for date extraction**

Shows how to extract publication dates with 100% success rate:
- Parse PDFs with PyMuPDF
- Pattern matching (Dutch months, ordinal indicators, standalone dates)
- Docling vs PyMuPDF comparison
- Fallback strategy
- Test on all 14 PDFs

**Who should use:** Users wanting to understand date extraction logic

---

### 08_toc_extraction_demo.ipynb
**Demonstrate robust TOC extraction with 100% success**

Shows the complete TOC extraction pipeline:
- Load PDFs from all 8 wells
- Find TOC boundaries with keyword + structural detection
- Extract entries with `RobustTOCExtractor`
- Adaptive pattern matching (table, dotted, multi-line formats)
- PyMuPDF fallback when Docling corrupts TOC
- Visualize 14/14 success rate

**Who should use:** Users implementing TOC extraction or debugging failures

---

### 09_toc_categorization.ipynb
**Demonstrate 13-category system**

Shows how TOC entries are categorized:
- Load TOC database (207 entries across 14 PDFs)
- Demonstrate `create_improved_categorization.py` workflow
- Explain 13 categories (project_admin, well_testing, intervention, etc.)
- Visualize category distribution across wells
- Show coverage improvement (62.8% → 98.5%)
- Demonstrate how categories improve RAG retrieval

**Who should use:** Users understanding section type filtering

---

### 10_build_toc_database.ipynb
**Demonstrate complete database building**

Shows the full database creation workflow:
- Scan all 8 wells for well reports
- Extract publication dates (100% success)
- Extract TOC entries (100% success)
- Apply categorization (98.5% coverage)
- Build multi-document structure
- Save to `toc_database_multi_doc.json`

**Who should use:** Users building their own TOC database

---

## Usage Order

**For new users:**
1. Start with `00_complete_walkthrough.ipynb` (full workflow)
2. Then explore specific topics as needed

**For developers:**
1. `08_toc_extraction_demo.ipynb` (core TOC extraction)
2. `07_publication_date_extraction.ipynb` (date extraction)
3. `09_toc_categorization.ipynb` (categorization)
4. `10_build_toc_database.ipynb` (database building)

## vs Production Notebooks

| Location | Purpose | ChromaDB | Outputs |
|----------|---------|----------|---------|
| `notebooks/demos/` | **Learning & demos** | Sandbox | Sandbox |
| `notebooks/` (root) | **Production usage** | Production | Production |

Production notebooks (in `notebooks/` root):
- `01_data_exploration_v1.ipynb` - Dataset exploration
- `03_test_rag_system.ipynb` - Basic RAG test
- `04_interactive_rag_demo.ipynb` - Full RAG demo
- `05_test_summarization.ipynb` - Summarization demo
- `06_sub_challenge_1_guide.ipynb` - Sub-Challenge 1 guide

## Sandbox Reset

If demo outputs become corrupted, reset the sandbox:

```bash
# From project root
rm -rf notebooks/sandbox/chroma_db/*
rm -rf notebooks/sandbox/outputs/*
```

Then re-run the demo notebooks to rebuild.
