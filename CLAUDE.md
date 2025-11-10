# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**GeoHackathon 2025: Automated Well Performance Analysis**

AI-powered system for extracting parameters from well completion reports (PDFs) and running nodal analysis.

**Sub-Challenges:**
- Sub-Challenge 1 (50%): RAG-based summarization of well reports
- Sub-Challenge 2 (20%): Extract structured parameters (MD, TVD, ID) from documents
- Sub-Challenge 3 (30%): Agentic workflow that autonomously queries RAG → extracts params → runs nodal analysis

**Tech Stack:**
- Document parsing: Docling + RapidOCR
- Embeddings: nomic-embed-text-v1.5 (137M params)
- Vector store: ChromaDB
- LLM: Ollama + Llama 3.2 3B
- Agent framework: LangGraph
- Vision (bonus): Moondream2 (1.6B) or Florence-2-base (230M)

**Critical Constraints:**
- All models <500M params (Llama 3.2 3B is exception, smallest viable LLM)
- CPU-only, no GPU required
- Pure pip install, no system dependencies
- Fully open source, runs locally

---

## Project Structure

```
.
├── src/                          # Main source code
│   ├── document_parser.py        # Docling-based PDF parsing with OCR
│   ├── embeddings.py             # nomic-embed-text-v1.5 + ChromaDB
│   ├── rag_system.py             # RAG query with Ollama
│   ├── parameter_extractor.py    # Extract MD/TVD/ID using Pydantic
│   ├── nodal_analysis_wrapper.py # Wrapper for NodalAnalysis.py
│   ├── agent.py                  # LangGraph agent (Sub-Challenge 3)
│   └── vision_extractor.py       # Vision model for diagrams (bonus)
├── scripts/
│   ├── quick_explore.py          # CLI tool to scan training dataset
│   ├── analyze_all_tocs.py       # ✅ Step 1: Extract TOC sections from all PDFs
│   ├── robust_toc_extractor.py   # ✅ Core TOC extraction class
│   ├── test_robust_extractor.py  # ✅ Validate TOC extraction on 14 PDFs
│   ├── test_with_fallback.py     # ✅ Demonstrate PyMuPDF fallback
│   ├── build_toc_database.py     # Build TOC-based document index
│   └── index_all_wells.py        # Index all wells for RAG
├── notebooks/
│   ├── 01_data_exploration.ipynb # Jupyter notebook for exploring data
│   └── README.md                 # Notebook setup instructions
├── tests/                        # Test suites (to be created)
│   ├── test_sub_challenge_1.py
│   ├── test_sub_challenge_2.py
│   └── test_sub_challenge_3.py
├── outputs/
│   ├── exploration/
│   │   └── quick_scan_summary.json     # Dataset scan results
│   └── toc_analysis/
│       ├── ✅ 14 extracted TOC sections (100% success)
│       └── toc_analysis_results.json    # TOC analysis metadata
├── .claude/tasks/                # Implementation plans & session logs
│   ├── geohackathon-implementation-plan.md  # Full 4-week plan
│   ├── sub-challenge-1-detailed-plan.md     # Day 1-7 breakdown
│   ├── training-data-structure-analysis.md  # Dataset analysis
│   └── session-log-*.md                     # Session logs
├── Training data-shared with participants/  # Well reports (not in git)
│   ├── Well 1/ through Well 8/
│   ├── NodalAnalysis.py          # Provided nodal analysis script
│   └── boreholes.xlsx            # Master well index
├── venv/                         # Python virtual environment
├── requirements.txt              # All dependencies
├── README.md                     # Project documentation
└── START_HERE.md                 # Quick start guide
```

---

## Key Architecture Patterns

### 0. TOC Extraction System (✅ Completed - 100% Success)

**Achievement:** Successfully extracted Table of Contents from 14/14 PDFs across Wells 1-8 using adaptive pattern matching + PyMuPDF fallback.

**Flow:** PDF → Docling Parser → TOC Boundary Detection → RobustTOCExtractor → Structured Entries

**Core Components:**

1. **TOC Boundary Detection** (`scripts/analyze_all_tocs.py`):
   - Searches for keywords: "contents", "content", "table of contents", "index"
   - Fallback: Detects structural patterns (multiple numbered lines)
   - PyMuPDF fallback: When Docling corrupts TOC, use raw text extraction

2. **RobustTOCExtractor** (`scripts/robust_toc_extractor.py`):
   - Hierarchical pattern matching for multiple TOC formats
   - Adaptive table parsing with intelligent column detection
   - Dotted format: `1.1 Title ........ 5`
   - Multi-line format: Section number on one line, title+page on next
   - Space-separated format: `1.1  Title     5`

**Key Design Decisions:**
- **Hierarchical approach**: Try table extraction first, then fallback to plain text patterns
- **Adaptive table parsing**: Intelligently detects which column contains section numbers, titles, and page numbers
- **PyMuPDF fallback**: When Docling's aggressive table detection corrupts clean dotted format, use raw text
- **Minimum threshold**: Require ≥3 TOC entries to consider extraction successful

**Usage:**

```bash
# Step 1: Analyze all TOCs and save to outputs/toc_analysis/
python scripts/analyze_all_tocs.py

# Step 2: Test extraction on all 14 saved TOC sections
python scripts/test_robust_extractor.py

# Step 3: Demonstrate PyMuPDF fallback on failed PDF
python scripts/test_with_fallback.py
```

**Results:**
- TOC boundary detection: 14/14 (100%)
- TOC entry extraction: 14/14 (100%)
- Pattern distribution: Adaptive Table (12 PDFs), Multi-line Dotted (2 PDFs)

**Common Issues & Solutions:**

| Issue | Root Cause | Solution |
|-------|------------|----------|
| Infinite loop in `_extract_multiline_dotted()` | Counter not incremented when no match found | Added `found` boolean flag to track matches |
| Missing "Content" singular keyword | Only searched for "contents" plural | Added "content" with word boundary check |
| Docling table corruption | Aggressive table detection on dotted format | PyMuPDF fallback preserves clean format |

---

### 1. RAG Pipeline (Sub-Challenge 1)
**Flow:** PDF → Docling Parser → Text/Tables → Chunk → Embed → ChromaDB → Query → LLM

```python
# Document parsing with OCR
parser = WellReportParser(enable_ocr=True)
parsed = parser.parse_pdf(pdf_path)  # Returns: {text, tables, images, metadata}

# Embedding and storage
em = EmbeddingManager()
em.add_document(doc_id="Well_5", text=parsed['text'], tables=parsed['tables'], metadata={...})

# RAG query
rag = RAGSystem(em)
result = rag.query("What is the well depth?")  # Returns: {answer, sources, metadata}
```

**Key Design Decisions:**
- Use overlapping chunks (1000 chars, 200 overlap) for better retrieval
- Store tables as separate chunks with `chunk_type: "table"` metadata
- Low temperature (0.1) for factual answers
- Always cite context sources
- **Use TOC-based chunking**: Leverage extracted TOC to create section-aligned chunks

---

### 2. Structured Extraction (Sub-Challenge 2)
**Flow:** RAG → Retrieve table chunks → LLM with JSON mode → Pydantic validation → Export

```python
class WellSection(BaseModel):
    measured_depth: float      # MD in meters
    true_vertical_depth: float # TVD in meters
    inner_diameter: float      # ID in inches

class WellCompletionData(BaseModel):
    well_name: str
    sections: List[WellSection]
    unit_system: str = "meters"

# Extract with validation
extractor = ParameterExtractor(rag_system)
well_data = extractor.extract_well_parameters("NLW-GT-03")
nodal_format = extractor.export_for_nodal_analysis(well_data)
# Returns: {"MD": [...], "TVD": [...], "ID": [...]}
```

**Critical:** Output must match `NodalAnalysis.py` format exactly (see line 23-28 of that file).

---

### 3. Agentic Workflow (Sub-Challenge 3)
**Flow:** User prompt → LangGraph agent → Tool calls (RAG query, param extraction, nodal analysis) → Response

```python
# Agent with tools
agent = WellAnalysisAgent(rag_system, parameter_extractor, nodal_wrapper)

# Tools available to agent:
# - query_well_report(question: str) -> str
# - extract_well_parameters(well_name: str) -> Dict
# - run_nodal_analysis(well_data: str) -> Dict
# - list_available_wells() -> List[str]

# Execute
result = agent.analyze_well("Analyze well performance for NLW-GT-03")
```

**Important:** Agent should complete workflow in ≤3 tool calls when all info is provided.

---

## Commands

### Environment Setup

**Activate virtual environment (ALWAYS do this first):**
```bash
# Windows (adjust path as needed)
cd "C:\Users\Thai Phi\Downloads\Hackathon"
venv\Scripts\activate

# Git Bash on Windows
source venv/Scripts/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

### Data Exploration

**Quick dataset scan:**
```bash
python scripts/quick_explore.py
```
Output: Scans all 8 wells, shows PDF/Excel counts, identifies best wells (Well 5, 7, 1)

**TOC Extraction Pipeline (✅ 100% Success):**
```bash
# Step 1: Extract all TOC sections (outputs to outputs/toc_analysis/)
python scripts/analyze_all_tocs.py

# Step 2: Validate extraction on all 14 TOC sections
python scripts/test_robust_extractor.py

# Step 3: Test PyMuPDF fallback on specific PDF
python scripts/test_with_fallback.py

# Output: 14/14 PDFs with successful TOC extraction
```

**Multi-Document TOC Database (✅ 14/14 PDFs, 11 Categories):**
```bash
# Build complete multi-document TOC database with 11-category mapping
python scripts/build_multi_doc_toc_database_full.py

# Output: outputs/exploration/toc_database_multi_doc_full.json
# - Supports multiple PDFs per well (not just best)
# - Tracks publication dates for version control
# - Maps 193 TOC entries to 11 section type categories
# - Ready for page-range based chunking

# Test specific well TOC extraction
python scripts/test_well2_toc.py
```

**See detailed documentation:** `.claude/tasks/multi-doc-toc-database-implementation.md`

**Deep exploration (Jupyter):**
```bash
cd notebooks
jupyter notebook
# Then open: 01_data_exploration.ipynb
```
Purpose: Parse Well 5 EOWR, extract tables with MD/TVD/ID, test OCR

**Check Jupyter server status:**
```bash
# If server running in background
ps aux | grep jupyter

# URL: http://localhost:8888/tree?token=<token>
```

### Ollama Setup (Required for Sub-Challenge 1+)

```bash
# Download from: https://ollama.ai
# After installation:
ollama pull llama3.2:3b
ollama run llama3.2:3b "Hello test"  # Verify
```

### Testing & Code Quality

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_parser.py::test_parse_well_5 -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Format code
black src/

# Lint
flake8 src/

# Type check
mypy src/
```

### Git Workflow

Use Conventional Commits format: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`

```bash
git add .
git commit -m "feat: implement document parser"
```

---

## Critical Implementation Constraints

**MUST FOLLOW:**
1. Models <500M params (Llama 3.2 3B is exception, smallest viable LLM)
2. CPU-only execution
3. Pure pip install (no LibreOffice, apt, brew, or system dependencies)
4. Fully open source, no API keys
5. Local execution for data security

**Rejected approaches:** RAG-Anything (needs LibreOffice), large embedding models (>500M params)

---

## Code Style Guidelines

**MUST FOLLOW:**

1. **NO EMOJIS IN CODE** - Never use emojis in Python code, comments, docstrings, or print statements
   - ❌ Bad: `print("✅ Success!")` or `# 🎯 TODO: fix this`
   - ✅ Good: `print("Success!")` or `# TODO: fix this`
   - Emojis can cause encoding issues and make code less portable
   - Only use plain ASCII characters in all code files

2. **Clean, readable code:**
   - Use descriptive variable names
   - Add docstrings to functions and classes
   - Keep functions focused and small
   - Follow PEP 8 style guide

3. **Error handling:**
   - Use try-except blocks for file operations
   - Provide clear error messages
   - Implement fallback strategies (like PyMuPDF fallback)

4. **Testing:**
   - Write unit tests for core functions
   - Test on multiple PDFs from different wells
   - Validate edge cases (empty files, corrupted PDFs, etc.)

5. **Documentation:**
   - Comment complex algorithms
   - Document assumptions and limitations
   - Provide usage examples in docstrings

---

## NodalAnalysis.py Integration

**Location:** `Training data-shared with participants/NodalAnalysis.py`

**Input Format Required:**
```python
well_trajectory = [
    {"MD": 0.0,    "TVD": 0.0,    "ID": 0.3397},   # in meters
    {"MD": 500.0,  "TVD": 500.0,  "ID": 0.2445},
    {"MD": 1500.0, "TVD": 1500.0, "ID": 0.1778},
    {"MD": 2500.0, "TVD": 2500.0, "ID": 0.1778},
]
```

**Hardcoded Parameters (DO NOT EXTRACT, already set):**
- rho = 1000.0 (water density)
- mu = 1e-3 (viscosity)
- reservoir_pressure = 230.0 bar
- wellhead_pressure = 10.0 bar
- PI = 5.0 (Productivity Index)
- esp_depth = 500.0 m

**What to Extract from Documents:**
- MD: Measured Depth (meters)
- TVD: True Vertical Depth (meters)
- ID: Inner Diameter (meters or convert from inches)

**Output:** The script calculates flow rate and bottom hole pressure (BHP)

---

## Dataset Structure

**8 Wells Available:**
1. Well 1 (ADK-GT-01): 9 PDFs, High quality
2. Well 2: 11 PDFs, High quality
3. Well 3: 4 PDFs, Medium quality
4. Well 4 (Multi-well): 20 PDFs, High quality
5. **Well 5 (NLW-GT-03)**: 22 PDFs, **BEST QUALITY** ⭐
6. Well 6: 12 PDFs, High quality
7. Well 7 (BRI-GT-01): 14 PDFs, High quality, well organized
8. Well 8: 11 PDFs, High quality

**Recommended Starting Well:** Well 5 (NLW-GT-03) - most comprehensive documentation

**Key Files in Each Well:**
- `Well report/EOWR/` - End of Well Reports (contains casing tables with MD, TVD, ID)
- `Technical log/` - Drilling logs
- `Production data/` - Excel files with production history
- `Well test/` - Test results
- `PVT/` - Pressure-Volume-Temperature data

**Critical Data Location:**
- MD, TVD, ID are typically in EOWR PDF files in casing completion tables
- Look for tables with headers: "Measured Depth", "True Vertical Depth", "Inner Diameter" (or variations)
- Some documents are scanned → need OCR
- Some diagrams are handwritten → need vision model (bonus challenge)

---

## Implementation Phases

**Detailed implementation plans are in `.claude/tasks/` - reference those for hour-by-hour breakdowns.**

### Phase 1: Sub-Challenge 1 (Week 1, 50%)
1. ✅ **TOC Extraction System** - 100% success on 14 PDFs
2. Document parser with Docling + RapidOCR
3. Embeddings (nomic-embed-text-v1.5) + ChromaDB
4. RAG system with Ollama (temp=0.1 for factual answers)
5. Test on all 8 wells, optimize chunk size

**Target:** <10s per query, >90% accuracy

### Phase 2: Sub-Challenge 2 (Week 2, 20%)
1. Parameter extraction with Pydantic validation
2. Query RAG for table chunks
3. Ollama JSON mode for structured output
4. Export in NodalAnalysis.py format

**Target:** <15s per well, <5% error vs manual

### Phase 3: Sub-Challenge 3 (Week 3, 30%)
1. Nodal analysis wrapper
2. LangGraph agent with tools (query, extract, analyze, list)
3. ReAct agent optimized for ≤3 tool calls
4. End-to-end testing

**Target:** <30s end-to-end, >95% success rate

### Phase 4: Bonus (Week 4, Optional)
1. Vision model (Moondream2 or Florence-2)
2. Multimodal fusion with fallback logic

### Phase 5: Polish (Days 29-30)
1. Code cleanup, docstrings, type hints
2. README, demo video (<10 min)
3. Full test suite, package submission

---

## TOC Extraction: Lessons Learned

**Achievement:** Built a robust TOC extraction system that achieves 100% success (14/14 PDFs) across diverse formats.

**Key Insights:**

1. **Docling's limitations:**
   - Aggressive table detection can corrupt clean dotted formats
   - Solution: PyMuPDF fallback preserves original text structure

2. **Pattern diversity:**
   - Markdown tables (2, 3, 4 columns)
   - Dotted format: `1.1 Title ........ 5`
   - Multi-line format: Section on one line, title+page on next
   - Space-separated: `1.1  Title     5`

3. **Adaptive table parsing:**
   - Don't assume column order
   - Intelligently detect: section column, title column, page column
   - Handle combined columns (title + dots + page in single column)

4. **Infinite loop pitfalls:**
   - Always track whether match was found in lookahead loops
   - Explicitly increment counter when no match to avoid getting stuck

5. **Keyword matching:**
   - Search for both "contents" and "content"
   - Use word boundaries to avoid false matches in longer words

**Code Reference:**
- `scripts/robust_toc_extractor.py:208-267` - Multi-line dotted extractor with infinite loop fix
- `scripts/robust_toc_extractor.py:72-158` - Adaptive table parser
- `scripts/analyze_all_tocs.py:244-267` - PyMuPDF fallback logic

---

## Important Files

**Before coding:** Run `notebooks/01_data_exploration.ipynb` to understand actual data format

**Plans:** `.claude/tasks/` - Full implementation plans with hour-by-hour breakdowns
**Quick start:** `START_HERE.md` - Resume guide
**Dataset scan:** `outputs/exploration/quick_scan_summary.json`
**TOC Analysis:** `outputs/toc_analysis/toc_analysis_results.json` - Metadata for 14 extracted TOCs

---

## Common Issues

**Virtual environment not activated:** Always activate first: `venv\Scripts\activate`

**Jupyter not responding:** Check with `ps aux | grep jupyter`, restart with `cd notebooks && jupyter notebook`

**Ollama not running:** Check `ollama --version`, pull model with `ollama pull llama3.2:3b`

**Windows path spaces:** Always quote paths: `cd "C:/Users/Thai Phi/Downloads/Hackathon"`

**Unicode errors:** Use ASCII alternatives (already fixed in `scripts/quick_explore.py`)

**Docling corrupts TOC:** Use PyMuPDF fallback (see `scripts/test_with_fallback.py`)

**TOC extraction fails:** Check if TOC uses unusual format, extend `RobustTOCExtractor` patterns

---

## Testing & Performance Targets

**TDD Approach:** Write test first → minimal code → refactor → repeat

**Performance Targets:**
- Sub-Challenge 1: <10s per query, >90% accuracy
- Sub-Challenge 2: <15s per well, <5% error
- Sub-Challenge 3: <30s end-to-end, ≤3 tool calls, >95% success
- Overall: <45s total, <10 min setup

---

## Development Tips

1. **Start with Well 5 (NLW-GT-03)** - best quality data, most comprehensive
2. **Run Jupyter exploration BEFORE coding** - see actual data format first
3. **Test on CPU only** - judges don't have GPU
4. **Keep chunks small** - better for retrieval
5. **Use low temperature** - factual answers (0.1)
6. **Validate everything** - use Pydantic models
7. **Handle errors gracefully** - judges will test edge cases
8. **Document clearly** - judges need to understand your approach
9. **Optimize for judge experience** - easy install, clear output
10. **Commit often** - use Conventional Commits format
11. **Leverage TOC extraction** - use extracted structure for better chunking
12. **Test fallback strategies** - PyMuPDF when Docling fails

---

## Current State

**✅ Completed:**
- Virtual environment setup at `venv/`
- Dependencies installed (docling, jupyter, pandas, torch)
- Quick scan of 8 wells, 103 PDFs identified
- **TOC Extraction System: 100% success (14/14 PDFs)**
  - `scripts/analyze_all_tocs.py` - Extract TOC sections
  - `scripts/robust_toc_extractor.py` - Core extraction class
  - `scripts/test_robust_extractor.py` - Validation tests
  - `scripts/test_with_fallback.py` - PyMuPDF fallback demo
  - `outputs/toc_analysis/` - 14 extracted TOC sections

**⏳ Next Steps:**
1. Build document parser with TOC-aware chunking
2. Set up ChromaDB with nomic-embed-text-v1.5
3. Implement RAG system with Ollama
4. Test on Well 5

---

## Key Success Factors

1. **Focus on Sub-Challenge 1 first** - it's 50% of grade
2. **Use Pydantic for validation** - ensures correct output format
3. **Test on all training wells** - don't overfit to one well
4. **Optimize for CPU** - no GPU available for judges
5. **Clear documentation** - judges need to run your code
6. **Handle failures gracefully** - robust error handling with fallbacks
7. **Fast execution** - <45 seconds total is target
8. **Easy setup** - judges must be able to install in <10 min
9. **Leverage TOC structure** - use extracted TOC for better document understanding
10. **Data-driven development** - analyze formats first, then build extractors
