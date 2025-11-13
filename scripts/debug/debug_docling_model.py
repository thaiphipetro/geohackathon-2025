"""
Debug: Understand Docling's document model structure
"""

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from pathlib import Path

pdf_path = "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf"

if not Path(pdf_path).exists():
    print(f"[ERROR] PDF not found: {pdf_path}")
    exit(1)

# Configure with OCR
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True

converter = DocumentConverter(
    format_options={
        "pdf": PdfFormatOption(pipeline_options=pipeline_options)
    }
)

print("Converting PDF with OCR...")
result = converter.convert(pdf_path)
doc_model = result.document

print(f"\nDocument model type: {type(doc_model)}")
print(f"Available attributes: {dir(doc_model)}")

# Check if texts attribute exists
if hasattr(doc_model, 'texts'):
    print(f"\nDocument has 'texts' attribute")
    print(f"Number of text items: {len(doc_model.texts)}")
    if len(doc_model.texts) > 0:
        first_item = doc_model.texts[0]
        print(f"First text item type: {type(first_item)}")
        print(f"First text item attributes: {dir(first_item)}")
else:
    print("\n[WARN] Document does NOT have 'texts' attribute")

# Check for other attributes that might contain page-wise content
for attr in ['pages', 'body', 'main_text', 'page_texts']:
    if hasattr(doc_model, attr):
        print(f"\n[FOUND] Document has '{attr}' attribute")
        value = getattr(doc_model, attr)
        print(f"  Type: {type(value)}")
        if hasattr(value, '__len__'):
            print(f"  Length: {len(value)}")
