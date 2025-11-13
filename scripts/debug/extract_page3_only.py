"""
Extract ONLY page 3 from Well 7 EOWR to see what OCR extracts
"""

import sys
from pathlib import Path
import fitz
import tempfile
import os
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption

pdf_path = "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf"

print("="*80)
print("EXTRACTING PAGE 3 ONLY")
print("="*80)

# Extract page 3 only (page index 2, since 0-indexed)
doc = fitz.open(pdf_path)
page_3 = doc[2]  # Page 3 (0-indexed)

# Get raw text from PyMuPDF
raw_text = page_3.get_text()

print("\n[1] PyMuPDF Raw Text Extraction from Page 3:")
print("-"*80)
print(raw_text)
print("-"*80)
print(f"Length: {len(raw_text)} characters")

# Create temp PDF with just page 3
temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
temp_path = temp_pdf.name
temp_pdf.close()

new_doc = fitz.open()
new_doc.insert_pdf(doc, from_page=2, to_page=2)
new_doc.save(temp_path)
new_doc.close()
doc.close()

# Parse with Docling OCR
print("\n[2] Docling OCR Extraction from Page 3:")
print("-"*80)

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert(temp_path)
docling_text = result.document.export_to_markdown()

print(docling_text)
print("-"*80)
print(f"Length: {len(docling_text)} characters")

os.unlink(temp_path)

# Count lines with actual content
print("\n[3] Analysis:")
print("-"*80)

docling_lines = [line for line in docling_text.split('\n') if line.strip()]
raw_lines = [line for line in raw_text.split('\n') if line.strip()]

print(f"Docling: {len(docling_lines)} non-empty lines")
print(f"PyMuPDF: {len(raw_lines)} non-empty lines")

# Search for "Contents" keyword
if 'contents' in docling_text.lower():
    print("\nDocling: FOUND 'contents' keyword")
else:
    print("\nDocling: NO 'contents' keyword found")

if 'contents' in raw_text.lower():
    print("PyMuPDF: FOUND 'contents' keyword")
else:
    print("PyMuPDF: NO 'contents' keyword found")

# Search for numbered sections
import re
docling_numbered = [line for line in docling_lines if re.match(r'^\s*\d+\.', line)]
raw_numbered = [line for line in raw_lines if re.match(r'^\s*\d+\.', line)]

print(f"\nDocling: {len(docling_numbered)} numbered lines")
if docling_numbered:
    print("Examples:")
    for line in docling_numbered[:5]:
        print(f"  {line}")

print(f"\nPyMuPDF: {len(raw_numbered)} numbered lines")
if raw_numbered:
    print("Examples:")
    for line in raw_numbered[:5]:
        print(f"  {line}")

print("\n" + "="*80)
