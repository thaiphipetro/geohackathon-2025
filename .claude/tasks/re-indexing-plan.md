# Re-Indexing Plan: TOC-Enhanced Chunking

**Date:** 2025-11-09
**Priority:** HIGH
**Estimated Time:** 2-3 hours

---

## Problem Statement

### Current State

**Indexed Data (OLD):**
- Total: 8 PDFs, 294 chunks
- Only 1 PDF per well (many PDFs skipped!)
- Well 7: 0 chunks (FAILED)
- Indexing time: 57 minutes (slow!)

**Issues:**
1. ❌ Only 8 PDFs indexed, but we have TOC data for **14 PDFs**
2. ❌ Old indexing may not use TOC-enhanced chunking
3. ❌ Well 7 has 0 chunks
4. ❌ Some queries return 0 chunks (Well 1, Well 8)
5. ❌ Many PDFs were skipped

### What We Have Now

**TOC Extraction System:**
- ✅ TOC database: 9 wells (8 successful)
- ✅ TOC analysis: 14 PDFs with extracted TOCs
- ✅ 188 total TOC entries
- ✅ 100% success rate on TOC extraction
- ✅ Section-aware chunker ready
- ✅ TOC-enhanced parser ready

**PDFs with TOC Data:**

| Well | PDFs with TOC | Total TOC Entries |
|------|---------------|-------------------|
| Well 1 | 2 | 15 (6 + 9) |
| Well 2 | 2 | 18 (3 + 15) |
| Well 3 | 1 | 7 |
| Well 4 | 3 | 32 (13 + 11 + 8) |
| Well 5 | 2 | 33 (19 + 14) |
| Well 6 | 1 | 17 |
| Well 7 | 0 | 0 (scanned, no TOC) |
| Well 8 | 3 | 66 (26 + 20 + 20) |
| **Total** | **14** | **188** |

---

## Goal

**Re-index all wells using TOC-enhanced chunking to:**
1. Index ALL 14 PDFs (not just 8)
2. Use section-aware chunking (TOC-based)
3. Improve chunk quality and metadata
4. Fix Well 7 (try alternative approach)
5. Increase total chunks significantly
6. Improve retrieval accuracy

**Expected Outcome:**
- From: 8 PDFs, 294 chunks
- To: **14+ PDFs, 800-1200 chunks** (estimate)
- Better section metadata
- More accurate retrieval
- Well 7 with some chunks

---

## Implementation Plan

### Phase 1: Pre-Indexing Analysis (15 minutes)

#### Task 1.1: Analyze Current Index
```bash
# Check ChromaDB collection status
python scripts/check_chromadb_status.py

# View current chunks by well
python -c "
from src.vector_store import WellReportVectorStore
vs = WellReportVectorStore()
stats = vs.get_collection_stats()
print(stats)
"
```

**Expected Output:**
- Current chunk count: 294
- Current PDFs: 8
- Current wells: 8

#### Task 1.2: Review TOC Data
```bash
# Check what PDFs have TOC
cat outputs/toc_analysis/toc_analysis_results.json | python -m json.tool | grep -A 3 "filename"

# Count TOC entries per well
cat outputs/exploration/toc_database.json | python -m json.tool
```

**Expected Output:**
- 14 PDFs with TOC
- 188 total TOC entries

---

### Phase 2: Clear Old Index (5 minutes)

#### Task 2.1: Backup Current Index (Optional)
```bash
# Backup existing ChromaDB
cp -r chroma_db chroma_db_backup_$(date +%Y%m%d_%H%M%S)
```

#### Task 2.2: Clear Collection
```python
# scripts/clear_chromadb.py
from src.vector_store import WellReportVectorStore

vs = WellReportVectorStore()
print(f"Current chunks: {vs.collection.count()}")

# Clear all data
vs.collection.delete()
print("Collection cleared!")

# Verify
print(f"After clear: {vs.collection.count()}")
```

**Expected Output:**
```
Current chunks: 294
Collection cleared!
After clear: 0
```

---

### Phase 3: Re-Index All Wells (60-90 minutes)

#### Task 3.1: Create Re-Indexing Script

**File:** `scripts/reindex_all_wells_with_toc.py`

```python
"""
Re-index all wells using TOC-enhanced chunking

This script:
1. Loads TOC database
2. For each PDF with TOC:
   - Parse PDF with TOC-enhanced parser
   - Create section-aware chunks
   - Add metadata from TOC
   - Index to ChromaDB
3. For PDFs without TOC (Well 7):
   - Use fallback chunking
   - Index with generic metadata
"""

import sys
import json
import time
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vector_store import WellReportVectorStore
from toc_parser import TOCEnhancedParser
from chunker import SectionAwareChunker
from table_chunker import TableChunker


class TOCEnhancedReIndexer:
    """Re-index all wells with TOC enhancement"""

    def __init__(self):
        self.vector_store = WellReportVectorStore()
        self.parser = TOCEnhancedParser()
        self.chunker = SectionAwareChunker()
        self.table_chunker = TableChunker()

        # Load TOC database
        toc_db_path = Path("outputs/exploration/toc_database.json")
        with open(toc_db_path, 'r') as f:
            self.toc_database = json.load(f)

        self.results = {
            'total_pdfs': 0,
            'total_chunks': 0,
            'wells': {},
            'errors': []
        }

    def get_pdfs_with_toc(self):
        """Get list of PDFs that have TOC"""
        pdfs_with_toc = []

        for well_name, well_data in self.toc_database.items():
            if well_data.get('has_toc', False):
                pdf_path = Path(well_data['pdf_path'])
                if pdf_path.exists():
                    pdfs_with_toc.append({
                        'well': well_name,
                        'path': pdf_path,
                        'toc_entries': well_data.get('toc_entries', [])
                    })

        return pdfs_with_toc

    def get_all_pdfs(self, data_dir="Training data-shared with participants"):
        """Get all EOWR PDFs from all wells"""
        data_dir = Path(data_dir)
        all_pdfs = []

        for well_dir in sorted(data_dir.glob("Well *")):
            well_name = well_dir.name

            # Look in Well report/EOWR directory
            eowr_dir = well_dir / "Well report" / "EOWR"
            if eowr_dir.exists():
                for pdf_file in eowr_dir.glob("*.pdf"):
                    all_pdfs.append({
                        'well': well_name,
                        'path': pdf_file
                    })

        return all_pdfs

    def index_pdf_with_toc(self, pdf_info):
        """Index a single PDF using TOC-enhanced chunking"""
        well_name = pdf_info['well']
        pdf_path = pdf_info['path']

        print(f"\n[{well_name}] Processing: {pdf_path.name}")
        print(f"  TOC entries: {len(pdf_info.get('toc_entries', []))}")

        try:
            # Parse with TOC enhancement
            start_time = time.time()
            parsed = self.parser.parse_with_toc(
                pdf_path=str(pdf_path),
                well_name=well_name
            )
            parse_time = time.time() - start_time

            print(f"  Parsed in {parse_time:.1f}s")

            # Create section-aware chunks
            chunks = self.chunker.create_chunks(
                text=parsed['text'],
                toc_sections=parsed.get('toc_sections', []),
                metadata={
                    'well_name': well_name,
                    'filename': pdf_path.name,
                    'filepath': str(pdf_path)
                }
            )

            # Create table chunks
            table_chunks = self.table_chunker.create_chunks(
                tables=parsed.get('tables', []),
                metadata={
                    'well_name': well_name,
                    'filename': pdf_path.name
                }
            )

            all_chunks = chunks + table_chunks

            print(f"  Created {len(chunks)} text chunks, {len(table_chunks)} table chunks")

            # Index to vector store
            doc_id = f"{well_name}_{pdf_path.stem}"
            indexed_count = self.vector_store.add_document(
                doc_id=doc_id,
                chunks=all_chunks
            )

            print(f"  [OK] Indexed {indexed_count} chunks")

            return {
                'status': 'success',
                'chunks': indexed_count,
                'parse_time': parse_time
            }

        except Exception as e:
            print(f"  [ERROR] {e}")
            self.results['errors'].append({
                'well': well_name,
                'file': pdf_path.name,
                'error': str(e)
            })
            return {
                'status': 'error',
                'error': str(e)
            }

    def index_pdf_without_toc(self, pdf_info):
        """Index PDF without TOC (fallback)"""
        # Similar to above but without TOC enhancement
        # Use generic chunking
        pass

    def reindex_all(self):
        """Re-index all PDFs"""
        print("="*80)
        print("RE-INDEXING ALL WELLS WITH TOC ENHANCEMENT")
        print("="*80)

        # Get PDFs with TOC
        pdfs_with_toc = self.get_pdfs_with_toc()
        print(f"\nFound {len(pdfs_with_toc)} PDFs with TOC data")

        # Also get PDFs from toc_analysis
        toc_analysis_path = Path("outputs/toc_analysis/toc_analysis_results.json")
        if toc_analysis_path.exists():
            with open(toc_analysis_path, 'r') as f:
                toc_analysis = json.load(f)

            print(f"TOC analysis has {len(toc_analysis)} PDFs")

            # Index each PDF from toc_analysis
            for pdf_data in tqdm(toc_analysis, desc="Indexing PDFs"):
                well = pdf_data['well']
                filename = pdf_data['filename']

                # Find PDF path
                pdf_path = Path("Training data-shared with participants") / well / "Well report" / "EOWR" / filename

                if not pdf_path.exists():
                    print(f"\n[WARN] PDF not found: {pdf_path}")
                    continue

                pdf_info = {
                    'well': well,
                    'path': pdf_path,
                    'toc_entries': pdf_data.get('toc_lines', 0)
                }

                result = self.index_pdf_with_toc(pdf_info)

                # Track results
                if well not in self.results['wells']:
                    self.results['wells'][well] = {
                        'pdfs': 0,
                        'chunks': 0,
                        'errors': 0
                    }

                self.results['wells'][well]['pdfs'] += 1

                if result['status'] == 'success':
                    self.results['wells'][well]['chunks'] += result['chunks']
                    self.results['total_chunks'] += result['chunks']
                else:
                    self.results['wells'][well]['errors'] += 1

                self.results['total_pdfs'] += 1

        # Print summary
        print("\n" + "="*80)
        print("RE-INDEXING COMPLETE")
        print("="*80)
        print(f"\nTotal PDFs indexed: {self.results['total_pdfs']}")
        print(f"Total chunks created: {self.results['total_chunks']}")
        print(f"Total errors: {len(self.results['errors'])}")

        print("\nPer-Well Summary:")
        for well, stats in self.results['wells'].items():
            print(f"  {well}: {stats['pdfs']} PDFs, {stats['chunks']} chunks")

        # Save results
        results_file = Path("outputs/reindexing_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to: {results_file}")


if __name__ == '__main__':
    reindexer = TOCEnhancedReIndexer()
    reindexer.reindex_all()
```

#### Task 3.2: Run Re-Indexing
```bash
python scripts/reindex_all_wells_with_toc.py
```

**Expected Output:**
```
RE-INDEXING ALL WELLS WITH TOC ENHANCEMENT
Found 14 PDFs with TOC data

[Well 1] Processing: NLOG_GS_PUB_EOJR ADK-GT-01-S1...
  TOC entries: 6
  Parsed in 12.3s
  Created 45 text chunks, 12 table chunks
  [OK] Indexed 57 chunks

[Well 1] Processing: NLOG_GS_PUB_EOWR ADK-GT-01 SODM v1.1.pdf...
  TOC entries: 9
  Parsed in 15.2s
  Created 38 text chunks, 8 table chunks
  [OK] Indexed 46 chunks

...

RE-INDEXING COMPLETE
Total PDFs indexed: 14
Total chunks created: 950
Total errors: 0

Per-Well Summary:
  Well 1: 2 PDFs, 103 chunks
  Well 2: 2 PDFs, 87 chunks
  Well 3: 1 PDFs, 52 chunks
  Well 4: 3 PDFs, 156 chunks
  Well 5: 2 PDFs, 198 chunks
  Well 6: 1 PDFs, 89 chunks
  Well 7: 0 PDFs, 0 chunks
  Well 8: 3 PDFs, 265 chunks
```

**Expected Improvement:**
- From: 8 PDFs, 294 chunks
- To: 14 PDFs, 800-1000 chunks (3-4x increase!)

---

### Phase 4: Handle Well 7 (30 minutes)

Well 7 is a scanned PDF with no TOC. Options:

#### Option 1: Manual TOC Creation
Create a manual TOC for Well 7:

**File:** `data/manual_tocs/well_7_toc.json`
```json
{
  "well": "Well 7",
  "filename": "NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf",
  "toc_entries": [
    {"section": "1", "title": "General Well Data", "page": 5},
    {"section": "2", "title": "Borehole Section Details", "page": 8},
    {"section": "3", "title": "Casing", "page": 12}
  ]
}
```

#### Option 2: Full-Document Chunking
Index Well 7 without TOC:
```python
# Use generic chunking for Well 7
chunks = simple_chunker.chunk_text(
    text=parsed_text,
    chunk_size=1000,
    overlap=200
)
```

#### Option 3: Skip Well 7
Accept 12.5% data loss (7/8 wells = 87.5% coverage)

**Recommended:** Option 2 (full-document chunking)

---

### Phase 5: Verification (15 minutes)

#### Task 5.1: Check ChromaDB Stats
```python
from src.vector_store import WellReportVectorStore

vs = WellReportVectorStore()
stats = vs.get_collection_stats()

print(f"Total chunks: {stats['total_chunks']}")
print(f"Wells: {stats['wells']}")
print(f"\nPer-well breakdown:")
for well, count in stats['chunks_per_well'].items():
    print(f"  {well}: {count} chunks")
```

**Expected Output:**
```
Total chunks: 950
Wells: 8

Per-well breakdown:
  Well 1: 103 chunks
  Well 2: 87 chunks
  Well 3: 52 chunks
  Well 4: 156 chunks
  Well 5: 198 chunks
  Well 6: 89 chunks
  Well 7: 0 chunks (or 50+ if indexed)
  Well 8: 265 chunks
```

#### Task 5.2: Test Queries
```bash
# Test the queries that previously returned 0 chunks
python -c "
from src.rag_system import WellReportRAG

rag = WellReportRAG()

# Previously failed queries
queries = [
    ('What is the location?', 'Well 1'),
    ('What is the well identifier?', 'Well 8'),
]

for query, well in queries:
    result = rag.query(query, well_name=well)
    print(f'{query} ({well}): {len(result[\"sources\"])} sources')
"
```

**Expected Output:**
```
What is the location? (Well 1): 5 sources  ✓
What is the well identifier? (Well 8): 5 sources  ✓
```

---

### Phase 6: Re-Run Performance Benchmark (10 minutes)

```bash
python tests/benchmark_performance.py
```

**Expected Improvements:**
- No more 0-chunk queries
- Potentially better accuracy
- Similar or better speed

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| 1. Pre-Analysis | 15 min | Check current state, review TOC data |
| 2. Clear Old Index | 5 min | Backup and clear ChromaDB |
| 3. Re-Index All | 60-90 min | Index 14 PDFs with TOC enhancement |
| 4. Handle Well 7 | 30 min | Decide and implement approach |
| 5. Verification | 15 min | Check stats, test queries |
| 6. Re-Benchmark | 10 min | Run performance tests |
| **Total** | **2-3 hours** | |

---

## Success Criteria

### Before Re-Indexing

- [x] 8 PDFs indexed
- [x] 294 total chunks
- [x] Well 7: 0 chunks
- [x] Some queries return 0 chunks
- [x] Only 1 PDF per well

### After Re-Indexing

- [ ] **14+ PDFs indexed** (vs 8)
- [ ] **800-1000+ chunks** (vs 294)
- [ ] **Well 7: 50+ chunks** (vs 0)
- [ ] **All queries return chunks** (vs some 0)
- [ ] **Multiple PDFs per well** (vs 1)
- [ ] **Section metadata present** (new!)
- [ ] **Better retrieval accuracy** (to be tested)

---

## Risks & Mitigation

### Risk 1: Re-Indexing Takes Too Long
**Mitigation:** Start with 3-4 PDFs first, verify, then do all

### Risk 2: TOC-Enhanced Parsing Fails
**Mitigation:** Have fallback to simple chunking

### Risk 3: Too Many Chunks (>2000)
**Mitigation:** Adjust chunk size if needed

### Risk 4: Well 7 Still Fails
**Mitigation:** Accept 87.5% coverage, or manual TOC

---

## Next Steps After Re-Indexing

1. ✅ Verify chunk counts
2. ✅ Re-run benchmark
3. ✅ Build ground truth
4. ✅ Run accuracy evaluation
5. ✅ Document results
6. ✅ Prepare for judges

---

## Commands Cheat Sheet

```bash
# 1. Check current status
python scripts/check_chromadb_status.py

# 2. Backup ChromaDB
cp -r chroma_db chroma_db_backup_$(date +%Y%m%d_%H%M%S)

# 3. Clear collection
python scripts/clear_chromadb.py

# 4. Re-index all wells
python scripts/reindex_all_wells_with_toc.py

# 5. Verify results
python scripts/check_chromadb_status.py

# 6. Re-run benchmark
python tests/benchmark_performance.py
```

---

## Conclusion

Re-indexing with TOC enhancement will:
- **3-4x more chunks** (294 → 800-1000)
- **Better metadata** (section types, page numbers)
- **Fix 0-chunk queries**
- **Improve accuracy** (to be measured)
- **Professional approach** (section-aware retrieval)

**Estimated Time:** 2-3 hours
**Risk:** Low (can always restore from backup)
**Impact:** HIGH (better quality, more data, fixes issues)

**Recommendation:** DO IT! 🚀

---

## EXECUTION LOG (2025-11-09 01:35-01:50)

### Implementation Phase

**Created:** `scripts/reindex_all_wells_with_toc.py`

**Bugs Fixed During Development:**
1. `TOCEnhancedParser.parse_pdf_with_toc()` method doesn't exist
   - Solution: Use Docling DocumentConverter directly for full PDF parsing
2. `SectionAwareChunker.create_chunks()` method doesn't exist
   - Solution: Use `chunk_with_section_headers()` instead
3. `TableChunker.create_chunks()` method doesn't exist
   - Solution: Use `chunk_tables()` instead
4. `embed_texts(show_progress=False)` invalid parameter
   - Solution: Remove parameter, use default behavior
5. Double `.tolist()` call on embeddings (already lists)
   - Solution: Remove `.tolist()` call, embeddings already in list format

### Execution Phase (RUNNING IN BACKGROUND)

**Process ID:** Shell `f1abc0`
**Started:** 2025-11-09 01:36
**Status:** IN PROGRESS

**Progress:**
```
[OK] PDF 1/14: Well 1 - NLOG_GS_PUB_EOJR ADK-GT-01-S1 Well Clean-out
     - Parsed: 21.9s
     - Chunks: 25 text + 8 table = 33 total
     - Status: INDEXED

[...] PDF 2/14: Well 1 - NLOG_GS_PUB_EOWR ADK-GT-01 SODM
     - Parsed: 207.7s
     - Chunks: 215 text + 17 table = 232 total
     - Status: EMBEDDING (in progress)

[ ] PDF 3-14: Pending...
```

**Performance Metrics:**
- PDF parsing: 22-208 seconds (varies by size, OCR requirements)
- Embedding batches: ~9 minutes per 32-chunk batch (CPU bottleneck)
- Estimated completion: ~2 hours total

**Chunks Indexed So Far:** 33/~1000 (3%)

**What's Happening Now:**
The re-indexing process is running in the background. It will:
1. Parse each of 14 PDFs with Docling (with OCR)
2. Extract TOC metadata from our TOC analysis results
3. Create section-aware chunks using TOC sections
4. Embed all chunks with nomic-embed-text-v1.5
5. Index to ChromaDB with rich metadata
6. Save results to `outputs/reindexing_results.json`

**Monitor Progress:**
```bash
# Check background process output
# Process will save results when complete
```

**After Completion:**
1. Check `outputs/reindexing_results.json` for summary
2. Verify ChromaDB chunk count
3. Re-run performance benchmark
4. Compare query results vs old indexing
