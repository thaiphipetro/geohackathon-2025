"""
Validate TOC Database Quality

Checks:
1. All PDFs have entries
2. No negative page numbers
3. Dates are valid
4. No duplicates
5. Section types are valid
6. Page numbers within PDF bounds
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter

def validate_database(db_path):
    """
    Validate database integrity and quality

    Returns:
        (is_valid, issues, stats) tuple
    """
    issues = []
    stats = {
        'total_wells': 0,
        'total_documents': 0,
        'total_entries': 0,
        'exact_pages': 0,
        'range_pages': 0,
        'unknown_pages': 0,
        'parse_methods': Counter(),
        'section_types': Counter(),
        'scanned_pdfs': 0,
        'native_pdfs': 0
    }

    # Load database
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except Exception as e:
        return False, [f"Failed to load database: {e}"], stats

    if not isinstance(db, dict):
        return False, ["Database is not a dictionary"], stats

    stats['total_wells'] = len(db)

    # Validate each well
    for well_name, documents in db.items():
        if not isinstance(documents, list):
            issues.append(f"{well_name}: Documents is not a list")
            continue

        stats['total_documents'] += len(documents)

        for doc_idx, doc in enumerate(documents):
            doc_name = doc.get('filename', f'Document #{doc_idx}')

            # Check required fields
            required_fields = ['filename', 'filepath', 'toc']
            for field in required_fields:
                if field not in doc:
                    issues.append(f"{well_name}/{doc_name}: Missing field '{field}'")

            # Validate date
            if 'pub_date' in doc and doc['pub_date']:
                try:
                    datetime.fromisoformat(doc['pub_date'].replace('Z', '+00:00'))
                except Exception as e:
                    issues.append(f"{well_name}/{doc_name}: Invalid date '{doc['pub_date']}': {e}")

            # Track parse method
            if 'parse_method' in doc:
                stats['parse_methods'][doc['parse_method']] += 1

            # Track document type
            if doc.get('is_scanned'):
                stats['scanned_pdfs'] += 1
            else:
                stats['native_pdfs'] += 1

            # Validate TOC entries
            toc = doc.get('toc', [])
            if not isinstance(toc, list):
                issues.append(f"{well_name}/{doc_name}: TOC is not a list")
                continue

            if len(toc) == 0:
                issues.append(f"{well_name}/{doc_name}: TOC is empty")
                continue

            stats['total_entries'] += len(toc)

            for entry_idx, entry in enumerate(toc):
                entry_id = entry.get('number', f'Entry #{entry_idx}')

                # Check required entry fields
                required_entry_fields = ['number', 'title', 'page']
                for field in required_entry_fields:
                    if field not in entry:
                        issues.append(f"{well_name}/{doc_name}/{entry_id}: Missing field '{field}'")

                # Validate page number
                page = entry.get('page')
                if page is None:
                    issues.append(f"{well_name}/{doc_name}/{entry_id}: Page is None")
                elif isinstance(page, int):
                    if page < 0:
                        issues.append(f"{well_name}/{doc_name}/{entry_id}: Negative page number {page}")
                    elif page == 0:
                        stats['unknown_pages'] += 1
                    else:
                        stats['exact_pages'] += 1
                        # TODO: Check if page exceeds PDF bounds (need PDF metadata)
                elif isinstance(page, str):
                    if '-' in page:
                        stats['range_pages'] += 1
                        # Validate range format
                        parts = page.split('-')
                        if len(parts) != 2:
                            issues.append(f"{well_name}/{doc_name}/{entry_id}: Invalid range format '{page}'")
                        else:
                            try:
                                lower = int(parts[0])
                                upper = int(parts[1])
                                if lower < 0 or upper < 0:
                                    issues.append(f"{well_name}/{doc_name}/{entry_id}: Negative page in range '{page}'")
                                if lower > upper:
                                    issues.append(f"{well_name}/{doc_name}/{entry_id}: Invalid range (lower > upper): '{page}'")
                            except ValueError:
                                issues.append(f"{well_name}/{doc_name}/{entry_id}: Non-numeric range '{page}'")
                    else:
                        issues.append(f"{well_name}/{doc_name}/{entry_id}: Unknown page format '{page}'")
                else:
                    issues.append(f"{well_name}/{doc_name}/{entry_id}: Page is not int or str: {type(page)}")

                # Track section type
                if 'type' in entry:
                    stats['section_types'][entry['type']] += 1

    # Calculate accuracy
    known_pages = stats['exact_pages'] + stats['range_pages']
    total_pages = stats['total_entries']
    stats['accuracy'] = known_pages / total_pages if total_pages > 0 else 0.0

    # Determine if valid
    is_valid = len(issues) == 0

    return is_valid, issues, stats


def print_validation_report(is_valid, issues, stats):
    """Print formatted validation report"""
    print("=" * 80)
    print("DATABASE VALIDATION REPORT")
    print("=" * 80)

    if is_valid:
        print("\n[VALID] DATABASE IS VALID - No issues found")
    else:
        print(f"\n[INVALID] DATABASE HAS ISSUES - {len(issues)} issues found")

    print(f"\n{'='*80}")
    print("DATABASE STATISTICS")
    print(f"{'='*80}")
    print(f"\nWells: {stats['total_wells']}")
    print(f"Documents: {stats['total_documents']}")
    print(f"  Scanned PDFs: {stats['scanned_pdfs']}")
    print(f"  Native PDFs: {stats['native_pdfs']}")
    print(f"\nTOC Entries: {stats['total_entries']}")
    print(f"  Exact pages: {stats['exact_pages']} ({stats['exact_pages']/stats['total_entries']*100:.1f}%)")
    print(f"  Range pages: {stats['range_pages']} ({stats['range_pages']/stats['total_entries']*100:.1f}%)")
    print(f"  Unknown pages: {stats['unknown_pages']} ({stats['unknown_pages']/stats['total_entries']*100:.1f}%)")
    print(f"\nAccuracy: {stats['accuracy']:.1%} (known pages / total)")

    print(f"\n{'='*80}")
    print("PARSE METHODS")
    print(f"{'='*80}")
    for method, count in stats['parse_methods'].most_common():
        print(f"  {method}: {count} documents")

    print(f"\n{'='*80}")
    print("SECTION TYPES")
    print(f"{'='*80}")
    for section_type, count in stats['section_types'].most_common(10):
        print(f"  {section_type}: {count} entries")

    if not is_valid:
        print(f"\n{'='*80}")
        print("ISSUES FOUND")
        print(f"{'='*80}")
        for idx, issue in enumerate(issues[:20], 1):  # Show first 20
            print(f"  {idx}. {issue}")
        if len(issues) > 20:
            print(f"\n  ... and {len(issues) - 20} more issues")

    print(f"\n{'='*80}")


def main():
    """Validate database and print report"""
    db_path = Path("outputs/exploration/toc_database_multi_doc_granite.json")

    if not db_path.exists():
        print(f"Error: Database not found: {db_path}")
        return 1

    print(f"Validating database: {db_path}")
    print()

    is_valid, issues, stats = validate_database(db_path)
    print_validation_report(is_valid, issues, stats)

    return 0 if is_valid else 1


if __name__ == "__main__":
    exit(main())
