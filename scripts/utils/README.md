# Utility Scripts

Utility scripts for specific tasks and maintenance.

## Scripts

- **add_new_documents.py** - Add new documents to database
- **build_structure_only_database_parallel.py** - Build structure database in parallel
- **compare_prompts.py** - Compare different prompting strategies
- **discover_well_documents.py** - Discover well documents in dataset
- **validate_well7_extraction.py** - Validate Well 7 extraction results
- **validate_well_inventory.py** - Validate well inventory completeness

## Usage

Run utility scripts as needed:

```bash
cd scripts/utils
python discover_well_documents.py
```

## Production Scripts

For main production workflows, use:

```bash
# Quick dataset exploration
python scripts/quick_explore.py

# Build complete TOC database
python scripts/toc_extraction/core/build_multi_doc_toc_database_granite.py

# Index all wells for RAG
python scripts/index_all_wells.py
```

## Note

These utilities are for specific maintenance tasks and may require configuration or parameters. Check each script's source for usage details.
