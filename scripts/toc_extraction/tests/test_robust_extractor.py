"""
Step 3: Test RobustTOCExtractor on all 14 PDFs
Validates the extractor works on all real TOC sections from Step 1
"""

import sys
from pathlib import Path
import json
from robust_toc_extractor import RobustTOCExtractor

project_root = Path(__file__).parent.parent
analysis_dir = project_root / "outputs" / "toc_analysis"


def load_toc_section(toc_file_path: Path) -> list:
    """Load TOC lines from a saved file"""
    with open(toc_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Skip header (first 3 lines)
    toc_lines = []
    started = False

    for line in lines:
        if '=' * 80 in line and not started:
            started = True
            continue

        if started:
            # Remove line numbers (format: "  123: actual content")
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    toc_lines.append(parts[1].rstrip('\n'))
            else:
                toc_lines.append(line.rstrip('\n'))

    return toc_lines


def main():
    """Test RobustTOCExtractor on all saved TOC sections"""

    # Load analysis results
    results_file = analysis_dir / "toc_analysis_results.json"

    with open(results_file, 'r', encoding='utf-8') as f:
        analysis_results = json.load(f)

    # Filter to only TOCs that were found
    toc_results = [r for r in analysis_results if r.get('has_toc_section')]

    print("="*80)
    print("STEP 3: TEST ROBUST TOC EXTRACTOR")
    print("="*80)
    print(f"\nTesting on {len(toc_results)} TOC sections from Step 1")
    print("\n" + "="*80)

    extractor = RobustTOCExtractor()
    test_results = []

    for i, result in enumerate(toc_results, 1):
        well = result['well']
        filename = result['filename']
        toc_file = Path(result['toc_file'])

        print(f"\n[{i}/{len(toc_results)}] {well}: {filename}")
        print("-"*80)

        # Load TOC section
        toc_lines = load_toc_section(toc_file)

        # Extract TOC entries
        entries, pattern_name = extractor.extract(toc_lines, debug=False)

        # Analyze result
        success = len(entries) >= 3  # At least 3 entries to be considered successful

        if success:
            print(f"  [OK] SUCCESS: {len(entries)} entries extracted using {pattern_name}")
            print(f"  Sample entries:")
            for entry in entries[:5]:
                print(f"    {entry['number']:6s} {entry['title'][:50]:50s} (page {entry['page']})")
            if len(entries) > 5:
                print(f"    ... and {len(entries) - 5} more")
        else:
            print(f"  [FAIL] FAILED: Only {len(entries)} entries extracted")
            print(f"  Pattern: {pattern_name}")

        test_results.append({
            'well': well,
            'filename': filename,
            'success': success,
            'entry_count': len(entries),
            'pattern': pattern_name,
            'entries': entries[:10]  # Save first 10 for inspection
        })

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    total = len(test_results)
    successful = sum(1 for r in test_results if r['success'])
    failed = total - successful

    print(f"\nTotal TOCs tested: {total}")
    print(f"Successfully extracted: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"Failed: {failed}/{total}")

    # Breakdown by well
    print("\n" + "-"*80)
    print("BREAKDOWN BY WELL")
    print("-"*80)

    for well_num in [1, 2, 3, 4, 5, 6, 8]:
        well_name = f"Well {well_num}"
        well_tests = [r for r in test_results if r['well'] == well_name]

        if not well_tests:
            continue

        well_success = sum(1 for r in well_tests if r['success'])
        print(f"\n{well_name}: {well_success}/{len(well_tests)} PDFs")

        for r in well_tests:
            if r['success']:
                status = f"[OK] {r['entry_count']:2d} entries ({r['pattern']})"
            else:
                status = f"[FAIL] FAILED"
            print(f"  {status:50s} - {r['filename']}")

    # Pattern distribution
    print("\n" + "-"*80)
    print("PATTERN DISTRIBUTION")
    print("-"*80)

    pattern_counts = {}
    for r in test_results:
        if r['success']:
            pattern = r.get('pattern', 'Unknown')
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

    for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pattern:30s}: {count} PDFs")

    # Failed cases
    if failed > 0:
        print("\n" + "-"*80)
        print("FAILED CASES (NEED ATTENTION)")
        print("-"*80)

        for r in test_results:
            if not r['success']:
                print(f"\n{r['well']}: {r['filename']}")
                print(f"  Entry count: {r['entry_count']}")
                print(f"  Pattern matched: {r['pattern']}")

    # Save results
    output_file = analysis_dir / "extraction_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2)

    print(f"\n[OK] Test results saved to: {output_file}")

    print("\n" + "="*80)

    # Return success rate
    return successful, total


if __name__ == '__main__':
    successful, total = main()

    # Exit code: 0 if all passed, 1 if any failed
    sys.exit(0 if successful == total else 1)
