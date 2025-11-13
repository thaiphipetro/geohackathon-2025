"""
Discover all documents in a well folder and prepare for indexing

Usage:
    # Scan Well 5 to see what's available
    python scripts/discover_well_documents.py --well "Well 5"

    # Generate a file list for selective indexing
    python scripts/discover_well_documents.py --well "Well 5" --output well5_pdfs.txt
"""

import sys
import argparse
from pathlib import Path
from collections import defaultdict


def discover_well_documents(well_name, base_dir="Training data-shared with participants"):
    """
    Scan a well folder and categorize all documents

    Returns:
        Dict with document counts and paths by type
    """
    well_path = Path(base_dir) / well_name

    if not well_path.exists():
        print(f"[ERROR] Well folder not found: {well_path}")
        return None

    # Categorize documents
    docs = {
        'pdfs': defaultdict(list),
        'excel': defaultdict(list),
        'images': defaultdict(list),
        'other': defaultdict(list),
    }

    # Scan all subdirectories
    for file_path in well_path.rglob("*"):
        if not file_path.is_file():
            continue

        # Get relative folder name
        try:
            rel_path = file_path.relative_to(well_path)
            folder = str(rel_path.parent) if rel_path.parent != Path('.') else "root"
        except ValueError:
            folder = "unknown"

        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            docs['pdfs'][folder].append(file_path)
        elif suffix in ['.xlsx', '.xls', '.csv']:
            docs['excel'][folder].append(file_path)
        elif suffix in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            docs['images'][folder].append(file_path)
        else:
            docs['other'][folder].append(file_path)

    return docs


def print_summary(well_name, docs):
    """Print document summary"""
    print("=" * 80)
    print(f"DOCUMENT DISCOVERY: {well_name}")
    print("=" * 80)

    # PDFs
    total_pdfs = sum(len(files) for files in docs['pdfs'].values())
    print(f"\nPDFs Found: {total_pdfs}")
    print("-" * 80)
    for folder, files in sorted(docs['pdfs'].items()):
        print(f"  {folder}: {len(files)} PDFs")
        for pdf in sorted(files):
            print(f"    - {pdf.name}")

    # Excel
    total_excel = sum(len(files) for files in docs['excel'].values())
    if total_excel > 0:
        print(f"\nExcel Files Found: {total_excel}")
        print("-" * 80)
        for folder, files in sorted(docs['excel'].items()):
            print(f"  {folder}: {len(files)} Excel files")
            for excel in sorted(files):
                print(f"    - {excel.name}")

    # Images
    total_images = sum(len(files) for files in docs['images'].values())
    if total_images > 0:
        print(f"\nImage Files Found: {total_images}")
        print("-" * 80)
        for folder, files in sorted(docs['images'].items()):
            print(f"  {folder}: {len(files)} images")
            for img in sorted(files):
                print(f"    - {img.name}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total PDFs:       {total_pdfs}")
    print(f"Total Excel:      {total_excel}")
    print(f"Total Images:     {total_images}")
    print("=" * 80)


def generate_pdf_list(well_name, docs, output_file):
    """
    Generate a text file with PDF paths for batch indexing

    Format: pdf_path,well_name
    """
    pdfs = []
    for folder_pdfs in docs['pdfs'].values():
        pdfs.extend(folder_pdfs)

    if not pdfs:
        print(f"[WARN] No PDFs found in {well_name}")
        return

    output_path = Path(output_file)

    with open(output_path, 'w') as f:
        f.write(f"# PDFs to index for {well_name}\n")
        f.write(f"# Format: pdf_path,well_name\n")
        f.write(f"# Generated: {len(pdfs)} PDFs\n")
        f.write(f"#\n")
        f.write(f"# Usage:\n")
        f.write(f"#   python scripts/add_new_documents.py --pdf-list {output_file}\n")
        f.write(f"\n")

        for pdf in sorted(pdfs):
            # Use relative path for portability
            f.write(f"{pdf},{well_name}\n")

    print(f"\n[OK] PDF list written to: {output_path}")
    print(f"     Contains {len(pdfs)} PDFs")
    print(f"\nTo index all these PDFs:")
    print(f"  python scripts/add_new_documents.py --pdf-list {output_file}")


def generate_folder_specific_list(well_name, docs, folder_name, output_file):
    """Generate PDF list for a specific folder"""
    folder_pdfs = docs['pdfs'].get(folder_name, [])

    if not folder_pdfs:
        print(f"[WARN] No PDFs found in folder: {folder_name}")
        return

    output_path = Path(output_file)

    with open(output_path, 'w') as f:
        f.write(f"# PDFs from {well_name}/{folder_name}\n")
        f.write(f"# Generated: {len(folder_pdfs)} PDFs\n")
        f.write(f"\n")

        for pdf in sorted(folder_pdfs):
            f.write(f"{pdf},{well_name}\n")

    print(f"\n[OK] Folder-specific list written to: {output_path}")
    print(f"     Contains {len(folder_pdfs)} PDFs from '{folder_name}'")


def main():
    parser = argparse.ArgumentParser(description="Discover documents in a well folder")
    parser.add_argument('--well', required=True, help="Well name (e.g., 'Well 5')")
    parser.add_argument('--output', help="Output file for PDF list (e.g., well5_pdfs.txt)")
    parser.add_argument('--folder', help="Generate list for specific folder only")
    parser.add_argument('--base-dir', default="Training data-shared with participants",
                        help="Base directory for training data")

    args = parser.parse_args()

    # Discover documents
    docs = discover_well_documents(args.well, args.base_dir)

    if docs is None:
        sys.exit(1)

    # Print summary
    print_summary(args.well, docs)

    # Generate output file if requested
    if args.output:
        if args.folder:
            generate_folder_specific_list(args.well, docs, args.folder, args.output)
        else:
            generate_pdf_list(args.well, docs, args.output)

        print("\nNext steps:")
        print(f"  1. Review the generated file: {args.output}")
        print(f"  2. Remove any PDFs you don't want to index (optional)")
        print(f"  3. Run: python scripts/add_new_documents.py --pdf-list {args.output}")


if __name__ == '__main__':
    main()
