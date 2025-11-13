# Well 5 Comprehensive Integration Plan

**Created:** 2025-11-10
**Updated:** 2025-11-10 (Added Phase 0: RAG Model Comparison)
**Status:** Documented - Awaiting main reindex completion
**Well:** Well 5 (NLW-GT-03) - Best Quality Well

---

## Executive Summary

**Current Status:** Only 6% of Well 5 data is indexed (2/31 files)

**Discovery:**
- 31 total files across 4 formats (PDF, Excel, PNG, DOCX)
- 29 files pending integration (94% of available data)
- Critical MD/TVD/ID parameters exist in multiple unindexed files
- Time-series data (172K rows) requires special handling strategy

**Impact:**
- Sub-Challenge 2 parameters (MD/TVD/ID) available in unindexed files
- Production performance data not yet accessible to RAG
- Visual well logs not yet integrated
- 10x data expansion opportunity

---

## Complete File Inventory

### Summary Statistics
```
Total Files: 31
├── PDFs:        22 (2 indexed, 20 pending)
├── Excel:        4 (0 indexed, 4 pending)
├── PNG Images:   4 (0 indexed, 4 pending)
└── DOCX:         1 (0 indexed, 1 pending)

Currently Indexed:   2 files (6%)
Pending Integration: 29 files (94%)
```

---

## Detailed File Analysis

### 1. PDF Files (22 total)

**Status:** 2/22 indexed (9%)

#### Category A: Well Reports (2 PDFs) - ALREADY INDEXED ✅
- `Well report/NLOG_GS_PUB_EOWR_SodM_NLW-GT-03-S1 v1.0_Redacted.pdf`
- `Well report/NLOG_GS_PUB_App 07. Final-Well-Report_NLW-GT-03.pdf`
- **Integration:** Already in ChromaDB with comprehensive extraction (text + tables + pictures)
- **Status:** COMPLETE

#### Category B: Technical Logs (20 PDFs) - NOT INDEXED ⏳

##### Sub-category B1: Lithology/Geology (2 PDFs)
- `Technical log/NLOG_GS_PUB_20200804_Litholog_NLW-GT-03_2550m.pdf` (8 pages)
- `Technical log/NLOG_GS_PUB_App 01. Litholog NLW-GT-03-S1_with adapted top Delft.pdf`
- **Value:** Rock formations, geological interpretations, depth markers
- **Priority:** HIGH - Critical for understanding well geology
- **Use Case:** RAG queries about lithology, formations, stratigraphy

##### Sub-category B2: Survey/Trajectory Reports (2 PDFs)
- `Technical log/NLOG_GS_PUB_App 02a. Survey Report_NLW-GT-03_Final.pdf`
- `Technical log/NLOG_GS_PUB_App 02b. Survey Report_NLW-GT-03s1_Final.pdf`
- **Value:** MD, TVD, azimuth, inclination (CRITICAL for nodal analysis!)
- **Priority:** CRITICAL - Contains MD/TVD parameters needed for Sub-Challenge 2
- **Use Case:** Direct parameter extraction for nodal analysis input
- **Note:** Excel versions also exist (see Excel section)

##### Sub-category B3: Casing/Completion (3 PDFs)
- `Technical log/NLOG_GS_PUB_App 03a. 20in casing tally NLW-GT-03 FINAL.pdf` (2 pages)
- `Technical log/NLOG_GS_PUB_App 03b. 13.375in casing tally NLW-GT-03-S1 FINAL.pdf` (4 pages)
- `Technical log/NLOG_GS_PUB_App 03c. 7.625 ESPString tally.pdf`
- **Value:** Casing depths, inner diameters (CRITICAL for nodal analysis!)
- **Priority:** CRITICAL - Contains ID parameters needed for Sub-Challenge 2
- **Use Case:** Extract MD, ID for each casing section → nodal analysis input
- **Expected Format:** Tables with columns: Depth (MD), Casing OD, Casing ID, Grade

##### Sub-category B4: Cementing (2 PDFs)
- `Technical log/NLOG_GS_PUB_App 04a. Cement pump graph 20in csg NLW-GT-03.pdf` (1 page)
- `Technical log/NLOG_GS_PUB_App 04b. Cement pump graph 13.375in csg NLW-GT-03-S1.pdf` (2 pages)
- **Value:** Cement quality, zonal isolation, cement top depth
- **Priority:** MEDIUM - Supplementary information for completion quality
- **Use Case:** RAG queries about cement job quality, zonal isolation

##### Sub-category B5: Pressure Tests (2 PDFs)
- `Technical log/NLOG_GS_PUB_App 05. NLW-GT-03 FIT 20in shoe.pdf` (1 page)
- `Technical log/NLOG_GS_PUB_App 12. Pressure tests NLW-GT-03-(S1).pdf` (7 pages)
- **Value:** Formation integrity test (FIT), leak-off test (LOT), pressure gradients
- **Priority:** HIGH - Important for reservoir characterization
- **Use Case:** Reservoir pressure estimation, formation strength analysis

##### Sub-category B6: Drilling Equipment (3 PDFs)
- `Technical log/NLOG_GS_PUB_App 08. BHAs 1 to 6 NLW-GT-03 (s1).pdf` (5 pages)
- `Technical log/NLOG_GS_PUB_App 09. BHA performance reports NLW-GT-03-(S1).pdf` (5 pages)
- `Technical log/NLOG_GS_PUB_App 10. Bit record_NLW-GT-03 & s1.pdf`
- **Value:** Drilling performance, ROP, torque, BHA configuration
- **Priority:** LOW - Historical reference, not critical for production analysis
- **Use Case:** RAG queries about drilling operations (historical context)

##### Sub-category B7: Wireline Logs (5 PDFs)
- `Technical log/NLOG_GS_PUB_Trias_NLWGT03S1_16in_bhp_field.PDF` (Bottom hole pressure)
- `Technical log/NLOG_GS_PUB_Trias_NLWGT03S1_16in_composite_field.PDF` (Composite log)
- `Technical log/NLOG_GS_PUB_Trias_NLWGT03S1_16in_dsl_field.PDF` (Dual Laterolog)
- `Technical log/NLOG_GS_PUB_Trias_NLWGT03S1_16in_xmac_field.PDF` (XMAC tool)
- `Technical log/NLOG_GS_PUB_Trias_NLWGT03S1_16in_zdl_field.PDF` (Z-Density log)
- **Value:** Resistivity, porosity, density, saturation, petrophysical properties
- **Priority:** HIGH - Essential for reservoir characterization
- **Use Case:** RAG queries about formation properties, porosity, saturation
- **Note:** Supplement PNG well log images (see Image section)

##### Sub-category B8: Engineering Analysis (1 PDF)
- `Technical log/NLOG_GS_PUB_TNO-Devli_Report_Final_20-11-24.pdf`
- **Value:** Third-party engineering review, independent verification
- **Priority:** MEDIUM - External expert analysis
- **Use Case:** RAG queries about engineering recommendations, risk assessment

---

### 2. Excel Files (4 total)

**Status:** 0/4 indexed (0%)

#### File 1: Production Data (CRITICAL for Sub-Challenge 3)
- **Path:** `Production data/NAALDWIJK-GT-03_2020_2025.xlsx`
- **Structure:**
  - Sheets: 1 ("Sheet0")
  - Rows: 49
  - Columns: 11
- **Content:** Production and injection well characteristics over 5 years (2020-2025)
- **Columns:**
  - "Kenmerken van productieput" (Production well features)
  - "Kenmerken van injectieput" (Injection well features)
- **Value:** Production rates, pressures, temperatures, flow rates
- **Priority:** CRITICAL - Real-world performance data for validation
- **Use Case:**
  - Validate nodal analysis predictions against actual production
  - Time-series analysis of well performance
  - Identify production trends and anomalies
- **Integration Challenge:**
  - Multi-header structure (merged cells)
  - Mixed Dutch/English text
  - Requires custom Excel parser with header detection
- **Recommended Approach:**
  - Parse with pandas, skip rows until header found
  - Translate Dutch headers to English
  - Create one chunk per data row with column context
  - Metadata: date, production_rate, injection_rate, pressures

#### File 2 & 3: Survey Reports (CRITICAL for Sub-Challenge 2)
- **Paths:**
  - `Technical log/NLOG_GS_PUB_App 02a. Survey Report_NLW-GT-03_Final.xlsx` (176 rows)
  - `Technical log/NLOG_GS_PUB_App 02b. Survey Report_NLW-GT-03s1_Final.xlsx` (143 rows)
- **Structure:**
  - Single sheet: "Survey Report"
  - No column headers detected (complex formatting with merged cells)
- **Content:** MD, TVD, azimuth, inclination for entire well trajectory
- **Value:** ESSENTIAL for well trajectory and nodal analysis input
- **Priority:** CRITICAL - Primary source for MD/TVD data
- **Use Case:**
  - Direct extraction of MD/TVD pairs for nodal analysis
  - Well trajectory visualization
  - Deviation analysis
- **Integration Challenge:**
  - Complex header structure (likely merged rows)
  - Need to detect header row position
  - Parse numerical data with units
- **Recommended Approach:**
  - Inspect first 10 rows to find header
  - Extract MD, TVD, Azimuth, Inclination columns
  - Create chunks with depth intervals (e.g., every 100m)
  - Store full trajectory as structured metadata

#### File 4: Well Test Data (MASSIVE TIME-SERIES)
- **Path:** `Well test/NLOG_GS_PUB_19092020_Ptest_Data_GT03.xlsx`
- **Structure:**
  - Sheets: 1
  - Rows: 172,834 (6+ months of high-frequency data)
  - Columns: 15
- **Columns:**
  - Date, Time
  - THP (Tubing Head Pressure)
  - Sep_Pres (Separator Pressure)
  - Ann_Pres (Annulus Pressure)
  - TH_Temp (Tubing Head Temperature)
  - WaterlevelGT04
  - Waterflow_1, Waterflow_2
  - Gasflow-1
  - GF-1_Temp
  - Pres_ESP, Temp_ESP, FRQ_ESP (ESP sensor data)
- **Value:**
  - High-resolution pressure, temperature, flow rate time-series
  - ESP performance monitoring
  - Well test analysis data
- **Priority:** HIGH - But requires different indexing strategy
- **Use Case:**
  - Pressure buildup/drawdown analysis
  - ESP performance trends
  - Flow rate correlations
  - Anomaly detection
- **Integration Challenge:**
  - **TOO LARGE FOR SIMPLE EMBEDDING** (172K rows!)
  - Would create 172K chunks → impractical
  - Needs time-series aggregation strategy
- **Recommended Approach:**
  - **DO NOT index raw rows**
  - **Aggregate to summaries:**
    - Daily summaries: mean, min, max, std for each parameter (49 days → 49 chunks)
    - Hourly summaries for critical periods (e.g., during tests)
    - Event detection: shutdowns, startup, anomalies
    - Statistical profiles: P10/P50/P90 distributions
  - **Store raw data separately:**
    - Keep Excel file as-is for direct access
    - Or load into time-series database (TimescaleDB/InfluxDB)
  - **Index only summaries:** 172K rows → ~500 chunks
  - **Metadata:** date_range, parameter_type, aggregation_level

---

### 3. PNG Images (4 total)

**Status:** 0/4 indexed (0%)

#### All Images: Wireline Log Plots (VERY LARGE VERTICAL IMAGES)
- `Technical log/NLOG_GS_PUB_NLW-GT-03-MEM-GR-05-08-20-MD.png` (1680 x 28,031 px)
- `Technical log/NLOG_GS_PUB_NLW-GT-03-MEM-GR-05-08-20-TVD.png` (1680 x 25,668 px)
- `Technical log/NLOG_GS_PUB_NLW-GT-03-ST1-MD-MEM-TD-22_08_2020.png` (1680 x 19,920 px)
- `Technical log/NLOG_GS_PUB_NLW-GT-03-ST1-TVD-MEM-TD-22_08_2020.png` (1680 x 18,345 px)

**Content Analysis (from visual inspection):**
- Vertical well log plot with depth scale on right side
- Blue gamma ray trace on left
- Grid background with depth markers every 50-100 meters
- Header section with well identification, date, operator
- Extremely high resolution (suitable for detailed analysis)
- Aspect ratio: ~17:1 (very tall, narrow)

**Value:**
- Gamma ray log correlates to lithology (shale/sand identification)
- Depth markers allow cross-referencing with other data
- Visual representation supplements text logs
- Quality control (compare PNG vs PDF wireline logs)

**Priority:** MEDIUM-HIGH

**Use Case:**
- RAG queries: "Show me the gamma ray log at 2000m"
- Visual confirmation of lithology
- Cross-reference with lithology reports
- Training data for vision models

**Integration Strategy:**

1. **Vision Model Analysis (SmolVLM or specialized OCR)**
   - Extract text from header: well name, date, operator, log type
   - Extract depth scale values (0, 500, 1000, 1500, 2000, 2500m)
   - Describe log curve patterns (high GR = shale, low GR = sand)
   - Identify key geological markers (contacts, anomalies)

2. **OCR for Depth Markers**
   - Extract numerical depth values from right scale
   - Read curve labels (GR, gamma ray units)
   - Capture header metadata

3. **Tiling Strategy (for large images)**
   - **Problem:** 28K pixel height exceeds typical VLM input limits
   - **Solution:** Tile images into depth intervals
     - Example: Tile into 500m segments → 5 tiles per image
     - Each tile: 1680 x 5000 px (more manageable)
   - Process each tile with VLM
   - Combine descriptions with depth context

4. **Potential Digitization (Advanced - Future)**
   - Trace extraction: Convert visual curve to numerical data
   - Requires specialized image processing libraries
   - Output: Depth vs GR values (digital log data)
   - Recommend: Future enhancement after basic integration

**Integration Chunks:**
- One chunk per depth interval (e.g., 500m segments)
- Text: VLM description + OCR text
- Metadata: image_path, depth_start, depth_end, log_type (GR), well_name

---

### 4. DOCX File (1 total)

**Status:** 0/1 indexed (0%)

#### File: NAALDWIJK_G3.docx
- **Location:** Root of Well 5 folder
- **Size:** 781 KB (substantial document)
- **Content:** Unknown - requires inspection
- **Priority:** MEDIUM
- **Value:** Unknown until inspected

**Integration Challenge:**
- Docling supports DOCX format (Microsoft Word 2007+)
- Not tested yet in current pipeline
- May contain:
  - Project summary/overview
  - Meeting notes
  - Technical analysis
  - Reporting documents

**Recommended Approach:**
1. **Quick inspection:** Open and scan first few pages to assess content
2. **If valuable:** Use Docling DOCX parser (already supported)
3. **Integration:** Same pipeline as PDFs (text + tables + images)
4. **If not relevant:** Skip or deprioritize

---

## Integration Strategy (7 Phases)

### Phase 0: RAG Model Comparison (PREREQUISITE - 1 hour)
**Target:** Determine optimal LLM for Well 5 RAG before full integration

**Objective:** Test Llama 3.2 3B vs Granite 3B Dense on Well 5 data to choose best model for 11-hour integration effort.

**Rationale:**
- Granite 3B optimized specifically for RAG tasks (IBM enterprise focus)
- Reference: IBM Granite + Docling RAG cookbook validates our Docling approach
- 1-hour investment now prevents suboptimal model for 11 hours of work
- Well 5 already has 2 PDFs indexed (perfect test set)

---

#### Model Comparison Setup

**Models to Test:**
1. **Llama 3.2 3B** (current)
   - General purpose, proven
   - 8K context window
   - Strong community support

2. **Granite 3B Dense** (alternative)
   - Optimized for enterprise RAG
   - Fine-tuned for document QA
   - Apache 2.0 license
   - Reference: https://github.com/ibm-granite-community/granite-snack-cookbook

**Setup Commands:**
```bash
# Current model (already have)
ollama list | grep llama3.2

# Pull Granite 3B Dense
ollama pull granite3-dense:2b

# Verify both loaded
ollama list
```

---

#### Test Query Suite (8 queries)

**Test Set 1: Factual Extraction (Critical for Sub-Challenge 2)**

**Q1: Casing Specifications**
```
Question: What is the inner diameter of the 13.375 inch casing installed in Well 5?
Expected: Specific ID value in inches/meters
Source: EOWR PDF casing tables
```

**Q2: Depth Information**
```
Question: What is the total measured depth (MD) of Well 5?
Expected: Specific MD value in meters
Source: EOWR or Final Well Report
```

**Q3: Well Trajectory**
```
Question: Provide the measured depth and true vertical depth at the kickoff point.
Expected: MD and TVD values at KOP
Source: Survey reports or EOWR
```

**Test Set 2: Table Extraction**

**Q4: Casing Program**
```
Question: List all casing sizes installed in Well 5 from surface to total depth.
Expected: Complete casing program (20", 13.375", 7.625", etc.)
Source: Casing tables
```

**Q5: Production Data**
```
Question: What was the maximum tubing head pressure recorded?
Expected: Specific pressure value with units
Source: Well test data or EOWR
```

**Test Set 3: Contextual Understanding**

**Q6: Well History**
```
Question: Describe the major challenges encountered during drilling.
Expected: Summary of drilling issues
Source: EOWR narrative sections
```

**Q7: Picture/Diagram Context**
```
Question: Are there any schematics or diagrams of the wellbore completion?
Expected: Reference to picture chunks with captions
Source: Picture metadata from VLM
```

**Test Set 4: Multi-hop Reasoning**

**Q8: Parameter Synthesis**
```
Question: What parameters from Well 5 would be needed to run a nodal analysis?
Expected: MD, TVD, ID, reservoir pressure, wellhead pressure
Source: Multiple sections
```

---

#### Evaluation Metrics

**Quantitative Metrics:**

| Metric | Weight | Measurement |
|--------|--------|-------------|
| **Accuracy** | 40% | Correct factual answer (Y/N) |
| **Citation Quality** | 30% | References correct source document |
| **Speed** | 15% | Response time (seconds) |
| **No Hallucination** | 15% | Doesn't fabricate data (Y/N) |

**Qualitative Assessment (1-5 scale):**
- **Completeness:** Answers full question
- **Precision:** Specific vs vague
- **Context Usage:** Appropriate document context

**Success Thresholds:**

Granite wins if:
- ✅ >10% better citation rate
- ✅ >20% fewer hallucinations
- ✅ Comparable or better speed (<2x slower acceptable)
- ✅ Better technical data handling

Llama 3.2 wins if:
- ✅ Comparable accuracy (±5%)
- ✅ Faster response time
- ✅ Already proven to work (risk mitigation)

---

#### Implementation Script

**Create:** `scripts/compare_rag_models.py`

**Key Functions:**
```python
class RAGModelComparison:
    def __init__(self):
        self.models = {
            'llama3.2': 'llama3.2:3b',
            'granite': 'granite3-dense:2b'
        }
        self.test_queries = [...]  # 8 queries
        self.results = {'llama3.2': [], 'granite': []}

    def test_model(self, model_name, query):
        # Query RAG system with specific model
        # Measure: answer, sources, time
        pass

    def evaluate_answer(self, result, expected_source):
        # Score: accuracy, citation, hallucination
        pass

    def run_comparison(self):
        # Test all queries on both models
        # Print side-by-side results
        pass

    def print_summary(self):
        # Aggregate metrics
        # Recommend model
        pass
```

---

#### Execution Timeline

| Step | Duration | Description |
|------|----------|-------------|
| 1. Pull Granite model | 10 min | Download via Ollama |
| 2. Create comparison script | 20 min | Implement test harness |
| 3. Run 8 test queries | 20 min | 8 queries × 2 models × ~1 min |
| 4. Evaluate results | 10 min | Score answers, calculate metrics |
| 5. Make decision | 5 min | Choose winner |
| **Total** | **65 min** | ~1 hour |

---

#### Decision Outcomes

**Scenario A: Llama 3.2 Wins**
- **Action:** Continue with current model
- **Rationale:** Proven, working, minimal risk
- **Proceed to:** Phase 1 (High-Priority PDFs)

**Scenario B: Granite Wins**
- **Action:** Switch RAG system to Granite
- **Changes Required:**
  - Update `src/rag_system.py`: `model='granite3-dense:2b'`
  - Adjust prompt templates for Granite's style
  - Re-test on Well 5 data
- **Proceed to:** Phase 1 (with Granite)

**Scenario C: Tie (within 5%)**
- **Action:** Use Llama 3.2 (de-risk)
- **Rationale:** Don't change what works unless clear winner
- **Proceed to:** Phase 1

---

#### Deliverables

1. **Comparison Report:** `outputs/rag_model_comparison.json`
2. **Test Results:** 16 answers (8 queries × 2 models)
3. **Recommendation:** Model selection for integration
4. **Updated Config:** If switching to Granite

---

#### Re-validation Points

**After Phase 1 Complete (5 more PDFs indexed):**
- Re-run subset of queries (Q1-Q3)
- Validate: Does chosen model still perform well?

**After Phase 2 Complete (Excel integrated):**
- Test: Structured data extraction
- Compare: Which model handles Excel-derived chunks better?

---

### Phase 1: High-Priority PDFs (IMMEDIATE - 30 minutes)
**Target:** Casing tallies + Survey reports (critical for Sub-Challenge 2)

**Files:** 5 PDFs
- `App 02a. Survey Report_NLW-GT-03_Final.pdf`
- `App 02b. Survey Report_NLW-GT-03s1_Final.pdf`
- `App 03a. 20in casing tally NLW-GT-03 FINAL.pdf`
- `App 03b. 13.375in casing tally NLW-GT-03-S1 FINAL.pdf`
- `App 03c. 7.625 ESPString tally.pdf`

**Method:** Use existing `add_new_documents.py`

**Command:**
```bash
# Option 1: Add individually
python scripts/add_new_documents.py \
  --pdf "Training data-shared with participants/Well 5/Technical log/NLOG_GS_PUB_App 02a. Survey Report_NLW-GT-03_Final.pdf" \
  --well "Well 5"

# Option 2: Create batch file
python scripts/discover_well_documents.py --well "Well 5" --folder "Technical log" --output well5_tier1.txt
# Edit file to keep only 5 priority PDFs
python scripts/add_new_documents.py --pdf-list well5_tier1.txt
```

**Expected Output:**
- 5 PDFs → ~50-100 chunks
- Tables extracted: Casing tally tables, survey tables
- Pictures: Diagrams if any
- Time: ~6 minutes per PDF = 30 min total

**Impact:** Unlocks Sub-Challenge 2 parameter extraction (MD, TVD, ID)

**Validation:**
- Query: "What is the inner diameter of the 13.375 inch casing?"
- Query: "Provide MD and TVD at 2000 meters depth"
- Expected: RAG returns accurate values from these PDFs

---

### Phase 2: Critical Excel Files (NEXT - Requires new parser)
**Target:** Survey Excel + Production data

**Files:** 3 Excel files
- `Technical log/NLOG_GS_PUB_App 02a. Survey Report_NLW-GT-03_Final.xlsx` (176 rows)
- `Technical log/NLOG_GS_PUB_App 02b. Survey Report_NLW-GT-03s1_Final.xlsx` (143 rows)
- `Production data/NAALDWIJK-GT-03_2020_2025.xlsx` (49 rows)

**Method:** Build Excel parser with pandas

**Implementation Approach:**
```python
class ExcelChunker:
    def chunk_survey_data(self, excel_path):
        # Detect header row (skip merged cells at top)
        # Extract: MD, TVD, Azimuth, Inclination
        # Create chunks per depth interval (e.g., every 100m)
        # Metadata: depth_start, depth_end, well_name
        pass

    def chunk_production_data(self, excel_path):
        # Skip rows until header found
        # Translate Dutch column names
        # One chunk per row (date-based)
        # Metadata: date, data_type (production/injection)
        pass
```

**Challenges:**
- Complex headers (merged cells)
- Mixed languages (Dutch/English)
- No standard format across files
- Need robust header detection

**Expected Output:**
- Survey data: ~20-30 chunks (depth intervals)
- Production data: ~49 chunks (one per row)
- Total: ~100 chunks

**Time Estimate:** 2 hours
- 1 hour: Build Excel parser
- 30 min: Test and debug
- 30 min: Run on all 3 files

**Impact:**
- Structured MD/TVD data (better than PDF parsing)
- Production performance data for RAG
- Time-series production analysis

---

### Phase 3: Remaining Technical PDFs (1 hour)
**Target:** Lithology, pressure tests, wireline logs, engineering reports

**Files:** 15 PDFs
- Lithology: 2 PDFs
- Pressure tests: 2 PDFs
- Wireline logs: 5 PDFs
- Cement graphs: 2 PDFs
- Drilling equipment: 3 PDFs
- Engineering report: 1 PDF

**Method:** Batch processing with `add_new_documents.py`

**Command:**
```bash
# Generate full Technical log list
python scripts/discover_well_documents.py --well "Well 5" --folder "Technical log" --output well5_technical.txt

# Remove Phase 1 PDFs (already indexed)
# Edit well5_technical.txt manually

# Batch index
python scripts/add_new_documents.py --pdf-list well5_technical.txt
```

**Expected Output:**
- 15 PDFs → ~200-300 chunks
- High table count (wireline log tables, lithology tables)
- Pictures: Cement graphs, BHA diagrams, log plots
- Time: ~4 minutes per PDF = 60 min total

**Impact:** Complete technical documentation coverage

---

### Phase 4: PNG Well Logs (ADVANCED - Vision processing)
**Target:** 4 large PNG well logs (70+ MB combined)

**Files:** 4 PNGs
- MD gamma ray log (28K px height)
- TVD gamma ray log (25K px height)
- MD sidetrack log (19K px height)
- TVD sidetrack log (18K px height)

**Method:** Vision model (SmolVLM) with tiling strategy

**Implementation Approach:**
```python
class LargeImageChunker:
    def tile_well_log(self, image_path, tile_height=5000):
        # Load large PNG
        # Tile into vertical segments (500m depth intervals)
        # Each tile: 1680 x 5000 px
        # Process each tile with SmolVLM
        # Extract: depth range, log description, geological features
        pass

    def extract_header_ocr(self, image_path):
        # OCR on top 500 pixels (header section)
        # Extract: well name, date, operator, log type
        pass
```

**Challenges:**
- Very large images (need tiling)
- Specialized domain (well logs require context)
- Text extraction (depth markers, labels)
- VLM may not understand well log conventions

**Approach:**
1. Resize/tile images for VLM processing
2. Extract header text with OCR (well name, date)
3. Process each depth interval (500m segments)
4. Describe log patterns (high GR = shale, low GR = sand)
5. Store images + descriptions

**Expected Output:**
- 4 images → ~20-25 tiles (5-6 tiles per image)
- One chunk per tile
- Metadata: depth_start, depth_end, log_type, image_path

**Time Estimate:** 3 hours
- 1 hour: Build tiling logic
- 1 hour: Test VLM on tiles
- 1 hour: Process all 4 images

**Impact:** Visual well log data accessible to RAG

---

### Phase 5: Time-Series Data (SPECIAL HANDLING - 4 hours)
**Target:** Well test Excel (172,834 rows)

**File:** `Well test/NLOG_GS_PUB_19092020_Ptest_Data_GT03.xlsx`

**Method:** Statistical summarization (DO NOT index raw rows)

**Problem:**
- 172,834 rows → 172K chunks (impractical!)
- Too large for simple embedding
- Most queries don't need row-level granularity

**Solution:** Aggregate to summaries

**Implementation Approach:**
```python
class TimeSeriesChunker:
    def aggregate_well_test_data(self, excel_path):
        # Load 172K rows
        df = pd.read_excel(excel_path)

        # Daily aggregates
        daily = df.groupby(df['Date'].dt.date).agg({
            'THP': ['mean', 'min', 'max', 'std'],
            'Sep_Pres': ['mean', 'min', 'max', 'std'],
            'Waterflow_1': ['mean', 'sum'],
            # ... all parameters
        })
        # 49 days → 49 chunks

        # Hourly summaries for key events
        # Event detection: shutdowns, anomalies

        # Statistical profiles
        # P10/P50/P90 distributions

        # Return chunks with summaries
        pass
```

**Aggregation Strategy:**
1. **Daily summaries:** Mean, min, max, std for all parameters (49 chunks)
2. **Hourly summaries:** For critical periods (test periods, shutdowns)
3. **Event detection:** Identify anomalies, shutdowns, startup events
4. **Statistical profiles:** Distribution summaries (P10/P50/P90)
5. **Trend analysis:** Moving averages, rate of change

**Storage Strategy:**
- **Raw data:** Keep Excel file as-is for direct access
- **Alternative:** Load into time-series database (optional)
- **Index:** Only summaries for RAG retrieval

**Expected Output:**
- 172K rows → ~500 chunks (daily + hourly + events)
- Metadata: date_range, parameter, aggregation_level
- Raw data: Reference to Excel file

**Time Estimate:** 4 hours
- 2 hours: Build aggregation logic
- 1 hour: Test and validate
- 1 hour: Generate and index summaries

**Impact:**
- Well test data accessible to RAG
- Queries like: "What was average pressure in September 2020?"
- No need to index 172K individual rows

---

### Phase 6: DOCX Inspection (30 minutes)
**Target:** NAALDWIJK_G3.docx (781 KB)

**Method:**
1. Quick inspection to assess content
2. If valuable: Use Docling DOCX parser
3. Index with standard pipeline

**Command:**
```bash
# Inspect first
python -c "
from docx import Document
doc = Document('Training data-shared with participants/Well 5/NAALDWIJK_G3.docx')
for i, para in enumerate(doc.paragraphs[:20]):
    print(f'{i}: {para.text}')
"

# If valuable, index
python scripts/add_new_documents.py \
  --pdf "Training data-shared with participants/Well 5/NAALDWIJK_G3.docx" \
  --well "Well 5"
```

**Time:** 30 minutes

---

## Recommended Prioritization

### TIER 1: CRITICAL for Sub-Challenge 2 (Do First)
**Impact:** Unlock parameter extraction

1. Survey PDFs (App 02a/02b) → MD/TVD extraction
2. Casing tallies (App 03a/03b/03c) → ID extraction
3. Survey Excel files → Structured MD/TVD data

**Estimated Time:** 2.5 hours
**Expected Chunks:** ~200

### TIER 2: HIGH VALUE for RAG (Do Second)
**Impact:** Comprehensive well understanding

4. Lithology PDFs → Geological context
5. Wireline log PDFs → Petrophysical properties
6. Pressure test PDFs → Reservoir characterization
7. Production Excel → Performance data

**Estimated Time:** 3 hours
**Expected Chunks:** ~400

### TIER 3: SUPPLEMENTARY (Do Third)
**Impact:** Visual data + quality assurance

8. PNG well logs → Visual supplements
9. Cement graphs → Quality verification
10. Engineering report → Independent analysis

**Estimated Time:** 3.5 hours
**Expected Chunks:** ~50

### TIER 4: REFERENCE (Do Later)
**Impact:** Historical context

11. Drilling equipment PDFs → Historical reference
12. Time-series data → Requires special handling
13. DOCX → Inspect first

**Estimated Time:** 5 hours
**Expected Chunks:** ~550

---

## Total Effort Estimate

| Phase | Files | Chunks | Time | Complexity | Priority |
|-------|-------|--------|------|------------|----------|
| **Phase 0: Model Comparison** | **0** | **0** | **1 hr** | **MEDIUM** | **PREREQUISITE** |
| Phase 1: Priority PDFs | 5 | ~100 | 30 min | LOW | CRITICAL |
| Phase 2: Critical Excel | 3 | ~100 | 2 hrs | HIGH | CRITICAL |
| Phase 3: Remaining PDFs | 15 | ~300 | 1 hr | LOW | HIGH |
| Phase 4: PNG Logs | 4 | ~25 | 3 hrs | HIGH | MEDIUM |
| Phase 5: Time-Series | 1 | ~500 | 4 hrs | HIGH | HIGH |
| Phase 6: DOCX | 1 | ~20 | 30 min | MEDIUM | LOW |
| **TOTAL** | **29** | **~1,045** | **12 hrs** | - | - |

**Current:** 2 files, ~800 chunks
**After Integration:** 31 files, ~1,845 chunks
**Data Expansion:** 2.3x chunk increase, 15.5x file coverage increase

---

## Key Insights

1. **Currently only using 6% of available data** (2/31 files)
2. **Critical MD/TVD/ID data exists in multiple formats** (PDF + Excel)
   - Excel likely more accurate (structured data)
   - PDF provides context and narrative
3. **Excel files require custom parsing** (not just Docling)
   - Complex headers with merged cells
   - Mixed languages (Dutch/English)
   - Need robust parser
4. **Time-series data needs special handling** (172K rows too large)
   - Aggregate to summaries
   - Don't index raw rows
5. **PNG well logs are massive** (70+ MB) but valuable
   - Tiling strategy required
   - VLM may need domain context
6. **Different file types need different integration strategies**
   - PDF: Docling (already working)
   - Excel: Pandas + custom parser
   - PNG: VLM + tiling + OCR
   - DOCX: Docling (to be tested)

---

## Testing & Validation Plan

### After Phase 1 (Priority PDFs)
**Test Queries:**
- "What is the inner diameter of the 20 inch casing?"
- "Provide measured depth and true vertical depth at 1500 meters"
- "What casing sizes are installed in this well?"

**Expected Results:**
- Accurate ID values from casing tallies
- MD/TVD pairs from survey reports
- Complete casing program summary

### After Phase 2 (Excel Integration)
**Test Queries:**
- "What was the production rate in January 2023?"
- "Show me the well trajectory from 0 to 2500 meters"
- "What is the maximum recorded tubing head pressure?"

**Expected Results:**
- Production data from Excel (not PDFs)
- Structured MD/TVD data
- Time-series statistics

### After Phase 3 (Technical PDFs)
**Test Queries:**
- "Describe the lithology at 2000 meters depth"
- "What is the porosity in the reservoir section?"
- "What were the results of the formation integrity test?"

**Expected Results:**
- Geological interpretations
- Petrophysical properties from wireline logs
- Pressure test results

### After Phase 4 (PNG Logs)
**Test Queries:**
- "Show me the gamma ray log from 1500 to 2000 meters"
- "Are there any shale sections in the well?"

**Expected Results:**
- References to PNG images with depth context
- Lithology interpretation from GR patterns

### After Phase 5 (Time-Series)
**Test Queries:**
- "What was the average ESP frequency during the well test?"
- "Were there any shutdowns in September 2020?"
- "Show me pressure trends over the test period"

**Expected Results:**
- Statistical summaries (not raw data)
- Event detection results
- Trend analysis

---

## Dependencies & Prerequisites

### Before Starting Integration:
1. ✅ Main reindex must complete (14 PDFs EOWR reports)
2. ✅ `add_new_documents.py` tested and working
3. ✅ ChromaDB verified stable with picture chunks
4. ⏳ Excel parser (Phase 2) - needs development
5. ⏳ PNG tiling logic (Phase 4) - needs development
6. ⏳ Time-series aggregation (Phase 5) - needs development

### Tools Required:
- ✅ Docling (PDF parsing)
- ✅ pandas (Excel parsing)
- ✅ SmolVLM (picture descriptions)
- ⏳ python-docx or Docling DOCX support (DOCX parsing)
- ⏳ PIL/Pillow (image tiling for large PNGs)

---

## Next Steps (After Main Reindex Completes)

1. **Verify main reindex success**
   - Check chunk counts: 14 PDFs → ~8,000 chunks?
   - Test RAG queries on indexed EOWR reports
   - Validate picture chunks working correctly

2. **Phase 0: RAG Model Comparison (1 hour) - NEW!**
   - Pull Granite 3B Dense model via Ollama
   - Run 8 test queries on both Llama 3.2 3B and Granite 3B
   - Compare: Accuracy, citation quality, speed, hallucination rate
   - Make decision: Which model to use for 12-hour integration?
   - Deliverable: `outputs/rag_model_comparison.json`

3. **Start with Phase 1 (Quick Win)**
   - Index 5 priority PDFs (30 minutes)
   - Test MD/TVD/ID extraction with chosen model
   - Validate Sub-Challenge 2 readiness

4. **Build Excel parser (Phase 2)**
   - Survey data parser
   - Production data parser
   - Test on all 3 Excel files

5. **Continue with remaining phases**
   - Follow priority order (TIER 1 → TIER 4)
   - Test after each phase
   - Re-validate model choice after Phase 1 and 2
   - Document any issues or discoveries

---

## Success Criteria

**Integration Complete When:**
- ✅ All 29 pending files processed
- ✅ ~1,845 total chunks in ChromaDB
- ✅ RAG can answer queries about:
  - Well trajectory (MD/TVD)
  - Casing program (ID)
  - Production performance
  - Geological formations
  - Petrophysical properties
  - Well test results
- ✅ Sub-Challenge 2 parameters extractable
- ✅ Picture chunks include:
  - PDF diagrams (existing)
  - PNG well logs (new)

**Quality Metrics:**
- Query accuracy: >90% on test questions
- Chunk retrieval: Correct documents referenced
- Parameter extraction: <5% error vs manual
- Response time: <10s per query

---

## Risk Assessment

### Low Risk:
- ✅ Phase 1 (PDF integration) - proven pipeline
- ✅ Phase 3 (more PDFs) - same as Phase 1

### Medium Risk:
- ⚠️ Phase 2 (Excel parsing) - complex headers, new code
- ⚠️ Phase 6 (DOCX) - untested format

### High Risk:
- ⚠️ Phase 4 (PNG logs) - very large images, tiling complexity
- ⚠️ Phase 5 (Time-series) - aggregation strategy, data volume

### Mitigation Strategies:
1. Test each phase incrementally
2. Validate outputs before moving to next phase
3. Keep raw files accessible (don't delete originals)
4. Document any parsing issues or edge cases
5. Build fallback strategies for complex formats

---

**End of Plan**

**Status:** Ready for execution after main reindex completes
**Last Updated:** 2025-11-10
