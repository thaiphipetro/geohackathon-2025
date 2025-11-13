"""
Test Granite-Docling-258M VLM for Well 7 TOC extraction

Standalone script - NO integration with existing code
Tests if Granite can extract TOC better than Llama 3.2 3B LLM

Current baseline (Llama 3B):
- 15 entries extracted
- 8 missing pages (53% fail)
- 47% page accuracy

Goal: Test if Granite achieves >= 80% page accuracy
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_vlm_pipeline():
    """
    Phase A: Test Docling's VLM pipeline with Granite-Docling-258M
    Simple approach - let Granite process entire document
    """
    print("="*80)
    print("PHASE A: GRANITE-DOCLING-258M VLM PIPELINE TEST")
    print("="*80)

    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption
        from docling.pipeline.vlm_pipeline import VlmPipeline
        from docling.datamodel.pipeline_options import VlmPipelineOptions
        from docling.datamodel import vlm_model_specs
    except ImportError as e:
        print(f"\n[ERROR] Failed to import Docling VLM components: {e}")
        print("[INFO] You may need to upgrade Docling: pip install --upgrade docling")
        return {'success': False, 'reason': 'Import error'}

    pdf_path = Path("Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf")

    if not pdf_path.exists():
        print(f"\n[ERROR] PDF not found: {pdf_path}")
        return {'success': False, 'reason': 'File not found'}

    print(f"\n[1/3] Setting up Granite-Docling VLM pipeline...")
    print(f"  Model: ibm-granite/granite-docling-258M")
    print(f"  Framework: Transformers")

    try:
        pipeline_options = VlmPipelineOptions(
            vlm_options=vlm_model_specs.GRANITEDOCLING_TRANSFORMERS
        )

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options
                )
            }
        )
    except Exception as e:
        print(f"\n[ERROR] Failed to setup VLM pipeline: {e}")
        return {'success': False, 'reason': str(e)}

    print(f"\n[2/3] Converting Well 7 EOWR with Granite-Docling...")
    print(f"  This may take a few minutes on first run (model download)")
    print(f"  PDF: {pdf_path.name}")

    start = time.time()
    try:
        result = converter.convert(str(pdf_path))
        convert_time = time.time() - start
    except Exception as e:
        print(f"\n[ERROR] Conversion failed: {e}")
        return {'success': False, 'reason': str(e)}

    markdown = result.document.export_to_markdown()

    print(f"\n[3/3] Conversion complete in {convert_time:.1f}s")
    print(f"  Markdown length: {len(markdown):,} chars")
    print(f"  Pages processed: {len(result.document.pages) if hasattr(result.document, 'pages') else 'Unknown'}")

    # Extract TOC from markdown using existing extractors
    print(f"\n[4/5] Extracting TOC from Granite output...")

    try:
        # Import existing TOC extraction tools
        sys.path.insert(0, str(Path(__file__).parent))
        from robust_toc_extractor import RobustTOCExtractor
        from analyze_all_tocs import find_toc_boundaries

        lines = markdown.split('\n')
        toc_start, toc_end = find_toc_boundaries(lines)

        if toc_start >= 0:
            print(f"  TOC boundaries found: lines {toc_start}-{toc_end}")
            toc_lines = lines[toc_start:toc_end]

            extractor = RobustTOCExtractor()
            toc_entries, pattern = extractor.extract(toc_lines)

            print(f"\n[5/5] TOC Extraction Results:")
            print(f"  Pattern used: {pattern}")
            print(f"  Entries extracted: {len(toc_entries)}")

            if len(toc_entries) >= 3:
                print(f"\n  First 5 entries:")
                for i, entry in enumerate(toc_entries[:5], 1):
                    num = entry.get('number', 'N/A')
                    title = entry.get('title', 'Unknown')
                    page = entry.get('page', 0)
                    print(f"    {i}. {num:5s} - {title:50s} (page {page})")

                if len(toc_entries) > 5:
                    print(f"    ... and {len(toc_entries) - 5} more entries")

                # Calculate page accuracy
                missing_pages = sum(1 for e in toc_entries if e.get('page', 0) == 0)
                accurate_pages = len(toc_entries) - missing_pages
                accuracy = (accurate_pages / len(toc_entries) * 100) if len(toc_entries) > 0 else 0

                print(f"\n  Page accuracy: {accuracy:.1f}% ({accurate_pages}/{len(toc_entries)} pages found)")

                if missing_pages > 0:
                    print(f"  Missing pages: {missing_pages}")

                return {
                    'success': True,
                    'entries': len(toc_entries),
                    'pattern': pattern,
                    'accurate_pages': accurate_pages,
                    'missing_pages': missing_pages,
                    'page_accuracy': accuracy,
                    'convert_time': convert_time,
                    'toc_entries': toc_entries
                }
            else:
                print(f"  [WARN] Only {len(toc_entries)} entries extracted (need >= 3)")
                return {'success': False, 'reason': f'Only {len(toc_entries)} entries'}
        else:
            print(f"  [WARN] No TOC boundaries found in markdown")
            return {'success': False, 'reason': 'No TOC found'}

    except Exception as e:
        print(f"\n[ERROR] TOC extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'reason': str(e)}


def test_transformers_api():
    """
    Phase B: Test direct transformers API with single-page extraction
    More control over prompt and output format
    """
    print("\n" + "="*80)
    print("PHASE B: GRANITE-DOCLING-258M TRANSFORMERS API TEST (SINGLE PAGE)")
    print("="*80)

    try:
        from transformers import AutoProcessor, AutoModelForVision2Seq
        from PIL import Image
        import torch
        import fitz  # PyMuPDF
    except ImportError as e:
        print(f"\n[ERROR] Failed to import required libraries: {e}")
        return {'success': False, 'reason': 'Import error'}

    pdf_path = Path("Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf")

    if not pdf_path.exists():
        print(f"\n[ERROR] PDF not found: {pdf_path}")
        return {'success': False, 'reason': 'File not found'}

    # Create output directory
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    print(f"\n[1/5] Extracting TOC page 3 as image...")
    try:
        doc = fitz.open(str(pdf_path))
        page = doc[2]  # page 3 (0-indexed)

        # High resolution for better OCR
        mat = fitz.Matrix(2, 2)  # 2x scale
        pix = page.get_pixmap(matrix=mat)

        img_path = output_dir / "test_well7_toc_page3.png"
        pix.save(str(img_path))

        image = Image.open(img_path)
        doc.close()

        print(f"  Saved to {img_path}")
        print(f"  Image size: {image.width}x{image.height} pixels")
    except Exception as e:
        print(f"\n[ERROR] Failed to extract page image: {e}")
        return {'success': False, 'reason': str(e)}

    print(f"\n[2/5] Loading Granite-Docling-258M model...")
    print(f"  This may take a few minutes on first run (model download)")

    start = time.time()
    try:
        processor = AutoProcessor.from_pretrained("ibm-granite/granite-docling-258M")
        model = AutoModelForVision2Seq.from_pretrained(
            "ibm-granite/granite-docling-258M",
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32
        )

        # Move to GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)

        load_time = time.time() - start
        print(f"  Model loaded in {load_time:.1f}s")
        print(f"  Device: {device}")
    except Exception as e:
        print(f"\n[ERROR] Failed to load model: {e}")
        return {'success': False, 'reason': str(e)}

    print(f"\n[3/5] Running VLM inference on TOC page...")

    # Try different prompts for best results
    prompts = [
        "Convert this page to docling format. Extract the table of contents with section numbers, titles, and page numbers.",
        "Extract the table of contents from this page. Return section numbers, titles, and page numbers in structured format.",
        "OCR this page and identify all table of contents entries with their section numbers, titles, and page numbers."
    ]

    results = []

    for prompt_idx, prompt_text in enumerate(prompts, 1):
        print(f"\n  Trying prompt {prompt_idx}/3...")
        print(f"  Prompt: {prompt_text[:80]}...")

        try:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt_text}
                ]
            }]

            prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
            inputs = processor(text=prompt, images=[image], return_tensors="pt").to(device)

            start = time.time()
            with torch.no_grad():
                generated_ids = model.generate(**inputs, max_new_tokens=1024)
            inference_time = time.time() - start

            toc_text = processor.decode(generated_ids[0], skip_special_tokens=True)

            print(f"  Inference completed in {inference_time:.1f}s")
            print(f"  Output length: {len(toc_text)} chars")

            results.append({
                'prompt': prompt_text,
                'output': toc_text,
                'inference_time': inference_time
            })

        except Exception as e:
            print(f"  [ERROR] Inference failed: {e}")
            continue

    print(f"\n[4/5] VLM Outputs:")

    for i, res in enumerate(results, 1):
        print(f"\n  --- Prompt {i} Output ---")
        print("-" * 80)
        print(res['output'][:500])  # First 500 chars
        if len(res['output']) > 500:
            print(f"... ({len(res['output']) - 500} more characters)")
        print("-" * 80)

    print(f"\n[5/5] Analysis:")
    print(f"  Total prompts tested: {len(prompts)}")
    print(f"  Successful runs: {len(results)}")

    if results:
        print(f"\n  Best result (longest output):")
        best = max(results, key=lambda x: len(x['output']))
        print(f"  Prompt: {best['prompt'][:80]}...")
        print(f"  Output length: {len(best['output'])} chars")
        print(f"  Inference time: {best['inference_time']:.1f}s")

        return {
            'success': True,
            'results': results,
            'best_output': best['output'],
            'load_time': load_time,
            'inference_time': best['inference_time']
        }
    else:
        return {'success': False, 'reason': 'All prompts failed'}


def print_comparison(result_a):
    """Print comparison table between Llama 3B and Granite-Docling"""
    print("\n" + "="*80)
    print("COMPARISON: LLAMA 3.2 3B LLM vs GRANITE-DOCLING-258M VLM")
    print("="*80)

    # Pre-compute formatted strings to avoid nested f-string issues
    granite_accurate = f"{result_a['accurate_pages']}/{result_a['entries']} ({result_a['page_accuracy']:.1f}%)"
    granite_missing = f"{result_a['missing_pages']} ({result_a['missing_pages']/result_a['entries']*100:.1f}%)"
    granite_time = f"{result_a['convert_time']:.1f}s (full doc)"

    print(f"\n{'Metric':<30} {'Llama 3B (current)':<25} {'Granite-Docling':<25}")
    print("-" * 80)
    print(f"{'Entries extracted':<30} {15:<25} {result_a['entries']:<25}")
    print(f"{'Accurate pages':<30} {'7/15 (47%)':<25} {granite_accurate:<25}")
    print(f"{'Missing pages':<30} {'8 (53%)':<25} {granite_missing:<25}")
    print(f"{'Model size':<30} {'3B (exception)':<25} {'258M (compliant)':<25}")
    print(f"{'Processing time':<30} {'~8s (LLM only)':<25} {granite_time:<25}")
    print(f"{'Pattern used':<30} {'LLM parsing':<25} {result_a['pattern']:<25}")


def print_recommendation(result_a):
    """Print recommendation based on results"""
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)

    accuracy = result_a['page_accuracy']

    if accuracy >= 80:
        print("\n[EXCELLENT] Granite-Docling significantly better than LLM!")
        print(f"  Page accuracy: {accuracy:.1f}% (target: >= 80%)")
        print(f"\nIMPACT:")
        print(f"  - Can enable section-aware chunking for Well 7")
        print(f"  - Better chunk boundaries = better retrieval accuracy")
        print(f"  - Meets <500M param constraint (258M)")
        print(f"\nNEXT STEPS:")
        print(f"  1. Integrate Granite as Tier 2.5 (before LLM fallback)")
        print(f"  2. Re-index Well 7 with section-aware chunking")
        print(f"  3. Test on other scanned PDFs (Wells 1, 2, 4, 6)")

    elif accuracy >= 50:
        print("\n[GOOD] Granite-Docling moderately better than LLM")
        print(f"  Page accuracy: {accuracy:.1f}% (LLM: 47%)")
        print(f"\nIMPACT:")
        print(f"  - Improvement over current state")
        print(f"  - May still need hybrid approach (some pages accurate, some not)")
        print(f"  - Meets <500M param constraint (258M)")
        print(f"\nNEXT STEPS:")
        print(f"  1. Consider integration as additional fallback tier")
        print(f"  2. Use hybrid chunking (accurate pages get sections, rest get titles)")
        print(f"  3. Test on other scanned PDFs to see if pattern holds")

    else:
        print("\n[NEUTRAL] Granite-Docling not significantly better than LLM")
        print(f"  Page accuracy: {accuracy:.1f}% (LLM: 47%)")
        print(f"\nIMPACT:")
        print(f"  - No significant improvement over current approach")
        print(f"  - Both methods struggle with scrambled 2-column TOC")
        print(f"\nNEXT STEPS:")
        print(f"  1. Keep current LLM fallback approach")
        print(f"  2. Delete this test script (no benefit)")
        print(f"  3. Consider alternative approaches:")
        print(f"     - Manual TOC correction")
        print(f"     - Bbox-guided extraction (Phase B)")
        print(f"     - Different VLM models")


def main():
    """Main test function"""
    print("\n" + "="*80)
    print("GRANITE-DOCLING-258M TOC EXTRACTION TEST")
    print("Testing on Well 7 EOWR (scanned 2-column TOC)")
    print("="*80)

    print("\nBASELINE (Llama 3.2 3B LLM):")
    print("  - 15 entries extracted")
    print("  - 8 missing pages (53% fail)")
    print("  - 47% page accuracy")
    print("  - Result: titles-only mode, hierarchical chunking")

    print("\nGOAL: Test if Granite-Docling achieves >= 80% page accuracy")
    print("="*80)

    # Phase A: Try VLM pipeline first (simple approach)
    result_a = test_vlm_pipeline()

    if result_a['success']:
        # Success! Print comparison and recommendation
        print_comparison(result_a)
        print_recommendation(result_a)

        print("\n" + "="*80)
        print("TEST COMPLETE - PHASE A SUCCESS")
        print("="*80)

    else:
        # Phase A failed, try Phase B
        print(f"\n[INFO] Phase A failed: {result_a.get('reason', 'Unknown error')}")
        print(f"[INFO] Trying Phase B: Single-page transformers API with custom prompts...")

        result_b = test_transformers_api()

        if result_b['success']:
            print("\n" + "="*80)
            print("PHASE B RESULTS")
            print("="*80)

            print("\n[SUCCESS] Granite-Docling produced output via transformers API")
            print("\nFull best output:")
            print("-" * 80)
            print(result_b['best_output'])
            print("-" * 80)

            print("\n[MANUAL REVIEW REQUIRED]")
            print("  Review the output above and determine:")
            print("  1. Are TOC entries present?")
            print("  2. Are section numbers correct?")
            print("  3. Are page numbers present and accurate?")
            print("  4. Can this be parsed into structured format?")

            print("\n[NEXT STEPS]")
            print("  If output is good:")
            print("    - Create parser for this output format")
            print("    - Integrate into production pipeline")
            print("  If output is poor:")
            print("    - Try different prompts/settings")
            print("    - Or abandon Granite approach")

        else:
            print("\n" + "="*80)
            print("TEST FAILED - BOTH PHASES")
            print("="*80)

            print(f"\n[FAIL] Phase A: {result_a.get('reason', 'Unknown error')}")
            print(f"[FAIL] Phase B: {result_b.get('reason', 'Unknown error')}")

            print("\n[CONCLUSION]")
            print("  Granite-Docling-258M does not improve Well 7 TOC extraction")
            print("  Keep current Llama 3.2 3B LLM fallback approach")
            print("  Delete this test script")


if __name__ == "__main__":
    main()
