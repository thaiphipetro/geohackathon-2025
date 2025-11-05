# Training Data Folder Structure Analysis
## GeoHackathon 2025 - Well Completion Reports

**Date:** 2025-01-04
**Location:** `Training data-shared with participants/`

---

## Executive Summary

The training dataset contains **comprehensive geothermal well documentation** from 8 different wells in the Netherlands, sourced from the Dutch subsurface portal (nlog.nl). This includes:

- **8 Wells** (Well 1-8) with complete documentation
- **93 PDF files** containing technical reports
- **17 Excel files** with production data and summaries
- **9 Word documents** with well overviews
- **1 Python script** for nodal analysis (the script we need to use)

**Total Dataset:** ~120 files documenting geothermal wells

---

## Top-Level Structure

```
Training data-shared with participants/
├── boreholes.xlsx                  # Master index of all wells (coordinates, depths, etc.)
├── NodalAnalysis.py               # NODAL ANALYSIS SCRIPT (provided by organizers)
│
├── Well 1/                        # Andijk GT-01 (ADK-GT-01)
├── Well 2/                        # Den Haag GT-01 (HAG-GT-01)
├── Well 3/                        # Monster-Duivenvoorde GT-06 (MDM-GT-06)
├── Well 4/                        # Naaldwijk GT-02 (NLW-GT-02)
├── Well 5/                        # Naaldwijk GT-03 (NLW-GT-03)
├── Well 6/                        # De Lier GT-01 (LIR-GT-01)
├── Well 7/                        # Vierpolders GT-01 (BRI-GT-01)
└── Well 8/                        # Monster-Duivenvoorde GT-01 (MSD-GT-01)
```

---

## Key Files at Root Level

### 1. `boreholes.xlsx`
**Purpose:** Master spreadsheet with summary information for all wells

**Expected Contents:**
- Well identifiers and names
- Geographic coordinates (X, Y)
- Total measured depth (MD)
- True vertical depth (TVD)
- Drilling dates
- Operator information
- Status (active/completed/abandoned)

**Use Case:** Quick reference for well metadata, useful for validating extracted information

---

### 2. `NodalAnalysis.py`
**Purpose:** The provided nodal analysis script for Sub-Challenge 3

**Key Components:**

#### Hardcoded Parameters (lines 5-20):
```python
rho = 1000.0                 # water density [kg/m3]
mu = 1e-3                    # viscosity [Pa.s]
reservoir_pressure = 230.0   # bar
wellhead_pressure = 10.0     # bar
PI = 5.0                     # Productivity Index [m3/hr per bar]
esp_depth = 500.0            # ESP intake depth [m]
pump_curve = {...}           # ESP pump performance curve
```

**Note from transcript:** *"We already hardcoded some parameters because otherwise you would need to extract more information from other documents. We thought for the short period of the hackathon this is just not feasible."*

#### Required Input (lines 23-28):
```python
well_trajectory = [
    {"MD": 0.0,    "TVD": 0.0,    "ID": 0.3397},   # MD, TVD in meters, ID in meters
    {"MD": 500.0,  "TVD": 500.0,  "ID": 0.2445},
    {"MD": 1500.0, "TVD": 1500.0, "ID": 0.1778},
    {"MD": 2500.0, "TVD": 2500.0, "ID": 0.1778},
]
```

**THIS IS WHAT WE NEED TO EXTRACT!**
- **MD:** Measured Depth (meters)
- **TVD:** True Vertical Depth (meters)
- **ID:** Inner Diameter (meters)

#### Output (lines 108-115):
```python
Solution found:
Flowrate: XXX.XX m3/hr
Bottomhole pressure: XXX.XX bar
Pump head: XXX.X m
```

**Critical Note:** The script structure shows EXACTLY what format Sub-Challenge 2 must produce!

---

## Individual Well Structure

Each well folder follows a similar structure with variations:

### Standard Well Folder Layout:

```
Well X/
├── [WellName].docx               # Overview document (Word format)
├── Production data/              # Historical production data
│   └── *.xlsx                    # Time-series production data
├── PVT/                          # Pressure-Volume-Temperature analysis
│   └── *.pdf                     # Fluid properties reports
├── Technical log/ or Technical Log/
│   ├── *Litholog*.pdf           # Lithology logs
│   ├── *Survey*.pdf             # Well trajectory surveys
│   ├── *Casing*.pdf             # Casing tallies and specifications
│   ├── *Cementing*.pdf          # Cementing reports
│   └── *.png                    # Log images/plots
├── Well report/                  # MOST IMPORTANT FOR SUB-CHALLENGE 1 & 2
│   └── *EOWR*.pdf               # End of Well Report (main completion report)
│   └── *EOJR*.pdf               # End of Job Report (operations)
└── Well test/                    # Well testing results
    └── *.pdf                     # Well test analysis reports
```

---

## Folder-by-Folder Breakdown

### **Well 1: Andijk (ADK-GT-01)**
```
Well 1/
├── ANDIJK.docx                   # Summary document
├── Production data/
│   └── ANDIJK-GT-01_2020_2025.xlsx
├── PVT/
│   └── NLOG_GS_PUB_ECW Geo Andijk (c18001) - PVT Report.pdf
├── Technical Log/
│   ├── NLOG_GS_PUB_ADK-GT-01-S1_Litholog.pdf
│   ├── NLOG_GS_PUB_ADK-GT-01_Litholog.pdf
│   ├── biostratigraphy reports (2 PDFs)
│   └── Winningsplan Andijk.pdf
├── Well report/
│   ├── NLOG_GS_PUB_EOJR ADK-GT-01-S1 Well Clean-out, flatpack + ESP v1.1_SodM.pdf
│   └── NLOG_GS_PUB_EOWR ADK-GT-01 SODM v1.1.pdf  ⭐ KEY DOCUMENT
└── Well Test/
    └── NLOG_GS_PUB_G1251_20190123 ADK Well Test Analysis.pdf
```

**Well ID:** ADK-GT-01 (Andijk Geothermal Well 01)
**Type:** Geothermal doublet well

---

### **Well 2: Den Haag (HAG-GT-01)**
```
Well 2/
├── [Unknown].docx
├── Production data/
├── PVT/
│   └── NLOG_GS_PUB_Panterra - Hag-GT1 Water-Gas Analysis Report.PDF
├── Technical log/
│   ├── NLOG_GS_PUB_WPMI-HAG-GT-1-NL01-REC-240-2702m MD-130910.pdf
│   ├── NLOG_GS_PUB_WPMI-HAG-GT-1-NL01-REC-240-2702m TVD-130910.pdf
│   └── Stratigraphy table
├── Well report/
│   ├── NLOG_GS_PUB_HAG GT-01-02 CT Cleanout SodM EOWR v1.0.pdf
│   └── NLOG_GS_PUB_110211 EWOR HAG GT 01.pdf  ⭐ KEY DOCUMENT
└── Well test/
    └── Multiple test reports (3 PDFs)
```

**Well ID:** HAG-GT-01 (Den Haag Geothermal Well 01)

---

### **Well 3: Monster-Duivenvoorde (MDM-GT-06)**
```
Well 3/
├── [Unknown].docx
├── Technical log/
│   ├── NLOG_GS_PUB_Litholog MDM-GT-06-S1.pdf
│   ├── NLOG_GS_PUB_Litholog MDM-GT-06-S2.pdf
│   └── NLOG_GS_PUB_Litholog MDM-GT-06.pdf
└── Well report/
    └── NLOG_GS_PUB_EOWR MDM-GT-06 SodM_v1.1.pdf  ⭐ KEY DOCUMENT
```

**Well ID:** MDM-GT-06
**Note:** Minimal documentation compared to other wells

---

### **Well 4: Naaldwijk GT-02 (NLW-GT-02)**
```
Well 4/
├── NAALDWIJK_G2.docx
├── Production data/
├── Technical log/
│   ├── Survey reports (2 PDFs for GT-02, 2 PDFs for GT-02-S1)
│   ├── Formation tops comparison
│   ├── GR/RM logs (multiple scales and formats)
│   ├── Litholog
│   └── TNO-Devli Report
├── Well report/
│   ├── NLOG_GS_PUB_EOWR - Trias Westland NLW-GT-02-S1 v1.0 SodM version.pdf
│   ├── NLOG_GS_PUB_End of well report NAALDWIJK-GT-02-S1 01-06-2018.pdf
│   └── NLOG_GS_PUB_EOWR NLW-GT-02 GRE workover SodM.pdf  ⭐ KEY DOCUMENTS
└── Well test/
    ├── NLOG_GS_PUB_G1340_5_Interference Test NLW.pdf
    ├── NLOG_GS_PUB_G1340-4-Well Test NLW-GT02_Final Report.pdf
    └── NLOG_GS_PUB_Work Plan rigless well test NLW-GT-02-S1 V4.1.pdf
```

**Well ID:** NLW-GT-02 (Naaldwijk Geothermal Well 02)
**Special Note:** Multiple sidetracks (GT-02, GT-02-S1)

---

### **Well 5: Naaldwijk GT-03 (NLW-GT-03)**
```
Well 5/
├── NAALDWIJK_G3.docx
├── Production data/
├── Technical log/
│   ├── NLOG_GS_PUB_App 01-12 (various technical appendices)
│   ├── Litholog with adapted top Delft
│   ├── Survey reports (GT-03, GT-03-S1)
│   ├── Casing tallies (20in, 13.375in, 7.625in ESPString)
│   ├── Cementing reports
│   ├── BHA records
│   ├── Bit records
│   ├── Trias composite logs (field prints)
│   └── TNO-Devli Report
├── Well report/
│   ├── NLOG_GS_PUB_EOWR_SodM_NLW-GT-03-S1 v1.0_Redacted.pdf
│   └── NLOG_GS_PUB_App 07. Final-Well-Report_NLW-GT-03.pdf  ⭐ KEY DOCUMENTS
└── Well test/
    [May be in other folders]
```

**Well ID:** NLW-GT-03 (Naaldwijk Geothermal Well 03)
**Special Note:** EXTENSIVE technical logs, this is a very well-documented well!

---

### **Well 6: De Lier (LIR-GT-01)**
```
Well 6/
├── [Unknown].docx
├── PVT/
│   └── NLOG_GS_PUB_PVT Report LIR-GT01 - Aug 12.pdf
├── Technical log/
│   ├── NLOG_GS_PUB_LIR-GT-01_EOWR SodM.pdf
│   ├── Lithostratigraphic Column
│   ├── USIT logs (2 sections)
│   ├── GR_RT logs (MD and TVD)
│   ├── Survey report
│   └── FEL logs (MD and TVD)
├── Well report/
│   └── NLOG_GS_PUB_2017 06 01 SSM EOWR LIR-GT-01 - FINAL.pdf  ⭐ KEY DOCUMENT
└── Well test/
    └── NLOG_GS_PUB_Welltest LIR-GT-01-final.pdf
```

**Well ID:** LIR-GT-01 (De Lier Geothermal Well 01)

---

### **Well 7: Vierpolders (BRI-GT-01)**
```
Well 7/
├── Vierpolders G1.docx
├── PVT/
│   └── NLOG_GS_PUB_Water and gas analysis Report BRI-GT-01.pdf
├── Technical log/
│   ├── NLOG_GS_PUB_Daily mud logging reports BRI-GT-01.pdf
│   ├── Appendices I-VI (lithology, surveys, casing tallies, cementing, FIT/LOT, CBL)
│   ├── Litholog
│   └── Wellpath Report
├── Well report/
│   ├── NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf  ⭐ KEY DOCUMENT
│   └── NLOG_GS_PUB_BIR-GT-01_AWB_Rev A 1_WellpathReport.pdf
└── Well test/
    └── NLOG_GS_PUB_Well Test Analysis BRI_GT-01.pdf
```

**Well ID:** BRI-GT-01 (Vierpolders Geothermal Well 01)
**Note:** Also referred to as BIR-GT-01 in some documents

---

### **Well 8: Monster-Duivenvoorde (MSD-GT-01)**
```
Well 8/
├── [Unknown].docx
├── Technical log/
│   ├── NLOG_GS_PUB_MSD-GT-01-MD 1200 RM.pdf
│   ├── NLOG_GS_PUB_MSD-GT-01-TVD 1200 RM.pdf
│   ├── P-XRMI-BOREHOLEPLOT and P-SDLT-DSNT field prints
│   ├── Survey report to TD
│   ├── Litholog with Memory Gamma
│   └── Appendices (CBL, Integrity Report)
└── Well report/
    ├── NLOG_GS_PUB_EOJR - MSD-GT-01 - perforating_Redacted.pdf
    ├── NLOG_GS_PUB_MSD-GT-01 EOWR_with_appendices_Redacted.pdf  ⭐ KEY DOCUMENT
    └── NLOG_GS_PUB_MSD-GT-01 EOJR - ESP installation_Redacted.pdf
```

**Well ID:** MSD-GT-01 (Monster-Duivenvoorde Geothermal Well 01)

---

## Document Types Explained (From Transcript)

### **From the Transcript:**
> *"Within these well reports there are quite a lot of important information. So of course you will see about the whole general process of the drilling of the well, the trajectory, the completion of the well. So that would give information about the different sections of the well, its diameter, the depth, and also it will give you some information about the inclination and the dog leg and all the things that you would need from the well."*

### Key Document Types:

#### 1. **Well Reports (EOWR = End of Well Report)**
**Most Important for Sub-Challenge 1 & 2!**

**Contents:**
- Well identification and location
- Drilling dates and timeline
- Operator and contractor information
- **Well trajectory data** (MD, TVD)
- **Casing and completion details** (diameters, depths) ⭐
- Wellhead information
- Cementing operations
- Equipment installed (ESPs, etc.)

**Example Names:**
- `EOWR [WellName] SodM v1.0.pdf`
- `End of well report [WellName].pdf`

**Transcript Quote:** *"This is actually in a form of a table or in some cases you'll get the table like this in the report that this is the main information that we need to extract in order to run the script."*

---

#### 2. **Technical Logs**
**Supporting documentation with detailed measurements**

**Types:**
- **Litholog:** Rock layer descriptions
- **Survey Reports:** Well trajectory (inclination, azimuth)
- **Casing Tallies:** Detailed casing string specifications
- **Cementing Reports:** Cement job details
- **GR/RM Logs:** Gamma Ray / Resistivity logs
- **BHA Records:** Bottom Hole Assembly configurations

**Use Case:** Additional source for MD, TVD, ID if well report is unclear

---

#### 3. **PVT Reports (Pressure-Volume-Temperature)**
**Fluid characterization**

**Contents:**
- Water composition analysis
- Gas composition (if present)
- Fluid properties (density, viscosity)
- Temperature profiles

**Transcript Quote:** *"After wells have been drilled there will be samples taken from them so you can get some fluid characterization which are known as the PVT reports or fluid characterization reports."*

**Note:** NOT needed for Sub-Challenges 1-3 (hardcoded in NodalAnalysis.py)

---

#### 4. **Well Test Reports**
**Performance testing data**

**Contents:**
- Production test results
- Pressure buildup/drawdown data
- Flow rates at different pressures
- Productivity Index (PI) calculations
- Interference test results

**Transcript Quote:** *"Sometimes you have some well tests so that will tell you how good your well is actually performing. So how much production you can get at a certain pressure that you impose into the system."*

**Note:** NOT needed for basic Sub-Challenges (hardcoded PI in NodalAnalysis.py)

---

#### 5. **Production Data (Excel)**
**Historical operational data**

**Contents:**
- Time-series production rates
- Pressures over time
- Temperatures
- ESP performance data

**Use Case:** Could be used for validation or bonus analysis

---

## Critical Information Locations

### **For Sub-Challenge 2: Parameter Extraction**

From the transcript, the organizers explicitly showed where to find the data:

> *"Here you have the information about the casing, tubular, cementing, all the things that are there. You won't need all of this, right? So you don't need this volume and the weight of the slurry and you know all the cementing job. You don't need this but of course this will be in my opinion this will be one of the most important tables that you should get the information from right, to the depth ID and OD of the diameters."*

### **Look for tables with these columns:**

| Section | Top MD (m) | Bottom MD (m) | Top TVD (m) | Bottom TVD (m) | OD (in) | ID (in) |
|---------|------------|---------------|-------------|----------------|---------|---------|
| Surface casing | 0 | 500 | 0 | 500 | 13.375 | 12.715 |
| Intermediate | 500 | 1500 | 500 | 1495 | 9.625 | 8.835 |
| Production | 1500 | 2500 | 1495 | 2485 | 7.000 | 6.276 |

**Column variations to handle:**
- MD / Measured Depth / Depth MD
- TVD / True Vertical Depth / Depth TVD
- ID / Inner Diameter / Internal Diameter / Di
- OD / Outer Diameter / External Diameter / Do

**Units to handle:**
- Meters (m) or Feet (ft)
- Inches (in) or Millimeters (mm)

---

## Special Cases & Challenges

### 1. **Multi-Well Reports**
From transcript:
> *"In this case there are two wells. So keep in mind that maybe sometimes you need to specify the well. Is it a GT1 or GT2? Maybe you need to make your rag application a little bit more intelligent that it identifies that within this report there are two wells."*

**Wells with multiple sidetracks:**
- Well 4: NLW-GT-02 and NLW-GT-02-S1
- Well 5: NLW-GT-03 and NLW-GT-03-S1

**Solution:** Agent must ask: "Which well do you want: GT-02 or GT-02-S1?"

---

### 2. **Scanned Documents**
From transcript:
> *"The most recent data are quite standardized in terms of the format. But going into the older documents, of course, you also see some handwritten more ad hoc type of structure."*

**Implication:** Need OCR capability (Docling + RapidOCR)

---

### 3. **Multilingual Content**
From transcript:
> *"We would also have a set which will be more challenging maybe even with some information that are handwritten or you know a little bit also multilingual."*

**Implication:** Some documents may be in Dutch or mixed languages

---

### 4. **Document Quality Variations**
From transcript:
> *"What we're going to do is that we're going to have one report which is more straightforward as information about one well and then we try to do how your workflow works there. We would also have a set which will be more challenging."*

**Quality spectrum:**
- **Easy:** Recent, digital, single well, clear tables (e.g., Well 5, Well 7)
- **Medium:** Older, scanned but clear, single well (e.g., Well 1, Well 6)
- **Hard:** Handwritten, multi-well, unclear tables, multilingual (e.g., Well 2, Well 3)

---

## Image/Diagram Files

### **Well Trajectory Diagrams**
From transcript:
> *"For the bonus challenge as I said we also have like this sort of a graphical representation which are showing the well trajectory and if for the bonus question someone is going to actually extract information from this again that's also will be great."*

**Found in:**
- Technical Log folders
- As part of Well Reports (embedded in PDFs)

**Files like:**
- `*composite*.pdf` - Composite log displays
- `*XRMI*BOREHOLEPLOT*.pdf` - Borehole image plots
- `*.png` - Exported images

**Bonus Challenge:** Extract MD, TVD, ID from these diagrams using vision models

---

## What We Need to Extract (Priority Order)

### **Sub-Challenge 1 (50%):** Text-based Information
From Well Reports, extract and summarize:
- ✅ Well names/identifiers
- ✅ Location (coordinates, region)
- ✅ Drilling dates (start, completion)
- ✅ Operator/contractor names
- ✅ Total depth
- ✅ General well information

---

### **Sub-Challenge 2 (20%):** Structured Data
From Casing/Completion Tables:
- ✅ **Measured Depth (MD)** - array of values [0, 500, 1500, 2500]
- ✅ **True Vertical Depth (TVD)** - array of values [0, 500, 1495, 2485]
- ✅ **Inner Diameter (ID)** - array of values [0.3397, 0.2445, 0.1778, 0.1778]

**Critical:** Must match the structure in `NodalAnalysis.py` lines 23-28!

---

### **Sub-Challenge 3 (30%):** Autonomous Execution
Agent must:
1. Identify which well to analyze
2. Query RAG for well information
3. Extract parameters (MD, TVD, ID)
4. Format as required by NodalAnalysis.py
5. Execute script
6. Return results

---

### **Bonus:** Vision-Based Extraction
From diagrams and plots:
- Extract MD, TVD, ID from visual representations
- Combine with text-based extraction
- Validate consistency

---

## Data Quality Assessment

### **High Quality Wells (Best for Initial Testing):**
1. **Well 5 (NLW-GT-03)** - Extensive, well-organized documentation
2. **Well 7 (BRI-GT-01)** - Clear structure, comprehensive appendices
3. **Well 1 (ADK-GT-01)** - Good documentation, has production data

### **Medium Quality Wells:**
4. **Well 4 (NLW-GT-02)** - Multi-well but well documented
5. **Well 6 (LIR-GT-01)** - Good logs and reports
6. **Well 8 (MSD-GT-01)** - Clear technical logs

### **Challenging Wells:**
7. **Well 2 (HAG-GT-01)** - Older, may have quality issues
8. **Well 3 (MDM-GT-06)** - Minimal documentation

---

## Recommended Processing Order

### **Phase 1: Validation (Use Best Quality Wells)**
1. Well 5 (NLW-GT-03) - Most comprehensive
2. Well 7 (BRI-GT-01) - Well organized
3. Well 1 (ADK-GT-01) - Has production data for validation

### **Phase 2: Testing (Medium Complexity)**
4. Well 4 (NLW-GT-02) - Test multi-well handling
5. Well 6 (LIR-GT-01) - Different log formats
6. Well 8 (MSD-GT-01) - Test consistency

### **Phase 3: Robustness (Challenging Cases)**
7. Well 2 (HAG-GT-01) - Older documents
8. Well 3 (MDM-GT-06) - Minimal data

---

## Key Insights from Transcript

### **What Judges Will Test:**

> *"The type of the question that jury will ask is about the data that you can find in the text of the well reports."*

**Example Questions from Transcript:**
1. "How many wells are reported in this well?"
2. "Can you specify the name of the wells that have been drilled?"
3. "Can you find the location of the well that has to be drilled?"
4. "Give me the true vertical depth of the GT-06 well"

### **Important Reminders:**

> *"In the second challenge, the sub challenge, you should be able to extract this information: measured depth, through vertical depth, and the inner diameter of the pipe. And then the agenting workflow when it extract this information or if something is missing, it needs to interact."*

**Key Point:** The agent must:
- Recognize when data is missing
- Ask the user for clarification
- Not make up data!

---

## Summary Statistics

### **Dataset Overview:**
- **Total Wells:** 8
- **Total Files:** 120
  - PDF: 93
  - Excel: 17
  - Word: 9
  - Python: 1

### **Well Documentation Completeness:**

| Well | Name | Well Report | Tech Logs | PVT | Well Test | Prod Data | Quality |
|------|------|-------------|-----------|-----|-----------|-----------|---------|
| 1 | ADK-GT-01 | ✅ | ✅ | ✅ | ✅ | ✅ | High |
| 2 | HAG-GT-01 | ✅ | ✅ | ✅ | ✅ | ❓ | Medium |
| 3 | MDM-GT-06 | ✅ | ✅ | ❌ | ❌ | ❌ | Low |
| 4 | NLW-GT-02 | ✅ | ✅ | ❌ | ✅ | ❓ | High |
| 5 | NLW-GT-03 | ✅ | ✅✅✅ | ❌ | ❓ | ❓ | Very High |
| 6 | LIR-GT-01 | ✅ | ✅ | ✅ | ✅ | ❌ | High |
| 7 | BRI-GT-01 | ✅ | ✅ | ✅ | ✅ | ❌ | High |
| 8 | MSD-GT-01 | ✅ | ✅ | ❌ | ❌ | ❌ | Medium |

---

## Next Steps

1. **Start with Well 5 (NLW-GT-03)** - Best documented
2. **Parse the EOWR (End of Well Report)** - Main completion info
3. **Focus on casing tables** - Contains MD, TVD, ID
4. **Test extraction** - Validate against manual reading
5. **Expand to other wells** - Test robustness

---

## Conclusion

The training data is **well-structured and comprehensive**, providing:
- ✅ Multiple well examples (8 wells)
- ✅ Various document qualities (easy to challenging)
- ✅ Complete documentation chain (reports → logs → tests)
- ✅ The exact script format needed (NodalAnalysis.py)
- ✅ Sufficient variety to test robustness

**The dataset is perfect for building and validating our RAG system!**

The key is to:
1. Start with high-quality wells (5, 7, 1)
2. Focus on Well Reports (EOWR files)
3. Extract from casing/completion tables
4. Validate against the NodalAnalysis.py structure

**Ready to start implementation! 🚀**
