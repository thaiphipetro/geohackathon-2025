# GeoHackathon 2025: Automated Well Performance Analysis

**Team:** [Your Team Name]
**Challenge:** SPE Europe Energy GeoHackathon 2025
**Goal:** Build an agentic AI workflow for automating well completion data extraction and performance analysis

---

## 🎯 Challenge Overview

Create an AI system that:
1. **Summarizes well completion reports** (Sub-Challenge 1: 50%)
2. **Extracts well parameters** (MD, TVD, ID) (Sub-Challenge 2: 20%)
3. **Automatically runs nodal analysis** (Sub-Challenge 3: 30%)
4. **Bonus:** Extracts data from diagrams using vision models

---

## 🏗️ Tech Stack

- **Document Processing:** Docling + RapidOCR
- **Embeddings:** nomic-embed-text-v1.5 (137M params)
- **Vector Store:** ChromaDB
- **LLM:** Ollama + Llama 3.2 3B
- **Agent Framework:** LangGraph
- **Vision (Bonus):** Moondream2 (1.6B params)

**All components:** ✅ Open source | ✅ CPU-friendly | ✅ Self-hosted

---

## 📁 Project Structure

```
geohackathon/
├── .claude/                      # Claude Code project files
│   └── tasks/                    # Implementation plans
├── src/                          # Source code
│   ├── document_parser.py        # PDF parsing with OCR
│   ├── embeddings.py             # Embedding & vector store
│   ├── rag_system.py             # RAG query system
│   ├── parameter_extractor.py    # Structured parameter extraction
│   ├── agent.py                  # LangGraph agent
│   └── vision_extractor.py       # Vision model (bonus)
├── tests/                        # Test suites
├── notebooks/                    # Jupyter notebooks for exploration
├── scripts/                      # Utility scripts
├── outputs/                      # Generated outputs
├── Training data-shared with participants/  # Well reports (not in git)
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Docker setup
├── CLAUDE.md                     # Project instructions
└── README.md                     # This file
```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone repository
git clone <your-repo-url>
cd geohackathon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Ollama

Download from: https://ollama.ai

```bash
# Pull Llama 3.2 3B model
ollama pull llama3.2:3b
```

### 3. Add Training Data

```bash
# Place training data in project root
Training data-shared with participants/
├── Well 1/
├── Well 2/
├── ...
└── NodalAnalysis.py
```

### 4. Explore Data (Optional)

```bash
# Quick exploration
python scripts/quick_explore.py

# Or use Jupyter notebook
cd notebooks
jupyter notebook
# Open 01_data_exploration.ipynb
```

### 5. Run Sub-Challenges

```bash
# Sub-Challenge 1: Summarization
python examples/sub_challenge_1.py

# Sub-Challenge 2: Parameter Extraction
python examples/sub_challenge_2.py --well "NLW-GT-03"

# Sub-Challenge 3: Full Agentic Workflow
python examples/sub_challenge_3.py
```

---

## 📊 Dataset

- **8 Wells** from Dutch geothermal projects
- **93 PDFs** (well reports, technical logs, tests)
- **17 Excel files** (production data)
- **9 Word documents** (well summaries)
- **Source:** nlog.nl (Dutch subsurface portal)

---

## 🎯 Implementation Status

### ✅ Completed
- [x] Project setup & structure
- [x] Data exploration notebook
- [x] Implementation plans
- [x] Git version control

### 🚧 In Progress
- [ ] Sub-Challenge 1: RAG system (Day 1-7)
- [ ] Sub-Challenge 2: Parameter extraction (Week 2)
- [ ] Sub-Challenge 3: Agentic workflow (Week 3)
- [ ] Bonus: Vision model (Week 4)

### 📅 Timeline
- **Week 1:** Sub-Challenge 1 (50% of grade)
- **Week 2:** Sub-Challenge 2 (20% of grade)
- **Week 3:** Sub-Challenge 3 (30% of grade)
- **Week 4:** Bonus + Final polish

---

## 📚 Documentation

- **Implementation Plans:** `.claude/tasks/`
- **Data Analysis:** `.claude/tasks/training-data-structure-analysis.md`
- **Sub-Challenge 1 Plan:** `.claude/tasks/sub-challenge-1-detailed-plan.md`
- **Exploration Notebook:** `notebooks/01_data_exploration.ipynb`

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_parser.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 🐋 Docker Setup

```bash
# Start services (Ollama + ChromaDB)
docker-compose up -d

# Stop services
docker-compose down
```

---

## 📦 Dependencies

See `requirements.txt` for full list.

**Core:**
- docling[rapidocr] - Document parsing with OCR
- sentence-transformers - Embeddings
- chromadb - Vector database
- ollama - LLM inference
- langchain, langgraph - Agent framework

**Development:**
- jupyter - Notebooks
- pytest - Testing
- black - Code formatting
- flake8 - Linting

---

## 🏆 Submission Requirements

- [x] Python code with comments
- [ ] README (this file)
- [ ] Requirements file
- [ ] Demo video (<10 minutes)
- [ ] Example outputs

---

## 📝 Best Practices

Following guidelines from `CLAUDE.md`:

- **TDD:** Write tests before implementation
- **Type hints:** All functions typed
- **Documentation:** Clear docstrings
- **Code quality:** Black + flake8 passing
- **Git commits:** Conventional Commits format

---

## 🔒 Constraints Compliance

✅ **Models <500M parameters**
✅ **CPU-only (no GPU required)**
✅ **Pure pip install (no system dependencies)**
✅ **Fully open source**
✅ **Runs locally (data security)**

---

## 🤝 Contributing

This is a hackathon project. For team members:

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -m "feat: add feature"`
3. Push and create PR: `git push origin feature/your-feature`

---

## 📜 License

[Add your license here]

---

## 🙏 Acknowledgments

- **SPE Europe** - For organizing the GeoHackathon
- **TNO** - For providing the dataset and challenge
- **nlog.nl** - For well data access
- **Open source community** - For amazing tools

---

## 📧 Contact

[Your contact information]

---

**Status:** 🚧 In Development
**Last Updated:** 2025-01-04

---

## 🚀 Let's Build Something Great!
