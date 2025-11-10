# Sandbox Directory

This directory provides an **isolated environment** for demo notebooks to run without affecting the production RAG system.

## Purpose

- **Safe Learning**: Experiment with TOC extraction, categorization, and database building without breaking production
- **Clean Separation**: All demo outputs go here, not to main `outputs/` or `chroma_db/`
- **Easy Reset**: Delete this directory to start fresh

## Structure

```
sandbox/
├── chroma_db/          # Isolated ChromaDB (separate from production)
├── outputs/            # Demo outputs
│   ├── toc_analysis/   # Extracted TOC sections
│   └── exploration/    # TOC databases
└── README.md           # This file
```

## What Uses This

Demo notebooks in `notebooks/demos/`:
- `00_complete_walkthrough.ipynb` - Full workflow demo
- `07_publication_date_extraction.ipynb` - Date extraction demo
- `08_toc_extraction_demo.ipynb` - TOC extraction demo
- `09_toc_categorization.ipynb` - Categorization demo
- `10_build_toc_database.ipynb` - Database building demo

## Isolation Guarantees

✅ **Separate ChromaDB**: Uses `notebooks/sandbox/chroma_db/` (not `chroma_db/`)
✅ **Separate Outputs**: Uses `notebooks/sandbox/outputs/` (not `outputs/`)
✅ **Read-Only Training Data**: Only reads from `Training data-shared with participants/`
✅ **No Production Impact**: Cannot affect main RAG system or databases

## Production vs Sandbox

| Component | Production | Sandbox |
|-----------|-----------|---------|
| ChromaDB | `chroma_db/` | `notebooks/sandbox/chroma_db/` |
| TOC Database | `outputs/exploration/toc_database_multi_doc_full.json` | `notebooks/sandbox/outputs/exploration/toc_database_demo.json` |
| TOC Analysis | `outputs/toc_analysis/` | `notebooks/sandbox/outputs/toc_analysis/` |
| Training Data | `Training data-shared with participants/` (read-only) | Same (read-only) |

## Reset Sandbox

To start fresh:

```bash
# Delete all sandbox data
rm -rf notebooks/sandbox/chroma_db/*
rm -rf notebooks/sandbox/outputs/*

# Or delete entire sandbox and recreate
rm -rf notebooks/sandbox
mkdir -p notebooks/sandbox/{chroma_db,outputs/{toc_analysis,exploration}}
```

## Git Ignore

All sandbox data is git-ignored via `.gitignore`. Only this README and the `.gitignore` file are committed.
