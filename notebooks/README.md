# Notebooks Guide

This folder contains Jupyter notebooks for exploring, testing, and demonstrating the RAG system.

## Available Notebooks

### 📊 `01_data_exploration.ipynb` - Dataset Analysis
Initial dataset exploration and understanding.
- Scan well reports structure
- Test Docling parser
- Extract sample tables
- **Status**: ✅ Complete

### 📝 `05_test_summarization.ipynb` - **SUMMARIZATION DEMO (NEW!)**
**Sub-Challenge 1: Complete report summarization system**
- Multi-PDF indexing (all PDFs in Well report/ folder)
- User prompt-driven summarization with word limits
- Context-aware table prioritization
- Word limit accuracy testing
- Export summaries to JSON
- **Status**: ✅ Ready to use

### 🔍 `04_interactive_rag_demo.ipynb` - **Q&A DEMO**
Complete interactive RAG Q&A system with rich formatting.
- Initialize RAG with Ollama + ChromaDB
- Index Well 5 interactively
- Test queries with beautiful output
- Batch testing and performance metrics
- Export results to JSON
- **Status**: ✅ Ready to use

### 🧪 `03_test_rag_system.ipynb` - Basic RAG Test
Simpler RAG testing without rich formatting (good for understanding core pipeline).
- **Status**: ✅ Complete

## Quick Start

### 1. Prerequisites
```bash
# Start ChromaDB (required)
docker-compose up -d chromadb

# Verify Ollama (required for RAG demos)
ollama list  # Should show llama3.2:3b
```

### 2. Launch Jupyter
```bash
cd notebooks
jupyter notebook
```

### 3. Open Interactive Demo (Recommended)
- Open `04_interactive_rag_demo.ipynb`
- Run cells from top to bottom (`Shift + Enter`)
- Or run all: `Kernel → Restart & Run All`

## What Each Notebook Does

### 📊 Data Exploration (`01_data_exploration.ipynb`)
- Scan all 8 wells and count files
- Test Docling parsing on Well 5
- Extract tables with MD, TVD, ID data
- Compare multiple wells
- **Output**: `outputs/exploration/`

### 🔍 Interactive Demo (`04_interactive_rag_demo.ipynb`)
- Initialize complete RAG system
- Index Well 5 (63 chunks from 16 pages)
- Test queries with rich formatted output
- Batch testing (6 standard queries)
- Performance benchmarking
- Section type mapping visualization
- **Output**: `outputs/rag/test_results.json`

### 🧪 Basic Test (`03_test_rag_system.ipynb`)
- Same as interactive demo but simpler output
- Good for understanding the pipeline
- No rich formatting

## Expected Runtime

| Notebook | Time | Description |
|----------|------|-------------|
| `01_data_exploration.ipynb` | ~10 min | Dataset analysis |
| `04_interactive_rag_demo.ipynb` | ~15 min | Full RAG demo |
| `03_test_rag_system.ipynb` | ~10 min | Basic RAG test |

## Demo Features (Interactive Notebook)

✨ **Rich Formatting**
- Color-coded outputs
- Tables and panels
- Progress indicators

📈 **Performance Metrics**
- Query latency breakdown
- Batch testing statistics
- Benchmarking (5 iterations)

🎯 **Section Mapping**
- Query → Section type visualization
- Retrieval precision analysis

💾 **Export Functionality**
- Save results to JSON
- Share with team

## Troubleshooting

### ChromaDB Connection Error
```bash
# Error: "Connection refused" or "Could not connect to ChromaDB"
# Fix: Start ChromaDB container
docker-compose up -d chromadb

# Verify it's running
docker-compose ps chromadb
```

### Ollama Model Not Found
```bash
# Error: "model 'llama3.2:3b' not found"
# Fix: Pull the model
ollama pull llama3.2:3b

# Verify
ollama list
```

### Import Errors
```python
# Error: "No module named 'rag_system'"
# Fix: Check sys.path in first cell
import sys
sys.path.insert(0, '../src')
```

### Rich Module Not Found
```bash
# Error: "No module named 'rich'"
# Fix: Install rich for pretty output
pip install rich
```

### ModuleNotFoundError (Other)
```bash
# Install all dependencies
pip install -r ../requirements.txt
```

## Next Steps

After running the interactive demo:

**✅ Sub-Challenge 1 Complete** - RAG system working with 100% retrieval precision!

**Next:**
1. **Sub-Challenge 2 (20%)**: Extract MD, TVD, ID parameters
   - Use RAG to find casing/depth sections
   - Structured extraction with Pydantic
   - Export to NodalAnalysis.py format

2. **Sub-Challenge 3 (30%)**: Agentic workflow
   - LangGraph agent with tools
   - Autonomous: query → extract → analyze
   - End-to-end automation

## Output Files

Notebooks generate:
- `../outputs/rag/test_results.json` - Query test results from interactive demo
- `../outputs/exploration/` - Dataset exploration outputs

---

**Ready to try the demo? Open `04_interactive_rag_demo.ipynb` 🚀**
