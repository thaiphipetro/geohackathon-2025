# Sub-Challenge 1: RAG-Based Summarization
## Detailed Implementation Plan (7 Days)

**Challenge Weight:** 50% of total grade (HIGHEST PRIORITY!)
**Goal:** Create accurate and complete summaries of well completion reports based on user prompts

---

## Success Criteria

### Judge Evaluation Criteria (from transcript):
1. **Accuracy of Response** - Correct information retrieved from reports
2. **Speed of Response** - Fast query times (<10 seconds target)
3. **Number of Prompts** - Minimal interaction needed to get answer
4. **Completeness** - Within given word count, all relevant info included

### Our Targets:
- ✅ >90% accuracy on judge questions
- ✅ <10 seconds average response time
- ✅ Handle all 8-10 training documents
- ✅ Robust to document variations (scanned, multilingual, handwritten)
- ✅ Graceful handling of missing information

### Judge Question Types (Expected):
From transcript: *"How many wells are reported? Can you specify the name of the wells? Can you find the location of the well? What is the text part in the well report?"*

**We expect:**
- Well identification questions
- Location/date queries
- Drilling details
- Personnel/operator information
- Trajectory information (text-based)
- Equipment information

---

## Timeline Overview

| Day | Focus | Hours | Key Deliverable |
|-----|-------|-------|-----------------|
| **Day 1** | Environment + Parsing | 8h | Parse first document successfully |
| **Day 2** | Embeddings + Vector Store | 8h | Query returns relevant chunks |
| **Day 3** | RAG System | 8h | First end-to-end query working |
| **Day 4** | Batch Processing | 8h | All training docs indexed |
| **Day 5** | Testing + Validation | 8h | >80% accuracy on test set |
| **Day 6** | Optimization | 8h | Speed <10s, accuracy >90% |
| **Day 7** | Edge Cases + Polish | 8h | Robust to all document types |

**Total Time:** 56 hours (~7 working days at 8 hours/day)

---

## Day 1: Environment Setup & Document Parsing
**Goal:** Successfully parse first well report with text, tables, and metadata
**Time Allocation:** 8 hours

### Hour 1-2: Environment Setup

#### Task 1.1: Project Structure (30 min)
```bash
# Create directory structure
mkdir -p geohackathon/{src,tests,data,outputs,notebooks,.logs}
cd geohackathon

# Initialize git
git init
git add .gitignore

# Create .gitignore
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
env/

# Data
data/
chroma_db/
*.pdf

# Logs
.logs/
*.log

# Outputs
outputs/

# IDE
.vscode/
.idea/

# Models
models/
*.pt
*.bin

# OS
.DS_Store
Thumbs.db
EOF
```

**Validation:**
```bash
tree -L 2
# Should show clean directory structure
```

---

#### Task 1.2: Python Environment (30 min)
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Create requirements.txt
cat > requirements.txt << EOF
# Document Processing
docling>=1.0.0
docling[rapidocr]>=1.0.0

# Embeddings & Vector Store
sentence-transformers>=2.2.0
chromadb>=0.4.0

# LLM
ollama>=0.1.0

# Utilities
pydantic>=2.0.0
python-dotenv>=1.0.0
tqdm>=4.65.0
pandas>=2.0.0

# Development
pytest>=7.4.0
black>=23.0.0
flake8>=6.0.0
ipython>=8.12.0
jupyter>=1.0.0
EOF

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import docling; import chromadb; import sentence_transformers; print('✓ All imports successful')"
```

**Expected Output:**
```
✓ All imports successful
```

**Troubleshooting:**
- If `docling` fails: Check Python version (need 3.10+)
- If `rapidocr` fails: Try `pip install rapidocr-onnxruntime`
- If `chromadb` fails: May need `pip install chromadb-client`

---

#### Task 1.3: Ollama Setup (30 min)
```bash
# Download Ollama from https://ollama.ai
# Then install the model

ollama pull llama3.2:3b

# Test it works
ollama run llama3.2:3b "Hello, respond with just 'OK'"

# Expected: "OK" or similar short response
```

**Verify Ollama:**
```python
# test_ollama.py
import ollama

response = ollama.generate(
    model='llama3.2:3b',
    prompt='Say "Hello from Ollama" and nothing else'
)
print(response['response'])
```

**Expected Output:**
```
Hello from Ollama
```

---

#### Task 1.4: Logging Setup (30 min)

**File:** `src/logger_config.py`
```python
"""
Centralized logging configuration
All modules import from here
"""

import logging
import sys
from pathlib import Path

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logger with file and console handlers

    Args:
        name: Logger name (typically __name__)
        level: Logging level

    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)

    # File handler (DEBUG and above)
    log_dir = Path('.logs')
    log_dir.mkdir(exist_ok=True)

    file_handler = logging.FileHandler(log_dir / 'geohackathon.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Quick test
if __name__ == '__main__':
    logger = setup_logger(__name__)
    logger.info("✓ Logging setup successful")
    logger.debug("Debug message (only in file)")
```

**Test:**
```bash
python src/logger_config.py
# Should see: INFO - ✓ Logging setup successful
# Check .logs/geohackathon.log exists
```

---

### Hour 2-4: Document Parser Implementation

#### Task 2.1: Basic Parser (1 hour)

**File:** `src/document_parser.py`
```python
"""
Document parser with OCR support
Handles: PDF → text, tables, images, metadata
"""

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, OcrOptions
from typing import Dict, List, Optional
from pathlib import Path
import json

from logger_config import setup_logger

logger = setup_logger(__name__)


class WellReportParser:
    """Parse well completion reports from PDF"""

    def __init__(
        self,
        enable_ocr: bool = True,
        ocr_engine: str = "rapidocr"
    ):
        """
        Initialize parser

        Args:
            enable_ocr: Enable OCR for scanned PDFs
            ocr_engine: OCR engine to use (rapidocr, tesserocr, easyocr)
        """
        self.enable_ocr = enable_ocr
        self.ocr_engine = ocr_engine

        logger.info(f"Initializing parser (OCR: {enable_ocr}, Engine: {ocr_engine})")

        # Configure pipeline
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = enable_ocr

        if enable_ocr:
            pipeline_options.ocr_options = OcrOptions(
                engine=ocr_engine,
                force_ocr=False,  # Auto-detect if OCR needed
            )

        # Create converter
        self.converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        logger.info("✓ Parser initialized")

    def parse_pdf(self, pdf_path: str) -> Dict:
        """
        Parse PDF and extract all content

        Args:
            pdf_path: Path to PDF file

        Returns:
            {
                "text": full markdown text,
                "tables": list of tables,
                "images": list of images,
                "metadata": document metadata,
                "stats": parsing statistics
            }
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info(f"Parsing: {pdf_path.name}")

        try:
            # Convert document
            result = self.converter.convert(str(pdf_path))
            doc = result.document

            # Extract text as markdown
            text = doc.export_to_markdown()
            logger.debug(f"Extracted {len(text)} characters of text")

            # Extract tables
            tables = self._extract_tables(doc)
            logger.debug(f"Extracted {len(tables)} tables")

            # Extract images
            images = self._extract_images(doc)
            logger.debug(f"Found {len(images)} images")

            # Build metadata
            metadata = self._build_metadata(pdf_path, doc)

            # Calculate stats
            stats = {
                "text_length": len(text),
                "table_count": len(tables),
                "image_count": len(images),
                "page_count": metadata.get("page_count", 0),
                "has_scanned_content": metadata.get("has_ocr_content", False)
            }

            logger.info(f"✓ Parsed {pdf_path.name}: {stats['page_count']} pages, "
                       f"{stats['table_count']} tables, {stats['image_count']} images")

            return {
                "text": text,
                "tables": tables,
                "images": images,
                "metadata": metadata,
                "stats": stats
            }

        except Exception as e:
            logger.error(f"Failed to parse {pdf_path}: {e}")
            raise

    def _extract_tables(self, doc) -> List[Dict]:
        """Extract tables in structured format"""
        tables = []

        if not hasattr(doc, 'tables'):
            return tables

        for i, table in enumerate(doc.tables):
            try:
                table_data = {
                    "id": f"table_{i}",
                    "data": table.data if hasattr(table, 'data') else None,
                    "headers": table.headers if hasattr(table, 'headers') else None,
                    "page": table.page if hasattr(table, 'page') else None,
                    "bbox": table.bbox if hasattr(table, 'bbox') else None,
                    "text": self._table_to_text(table)
                }
                tables.append(table_data)
            except Exception as e:
                logger.warning(f"Failed to extract table {i}: {e}")

        return tables

    def _table_to_text(self, table) -> str:
        """Convert table to text representation"""
        text_parts = []

        # Add headers
        if hasattr(table, 'headers') and table.headers:
            text_parts.append("Headers: " + " | ".join(str(h) for h in table.headers))

        # Add data rows
        if hasattr(table, 'data') and table.data:
            for row in table.data:
                row_text = " | ".join(str(cell) for cell in row)
                text_parts.append(row_text)

        return "\n".join(text_parts)

    def _extract_images(self, doc) -> List[Dict]:
        """Extract image metadata"""
        images = []

        if not hasattr(doc, 'pictures'):
            return images

        for i, img in enumerate(doc.pictures):
            try:
                image_data = {
                    "id": f"image_{i}",
                    "page": img.page if hasattr(img, 'page') else None,
                    "bbox": img.bbox if hasattr(img, 'bbox') else None,
                    "caption": img.caption if hasattr(img, 'caption') else None
                }
                images.append(image_data)
            except Exception as e:
                logger.warning(f"Failed to extract image {i}: {e}")

        return images

    def _build_metadata(self, pdf_path: Path, doc) -> Dict:
        """Build document metadata"""
        return {
            "filename": pdf_path.name,
            "filepath": str(pdf_path),
            "page_count": len(doc.pages) if hasattr(doc, 'pages') else 0,
            "has_ocr_content": getattr(doc, 'has_ocr_content', False),
        }

    def save_parsed_output(self, parsed_data: Dict, output_dir: str = "outputs"):
        """
        Save parsed data to JSON for inspection

        Args:
            parsed_data: Output from parse_pdf()
            output_dir: Directory to save outputs
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # Create filename from source
        source_name = Path(parsed_data['metadata']['filename']).stem
        output_file = output_dir / f"{source_name}_parsed.json"

        # Save (excluding images to keep file small)
        save_data = {
            "text": parsed_data['text'][:1000] + "...",  # Truncate for readability
            "tables": parsed_data['tables'],
            "metadata": parsed_data['metadata'],
            "stats": parsed_data['stats']
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Saved parsed output to {output_file}")


# Quick test
if __name__ == '__main__':
    parser = WellReportParser(enable_ocr=True)
    print("✓ Parser created successfully")
```

**Validation:**
```bash
python src/document_parser.py
# Should see: ✓ Parser created successfully
```

---

#### Task 2.2: Test on First Document (1 hour)

**File:** `tests/test_parser.py`
```python
"""
Test document parser on training data
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from document_parser import WellReportParser
from logger_config import setup_logger

logger = setup_logger(__name__)


def test_parse_first_document():
    """Test parsing on first available document"""

    # Find first PDF in training data
    data_dir = Path("data")

    if not data_dir.exists():
        logger.error("Data directory not found. Please add training data to ./data/")
        return False

    # Find first PDF
    pdf_files = list(data_dir.rglob("*.pdf"))

    if not pdf_files:
        logger.error("No PDF files found in data directory")
        return False

    test_pdf = pdf_files[0]
    logger.info(f"Testing with: {test_pdf}")

    # Parse
    parser = WellReportParser(enable_ocr=True)

    try:
        result = parser.parse_pdf(str(test_pdf))

        # Validate result structure
        assert "text" in result
        assert "tables" in result
        assert "images" in result
        assert "metadata" in result
        assert "stats" in result

        # Print summary
        print("\n" + "="*60)
        print("PARSING TEST RESULTS")
        print("="*60)
        print(f"File: {test_pdf.name}")
        print(f"Pages: {result['stats']['page_count']}")
        print(f"Text length: {result['stats']['text_length']} characters")
        print(f"Tables: {result['stats']['table_count']}")
        print(f"Images: {result['stats']['image_count']}")
        print(f"Has scanned content: {result['stats']['has_scanned_content']}")
        print("="*60)

        # Show first 500 chars of text
        print("\nFirst 500 characters of text:")
        print("-"*60)
        print(result['text'][:500])
        print("-"*60)

        # Show table info
        if result['tables']:
            print(f"\nFirst table preview:")
            print("-"*60)
            print(result['tables'][0]['text'][:300])
            print("-"*60)

        # Save output
        parser.save_parsed_output(result)

        logger.info("✓ Test passed")
        return True

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_parse_first_document()
    sys.exit(0 if success else 1)
```

**Run Test:**
```bash
# First, add one training PDF to data directory
mkdir -p data/Well_1
# Copy a well report PDF to data/Well_1/

# Run test
python tests/test_parser.py
```

**Expected Output:**
```
============================================================
PARSING TEST RESULTS
============================================================
File: well_report.pdf
Pages: 45
Text length: 125432 characters
Tables: 12
Images: 8
Has scanned content: True
============================================================

First 500 characters of text:
------------------------------------------------------------
# Well Completion Report
## NLW-GT-03

### General Information
Location: Netherlands
Operator: Geothermal Company
Date: 2020-08-15
...
------------------------------------------------------------

✓ Test passed
```

**Troubleshooting:**
- **No text extracted**: Check if PDF is pure image (scanned), enable OCR
- **Tables empty**: Table structure might be complex, check output JSON
- **Slow parsing**: Normal for first run, models downloading
- **OCR errors**: Try different engine: `ocr_engine="tesserocr"`

---

### Hour 4-6: Batch Processing Setup

#### Task 3.1: Multi-Document Processor (1.5 hours)

**File:** `src/batch_processor.py`
```python
"""
Batch process all training documents
Creates index of all parsed documents
"""

from pathlib import Path
from typing import List, Dict
import json
from tqdm import tqdm
import time

from document_parser import WellReportParser
from logger_config import setup_logger

logger = setup_logger(__name__)


class BatchDocumentProcessor:
    """Process multiple documents in batch"""

    def __init__(
        self,
        data_dir: str = "data",
        output_dir: str = "outputs/parsed",
        enable_ocr: bool = True
    ):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.parser = WellReportParser(enable_ocr=enable_ocr)
        self.processed_docs = []

    def find_all_pdfs(self) -> List[Path]:
        """Find all PDF files in data directory"""
        logger.info(f"Searching for PDFs in {self.data_dir}")

        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

        pdf_files = list(self.data_dir.rglob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")

        return pdf_files

    def process_all(self) -> List[Dict]:
        """
        Process all PDFs

        Returns:
            List of parsed document results
        """
        pdf_files = self.find_all_pdfs()

        if not pdf_files:
            logger.warning("No PDF files found to process")
            return []

        logger.info(f"Processing {len(pdf_files)} documents...")

        results = []
        failed = []

        for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                start_time = time.time()

                # Parse
                result = self.parser.parse_pdf(str(pdf_file))

                # Add timing
                result['processing_time'] = time.time() - start_time

                # Save individual output
                self._save_parsed_doc(result)

                results.append(result)
                self.processed_docs.append(result)

                logger.info(f"✓ Processed {pdf_file.name} in {result['processing_time']:.1f}s")

            except Exception as e:
                logger.error(f"✗ Failed to process {pdf_file.name}: {e}")
                failed.append({
                    "file": str(pdf_file),
                    "error": str(e)
                })

        # Save summary
        self._save_summary(results, failed)

        logger.info(f"✓ Batch processing complete: {len(results)} succeeded, {len(failed)} failed")

        return results

    def _save_parsed_doc(self, parsed_data: Dict):
        """Save individual parsed document"""
        filename = Path(parsed_data['metadata']['filename']).stem
        output_file = self.output_dir / f"{filename}.json"

        # Truncate text for file size
        save_data = {
            **parsed_data,
            "text_preview": parsed_data['text'][:1000] + "...",
            "text_length": len(parsed_data['text'])
        }
        save_data.pop('text')  # Remove full text from JSON

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

    def _save_summary(self, results: List[Dict], failed: List[Dict]):
        """Save processing summary"""
        summary_file = self.output_dir / "processing_summary.json"

        summary = {
            "total_processed": len(results),
            "total_failed": len(failed),
            "documents": [
                {
                    "filename": r['metadata']['filename'],
                    "pages": r['stats']['page_count'],
                    "tables": r['stats']['table_count'],
                    "images": r['stats']['image_count'],
                    "text_length": r['stats']['text_length'],
                    "processing_time": r['processing_time']
                }
                for r in results
            ],
            "failed_documents": failed,
            "statistics": {
                "total_pages": sum(r['stats']['page_count'] for r in results),
                "total_tables": sum(r['stats']['table_count'] for r in results),
                "avg_processing_time": sum(r['processing_time'] for r in results) / len(results) if results else 0
            }
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"✓ Summary saved to {summary_file}")


# CLI interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Batch process well reports')
    parser.add_argument('--data-dir', default='data', help='Data directory')
    parser.add_argument('--output-dir', default='outputs/parsed', help='Output directory')
    parser.add_argument('--no-ocr', action='store_true', help='Disable OCR')

    args = parser.parse_args()

    processor = BatchDocumentProcessor(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        enable_ocr=not args.no_ocr
    )

    results = processor.process_all()

    print(f"\n{'='*60}")
    print(f"Processed {len(results)} documents")
    print(f"See outputs in: {processor.output_dir}")
    print(f"{'='*60}")
```

**Run Batch Processing:**
```bash
python src/batch_processor.py --data-dir data
```

**Expected Output:**
```
Processing PDFs: 100%|████████████| 8/8 [02:15<00:00, 16.9s/it]
✓ Batch processing complete: 8 succeeded, 0 failed
============================================================
Processed 8 documents
See outputs in: outputs/parsed
============================================================
```

**Validation Checklist:**
- [x] All training PDFs processed without errors
- [x] JSON files created for each document
- [x] Summary file shows statistics
- [x] Processing time reasonable (<30s per doc)

---

### Hour 6-8: Quality Validation

#### Task 4.1: Manual Inspection (1 hour)

Create inspection script to review parsed content:

**File:** `scripts/inspect_parsed_docs.py`
```python
"""
Interactive tool to inspect parsed documents
"""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()


def inspect_document(doc_path: Path):
    """Inspect a single parsed document"""

    with open(doc_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Display summary
    console.rule(f"[bold blue]{data['metadata']['filename']}")

    # Stats table
    stats_table = Table(title="Document Statistics")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="magenta")

    for key, value in data['stats'].items():
        stats_table.add_row(key, str(value))

    console.print(stats_table)

    # Tables summary
    if data['tables']:
        console.print(f"\n[bold green]Found {len(data['tables'])} tables:")
        for i, table in enumerate(data['tables'][:3]):  # Show first 3
            console.print(f"\nTable {i+1} (Page {table.get('page', 'unknown')}):")
            console.print(table['text'][:200] + "...")

    # Text preview
    console.print("\n[bold green]Text preview:")
    console.print(data.get('text_preview', 'No preview available'))

    console.print("\n" + "="*60 + "\n")


def main():
    """Inspect all parsed documents"""
    output_dir = Path("outputs/parsed")

    if not output_dir.exists():
        console.print("[red]No parsed documents found. Run batch_processor.py first.")
        return

    json_files = list(output_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "processing_summary.json"]

    if not json_files:
        console.print("[red]No document files found")
        return

    console.print(f"[green]Found {len(json_files)} parsed documents\n")

    for doc_file in json_files:
        inspect_document(doc_file)

        # Ask to continue
        if json_files.index(doc_file) < len(json_files) - 1:
            response = input("Continue to next document? (y/n): ")
            if response.lower() != 'y':
                break


if __name__ == '__main__':
    # Install rich if needed: pip install rich
    main()
```

**Manual Checks:**
1. Text extraction complete? ✓
2. Tables properly formatted? ✓
3. Well names identified? ✓
4. Dates and locations present? ✓
5. Any garbage text? ✗

---

#### Task 4.2: Create Test Question Dataset (1 hour)

Create expected questions judges will ask:

**File:** `tests/test_questions.json`
```json
{
  "test_questions": [
    {
      "id": "q1",
      "category": "well_identification",
      "question": "What wells are reported in this document?",
      "expected_info": ["well names", "well identifiers"],
      "difficulty": "easy"
    },
    {
      "id": "q2",
      "category": "location",
      "question": "What is the location of the well?",
      "expected_info": ["coordinates", "region", "country"],
      "difficulty": "easy"
    },
    {
      "id": "q3",
      "category": "dates",
      "question": "When was the drilling completed?",
      "expected_info": ["completion date", "drilling duration"],
      "difficulty": "easy"
    },
    {
      "id": "q4",
      "category": "operator",
      "question": "Who was responsible for the drilling operation?",
      "expected_info": ["operator name", "contractor"],
      "difficulty": "easy"
    },
    {
      "id": "q5",
      "category": "depth",
      "question": "What is the total depth of the well?",
      "expected_info": ["measured depth", "TVD"],
      "difficulty": "medium"
    },
    {
      "id": "q6",
      "category": "multi_well",
      "question": "Is this report for well GT-01 or GT-02?",
      "expected_info": ["well identifier"],
      "difficulty": "medium"
    },
    {
      "id": "q7",
      "category": "equipment",
      "question": "What drilling equipment was used?",
      "expected_info": ["rig name", "equipment list"],
      "difficulty": "medium"
    },
    {
      "id": "q8",
      "category": "summarization",
      "question": "Summarize the key well completion details in 100 words",
      "expected_info": ["well name", "location", "depth", "completion date"],
      "difficulty": "hard"
    },
    {
      "id": "q9",
      "category": "missing_info",
      "question": "What was the weather during drilling?",
      "expected_info": ["should respond 'not found'"],
      "difficulty": "hard"
    },
    {
      "id": "q10",
      "category": "technical",
      "question": "What casing sizes were used in the well completion?",
      "expected_info": ["casing diameters", "depths"],
      "difficulty": "hard"
    }
  ]
}
```

---

**End of Day 1 Checkpoint:**
✅ Environment fully set up
✅ Document parser working
✅ All training documents parsed
✅ Quality validation complete
✅ Test questions defined

**Deliverables:**
- Working document parser
- Parsed JSON for all training docs
- Processing summary report
- Test question dataset

**Tomorrow:** Build embeddings and vector store

---

## Day 2: Embeddings & Vector Store
**Goal:** Create searchable vector database of all well reports
**Time Allocation:** 8 hours

### Hour 1-3: Embedding System

#### Task 1.1: Embedding Manager (2 hours)

**File:** `src/embeddings.py`
```python
"""
Embedding generation and vector storage
Uses nomic-embed-text-v1.5 (137M params, CPU-optimized)
"""

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import numpy as np
from tqdm import tqdm
import time

from logger_config import setup_logger

logger = setup_logger(__name__)


class EmbeddingManager:
    """Manage embeddings and vector storage"""

    def __init__(
        self,
        model_name: str = "nomic-ai/nomic-embed-text-v1.5",
        persist_directory: str = "./chroma_db",
        collection_name: str = "well_reports"
    ):
        """
        Initialize embedding model and vector store

        Args:
            model_name: SentenceTransformer model name
            persist_directory: ChromaDB storage path
            collection_name: Collection name in ChromaDB
        """
        self.model_name = model_name
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Load embedding model
        logger.info(f"Loading embedding model: {model_name}")
        start_time = time.time()

        self.embedder = SentenceTransformer(
            model_name,
            trust_remote_code=True,
            device="cpu"  # Force CPU for compatibility
        )

        load_time = time.time() - start_time
        logger.info(f"✓ Model loaded in {load_time:.1f}s")

        # Get embedding dimension
        self.embedding_dim = self.embedder.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.embedding_dim}")

        # Initialize ChromaDB
        logger.info("Initializing ChromaDB...")
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Well completion reports and data"}
        )

        logger.info(f"✓ Collection '{collection_name}' ready ({self.collection.count()} existing documents)")

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
        min_chunk_size: int = 100
    ) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Full text to chunk
            chunk_size: Target characters per chunk
            overlap: Overlap between chunks
            min_chunk_size: Minimum chunk size to keep

        Returns:
            List of text chunks
        """
        if len(text) < min_chunk_size:
            return [text] if text.strip() else []

        chunks = []
        start = 0

        while start < len(text):
            # Find chunk end
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for period followed by space/newline
                sentence_end = text.rfind('. ', start, end)
                if sentence_end > start:
                    end = sentence_end + 1

            chunk = text[start:end].strip()

            if len(chunk) >= min_chunk_size:
                chunks.append(chunk)

            # Move start position
            start = end - overlap if end < len(text) else end

        logger.debug(f"Chunked text into {len(chunks)} chunks")
        return chunks

    def embed_texts(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        Create embeddings for texts

        Args:
            texts: List of text strings
            show_progress: Show progress bar

        Returns:
            Array of embeddings (n_texts, embedding_dim)
        """
        logger.debug(f"Embedding {len(texts)} texts...")

        embeddings = self.embedder.encode(
            texts,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            batch_size=32  # Optimize for CPU
        )

        return embeddings

    def add_document(
        self,
        doc_id: str,
        text: str,
        tables: List[Dict],
        metadata: Dict,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> int:
        """
        Add document to vector store

        Args:
            doc_id: Unique document ID
            text: Document text content
            tables: List of tables
            metadata: Document metadata
            chunk_size: Chunk size for text
            overlap: Overlap between chunks

        Returns:
            Number of chunks added
        """
        logger.info(f"Adding document: {doc_id}")

        # Chunk text
        text_chunks = self.chunk_text(text, chunk_size, overlap)
        logger.debug(f"Created {len(text_chunks)} text chunks")

        # Process tables as separate chunks
        table_chunks = []
        for i, table in enumerate(tables):
            table_text = self._table_to_text(table)
            if table_text:
                table_chunks.append(table_text)

        logger.debug(f"Created {len(table_chunks)} table chunks")

        all_chunks = text_chunks + table_chunks
        total_chunks = len(all_chunks)

        if total_chunks == 0:
            logger.warning(f"No chunks created for {doc_id}")
            return 0

        # Create embeddings
        logger.debug("Creating embeddings...")
        embeddings = self.embed_texts(all_chunks, show_progress=False)

        # Prepare metadata for each chunk
        chunk_metadata = []

        # Text chunks metadata
        for i in range(len(text_chunks)):
            chunk_metadata.append({
                **metadata,
                "doc_id": doc_id,
                "chunk_type": "text",
                "chunk_index": i,
                "total_chunks": total_chunks
            })

        # Table chunks metadata
        for i in range(len(table_chunks)):
            chunk_metadata.append({
                **metadata,
                "doc_id": doc_id,
                "chunk_type": "table",
                "chunk_index": i,
                "table_page": tables[i].get('page') if i < len(tables) else None
            })

        # Generate IDs
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(total_chunks)]

        # Add to ChromaDB
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=all_chunks,
            metadatas=chunk_metadata,
            ids=chunk_ids
        )

        logger.info(f"✓ Added {total_chunks} chunks for {doc_id}")
        return total_chunks

    def _table_to_text(self, table: Dict) -> str:
        """Convert table to searchable text"""
        if not table.get('text'):
            return ""

        parts = [f"[TABLE from page {table.get('page', 'unknown')}]"]
        parts.append(table['text'])

        return "\n".join(parts)

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Query vector store

        Args:
            query_text: Search query
            n_results: Number of results
            filter_metadata: Optional metadata filters

        Returns:
            {
                "documents": list of text chunks,
                "metadatas": list of metadata,
                "distances": similarity scores,
                "ids": chunk IDs
            }
        """
        logger.debug(f"Querying: '{query_text[:50]}...'")

        # Create query embedding
        query_embedding = self.embed_texts([query_text], show_progress=False)

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            where=filter_metadata
        )

        # Format results
        formatted = {
            "documents": results['documents'][0],
            "metadatas": results['metadatas'][0],
            "distances": results['distances'][0],
            "ids": results['ids'][0]
        }

        logger.debug(f"Found {len(formatted['documents'])} results")
        return formatted

    def get_stats(self) -> Dict:
        """Get collection statistics"""
        count = self.collection.count()

        return {
            "total_chunks": count,
            "collection_name": self.collection_name,
            "embedding_dimension": self.embedding_dim,
            "model": self.model_name
        }

    def clear_collection(self):
        """Clear all data from collection (use with caution!)"""
        logger.warning("Clearing collection...")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Well completion reports and data"}
        )
        logger.info("✓ Collection cleared")


# Quick test
if __name__ == '__main__':
    em = EmbeddingManager()
    stats = em.get_stats()
    print(f"✓ EmbeddingManager initialized")
    print(f"  Model: {stats['model']}")
    print(f"  Dimension: {stats['embedding_dimension']}")
    print(f"  Existing chunks: {stats['total_chunks']}")
```

**Test:**
```bash
python src/embeddings.py
```

**Expected Output:**
```
✓ EmbeddingManager initialized
  Model: nomic-ai/nomic-embed-text-v1.5
  Dimension: 768
  Existing chunks: 0
```

---

#### Task 1.2: Index All Documents (1 hour)

**File:** `scripts/index_documents.py`
```python
"""
Index all parsed documents into vector store
"""

import json
from pathlib import Path
import sys
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from embeddings import EmbeddingManager
from logger_config import setup_logger

logger = setup_logger(__name__)


def load_parsed_document(json_path: Path) -> dict:
    """Load parsed document from JSON"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def index_all_documents(parsed_dir: str = "outputs/parsed"):
    """Index all parsed documents"""

    parsed_dir = Path(parsed_dir)

    if not parsed_dir.exists():
        logger.error(f"Parsed directory not found: {parsed_dir}")
        logger.error("Please run batch_processor.py first")
        return

    # Find all parsed docs
    json_files = list(parsed_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "processing_summary.json"]

    if not json_files:
        logger.error("No parsed documents found")
        return

    logger.info(f"Found {len(json_files)} documents to index")

    # Initialize embedding manager
    em = EmbeddingManager()

    # Clear existing data (optional - comment out to keep existing)
    # em.clear_collection()

    # Index each document
    total_chunks = 0

    for json_file in tqdm(json_files, desc="Indexing documents"):
        try:
            # Load parsed data (note: full text not in JSON)
            # Need to re-parse or load from separate text file

            # For now, load what we have
            parsed_data = load_parsed_document(json_file)

            # Get original PDF path
            pdf_path = Path(parsed_data['metadata']['filepath'])

            if not pdf_path.exists():
                logger.warning(f"Original PDF not found: {pdf_path}, skipping")
                continue

            # Re-parse to get full text (TODO: optimize by saving full text separately)
            from document_parser import WellReportParser
            parser = WellReportParser(enable_ocr=False)  # Faster without OCR
            full_data = parser.parse_pdf(str(pdf_path))

            # Add to vector store
            doc_id = pdf_path.stem
            chunks_added = em.add_document(
                doc_id=doc_id,
                text=full_data['text'],
                tables=full_data['tables'],
                metadata=full_data['metadata']
            )

            total_chunks += chunks_added
            logger.info(f"✓ Indexed {doc_id}: {chunks_added} chunks")

        except Exception as e:
            logger.error(f"Failed to index {json_file.name}: {e}")

    # Print summary
    stats = em.get_stats()

    print("\n" + "="*60)
    print("INDEXING COMPLETE")
    print("="*60)
    print(f"Documents indexed: {len(json_files)}")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Average chunks per doc: {stats['total_chunks'] / len(json_files):.1f}")
    print("="*60)


if __name__ == '__main__':
    index_all_documents()
```

**Run:**
```bash
python scripts/index_documents.py
```

**Expected Output:**
```
Indexing documents: 100%|████████| 8/8 [01:30<00:00, 11.3s/it]
============================================================
INDEXING COMPLETE
============================================================
Documents indexed: 8
Total chunks: 856
Average chunks per doc: 107.0
============================================================
```

---

### Hour 3-4: Query Testing

#### Task 2.1: Test Retrieval Quality (1 hour)

**File:** `tests/test_retrieval.py`
```python
"""
Test retrieval quality before adding LLM
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from embeddings import EmbeddingManager
from logger_config import setup_logger

logger = setup_logger(__name__)


def test_retrieval():
    """Test if retrieval returns relevant chunks"""

    em = EmbeddingManager()

    # Test queries
    test_queries = [
        "What is the well name?",
        "What is the drilling location?",
        "When was drilling completed?",
        "What is the total depth?",
        "What casing sizes were used?"
    ]

    print("\n" + "="*60)
    print("RETRIEVAL QUALITY TEST")
    print("="*60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-"*60)

        results = em.query(query, n_results=3)

        for i, (doc, distance) in enumerate(zip(results['documents'], results['distances'])):
            print(f"\n[Result {i+1}] (distance: {distance:.3f})")
            print(f"Source: {results['metadatas'][i]['filename']}")
            print(f"Type: {results['metadatas'][i]['chunk_type']}")
            print(f"Content preview: {doc[:200]}...")

        print("-"*60)

    print("\n" + "="*60)

    # Manual validation prompt
    print("\nMANUAL VALIDATION:")
    print("Review the results above. For each query:")
    print("1. Are the retrieved chunks relevant?")
    print("2. Do they contain information to answer the question?")
    print("3. Is the most relevant chunk ranked first?")
    print("\n" + "="*60)


if __name__ == '__main__':
    test_retrieval()
```

**Run:**
```bash
python tests/test_retrieval.py
```

**Manual Check:**
- Are retrieved chunks relevant? ✓/✗
- Do they answer the question? ✓/✗
- Ranking good? ✓/✗

---

**Day 2 Checkpoint:**
✅ Embedding model loaded
✅ All documents indexed in ChromaDB
✅ Retrieval returns relevant chunks
✅ Average <2s per query

**Tomorrow:** Build RAG system with LLM

---

## Day 3: RAG System Implementation
**Goal:** End-to-end RAG query system
**Time Allocation:** 8 hours

### Hour 1-4: RAG System Core

**File:** `src/rag_system.py`

[FULL IMPLEMENTATION PROVIDED IN PLAN - SEE ABOVE]

### Hour 4-6: Interactive Testing

**File:** `examples/sub_challenge_1_demo.py`
```python
"""
Interactive demo for Sub-Challenge 1
Test RAG system interactively
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from embeddings import EmbeddingManager
from rag_system import RAGSystem
from logger_config import setup_logger

logger = setup_logger(__name__)


def interactive_demo():
    """Interactive RAG demo"""

    print("="*60)
    print("SUB-CHALLENGE 1: RAG DEMO")
    print("="*60)
    print("Loading models...")

    # Initialize
    em = EmbeddingManager()
    rag = RAGSystem(em)

    print("✓ Ready!")
    print("\nType 'quit' to exit")
    print("Type 'stats' to see system info")
    print("-"*60)

    while True:
        print("\n")
        question = input("Question: ").strip()

        if question.lower() == 'quit':
            break

        if question.lower() == 'stats':
            stats = em.get_stats()
            print(f"\nSystem Statistics:")
            print(f"  Total chunks: {stats['total_chunks']}")
            print(f"  Model: {stats['model']}")
            continue

        if not question:
            continue

        # Query
        print("\nThinking...")
        result = rag.query(question)

        print("\n" + "-"*60)
        print("ANSWER:")
        print("-"*60)
        print(result['answer'])
        print("-"*60)
        print(f"Time: {result['metadata']['generation_time']:.2f}s")
        print(f"Sources: {len(result['sources'])} chunks used")


if __name__ == '__main__':
    interactive_demo()
```

**Run:**
```bash
python examples/sub_challenge_1_demo.py
```

---

### Hour 6-8: Quality Testing

**Create automated test suite**

[CONTINUES WITH DETAILED TESTING PROTOCOL...]

---

**I'll continue with Days 4-7 if you want the complete detail. Would you like me to:**

1. ✅ **Continue with full Days 4-7 detail?** (Testing, optimization, edge cases)
2. ✅ **Start implementing Day 1 code now?** (Begin actual development)
3. ✅ **Create a quick-start script?** (Automated setup)

Which would you prefer? 🚀