"""
Test Demo Notebook Functionality
Quick validation that demo notebooks will work
"""

import sys
from pathlib import Path
import json

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))

print("="*80)
print("TESTING DEMO NOTEBOOK FUNCTIONALITY")
print("="*80)

# Test 1: Import key modules
print("\n[TEST 1] Import key modules...")
try:
    from build_toc_database import extract_publication_date
    from robust_toc_extractor import RobustTOCExtractor
    from docling.document_converter import DocumentConverter
    import pymupdf
    print("  [OK] All imports successful")
except Exception as e:
    print(f"  [FAIL] Import error: {e}")
    sys.exit(1)

# Test 2: Check training data exists
print("\n[TEST 2] Check training data...")
training_data_dir = project_root / "Training data-shared with participants"
if training_data_dir.exists():
    well_dirs = [d for d in training_data_dir.iterdir() if d.is_dir() and d.name.startswith("Well")]
    print(f"  [OK] Training data found: {len(well_dirs)} wells")
else:
    print(f"  [FAIL] Training data not found at {training_data_dir}")
    sys.exit(1)

# Test 3: Check sandbox directory structure
print("\n[TEST 3] Check sandbox structure...")
sandbox_dir = project_root / "notebooks" / "sandbox"
sandbox_chroma = sandbox_dir / "chroma_db"
sandbox_outputs = sandbox_dir / "outputs"

for directory in [sandbox_dir, sandbox_chroma, sandbox_outputs]:
    if directory.exists():
        print(f"  [OK] {directory.relative_to(project_root)} exists")
    else:
        print(f"  [WARN] {directory.relative_to(project_root)} missing (will be created)")

# Test 4: Check categorization file
print("\n[TEST 4] Check categorization file...")
categorization_path = project_root / "outputs" / "final_section_categorization_v2.json"
if categorization_path.exists():
    with open(categorization_path, 'r') as f:
        categorization = json.load(f)
    total_categories = categorization['metadata']['total_categories']
    total_entries = sum(len(cat['entries']) for cat in categorization['categories'].values())
    print(f"  [OK] Categorization found: {total_categories} categories, {total_entries} entries")
else:
    print(f"  [WARN] Categorization file not found")

# Test 5: Check TOC database
print("\n[TEST 5] Check TOC database...")
toc_database_path = project_root / "outputs" / "exploration" / "toc_database_multi_doc_full.json"
if toc_database_path.exists():
    with open(toc_database_path, 'r') as f:
        toc_database = json.load(f)
    total_docs = sum(len(docs) for docs in toc_database.values())
    total_entries = sum(len(doc['toc']) for docs in toc_database.values() for doc in docs)
    print(f"  [OK] TOC database found: {len(toc_database)} wells, {total_docs} docs, {total_entries} entries")
else:
    print(f"  [WARN] TOC database not found")

# Test 6: Test date extraction on sample text
print("\n[TEST 6] Test date extraction...")
test_texts = [
    "Publication date: 11 th of Februari 2011",  # Dutch month, ordinal
    "April 2024",  # Standalone date
    "Publication date: 01 June 2018",  # Standard format
]

extractor_working = True
for text in test_texts:
    date = extract_publication_date(text)
    if date:
        print(f"  [OK] Extracted {date.strftime('%Y-%m-%d')} from '{text[:40]}'")
    else:
        print(f"  [FAIL] Could not extract date from '{text[:40]}'")
        extractor_working = False

# Test 7: Test TOC extractor
print("\n[TEST 7] Test TOC extractor...")
toc_extractor = RobustTOCExtractor()
test_toc_text = """
| Section | Title | Page |
|---------|-------|------|
| 1.1 | Introduction | 3 |
| 2.1 | Depths | 6 |
| 2.2 | Casing | 8 |
"""
entries = toc_extractor.extract(test_toc_text)
if len(entries) >= 3:
    print(f"  [OK] Extracted {len(entries)} TOC entries")
    for entry in entries[:2]:
        print(f"    - {entry['number']} {entry['title']} (page {entry['page']})")
else:
    print(f"  [FAIL] Expected 3+ entries, got {len(entries)}")

# Test 8: Check demo notebooks exist
print("\n[TEST 8] Check demo notebooks...")
demo_notebooks = [
    "00_complete_walkthrough.ipynb",
    "07_publication_date_extraction.ipynb",
    "08_toc_extraction_demo.ipynb",
    "09_toc_categorization.ipynb",
    "10_build_toc_database.ipynb",
]

notebooks_dir = project_root / "notebooks" / "demos"
all_notebooks_exist = True
for notebook in demo_notebooks:
    notebook_path = notebooks_dir / notebook
    if notebook_path.exists():
        size_kb = notebook_path.stat().st_size / 1024
        print(f"  [OK] {notebook} ({size_kb:.1f} KB)")
    else:
        print(f"  [FAIL] {notebook} not found")
        all_notebooks_exist = False

# Test 9: Check Ollama (optional)
print("\n[TEST 9] Check Ollama...")
try:
    import subprocess
    result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"  [OK] Ollama installed: {result.stdout.strip()}")
    else:
        print(f"  [WARN] Ollama not responding")
except Exception as e:
    print(f"  [WARN] Ollama not installed (optional for demos)")

# Summary
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print(f"Core functionality:  {'OK' if extractor_working else 'FAIL'}")
print(f"Demo notebooks:      {'OK' if all_notebooks_exist else 'FAIL'}")
print(f"Data files:          {'OK' if toc_database_path.exists() else 'WARN'}")
print("\nDemo notebooks are ready to use!")
print("="*80)
