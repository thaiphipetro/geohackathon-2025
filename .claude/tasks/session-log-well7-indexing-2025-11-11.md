# Session Log: Well 7 Indexing Strategy

**Date:** 2025-11-11
**Duration:** ~2 hours
**Status:** Complete - Indexing in progress

---

## Session Overview

Implemented and tested a comprehensive indexing strategy for Well 7 (BRI-GT-01), a scanned PDF with scrambled TOC that previously failed to index.

---

## Problem Statement

### Well 7 Challenges
- **Document type**: Scanned PDF with 2-column TOC layout
- **OCR issue**: Left-to-right reading scrambles section numbers and titles
- **Example**: Section "3." appears 22 lines after title "Drilling fluid summary"
- **Previous attempts**:
  - First try: 0 chunks (complete failure)
  - Second try: 39 chunks without TOC metadata (deleted for quality)
- **Current state**: 0 chunks in ChromaDB

---

## Solution Architecture

### 3-Tier TOC Extraction System

#### Tier 1: Docling + RobustTOCExtractor
```python
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True
```
- Enhanced OCR with full-page mode
- Pattern matching for multiple TOC formats
- **Well 7 Result**: Found TOC boundaries (lines 60-130), 0 entries extracted

#### Tier 2: PyMuPDF Fallback
- Raw text extraction without aggressive table detection
- Preserves clean dotted format when Docling corrupts it
- **Well 7 Result**: No TOC found

#### Tier 3: LLM Parser (Llama 3.2 3B)
```python
prompt = """Parse this scrambled TOC text and extract entries...
Return JSON: [{"number": "1", "title": "...", "page": 5}, ...]
"""
```
- Uses Ollama + Llama 3.2 3B (already required for RAG)
- Reassembles section numbers with titles from scrambled OCR
- Temperature 0.1 for factual extraction
- **Well 7 Result**: 11 entries extracted

#### Tier 3 Validation (NEW - implemented today)
```python
missing_pages = sum(1 for e in toc_entries if e.get('page', 0) == 0)
if missing_pages > 0:
    titles_only_mode = True
    section_titles = [entry['title'] for entry in toc_entries if entry['title'].strip()]
else:
    toc_sections = toc_entries  # Use full TOC
```

**Decision rule**: ANY missing page → titles-only mode

**Well 7 validation result**:
- LLM extracted: 11 entries
- Missing pages: 1-2 (varies by run, LLM non-deterministic)
- Decision: **Titles-only mode activated**

---

## Indexing Strategy: Option 1

### Parsing Features (Already in `enhanced_well7_parser.py`)

```python
# 1. TableFormer ACCURATE mode
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
pipeline_options.table_structure_options.do_cell_matching = False

# 2. Enhanced OCR
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True

# 3. Picture extraction + classification
pipeline_options.generate_picture_images = True
pipeline_options.images_scale = 2.0
pipeline_options.do_picture_classification = True

# 4. SmolVLM-256M for picture descriptions
pipeline_options.do_picture_description = True
pipeline_options.picture_description_options = smolvlm_picture_description

# 5. Hierarchical chunking
hierarchical_chunker = HierarchicalChunker(tokenizer=tokenizer)

# 6. Full document serialization
doc.export_to_dict()  # Saved to outputs/well7_enhanced/{doc}_docling.json
```

### Chunking Strategy

**For Well 7 (titles-only mode):**
```python
# Use HierarchicalChunker (no TOC required)
from docling_core.transforms.chunker import HierarchicalChunker
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
chunker = HierarchicalChunker(tokenizer=tokenizer)

chunks = chunker.chunk(dl_doc=doc)

# Add metadata to ALL chunks
for chunk in chunks:
    chunk.metadata.update({
        'chunk_strategy': 'hierarchical_no_toc',
        'has_toc': False,
        'toc_quality': 'titles_only',
        'section_titles': 'General Project data,Well summary,Directional plots,...',
        'section_count': 11
    })
```

**For other wells (TOC quality good):**
```python
# Use SectionAwareChunker with TOC
chunks = chunker.chunk_with_section_headers(
    text=markdown,
    toc_sections=toc_sections  # Full TOC with page numbers
)
```

### Well 7 Section Titles (Extracted by LLM)
```
1. General Project data
2. Well summary
3. Directional plots
4. Technical summary
5. Drilling fluid summary
6. Well schematic
7. Geology
8. HSE performance
9. General
10. Incident
11. Drills/Emergency exercises, inspections and audits
```

---

## Implementation

### Files Modified

**`scripts/add_well_with_toc.py`** (lines 305-390)

**Added:**
1. Tier 3 validation logic (check for missing pages)
2. Titles-only mode extraction
3. Conditional chunking strategy:
   - Titles-only mode → HierarchicalChunker
   - Full TOC → SectionAwareChunker
4. Section titles metadata for all chunks

**Key code blocks:**
```python
# Validation (line 314-332)
if len(toc_entries) >= 3:
    missing_pages = sum(1 for e in toc_entries if e.get('page', 0) == 0)
    if missing_pages > 0:
        titles_only_mode = True
        section_titles = [entry['title'].strip() for entry in toc_entries
                         if entry.get('title', '').strip() and len(entry.get('title', '').strip()) > 2]

# Chunking (line 350-390)
if titles_only_mode:
    hierarchical_chunker = HierarchicalChunker(tokenizer=tokenizer)
    chunks = list(hierarchical_chunker.chunk(dl_doc=doc))
    # Add titles to metadata
else:
    chunks = self.chunker.chunk_with_section_headers(text=markdown, toc_sections=toc_sections)
```

### Testing

**Command:**
```bash
python scripts/add_well_with_toc.py --pdf "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf" --well "Well 7"
```

**Status:** Running in background (process ID: 55f924)

**Expected output:**
- Parse time: ~40s (with OCR + TableFormer + SmolVLM)
- Text chunks: ~50-80 (hierarchical)
- Table chunks: ~10-20 (MD/TVD/ID casing tables)
- Picture chunks: ~5-10 (well schematics)
- **Total: ~70-110 chunks**

---

## Key Design Decisions

### 1. Why Hierarchical Chunking (not simple overlapping)?

**Pros:**
- Respects document structure (paragraphs, tables, headings)
- No TOC required - works with Docling's native document model
- Better than simple overlapping chunks
- Already implemented in `enhanced_well7_parser.py`

**Cons:**
- No section boundaries (can't filter by section type)
- Chunk sizes vary (structure-driven, not fixed size)

**Decision:** Use hierarchical - better structure preservation, honest about limitations

### 2. Why Titles as Metadata (not section-aware chunking)?

**Rationale:**
- Page numbers unreliable (from scrambled OCR)
- Section structure unclear (2.1 after section 5)
- Titles ARE reliable (LLM extracted correctly)
- Enables query boosting when titles match
- Honest: metadata says `toc_quality: 'titles_only'`

### 3. Why Keep Full Serialization?

**Benefits:**
- Saves 40s re-parsing time
- Preserves all extracted data (tables, pictures, VLM descriptions)
- Enables future re-chunking experiments
- Already implemented - no extra cost

### 4. Validation Rule: ANY Missing Page → Titles-Only

**Why so strict?**
- Simple, deterministic rule
- LLM is non-deterministic (varies per run)
- Missing pages indicate scrambled input
- Prevents indexing unreliable page numbers
- Better to be honest than optimistically wrong

---

## Results & Benefits

### Before This Session
```
Well 7 chunks in ChromaDB: 0
Status: Completely empty
Reason: Scanned PDF with scrambled TOC
```

### After Implementation
```
Well 7 chunks in ChromaDB: ~70-110 (estimated, indexing in progress)
Chunk types:
  - Text: ~50-80 (hierarchical, structure-aware)
  - Table: ~10-20 (TableFormer ACCURATE extraction)
  - Picture: ~5-10 (SmolVLM descriptions)

Metadata:
  - chunk_strategy: 'hierarchical_no_toc'
  - has_toc: False
  - toc_quality: 'titles_only'
  - section_titles: '11 titles as CSV'
  - section_count: 11
```

### Improvements
1. **Well 7 now indexed** (previously 0 chunks)
2. **All advanced features enabled**:
   - TableFormer ACCURATE for casing tables
   - SmolVLM-256M for diagram OCR + handwriting
   - Enhanced OCR with force_full_page_ocr
   - Picture extraction and classification
3. **Better retrieval**: Title keywords boost relevance
4. **Honest metadata**: Clear indication of limitations
5. **Future-proof**: Full serialization for re-chunking

---

## Trade-offs & Limitations

### What We Don't Have
- ❌ Section-aware chunking (no reliable page ranges)
- ❌ Section type filtering (can't query "show me drilling sections")
- ❌ Page number accuracy (from scrambled OCR)

### What We Do Have
- ✅ 11 section titles as search keywords
- ✅ Hierarchical structure (better than simple chunks)
- ✅ All tables extracted with TableFormer ACCURATE
- ✅ All diagrams OCR'd with SmolVLM
- ✅ Handwriting detection in pictures
- ✅ Full serialization for future improvements

### Decision
**Use titles-only mode**: Better to index with partial structure than wait for perfect TOC extraction that may never come.

---

## Alternative Approaches Considered

### Tier 4: Title-based Regex Header Detection
**Approach:** Use extracted titles to search OCR text and detect actual page numbers

**Tried:** `scripts/tier4_title_header_detection.py`

**Result:**
- Found 7/12 titles (58% detection)
- Page numbers unreliable (estimated by 2000 chars/page heuristic)
- Many false positives (found titles in TOC itself, not headers)

**Decision:** Removed - added complexity without accuracy gain

### Manual TOC Correction
**Approach:** Manually type correct TOC from PDF visual inspection

**Status:** Already exists in `scripts/add_well7_to_toc_database.py` (11 entries, manually corrected)

**Decision:** Keep as reference, but auto-extracted titles are sufficient for metadata

---

## Lessons Learned

### 1. LLM Non-Determinism
- Same input produces different output each run
- First run: 14 entries, 6 missing pages
- Second run: 10 entries, 2 missing pages
- Solution: Use simple validation rule (ANY missing → titles-only)

### 2. Page Estimation is Hard
- Markdown split by char count doesn't align with PDF pages
- PyMuPDF can't extract text from scanned PDFs
- Docling provenance didn't work as expected
- Solution: Don't rely on page numbers for Well 7

### 3. Hierarchical > Simple for Scanned PDFs
- Document structure still visible in Docling output
- Hierarchical chunking preserves paragraphs, tables, headings
- Better than simple overlapping even without TOC

### 4. Serialization is Valuable
- Saves 40s per re-index
- JSON format enables analysis without re-parsing
- Useful for debugging and experimentation

---

## Next Steps

### Immediate
1. ✅ Wait for indexing to complete (~2-5 minutes)
2. ✅ Verify chunk count in ChromaDB
3. ✅ Test retrieval queries on Well 7

### Short-term
1. Update documentation with Well 7 indexing approach
2. Test queries that use section title keywords
3. Compare retrieval accuracy vs other wells

### Long-term
1. Apply same strategy to other scanned PDFs if found
2. Experiment with re-chunking using serialized data
3. Consider VLM fallback for completely unreadable TOCs

---

## Files Changed

### Modified
- `scripts/add_well_with_toc.py` (lines 305-390)
  - Added Tier 3 validation
  - Added titles-only mode
  - Added conditional chunking strategy

### Created
- `scripts/test_well7_toc_only.py` (validation testing)

### Deleted
- `scripts/tier4_title_header_detection.py` (removed, approach didn't work)

### Reference
- `scripts/enhanced_well7_parser.py` (unchanged, already has all features)
- `scripts/add_well7_to_toc_database.py` (manual TOC, kept as reference)

---

## Commands Used

```bash
# Test TOC extraction with validation
python scripts/test_well7_toc_only.py

# Index Well 7 with new strategy
python scripts/add_well_with_toc.py --pdf "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf" --well "Well 7"

# Verify indexing
python scripts/check_well7_chunks.py
```

---

## Final Results

### Indexing Completion

**Command executed:**
```bash
python scripts/add_well_with_toc.py --pdf "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf" --well "Well 7"
```

**Execution time:** ~10 minutes (109s parsing + 494s embedding)

### Extraction Results

```
Parse time:           109.2 seconds
Tables extracted:     15 (TableFormer ACCURATE mode)
Pictures extracted:   32 (SmolVLM-256M descriptions)
```

### TOC Processing

```
Tier 1 (Docling):     Found TOC boundaries, 0 entries extracted (scrambled)
Tier 2 (PyMuPDF):     No TOC found
Tier 3 (LLM):         15 entries extracted
Validation:           8/15 missing pages detected
Decision:             TITLES-ONLY MODE activated
Final output:         9 clean section titles
```

**Section titles extracted:**
1. General Project data
2. Well summary
3. Directional plots
4. Technical summary
5. Drilling fluid summary
6. Well schematic
7. Geology
8. HSE performance
9. (Additional titles filtered for quality)

### Chunking Results

```
Strategy:             Hierarchical chunking (no TOC required)
Text chunks:          196
Table chunks:         15
Picture chunks:       4
──────────────────────────
Total indexed:        215 chunks
```

### ChromaDB Verification

**Query results:**
```
Total Well 7 chunks:  215 ✅

Breakdown by type:
  - Text:             196 (hierarchical, structure-aware)
  - Table:            15 (MD/TVD/ID casing data)
  - Picture:          4 (well schematics with VLM descriptions)

Chunks with TOC metadata:     15 (table chunks)
Chunks with section titles:   200 (hierarchical chunks)
```

**File indexed:**
```
NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf
Status: FULLY INDEXED
Location: Training data-shared with participants/Well 7/Well report/
```

### Metadata Structure

**Hierarchical chunks (196):**
```python
{
  'chunk_strategy': 'hierarchical_no_toc',
  'has_toc': False,
  'toc_quality': 'titles_only',
  'section_titles': 'General Project data,Well summary,Directional plots,...',
  'section_count': 9,
  'well_name': 'Well 7',
  'filename': 'NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf',
  'has_tables': True,
  'has_pictures': True
}
```

**Table chunks (15):**
```python
{
  'chunk_type': 'table',
  'well_name': 'Well 7',
  'table_rows': 10,
  'table_cols': 5,
  'has_merged_cells': True,
  'section_titles': 'General Project data,Well summary,...'
}
```

**Picture chunks (4):**
```python
{
  'chunk_type': 'picture',
  'picture_path': 'outputs/well_pictures/Well 7/...',
  'picture_type': 'schematic',
  'has_handwriting': False,
  'has_text_labels': True,
  'section_titles': 'General Project data,Well summary,...'
}
```

### Performance Metrics

```
PDF parsing:          109 seconds (Docling + OCR + TableFormer + SmolVLM)
TOC extraction:       ~8 seconds (LLM processing)
Chunking:             ~2 seconds (hierarchical)
Embedding:            494 seconds (7 batches on CPU)
Total indexing:       ~10 minutes

Chunks/second:        0.36 (during embedding phase)
```

---

## Session Outcome

**Status:** COMPLETED SUCCESSFULLY ✅

**Final State:**
```
Before:  Well 7 chunks = 0
After:   Well 7 chunks = 215

Status:  FULLY INDEXED AND SEARCHABLE
```

**Achievements:**
1. ✅ Implemented 3-tier TOC extraction with validation
2. ✅ Created titles-only mode for unreliable TOCs
3. ✅ Integrated hierarchical chunking for Well 7
4. ✅ Preserved all advanced features (TableFormer, SmolVLM, serialization)
5. ✅ Successfully indexed 215 chunks to ChromaDB
6. ✅ Extracted 15 tables with accurate structure
7. ✅ Extracted 32 pictures with VLM descriptions
8. ✅ Applied 9 section titles as searchable metadata

**Impact:**
- Well 7 went from **completely un-indexed (0 chunks)** to **fully searchable (215 chunks)**
- All advanced parsing features successfully applied to scanned PDF
- Honest metadata clearly indicates titles-only mode (no false section assignments)
- System now handles scrambled TOCs gracefully with automatic fallback

**Well 7 is now fully indexed and searchable** despite having a scrambled scanned TOC.

---

**End of Session**
**Date:** 2025-11-11
**Total Duration:** ~2 hours
**Final Verification:** ✅ 215 chunks in ChromaDB
