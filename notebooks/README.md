# Notebooks Guide

Production-ready Jupyter notebooks for the Well Report RAG QA System.

## Available Notebooks

### Core System Notebooks

#### 📚 `07_production_rag_qa_demo.ipynb` - **PRODUCTION RAG QA SYSTEM (NEW!)** ⭐
**Complete guide to the production RAG QA system**
- System architecture overview
- Database statistics (5,258 documents, 8 wells)
- Query examples (basic, well-specific, section-filtered)
- Source citation deep dive
- Performance testing and benchmarks
- Use cases and advanced features
- **Status**: Production Ready
- **Runtime**: <3 minutes

#### 🎯 `06_sub_challenge_1_guide.ipynb` - **SUB-CHALLENGE 1 GRADING GUIDE** ⭐
**Official grading guide for Sub-Challenge 1 (50% of total grade)**
- Grading criteria breakdown (Answer Quality 40%, Source Citation 30%, Response Time 20%, Robustness 10%)
- Sample evaluation queries with expected results
- How to use section filters
- Submission checklist
- **Status**: Production Ready
- **Runtime**: <2 minutes

#### 🔍 `04_interactive_rag_demo.ipynb` - **INTERACTIVE Q&A DEMO**
**Interactive RAG Q&A system with rich formatting**
- Production system initialization
- Example queries with beautiful output
- Section-filtered queries
- Performance benchmarking
- **Status**: Production Ready
- **Runtime**: <3 minutes

### Supporting Notebooks

#### 📊 `01_data_exploration_v1.ipynb` - Dataset Analysis
Initial dataset exploration and understanding.
- Scan well reports structure
- Test Docling parser
- Extract sample tables
- **Status**: Complete
- **Runtime**: ~10 minutes

#### 🧪 `03_test_rag_system.ipynb` - Basic RAG Test
Simpler RAG testing without rich formatting (good for understanding core pipeline).
- **Status**: Complete
- **Runtime**: <2 minutes

#### 📝 `05_test_summarization.ipynb` - Summarization Demo
Complete report summarization system.
- Multi-PDF indexing
- User prompt-driven summarization with word limits
- Context-aware table prioritization
- **Status**: Complete
- **Runtime**: ~5 minutes

### Demo Notebooks (`demos/` folder)

#### `08_toc_extraction_demo.ipynb` - TOC Extraction
Demonstrates Table of Contents extraction from PDFs.
- **Status**: Complete

#### `09_toc_categorization.ipynb` - Section Type Mapping
Shows how TOC entries are mapped to section types.
- **Status**: Complete

#### `10_build_toc_database.ipynb` - TOC Database Building
Builds the TOC-based document index.
- **Status**: Complete

---

## Quick Start

### 1. Prerequisites

**No Docker required!** The system uses a pre-indexed local ChromaDB database.

```bash
# Verify Ollama is installed and running
ollama list  # Should show llama3.2:3b

# If not, pull the model
ollama pull llama3.2:3b
```

**Required:**
- Ollama with Llama 3.2 3B model
- Pre-indexed ChromaDB database at `../chroma_db_toc_aware/`

**Optional:**
- Rich library for beautiful output (already in requirements.txt)

### 2. Launch Jupyter

```bash
cd notebooks
jupyter notebook
```

### 3. Start with Production Demo (Recommended)

**Option A: Comprehensive Guide**
- Open `07_production_rag_qa_demo.ipynb`
- Complete production system walkthrough
- All features and use cases

**Option B: Grading Guide**
- Open `06_sub_challenge_1_guide.ipynb`
- Understand evaluation criteria
- See sample queries with grading

**Option C: Interactive Demo**
- Open `04_interactive_rag_demo.ipynb`
- Rich formatted output
- Quick testing

Run cells from top to bottom with `Shift + Enter`, or run all with `Kernel → Restart & Run All`.

---

## System Architecture

### Production RAG QA System

The notebooks use `WellReportQASystem` from `src/rag_qa_system.py`:

```python
from rag_qa_system import WellReportQASystem

# Initialize with pre-indexed database
qa_system = WellReportQASystem(
    chroma_dir="../chroma_db_toc_aware",
    collection_name="well_reports_toc_aware",
    llm_model="llama3.2:3b",
    temperature=0.1,
    top_k=5,
    verbose=True
)

# Query the system
result = qa_system.query("What is the total depth of Well 5?")
print(result.answer)
```

**Key Features:**
- Pre-indexed database: 5,258 documents across 8 wells
- TOC-aware metadata: 93.1% section type coverage
- LangChain 1.0+ API (modern direct approach)
- Local ChromaDB (no Docker required)
- Section filtering: casing, drilling, production, etc.
- Source citation with metadata

---

## What Each Notebook Does

### 📚 Production Demo (`07_production_rag_qa_demo.ipynb`)
**Purpose**: Complete guide to the production RAG QA system

**Covers**:
1. System architecture and key features
2. Database statistics and coverage analysis
3. Query examples (basic, filtered, combined)
4. Source citation and metadata
5. Performance testing
6. Use cases: technical Q&A, cross-well comparison, section-specific retrieval

**Output**: Understanding of production system capabilities

---

### 🎯 Grading Guide (`06_sub_challenge_1_guide.ipynb`)
**Purpose**: Official evaluation criteria for Sub-Challenge 1 (50% of grade)

**Covers**:
1. Grading criteria breakdown with percentages
2. Sample evaluation queries
3. How to interpret results
4. Using section filters for better answers
5. Submission checklist

**Output**: Understanding of how your system will be evaluated

---

### 🔍 Interactive Demo (`04_interactive_rag_demo.ipynb`)
**Purpose**: Interactive Q&A with beautiful formatted output

**Covers**:
- Production system initialization
- Database statistics visualization
- Example queries with rich formatting
- Section-filtered queries
- Performance benchmarking (5 iterations)

**Output**: Interactive testing environment

---

### 📊 Data Exploration (`01_data_exploration_v1.ipynb`)
**Purpose**: Understand the training dataset

**Covers**:
- Scan all 8 wells and count files
- Test Docling parsing on Well 5
- Extract tables with MD, TVD, ID data
- Compare multiple wells

**Output**: `outputs/exploration/`

---

### 🧪 Basic Test (`03_test_rag_system.ipynb`)
**Purpose**: Simple RAG pipeline understanding

**Covers**:
- Same as interactive demo but without rich formatting
- Good for understanding core pipeline
- Minimal dependencies

**Output**: Basic query results

---

## Expected Runtime

All notebooks use the pre-indexed database, so no indexing time required!

| Notebook | Time | Description |
|----------|------|-------------|
| `07_production_rag_qa_demo.ipynb` | <3 min | Production system guide |
| `06_sub_challenge_1_guide.ipynb` | <2 min | Grading criteria |
| `04_interactive_rag_demo.ipynb` | <3 min | Interactive demo |
| `03_test_rag_system.ipynb` | <2 min | Basic RAG test |
| `01_data_exploration_v1.ipynb` | ~10 min | Dataset analysis |
| `05_test_summarization.ipynb` | ~5 min | Summarization demo |

**Total time to run all core demos: <10 minutes!**

---

## Database Statistics

The pre-indexed ChromaDB database contains:

- **Total documents**: 5,258 chunks
- **Wells covered**: 8 wells (Well 1 through Well 8)
- **Section type coverage**: 93.1% of documents have section type metadata
- **Section types**: casing, drilling, production, completion, testing, geology, well_design, summary, appendix, operational, other
- **Embedding model**: nomic-embed-text-v1.5 (137M parameters)
- **Storage**: Local persistent ChromaDB at `../chroma_db_toc_aware/`

---

## Demo Features

### Production RAG QA System Features

**Query Capabilities**:
- Basic queries: "What is the total depth of Well 5?"
- Well-specific queries with filters
- Section-filtered queries: "Describe the casing program" (filter: section_type="casing")
- Combined filters: well_name + section_type

**Source Citation**:
- Every answer includes source documents
- Metadata: well_name, section_title, section_type, page_number
- Direct references for verification

**Performance**:
- Query latency: <10 seconds (target)
- Streaming support (enabled)
- Configurable temperature and top_k

**Rich Formatting** (Interactive Demo):
- Color-coded outputs
- Tables and panels
- Progress indicators
- Statistics visualization

---

## Troubleshooting

### Ollama Model Not Found
```bash
# Error: "model 'llama3.2:3b' not found"
# Fix: Pull the model
ollama pull llama3.2:3b

# Verify
ollama list
```

### ChromaDB Not Found
```bash
# Error: "Collection 'well_reports_toc_aware' not found"
# Fix: Ensure the pre-indexed database exists
ls ../chroma_db_toc_aware/

# If missing, run the indexer (from project root):
python scripts/index_all_wells.py
```

### Import Errors
```python
# Error: "No module named 'rag_qa_system'"
# Fix: Check sys.path in first cell (already included in notebooks)
import sys
sys.path.insert(0, '../src')
```

### Rich Module Not Found
```bash
# Error: "No module named 'rich'"
# Fix: Install from requirements
pip install rich

# Or install all dependencies:
pip install -r ../requirements.txt
```

### Ollama Connection Error
```bash
# Error: "Could not connect to Ollama"
# Fix: Start Ollama service
# Windows: Ollama should auto-start, check system tray
# Mac/Linux: ollama serve

# Verify it's running:
curl http://localhost:11434/api/tags
```

---

## Next Steps

After running the production demo notebooks:

### Sub-Challenge 1 Complete (50%)
The RAG QA system is production-ready!

### Next: Sub-Challenge 2 (20%)
**Parameter Extraction**
- Extract MD, TVD, ID parameters from documents
- Use RAG to find casing/depth sections
- Structured extraction with Pydantic
- Export to NodalAnalysis.py format

### Next: Sub-Challenge 3 (30%)
**Agentic Workflow**
- LangGraph agent with tools
- Autonomous: query → extract → analyze
- End-to-end automation

---

## Output Files

Notebooks may generate:
- `../outputs/rag/test_results.json` - Query test results
- `../outputs/exploration/` - Dataset exploration outputs

---

## Key Advantages of Production System

1. **No Docker required** - Local ChromaDB, easier setup
2. **Pre-indexed database** - No waiting for indexing (5,258 docs ready)
3. **TOC-aware metadata** - 93.1% coverage enables intelligent filtering
4. **Modern API** - LangChain 1.0+ direct approach (not deprecated chains)
5. **Fast queries** - <10 seconds typical latency
6. **High quality** - Section filtering improves answer relevance
7. **Source citation** - Every answer includes verifiable sources
8. **Production ready** - Real system, not demo code

---

**Ready to explore? Start with `07_production_rag_qa_demo.ipynb` or `06_sub_challenge_1_guide.ipynb`!**
