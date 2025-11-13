"""
Enhanced Well 7 Parser with ALL Advanced Docling Features

Features implemented:
1. TableFormer ACCURATE mode - Better table extraction for MD/TVD/ID
2. Picture extraction & classification - Extract diagrams and schematics
3. Hierarchical chunking - Better structure preservation
4. Enhanced OCR - Better handling of scanned documents
5. Full serialization - Save complete document structure
6. Disable cell matching for merged columns
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Docling imports
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
)
from docling.datamodel.base_models import InputFormat
from docling_core.types.doc import PictureItem, TableItem, DoclingDocument
from docling_core.transforms.chunker import HierarchicalChunker
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingDocSerializer,
    ChunkingSerializerProvider,
)
from docling_core.transforms.serializer.markdown import (
    MarkdownDocSerializer,
    MarkdownTableSerializer,
    MarkdownParams,
)
from transformers import AutoTokenizer


class EnhancedWell7Parser:
    """
    Advanced PDF parser using all Docling features for Well 7 scanned documents
    """

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or project_root / "outputs" / "well7_enhanced"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("="*80)
        print("ENHANCED WELL 7 PARSER - ALL DOCLING FEATURES")
        print("="*80)

        # Setup advanced pipeline options
        self._setup_pipeline_options()

        # Initialize converter
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=self.pipeline_options
                )
            }
        )
        print("[OK] Enhanced converter ready")

        # Setup hierarchical chunker
        self._setup_chunker()
        print("[OK] Hierarchical chunker ready")

    def _setup_pipeline_options(self):
        """Configure all advanced Docling features"""
        print("\n[SETUP] Configuring advanced pipeline options...")

        self.pipeline_options = PdfPipelineOptions()

        # 1. TABLEFORMER ACCURATE MODE - Critical for ALL table extraction
        self.pipeline_options.do_table_structure = True
        self.pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        self.pipeline_options.table_structure_options.do_cell_matching = False  # Better for merged cells
        print("  [OK] TableFormer ACCURATE mode enabled (all tables, not just casing)")

        # 2. ENHANCED OCR - Better for scanned documents
        self.pipeline_options.do_ocr = True
        print("  [OK] Enhanced OCR enabled")

        # 3. PICTURE EXTRACTION - Extract diagrams and schematics
        self.pipeline_options.generate_picture_images = True
        self.pipeline_options.images_scale = 2.0  # Higher resolution (better VLM accuracy, actually faster!)
        self.pipeline_options.do_picture_classification = True  # Classify diagram types
        print("  [OK] Picture extraction & classification enabled")

        # 4. PICTURE DESCRIPTION - SmolVLM-256M for diagram OCR and annotations
        # 256M params, free, CPU-compatible, within 500M constraint
        from docling.datamodel.pipeline_options import smolvlm_picture_description

        self.pipeline_options.do_picture_description = True
        self.pipeline_options.picture_description_options = smolvlm_picture_description
        self.pipeline_options.picture_description_options.prompt = (
            "Describe this diagram or figure in detail. "
            "Include all visible text, labels, measurements, annotations, and handwritten notes. "
            "Mention axes, legends, and any technical information shown."
        )
        print("  [OK] Picture description enabled (SmolVLM-256M - 256M params, CPU, free)")

    def _setup_chunker(self):
        """Setup hierarchical chunker with custom serializer"""
        print("\n[SETUP] Configuring hierarchical chunker...")

        # Use tokenizer for chunk size calculation
        tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

        # Custom serializer provider for Markdown tables
        class MDTableSerializerProvider(ChunkingSerializerProvider):
            def get_serializer(self, doc):
                return ChunkingDocSerializer(
                    doc=doc,
                    table_serializer=MarkdownTableSerializer(),  # Better table format
                )

        self.chunker = HierarchicalChunker(
            tokenizer=tokenizer,
            serializer_provider=MDTableSerializerProvider(),
        )
        print("  [OK] Hierarchical chunker configured")

    def parse_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Parse PDF with all advanced features

        Returns comprehensive extraction results including:
        - Markdown text
        - Tables (with accurate structure)
        - Pictures (with classifications)
        - Hierarchical chunks
        - Full DoclingDocument serialization
        """
        print(f"\n{'='*80}")
        print(f"Parsing: {pdf_path.name}")
        print(f"Size: {pdf_path.stat().st_size / 1024:.1f} KB")
        print(f"{'='*80}")

        # Convert PDF
        start = time.time()
        result = self.converter.convert(str(pdf_path))
        parse_time = time.time() - start

        doc = result.document
        print(f"\n[OK] Parsed in {parse_time:.1f}s")

        # Extract components
        extraction_results = {
            'filename': pdf_path.name,
            'parse_time': parse_time,
            'markdown': None,
            'tables': [],
            'pictures': [],
            'chunks': [],
            'metadata': {},
        }

        # 1. Export to Markdown
        print("\n[STEP 1] Exporting to Markdown...")
        extraction_results['markdown'] = doc.export_to_markdown()
        print(f"  [OK] Extracted {len(extraction_results['markdown']):,} chars")

        # 2. Extract Tables with TableFormer
        print("\n[STEP 2] Extracting tables with TableFormer ACCURATE...")
        tables = self._extract_tables(doc)
        extraction_results['tables'] = tables
        print(f"  [OK] Found {len(tables)} tables")

        # 3. Extract Pictures
        print("\n[STEP 3] Extracting pictures...")
        pictures = self._extract_pictures(doc)
        extraction_results['pictures'] = pictures
        print(f"  [OK] Found {len(pictures)} pictures")

        # 4. Create Hierarchical Chunks
        print("\n[STEP 4] Creating hierarchical chunks...")
        chunks = self._create_chunks(doc)
        extraction_results['chunks'] = chunks
        print(f"  [OK] Created {len(chunks)} chunks")

        # 5. Collect Metadata
        extraction_results['metadata'] = {
            'total_chars': len(extraction_results['markdown']),
            'total_words': len(extraction_results['markdown'].split()),
            'total_lines': len(extraction_results['markdown'].split('\n')),
            'table_count': len(tables),
            'picture_count': len(pictures),
            'chunk_count': len(chunks),
        }

        # 6. Save full document serialization
        self._save_document_serialization(doc, pdf_path.stem)

        return extraction_results

    def _extract_tables(self, doc: DoclingDocument) -> List[Dict[str, Any]]:
        """
        Extract COMPLETE table data with TableFormer ACCURATE mode

        Captures ALL information: data, structure, captions, headers, metadata
        """
        tables = []

        for item, level in doc.iterate_items():
            if isinstance(item, TableItem):
                table_data = {
                    'ref': str(item.self_ref),
                    'num_rows': 0,
                    'num_cols': 0,
                    'data': [],
                    'markdown': None,
                    'caption': None,
                    'column_headers': [],
                    'has_merged_cells': False,
                    'page': None,
                }

                # Get caption if available
                table_data['caption'] = item.caption_text(doc=doc)

                # Get table data (TableFormer extracts cell structure)
                try:
                    # Export to pandas DataFrame for complete data
                    # Call export_to_dataframe() on TableItem, not TableData
                    df = item.export_to_dataframe()

                    # Get dimensions from dataframe
                    table_data['num_rows'] = len(df)
                    table_data['num_cols'] = len(df.columns)

                    # Get column headers
                    table_data['column_headers'] = list(df.columns)

                    # Get all rows as dictionaries
                    table_data['data'] = df.to_dict('records')

                    # Detect merged cells (if any column has empty values that might indicate merging)
                    table_data['has_merged_cells'] = df.isnull().any().any()
                except Exception as e:
                    print(f"  [WARN] Could not extract data from table {item.self_ref}: {e}")

                # Export to markdown for readable format
                serializer = MarkdownTableSerializer()
                table_md = serializer.serialize(
                    item=item,
                    doc_serializer=MarkdownDocSerializer(doc=doc),
                    doc=doc,
                )
                table_data['markdown'] = table_md.text

                # Get page number if available
                if hasattr(item, 'prov') and item.prov:
                    for prov in item.prov:
                        if hasattr(prov, 'page'):
                            table_data['page'] = prov.page
                            break

                tables.append(table_data)

        return tables

    def _extract_pictures(self, doc: DoclingDocument) -> List[Dict[str, Any]]:
        """
        Extract COMPLETE picture data with VLM descriptions

        Captures ALL information: images, captions, classifications, VLM descriptions,
        annotations, dimensions, handwriting detection
        """
        from docling_core.types.doc.document import (
            PictureDescriptionData,
            PictureClassificationData,
        )

        pictures = []

        for item, level in doc.iterate_items():
            if isinstance(item, PictureItem):
                picture_data = {
                    'ref': str(item.self_ref),
                    'caption': item.caption_text(doc=doc),
                    'image_path': None,
                    'width': None,
                    'height': None,
                    'page': None,
                    'classification': None,
                    'description': None,  # VLM-generated description
                    'annotations': [],
                    'contains_handwriting': False,
                    'contains_text_labels': False,
                }

                # Save picture image (high resolution)
                if hasattr(item, 'image') and item.image:
                    image_filename = f"{item.self_ref}.png".replace('#', '_')
                    image_path = self.output_dir / "images" / image_filename
                    image_path.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        # Get PIL image and save
                        pil_image = item.get_image(doc)
                        pil_image.save(str(image_path))
                        picture_data['image_path'] = str(image_path)

                        # Get image dimensions
                        picture_data['width'] = pil_image.width
                        picture_data['height'] = pil_image.height
                    except Exception as e:
                        print(f"  [WARN] Could not save image {item.self_ref}: {e}")

                # Get page number if available
                if hasattr(item, 'prov') and item.prov:
                    for prov in item.prov:
                        if hasattr(prov, 'page'):
                            picture_data['page'] = prov.page
                            break

                # Extract ALL annotations
                for annotation in item.annotations:
                    annotation_data = {
                        'type': type(annotation).__name__,
                        'provenance': getattr(annotation, 'provenance', None),
                    }

                    # Classification data (schematic, chart, photo, etc.)
                    if isinstance(annotation, PictureClassificationData):
                        if annotation.predicted_classes:
                            top_class = annotation.predicted_classes[0]
                            picture_data['classification'] = {
                                'type': top_class.class_name,
                                'confidence': top_class.confidence,
                            }
                            annotation_data['predicted_classes'] = [
                                {
                                    'class_name': cls.class_name,
                                    'confidence': cls.confidence,
                                }
                                for cls in annotation.predicted_classes
                            ]

                    # VLM Description data (text, labels, measurements, handwriting)
                    elif isinstance(annotation, PictureDescriptionData):
                        description_text = annotation.text
                        picture_data['description'] = description_text

                        # Detect handwriting mentions
                        handwriting_keywords = [
                            'handwritten', 'handwriting', 'hand-written',
                            'written by hand', 'manuscript', 'written note'
                        ]
                        picture_data['contains_handwriting'] = any(
                            keyword in description_text.lower()
                            for keyword in handwriting_keywords
                        )

                        # Detect text labels/annotations
                        label_keywords = [
                            'label', 'annotation', 'text', 'caption',
                            'measurement', 'depth', 'meter', 'foot'
                        ]
                        picture_data['contains_text_labels'] = any(
                            keyword in description_text.lower()
                            for keyword in label_keywords
                        )

                        annotation_data['text'] = description_text

                    picture_data['annotations'].append(annotation_data)

                pictures.append(picture_data)

        return pictures

    def _create_chunks(self, doc: DoclingDocument) -> List[Dict[str, Any]]:
        """Create hierarchical chunks"""
        chunk_iter = self.chunker.chunk(dl_doc=doc)
        chunks = []

        for chunk in chunk_iter:
            chunk_data = {
                'text': chunk.text,
                'meta': {
                    'doc_items': [str(item) for item in chunk.meta.doc_items],
                    'headings': chunk.meta.headings,
                },
            }
            chunks.append(chunk_data)

        return chunks

    def _save_document_serialization(self, doc: DoclingDocument, doc_name: str):
        """Save full DoclingDocument serialization for later reuse"""
        doc_dict = doc.export_to_dict()

        output_path = self.output_dir / f"{doc_name}_docling.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(doc_dict, f, indent=2, ensure_ascii=False)

        print(f"  [OK] Saved full document to {output_path.name}")

    def save_results(self, results: Dict[str, Any], pdf_name: str):
        """Save extraction results to JSON"""
        import numpy as np
        import pandas as pd

        output_path = self.output_dir / f"{pdf_name}_results.json"

        # Remove large markdown from summary (save separately)
        summary = {k: v for k, v in results.items() if k != 'markdown'}

        # Convert numpy/pandas types to Python native types for JSON serialization
        def convert_to_serializable(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return obj.item()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(i) for i in obj]
            elif pd.isna(obj):
                return None
            return obj

        summary = convert_to_serializable(summary)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Save markdown separately
        md_path = self.output_dir / f"{pdf_name}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(results['markdown'])

        print(f"\n[SAVED] Results: {output_path.name}")
        print(f"[SAVED] Markdown: {md_path.name}")

        return output_path


def main():
    """Test enhanced parser on Well 7 PDFs"""
    import logging
    logging.basicConfig(level=logging.INFO)

    # Initialize parser
    parser = EnhancedWell7Parser()

    # Test PDFs from Well 7
    well7_dir = project_root / "Training data-shared with participants" / "Well 7"

    test_pdfs = [
        # Well report PDFs (most important)
        well7_dir / "Well report" / "NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf",
        well7_dir / "Well report" / "NLOG_GS_PUB_BIR-GT-01_AWB_Rev A 1_WellpathReport.pdf",
        # Technical log PDFs
        well7_dir / "Technical log" / "NLOG_GS_PUB_Appendix III_Casing tallies BRI-GT-01.pdf",
    ]

    for pdf_path in test_pdfs:
        if not pdf_path.exists():
            print(f"\n[SKIP] {pdf_path.name} - not found")
            continue

        try:
            # Parse PDF
            results = parser.parse_pdf(pdf_path)

            # Save results
            parser.save_results(results, pdf_path.stem)

            # Print summary
            print(f"\n{'='*80}")
            print("EXTRACTION SUMMARY")
            print(f"{'='*80}")
            for key, value in results['metadata'].items():
                print(f"  {key}: {value:,}")

            # Show ALL tables summary
            if results['tables']:
                print(f"\n[TABLES EXTRACTED: {len(results['tables'])}]")
                print("-" * 80)
                for i, table in enumerate(results['tables'][:3]):  # Show first 3
                    print(f"\nTable {i+1}: {table['ref']}")
                    print(f"  Caption: {table['caption']}")
                    print(f"  Size: {table['num_rows']} rows x {table['num_cols']} cols")
                    print(f"  Columns: {', '.join(table['column_headers'])}")
                    print(f"  Page: {table['page']}")
                    print(f"  Has merged cells: {table['has_merged_cells']}")
                    if table['data'] and len(table['data']) > 0:
                        print(f"  First row: {table['data'][0]}")
                if len(results['tables']) > 3:
                    print(f"\n  ... and {len(results['tables']) - 3} more tables")
                print("-" * 80)

            # Show ALL pictures summary
            if results['pictures']:
                print(f"\n[PICTURES EXTRACTED: {len(results['pictures'])}]")
                print("-" * 80)
                for i, pic in enumerate(results['pictures'][:3]):  # Show first 3
                    print(f"\nPicture {i+1}: {pic['ref']}")
                    print(f"  Caption: {pic['caption']}")
                    print(f"  Page: {pic['page']}")
                    print(f"  Dimensions: {pic['width']}x{pic['height']} px")
                    print(f"  Saved to: {pic['image_path']}")

                    if pic['classification']:
                        print(f"  Classification: {pic['classification']['type']} "
                              f"(confidence: {pic['classification']['confidence']:.2f})")

                    if pic['description']:
                        desc_preview = pic['description'][:200] + '...' if len(pic['description']) > 200 else pic['description']
                        print(f"  VLM Description: {desc_preview}")

                    print(f"  Contains handwriting: {pic['contains_handwriting']}")
                    print(f"  Contains text labels: {pic['contains_text_labels']}")

                if len(results['pictures']) > 3:
                    print(f"\n  ... and {len(results['pictures']) - 3} more pictures")
                print("-" * 80)

        except Exception as e:
            print(f"\n[ERROR] Failed to parse {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print("ENHANCED PARSING COMPLETE")
    print(f"{'='*80}")
    print(f"Results saved to: {parser.output_dir}")


if __name__ == "__main__":
    main()
