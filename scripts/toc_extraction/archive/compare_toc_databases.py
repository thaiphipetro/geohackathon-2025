"""
Compare TOC Database: Text-based vs Granite VLM

Compares the old text-based TOC database with the new Granite VLM database
to show improvements in page number accuracy.

Input:
  - outputs/exploration/toc_database_multi_doc_full.json (old, text-based)
  - outputs/exploration/toc_database_multi_doc_granite.json (new, Granite VLM)

Output:
  - Console report with detailed comparison
  - outputs/exploration/granite_vs_text_comparison.md (markdown report)
"""

import json
from pathlib import Path
from collections import defaultdict

def load_database(path):
    """Load TOC database from JSON file"""
    with open(path, 'r') as f:
        return json.load(f)

def count_page_types(db):
    """
    Count page types across all entries in database

    Returns:
        (exact, range, unknown, total_entries, total_pdfs)
    """
    exact = 0
    range_pages = 0
    unknown = 0
    total_entries = 0
    total_pdfs = 0

    for well_name, documents in db.items():
        for doc in documents:
            total_pdfs += 1
            for entry in doc['toc']:
                total_entries += 1
                page = entry.get('page', 0)

                if page == 0:
                    unknown += 1
                elif isinstance(page, str) and '-' in str(page):
                    range_pages += 1
                else:
                    exact += 1

    return exact, range_pages, unknown, total_entries, total_pdfs

def count_by_method(db):
    """Count PDFs by extraction method"""
    methods = defaultdict(list)

    for well_name, documents in db.items():
        for doc in documents:
            method = doc.get('parse_method', 'Unknown')
            methods[method].append((well_name, doc['filename']))

    return dict(methods)

def compare_databases():
    """Main comparison function"""

    # Paths
    old_path = Path("outputs/exploration/toc_database_multi_doc_full.json")
    new_path = Path("outputs/exploration/toc_database_multi_doc_granite.json")
    report_path = Path("outputs/exploration/granite_vs_text_comparison.md")

    # Check files exist
    if not old_path.exists():
        print(f"ERROR: Old database not found: {old_path}")
        return

    if not new_path.exists():
        print(f"ERROR: New database not found: {new_path}")
        return

    # Load databases
    print("Loading databases...")
    old_db = load_database(old_path)
    new_db = load_database(new_path)

    # Count statistics
    print("\nAnalyzing old database (text-based)...")
    old_exact, old_range, old_unknown, old_total, old_pdfs = count_page_types(old_db)
    old_known = old_exact + old_range
    old_accuracy = (old_known / old_total * 100) if old_total > 0 else 0

    print("Analyzing new database (Granite VLM)...")
    new_exact, new_range, new_unknown, new_total, new_pdfs = count_page_types(new_db)
    new_known = new_exact + new_range
    new_accuracy = (new_known / new_total * 100) if new_total > 0 else 0

    # Count methods
    old_methods = count_by_method(old_db)
    new_methods = count_by_method(new_db)

    # Calculate improvements
    unknown_reduction = old_unknown - new_unknown
    accuracy_improvement = new_accuracy - old_accuracy

    # Print console report
    print("\n" + "="*80)
    print("TOC DATABASE COMPARISON: TEXT-BASED vs GRANITE VLM")
    print("="*80)

    print("\n[OLD DATABASE - Text-based]")
    print(f"  File: {old_path.name}")
    print(f"  PDFs processed: {old_pdfs}")
    print(f"  Total TOC entries: {old_total}")
    print(f"  Exact pages: {old_exact} ({old_exact/old_total*100:.1f}%)")
    print(f"  Range pages: {old_range} ({old_range/old_total*100:.1f}%)")
    print(f"  Unknown pages: {old_unknown} ({old_unknown/old_total*100:.1f}%)")
    print(f"  Accuracy: {old_accuracy:.1f}% ({old_known}/{old_total} known)")

    print("\n[NEW DATABASE - Granite VLM]")
    print(f"  File: {new_path.name}")
    print(f"  PDFs processed: {new_pdfs}")
    print(f"  Total TOC entries: {new_total}")
    print(f"  Exact pages: {new_exact} ({new_exact/new_total*100:.1f}%)")
    print(f"  Range pages: {new_range} ({new_range/new_total*100:.1f}%)")
    print(f"  Unknown pages: {new_unknown} ({new_unknown/new_total*100:.1f}%)")
    print(f"  Accuracy: {new_accuracy:.1f}% ({new_known}/{new_total} known)")

    print("\n[IMPROVEMENT]")
    print(f"  Unknown pages reduced: {unknown_reduction} ({old_unknown} -> {new_unknown})")
    print(f"  Accuracy improved: +{accuracy_improvement:.1f}% ({old_accuracy:.1f}% -> {new_accuracy:.1f}%)")
    print(f"  Exact pages improved: +{new_exact - old_exact} ({old_exact} -> {new_exact})")

    print("\n[EXTRACTION METHODS - Old]")
    for method, pdfs in old_methods.items():
        print(f"  {method}: {len(pdfs)} PDFs")

    print("\n[EXTRACTION METHODS - New]")
    for method, pdfs in new_methods.items():
        print(f"  {method}: {len(pdfs)} PDFs")

    # Granite success breakdown
    if 'Granite' in new_methods:
        print("\n[GRANITE SUCCESS]")
        granite_pdfs = new_methods['Granite']
        print(f"  Total: {len(granite_pdfs)} PDFs")
        print(f"  Success rate: {len(granite_pdfs)/new_pdfs*100:.1f}%")

        # Show which wells benefited
        well_counts = defaultdict(int)
        for well_name, filename in granite_pdfs:
            well_counts[well_name] += 1

        print("\n  By well:")
        for well_name in sorted(well_counts.keys()):
            count = well_counts[well_name]
            print(f"    {well_name}: {count} PDF(s)")

    # Generate markdown report
    print(f"\n[GENERATING REPORT]")
    generate_markdown_report(
        report_path,
        old_db, new_db,
        old_exact, old_range, old_unknown, old_total, old_pdfs, old_accuracy,
        new_exact, new_range, new_unknown, new_total, new_pdfs, new_accuracy,
        old_methods, new_methods
    )
    print(f"  Saved to: {report_path}")

    print("\n" + "="*80)
    print("COMPARISON COMPLETE")
    print("="*80)

def generate_markdown_report(
    report_path,
    old_db, new_db,
    old_exact, old_range, old_unknown, old_total, old_pdfs, old_accuracy,
    new_exact, new_range, new_unknown, new_total, new_pdfs, new_accuracy,
    old_methods, new_methods
):
    """Generate markdown comparison report"""

    lines = []
    lines.append("# TOC Database Comparison: Text-based vs Granite VLM\n")
    lines.append(f"**Date:** {Path(__file__).stat().st_mtime}\n")
    lines.append("\n---\n")

    lines.append("\n## Summary\n")
    lines.append("| Metric | Old (Text-based) | New (Granite VLM) | Improvement |\n")
    lines.append("|--------|------------------|-------------------|-------------|\n")
    lines.append(f"| PDFs processed | {old_pdfs} | {new_pdfs} | - |\n")
    lines.append(f"| Total TOC entries | {old_total} | {new_total} | - |\n")
    lines.append(f"| Exact pages | {old_exact} ({old_exact/old_total*100:.1f}%) | {new_exact} ({new_exact/new_total*100:.1f}%) | +{new_exact-old_exact} |\n")
    lines.append(f"| Range pages | {old_range} ({old_range/old_total*100:.1f}%) | {new_range} ({new_range/new_total*100:.1f}%) | +{new_range-old_range} |\n")
    lines.append(f"| Unknown pages | {old_unknown} ({old_unknown/old_total*100:.1f}%) | {new_unknown} ({new_unknown/new_total*100:.1f}%) | {new_unknown-old_unknown} |\n")
    lines.append(f"| **Accuracy** | **{old_accuracy:.1f}%** | **{new_accuracy:.1f}%** | **+{new_accuracy-old_accuracy:.1f}%** |\n")

    lines.append("\n---\n")
    lines.append("\n## Extraction Methods\n")
    lines.append("\n### Old Database (Text-based)\n")
    for method, pdfs in old_methods.items():
        lines.append(f"- **{method}**: {len(pdfs)} PDFs\n")

    lines.append("\n### New Database (Granite VLM)\n")
    for method, pdfs in new_methods.items():
        lines.append(f"- **{method}**: {len(pdfs)} PDFs\n")

    if 'Granite' in new_methods:
        lines.append(f"\n**Granite Success Rate**: {len(new_methods['Granite'])/new_pdfs*100:.1f}%\n")

    lines.append("\n---\n")
    lines.append("\n## Per-Well Breakdown\n")

    all_wells = sorted(set(list(old_db.keys()) + list(new_db.keys())))

    for well_name in all_wells:
        lines.append(f"\n### {well_name}\n")

        old_docs = old_db.get(well_name, [])
        new_docs = new_db.get(well_name, [])

        if not old_docs and not new_docs:
            lines.append("No data\n")
            continue

        lines.append("| PDF | Old Method | Old Unknown | New Method | New Unknown | Improvement |\n")
        lines.append("|-----|------------|-------------|------------|-------------|-------------|\n")

        # Match documents by filename
        for old_doc in old_docs:
            filename = old_doc['filename']
            new_doc = next((d for d in new_docs if d['filename'] == filename), None)

            old_method = old_doc.get('parse_method', 'Unknown')
            old_unk = sum(1 for e in old_doc['toc'] if e.get('page', 0) == 0)

            if new_doc:
                new_method = new_doc.get('parse_method', 'Unknown')
                new_unk = sum(1 for e in new_doc['toc'] if e.get('page', 0) == 0)
                improvement = old_unk - new_unk
                improvement_str = f"{improvement:+d}" if improvement != 0 else "-"
            else:
                new_method = "N/A"
                new_unk = "N/A"
                improvement_str = "N/A"

            lines.append(f"| {filename[:50]} | {old_method} | {old_unk} | {new_method} | {new_unk} | {improvement_str} |\n")

    lines.append("\n---\n")
    lines.append("\n## Conclusion\n")

    if new_accuracy > old_accuracy:
        lines.append(f"Granite VLM improved TOC extraction accuracy by **{new_accuracy-old_accuracy:.1f}%** ")
        lines.append(f"({old_accuracy:.1f}% -> {new_accuracy:.1f}%), ")
        lines.append(f"reducing unknown pages from {old_unknown} to {new_unknown}.\n")
    else:
        lines.append(f"No significant improvement observed.\n")

    # Write report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

if __name__ == "__main__":
    compare_databases()
