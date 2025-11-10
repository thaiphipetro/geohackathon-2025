# Post-Rebuild Action Plan

**Status:** Planning
**Date:** 2025-11-09
**Context:** TOC database rebuild with 14/14 publication dates (100%)

---

## Overview

After completing the TOC database rebuild with improved publication date extraction, we need to validate the improvements, test the system, and move forward with Sub-Challenge tasks.

---

## Phase 1: Validation & Verification (15-20 min)

### 1.1 Verify Database Completeness
**Goal:** Confirm 14/14 publication dates and data integrity

**Tasks:**
- [ ] Load `outputs/exploration/toc_database_multi_doc_full.json`
- [ ] Count publication dates: should be 14/14 (100%)
- [ ] Verify Well 4 PDF now has date: 2018-06-01
- [ ] Check all TOC entries are present (207 total)
- [ ] Validate JSON structure is correct

**Script to create:**
```python
# scripts/verify_rebuilt_database.py
# - Load JSON
# - Count dates by well
# - Print summary statistics
# - Flag any issues
```

**Expected Output:**
```
Publication Dates: 14/14 (100%)
- Well 1: 2/2 ✓
- Well 2: 2/2 ✓ (includes Dutch date fix)
- Well 3: 1/1 ✓
- Well 4: 3/3 ✓ (includes PyMuPDF fallback fix)
- Well 5: 2/2 ✓
- Well 6: 1/1 ✓
- Well 8: 3/3 ✓
```

---

### 1.2 Analyze Metadata Coverage Improvement
**Goal:** Compare before/after metadata coverage in vector store

**Tasks:**
- [ ] Load `outputs/reindexing_results.json` (if exists)
- [ ] Query ChromaDB to count chunks with section metadata
- [ ] Calculate coverage percentage: chunks_with_section_type / total_chunks
- [ ] Compare with original 15.9% baseline

**Query to run:**
```python
# Check how many chunks have section_type metadata
results = collection.get(
    include=['metadatas']
)
chunks_with_types = sum(1 for m in results['metadatas'] if m.get('section_type'))
coverage = (chunks_with_types / len(results['metadatas'])) * 100
```

**Expected Coverage:** >85% (vs original 15.9%)

---

### 1.3 Spot-Check Document Quality
**Goal:** Manually verify a few entries look correct

**Tasks:**
- [ ] Check Well 2 (Dutch date): Should show 2011-02-01
- [ ] Check Well 4 (PyMuPDF fallback): Should show 2018-06-01
- [ ] Check Well 8 (standalone date): Should show 2024-04-01
- [ ] Verify TOC entries have proper section types where applicable

---

## Phase 2: Testing & Validation (20-30 min)

### 2.1 Test Section-Filtered RAG Queries
**Goal:** Verify TOC-based retrieval actually works

**Tasks:**
- [ ] Create `scripts/test_section_filtered_rag.py`
- [ ] Test queries with section filters:
  - "What is the casing scheme?" (filter: `casing`, `completion`)
  - "What drilling issues occurred?" (filter: `drilling_operations`, `hse`)
  - "What is the well trajectory?" (filter: `directional`, `borehole`)
- [ ] Compare results with/without section filtering
- [ ] Measure precision improvement

**Test Script:**
```python
# scripts/test_section_filtered_rag.py
from src.rag_system import RAGSystem

rag = RAGSystem()

# Query without filter
results_unfiltered = rag.query("What is the casing scheme?", well_name="Well 5")

# Query with section filter
results_filtered = rag.query(
    "What is the casing scheme?",
    well_name="Well 5",
    section_types=["casing", "completion", "technical_summary"]
)

# Compare relevance and precision
print(f"Unfiltered: {len(results_unfiltered)} chunks")
print(f"Filtered: {len(results_filtered)} chunks")
```

**Expected Result:** Filtered queries return more relevant chunks

---

### 2.2 Test Multi-Document Queries
**Goal:** Verify version control works (multiple PDFs per well)

**Tasks:**
- [ ] Query Well 1 (2 PDFs: 2018-11-14, 2018-01-01)
- [ ] Verify metadata shows which PDF chunk came from
- [ ] Test filtering by publication date range
- [ ] Test "latest version only" filter

**Test Query:**
```python
# Get latest version only
results = rag.query(
    "What is the final well status?",
    well_name="Well 1",
    latest_version_only=True  # Filter by most recent pub_date
)
```

---

### 2.3 Benchmark Query Performance
**Goal:** Ensure system meets <10s per query target

**Tasks:**
- [ ] Run 10 test queries across different wells
- [ ] Measure average response time
- [ ] Identify any slow queries (>10s)
- [ ] Profile if needed

**Target:** <10s average query time

---

## Phase 3: Documentation & Cleanup (10-15 min)

### 3.1 Update Task Logs
**Goal:** Document all improvements made

**Tasks:**
- [ ] Update `.claude/tasks/multi-doc-toc-database-implementation.md`:
  - Change "13/14 dates" to "14/14 dates (100%)"
  - Add PyMuPDF fallback section
  - Document Docling limitation with date extraction
- [ ] Create session log: `.claude/tasks/session-log-toc-improvements.md`
- [ ] Update `README.md` if needed

---

### 3.2 Clean Up Test Scripts
**Goal:** Organize temporary debug scripts

**Tasks:**
- [ ] Move debug scripts to `scripts/debug/` folder:
  - `show_first_page.py`
  - `show_well4_first_pages.py`
  - `show_well4_both_methods.py`
  - `test_date_pattern.py`
  - `test_well4_date_fix.py`
  - `debug_publication_dates.py`
- [ ] Keep core scripts in `scripts/`:
  - `build_multi_doc_toc_database_full.py`
  - `analyze_all_tocs.py`
  - `robust_toc_extractor.py`

---

## Phase 4: Move to Sub-Challenge 2 (Next Session)

### 4.1 Parameter Extraction Planning
**Goal:** Extract MD, TVD, ID from well reports using improved RAG

**Approach:**
1. **Query Strategy:**
   - Use section filtering: `casing`, `completion`, `technical_summary`
   - Target table chunks (chunk_type: "table")
   - Look for keywords: "measured depth", "TVD", "inner diameter", "casing"

2. **Extraction Method:**
   - Use Pydantic models for validation
   - LLM with JSON mode (Ollama + Llama 3.2)
   - Fallback to vision model if tables are scanned images

3. **Output Format:**
   - Match NodalAnalysis.py input format:
     ```python
     [
         {"MD": 0.0, "TVD": 0.0, "ID": 0.3397},
         {"MD": 500.0, "TVD": 500.0, "ID": 0.2445},
         ...
     ]
     ```

**Tasks for Next Session:**
- [ ] Create `src/parameter_extractor.py`
- [ ] Define Pydantic models for well sections
- [ ] Test extraction on Well 5 (best quality data)
- [ ] Validate against manual extraction
- [ ] Measure accuracy (<5% error target)

---

### 4.2 Test Strategy for Sub-Challenge 2

**Test Wells:**
1. **Well 5 (NLW-GT-03):** Best quality, comprehensive data
2. **Well 3:** Medium quality, simpler structure
3. **Well 6:** Good quality, test generalization

**Validation:**
- Manual extraction for ground truth
- Compare extracted vs manual values
- Calculate error percentage: |extracted - manual| / manual * 100
- Target: <5% average error

---

## Phase 5: Agent Workflow (Sub-Challenge 3)

**After Sub-Challenge 2 is working:**

### 5.1 Design Agent Tools
- `query_well_report(question: str, well_name: str) -> str`
- `extract_well_parameters(well_name: str) -> Dict`
- `run_nodal_analysis(well_data: Dict) -> Dict`
- `list_available_wells() -> List[str]`

### 5.2 LangGraph Agent Implementation
- ReAct agent with ≤3 tool call optimization
- State management for multi-step workflow
- Error handling and retry logic

### 5.3 End-to-End Testing
- Test complete workflow: query → extract → analyze
- Target: <30s end-to-end, >95% success rate

---

## Success Criteria

### Immediate (Phase 1-3):
- [x] TOC database: 14/14 PDFs, 14/14 pub dates (100%)
- [ ] Vector store: >85% metadata coverage
- [ ] Query performance: <10s average
- [ ] Documentation: Complete and up-to-date

### Short-term (Phase 4):
- [ ] Parameter extraction: <5% error rate
- [ ] Works on 3+ wells (Well 3, 5, 6)
- [ ] Output format matches NodalAnalysis.py

### Long-term (Phase 5):
- [ ] Agent workflow: <30s end-to-end
- [ ] Success rate: >95%
- [ ] Tool calls: ≤3 per workflow

---

## Timeline Estimate

**Total Time: 45-65 minutes**

- Phase 1 (Validation): 15-20 min
- Phase 2 (Testing): 20-30 min
- Phase 3 (Documentation): 10-15 min
- Phase 4 (Sub-Challenge 2): Next session (2-3 hours)
- Phase 5 (Sub-Challenge 3): Future session (3-4 hours)

---

## Potential Issues & Mitigation

### Issue 1: Metadata Coverage <85%
**Cause:** TOC entries don't match all chunks (page ranges have gaps)

**Mitigation:**
- Implement page range interpolation for chunks between TOC entries
- Use parent section inheritance
- Accept 70-80% as acceptable if quality is high

---

### Issue 2: Section Filtering Not Working
**Cause:** Metadata not properly indexed in ChromaDB

**Mitigation:**
- Verify metadata is in `metadatas` field during indexing
- Check ChromaDB collection schema
- Re-run reindexing if needed

---

### Issue 3: Query Performance >10s
**Cause:** Large embedding operations or slow retrieval

**Mitigation:**
- Reduce chunk size or limit results
- Cache embeddings for common queries
- Optimize ChromaDB queries
- Consider batch processing

---

## Next Immediate Actions

**Once rebuild completes:**

1. Run verification script (Phase 1.1)
2. Check metadata coverage (Phase 1.2)
3. Test section-filtered queries (Phase 2.1)
4. Document results (Phase 3.1)

**Then decide:**
- If everything looks good → Move to Sub-Challenge 2
- If issues found → Debug and fix before proceeding
