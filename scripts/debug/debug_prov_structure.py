"""
Debug script to understand Docling provenance structure
"""

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions

pdf_path = "Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf"

print("="*80)
print("DEBUGGING DOCLING PROVENANCE STRUCTURE")
print("="*80)

# Configure OCR
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True

converter = DocumentConverter(
    format_options={"pdf": PdfFormatOption(pipeline_options=pipeline_options)}
)

print("\n[INFO] Converting PDF with OCR...")
result = converter.convert(pdf_path)

print(f"\n[INFO] Document has {len(result.document.body)} items")

# Check first 10 items
for i, item in enumerate(result.document.body[:10]):
    print(f"\n[Item {i}]")
    print(f"  Type: {type(item)}")
    print(f"  Has text: {hasattr(item, 'text')}")

    if hasattr(item, 'text'):
        text_preview = item.text[:50] if item.text else "(empty)"
        print(f"  Text: {text_preview}...")

    print(f"  Has prov: {hasattr(item, 'prov')}")

    if hasattr(item, 'prov'):
        print(f"  Prov type: {type(item.prov)}")
        print(f"  Prov length: {len(item.prov) if item.prov else 0}")

        if item.prov and len(item.prov) > 0:
            prov_item = item.prov[0]
            print(f"  Prov[0] type: {type(prov_item)}")
            print(f"  Prov[0] value: {prov_item}")

            # Try different ways to get page number
            if isinstance(prov_item, tuple):
                print(f"  Prov[0][0] (page?): {prov_item[0]}")
                print(f"  Prov[0][1] (bbox?): {prov_item[1]}")
            elif hasattr(prov_item, 'page'):
                print(f"  Prov[0].page: {prov_item.page}")
            elif hasattr(prov_item, '__dict__'):
                print(f"  Prov[0].__dict__: {prov_item.__dict__}")

print("\n" + "="*80)
print("GROUPING BY PAGE")
print("="*80)

pages_text = {}

for item in result.document.body:
    try:
        if hasattr(item, 'prov') and item.prov and len(item.prov) > 0:
            prov_item = item.prov[0]

            # Try multiple ways to extract page number
            if isinstance(prov_item, tuple) and len(prov_item) >= 2:
                page_no = prov_item[0]
            elif hasattr(prov_item, 'page'):
                page_no = prov_item.page
            elif hasattr(prov_item, 'page_no'):
                page_no = prov_item.page_no
            else:
                page_no = 1
        else:
            page_no = 1
    except (AttributeError, IndexError, TypeError) as e:
        print(f"[ERROR] Failed to get page: {e}")
        page_no = 1

    if page_no not in pages_text:
        pages_text[page_no] = []

    if hasattr(item, 'text'):
        pages_text[page_no].append(item.text)

print(f"\nTotal pages extracted: {len(pages_text)}")
print(f"Pages: {sorted(pages_text.keys())}")

for page_no in sorted(pages_text.keys())[:5]:
    text_count = len(pages_text[page_no])
    total_chars = sum(len(t) for t in pages_text[page_no])
    print(f"  Page {page_no}: {text_count} items, {total_chars} chars")
