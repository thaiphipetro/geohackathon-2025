# Scripts Directory

Collection of scripts for the GeoHackathon 2025 project.

## Structure

```
scripts/
├── Production Scripts (at root level)
│   ├── quick_explore.py                # Quick dataset exploration
│   ├── check_chromadb_status.py       # Check ChromaDB status
│   ├── check_well7_chunks.py          # Validate Well 7 chunks
│   ├── create_improved_categorization.py  # Categorization logic
│   ├── delete_well7_chunks.py         # Delete specific chunks
│   └── index_all_wells.py             # Index all wells for RAG
│
├── toc_extraction/                    # Production TOC system
│   ├── core/                          # Main TOC scripts
│   ├── tests/                         # Integration tests
│   ├── archive/                       # Legacy scripts
│   └── README.md                      # Detailed documentation
│
├── debug/                             # Debug utilities (7 scripts)
│   └── README.md
├── tests/                             # Experimental tests (7 scripts)
│   └── README.md
└── utils/                             # Utility scripts (6 scripts)
    └── README.md
```

## Quick Start

### Data Exploration
```bash
# Quick scan of all wells
python scripts/quick_explore.py
```

### TOC Extraction (Main Workflow)
```bash
# Build complete TOC database (auto-discovers all wells)
python scripts/toc_extraction/core/build_multi_doc_toc_database_granite.py

# Validate database
python scripts/toc_extraction/core/validate_toc_database.py
```

Output: `outputs/exploration/toc_database_multi_doc_granite.json`

### RAG Indexing
```bash
# Index all wells for RAG queries
python scripts/index_all_wells.py
```

## Production Scripts (Root Level)

### quick_explore.py
Quick dataset scan showing PDF/Excel counts per well.

**Usage:**
```bash
python scripts/quick_explore.py
```

**Output:** `outputs/exploration/quick_scan_summary.json`

### index_all_wells.py
Index all wells into ChromaDB for RAG queries.

**Usage:**
```bash
python scripts/index_all_wells.py
```

### check_chromadb_status.py
Check ChromaDB collection status and document counts.

### check_well7_chunks.py
Validate Well 7 chunks in ChromaDB.

### create_improved_categorization.py
Create improved section categorization mapping.

### delete_well7_chunks.py
Delete Well 7 chunks from ChromaDB (for reindexing).

## TOC Extraction System

See `toc_extraction/README.md` for complete documentation.

**Main script:**
- `toc_extraction/core/build_multi_doc_toc_database_granite.py` - Auto-discovers wells and builds complete TOC database

**Features:**
- Auto-discovery of well folders
- Pattern-based categorization (13 categories)
- Smart routing (scanned → Granite VLM, native → text)
- 100% categorization coverage

## Experimental Scripts

### debug/
Debugging utilities for troubleshooting specific issues.
See `debug/README.md` for details.

### tests/
One-off test scripts for development.
See `tests/README.md` for details.

### utils/
Utility scripts for specific maintenance tasks.
See `utils/README.md` for details.

## Key Files

- **TOC Database:** `outputs/exploration/toc_database_multi_doc_granite.json`
- **Quick Scan:** `outputs/exploration/quick_scan_summary.json`
- **TOC Analysis:** `outputs/toc_analysis/` (14 extracted TOC sections)
- **Logs:** `outputs/logs/`

## Common Tasks

### Build TOC Database from Scratch
```bash
python scripts/toc_extraction/core/build_multi_doc_toc_database_granite.py
```

### Validate TOC Database
```bash
python scripts/toc_extraction/core/validate_toc_database.py
```

### Test Well 7 Extraction
```bash
python scripts/toc_extraction/tests/test_well7_granite_fixed.py
```

### Explore Dataset
```bash
python scripts/quick_explore.py
```

## Environment Setup

Always activate virtual environment first:
```bash
# Windows
cd "C:\Users\Thai Phi\Downloads\Hackathon"
venv\Scripts\activate

# Git Bash
source venv/Scripts/activate
```

## Notes

- **Production scripts** are at root level and in `toc_extraction/`
- **Experimental scripts** are organized in `debug/`, `tests/`, `utils/`
- **TOC system** supports auto-discovery of any number of wells
- **Main entry point:** `toc_extraction/core/build_multi_doc_toc_database_granite.py`

For detailed TOC system documentation, see `toc_extraction/README.md`.
