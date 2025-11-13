"""
Test Enhanced Extraction on Well 5 (NLW-GT-03)
Best quality well with comprehensive documentation
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from enhanced_well7_parser import EnhancedWell7Parser

print("=" * 80)
print("ENHANCED WELL 5 PARSER - ALL DOCLING FEATURES")
print("Well 5 (NLW-GT-03) - Best Quality Well")
print("=" * 80)

# Initialize parser (reuse Well 7 parser, it works for all wells)
parser = EnhancedWell7Parser()

# Update output directory for Well 5
parser.output_dir = project_root / "outputs" / "well5_enhanced"
parser.output_dir.mkdir(parents=True, exist_ok=True)

# Test PDFs from Well 5
well5_dir = project_root / "Training data-shared with participants" / "Well 5"

test_pdfs = [
    well5_dir / "Well report" / "NLOG_GS_PUB_EOWR_SodM_NLW-GT-03-S1 v1.0_Redacted.pdf",
    well5_dir / "Well report" / "NLOG_GS_PUB_App 07. Final-Well-Report_NLW-GT-03.pdf",
]

for pdf_path in test_pdfs:
    if not pdf_path.exists():
        print(f"\n[SKIP] {pdf_path.name} - not found")
        continue

    print(f"\n{'=' * 80}")
    print(f"Parsing: {pdf_path.name}")
    print(f"Size: {pdf_path.stat().st_size / 1024:.1f} KB")
    print("=" * 80)

    try:
        # Parse PDF
        results = parser.parse_pdf(pdf_path)

        # Save results
        parser.save_results(results, pdf_path.stem)

        # Print summary
        print(f"\n{'=' * 80}")
        print("EXTRACTION SUMMARY")
        print(f"{'=' * 80}")
        for key, value in results['metadata'].items():
            print(f"  {key}: {value:,}")

        # Show ALL tables summary
        if results['tables']:
            print(f"\n[TABLES EXTRACTED: {len(results['tables'])}]")
            print("-" * 80)
            for i, table in enumerate(results['tables'][:3]):  # Show first 3
                print(f"\nTable {i + 1}: {table['ref']}")
                print(f"  Caption: {table['caption']}")
                print(f"  Size: {table['num_rows']} rows x {table['num_cols']} cols")
                print(f"  Page: {table['page']}")
                print(f"  Has merged cells: {table['has_merged_cells']}")
                if table['data'] and len(table['data']) > 0:
                    # Print first row keys instead of values to avoid type errors
                    print(f"  First row has {len(table['data'][0])} columns")
            if len(results['tables']) > 3:
                print(f"\n  ... and {len(results['tables']) - 3} more tables")
            print("-" * 80)

        # Show ALL pictures summary
        if results['pictures']:
            print(f"\n[PICTURES EXTRACTED: {len(results['pictures'])}]")
            print("-" * 80)
            for i, pic in enumerate(results['pictures'][:3]):  # Show first 3
                print(f"\nPicture {i + 1}: {pic['ref']}")
                print(f"  Caption: {pic['caption']}")
                print(f"  Page: {pic['page']}")
                print(f"  Dimensions: {pic['width']}x{pic['height']} px")
                print(f"  Saved to: {pic['image_path']}")

                if pic['classification']:
                    print(f"  Classification: {pic['classification']['type']} "
                          f"(confidence: {pic['classification']['confidence']:.2f})")

                if pic['description']:
                    desc_preview = pic['description'][:200] + '...' if len(
                        pic['description']) > 200 else pic['description']
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

print(f"\n{'=' * 80}")
print("ENHANCED PARSING COMPLETE")
print(f"{'=' * 80}")
print(f"Results saved to: {parser.output_dir}")
