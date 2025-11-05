# Exploration Notebooks

This folder contains Jupyter notebooks for exploring and understanding the training data.

## Quick Start

### 1. Install Jupyter
```bash
pip install jupyter notebook
```

### 2. Launch Notebook
```bash
# From the project root directory
cd notebooks
jupyter notebook
```

### 3. Open the Exploration Notebook
- Open `01_data_exploration.ipynb`
- Run cells from top to bottom

## What This Notebook Does

The data exploration notebook helps you:

✅ **Understand the dataset structure**
- Scan all 8 wells
- Count files by type
- Identify key documents

✅ **Test Docling parsing**
- Parse Well 5 EOWR report (best quality)
- Extract text, tables, images
- Test OCR capability

✅ **Explore well reports**
- View extracted text
- Inspect tables (where MD, TVD, ID are!)
- Search for well identifiers

✅ **Understand NodalAnalysis.py**
- See the exact format needed
- Compare with extracted data

✅ **Compare multiple wells**
- Parse Wells 1, 5, 7
- See variations in format
- Identify challenges

## Output

The notebook saves:
- `outputs/exploration/*.md` - Extracted text files
- `outputs/exploration/*.csv` - Extracted tables
- `outputs/exploration/exploration_findings.md` - Summary report

## Expected Runtime

- **Full notebook:** ~10-15 minutes
- **Single well parsing:** ~1-2 minutes
- **Multiple wells:** ~5-10 minutes

## Tips

1. **Start with Well 5** - It's the best documented
2. **Focus on tables** - They contain MD, TVD, ID data
3. **Look for "casing" or "completion" tables** - These are key
4. **Check table formats** - Column names may vary

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install docling docling[rapidocr] pandas openpyxl tabulate rich
```

### "Notebook not found"
Make sure you're in the `notebooks/` directory:
```bash
cd "C:\Users\Thai Phi\Downloads\Hackathon\notebooks"
```

### Parsing takes too long
This is normal for the first parse. Models are downloading.
Subsequent parses will be faster.

### OCR not working
Install RapidOCR separately:
```bash
pip install rapidocr-onnxruntime
```

## Next Steps

After running this notebook, you'll be ready to:
1. Start Day 1 implementation (document parser)
2. Build the RAG system
3. Extract parameters for Sub-Challenge 2

---

**Ready to explore? Open `01_data_exploration.ipynb` and get started!** 🚀
