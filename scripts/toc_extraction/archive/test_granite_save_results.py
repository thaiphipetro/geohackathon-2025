"""
Re-run Granite-Docling test and SAVE results to files
Based on successful test - now we save the markdown output
"""

import sys
import time
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_and_save():
    """Run Granite-Docling VLM and save all results"""

    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import PdfFormatOption
    from docling.pipeline.vlm_pipeline import VlmPipeline
    from docling.datamodel.pipeline_options import VlmPipelineOptions
    from docling.datamodel import vlm_model_specs

    pdf_path = Path("Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf")
    output_dir = Path("outputs/granite_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("GRANITE-DOCLING-258M - SAVE RESULTS")
    print("="*80)

    print("\n[1/5] Setting up Granite-Docling VLM pipeline...")
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

    print("\n[2/5] Converting Well 7 EOWR with Granite-Docling...")
    print("  (This will take ~30-40 minutes on CPU)")

    start = time.time()
    result = converter.convert(str(pdf_path))
    convert_time = time.time() - start

    markdown = result.document.export_to_markdown()

    print(f"\n[3/5] Conversion complete in {convert_time:.1f}s")
    print(f"  Markdown length: {len(markdown):,} chars")

    # Save markdown output
    markdown_file = output_dir / "well7_granite_docling_full.md"
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    print(f"  Saved markdown to: {markdown_file}")

    # Extract TOC
    print("\n[4/5] Extracting TOC from Granite output...")

    sys.path.insert(0, str(Path(__file__).parent))
    from robust_toc_extractor import RobustTOCExtractor
    from analyze_all_tocs import find_toc_boundaries

    lines = markdown.split('\n')
    toc_start, toc_end = find_toc_boundaries(lines)

    toc_entries = []
    pattern = "None"

    if toc_start >= 0:
        toc_lines = lines[toc_start:toc_end]
        extractor = RobustTOCExtractor()
        toc_entries, pattern = extractor.extract(toc_lines)

    # Save TOC entries
    toc_file = output_dir / "well7_granite_toc_entries.json"
    with open(toc_file, 'w', encoding='utf-8') as f:
        json.dump({
            'source': 'Granite-Docling-258M VLM',
            'pattern': pattern,
            'entries': toc_entries,
            'total_entries': len(toc_entries),
            'missing_pages': sum(1 for e in toc_entries if e.get('page', 0) == 0),
            'convert_time_seconds': convert_time
        }, f, indent=2)
    print(f"  Saved TOC to: {toc_file}")

    # Calculate metrics
    missing_pages = sum(1 for e in toc_entries if e.get('page', 0) == 0)
    accurate_pages = len(toc_entries) - missing_pages
    accuracy = (accurate_pages / len(toc_entries) * 100) if len(toc_entries) > 0 else 0

    # Create comparison report
    print("\n[5/5] Creating comparison report...")

    report = f"""# Granite-Docling-258M Test Results
Date: {time.strftime('%Y-%m-%d %H:%M:%S')}
Document: Well 7 EOWR (NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf)

## Granite-Docling-258M Results

**Processing:**
- Model: ibm-granite/granite-docling-258M
- Framework: Transformers
- Device: CPU
- Processing time: {convert_time:.1f}s ({convert_time/60:.1f} minutes)
- Pages processed: 14

**Output:**
- Markdown length: {len(markdown):,} characters
- Output file: {markdown_file}

**TOC Extraction:**
- Pattern used: {pattern}
- Entries extracted: {len(toc_entries)}
- Accurate pages: {accurate_pages}/{len(toc_entries)} ({accuracy:.1f}%)
- Missing pages: {missing_pages}
- TOC file: {toc_file}

## Comparison with Llama 3.2 3B LLM

| Metric | Llama 3B | Granite-Docling | Winner |
|--------|----------|-----------------|--------|
| Entries | 15 | {len(toc_entries)} | {"Llama" if 15 > len(toc_entries) else "Granite"} |
| Page accuracy | 47% (7/15) | {accuracy:.1f}% ({accurate_pages}/{len(toc_entries)}) | {"Granite" if accuracy > 47 else "Llama"} |
| Missing pages | 8 (53%) | {missing_pages} ({missing_pages/len(toc_entries)*100:.1f}%) | {"Granite" if missing_pages < 8 else "Llama"} |
| Model size | 3B (exception) | 258M (compliant) | Granite |
| Processing time | ~8s (LLM only) | {convert_time:.1f}s (full doc) | Llama |
| Pattern | LLM parsing | {pattern} | Granite |

## TOC Entries Extracted

"""

    for i, entry in enumerate(toc_entries, 1):
        num = entry.get('number', 'N/A')
        title = entry.get('title', 'Unknown')
        page = entry.get('page', 0)
        report += f"{i}. {num:5s} - {title:50s} (page {page})\n"

    report += f"""

## Recommendation

"""

    if accuracy >= 80:
        report += f"""**EXCELLENT** - Granite-Docling significantly better than LLM!

Page accuracy: {accuracy:.1f}% (target: >= 80%)

**Impact:**
- Can enable section-aware chunking for Well 7
- Better chunk boundaries = better retrieval accuracy
- Meets <500M param constraint (258M)
- Native document structure understanding

**Next Steps:**
1. Integrate Granite as Tier 2.5 (before LLM fallback)
2. Re-index Well 7 with section-aware chunking
3. Test on other scanned PDFs (Wells 1, 2, 4, 6)
4. Compare full indexing quality (not just TOC)
"""
    elif accuracy >= 50:
        report += f"""**GOOD** - Granite-Docling moderately better than LLM

Page accuracy: {accuracy:.1f}% (LLM: 47%)

**Impact:**
- Improvement over current state
- May still need hybrid approach
- Meets <500M param constraint (258M)

**Next Steps:**
1. Consider integration as additional fallback tier
2. Use hybrid chunking (accurate pages get sections)
3. Test on other scanned PDFs
"""
    else:
        report += f"""**NEUTRAL** - Granite-Docling not significantly better

Page accuracy: {accuracy:.1f}% (LLM: 47%)

**Next Steps:**
1. Keep current LLM fallback approach
2. Consider Phase B (single-page API) with custom prompts
3. Or explore alternative approaches
"""

    # Save report
    report_file = output_dir / "well7_granite_test_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"  Saved report to: {report_file}")

    print("\n" + "="*80)
    print("ALL RESULTS SAVED")
    print("="*80)
    print(f"\nFiles created:")
    print(f"  1. {markdown_file} ({len(markdown):,} chars)")
    print(f"  2. {toc_file} ({len(toc_entries)} entries)")
    print(f"  3. {report_file}")
    print(f"\nPage accuracy: {accuracy:.1f}%")

    return {
        'success': True,
        'accuracy': accuracy,
        'entries': len(toc_entries),
        'markdown_file': str(markdown_file),
        'toc_file': str(toc_file),
        'report_file': str(report_file)
    }


if __name__ == "__main__":
    result = test_and_save()

    if result['success']:
        print(f"\nTest completed successfully!")
        print(f"Review the files in outputs/granite_test/")
