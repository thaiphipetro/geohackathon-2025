"""
Pre-flight validation: Well inventory check

Validates that all expected wells are present before indexing.
Prevents costly re-indexing due to missing wells.

Usage:
    # Check TOC database
    python scripts/validate_well_inventory.py --toc-database outputs/exploration/toc_database_multi_doc_full.json

    # Check ChromaDB
    python scripts/validate_well_inventory.py --check-chromadb

    # Check both
    python scripts/validate_well_inventory.py --check-all
"""

import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class WellInventoryValidator:
    """Validate well inventory before indexing"""

    # Expected wells in training data
    EXPECTED_WELLS = {
        'Well 1', 'Well 2', 'Well 3', 'Well 4',
        'Well 5', 'Well 6', 'Well 7', 'Well 8'
    }

    EXPECTED_WELL_COUNT = 8

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_toc_database(self, toc_db_path):
        """Validate TOC database has all expected wells"""
        print("="*80)
        print("VALIDATING TOC DATABASE")
        print("="*80)

        toc_db_path = Path(toc_db_path)

        if not toc_db_path.exists():
            self.errors.append(f"TOC database not found: {toc_db_path}")
            print(f"[ERROR] TOC database not found: {toc_db_path}")
            return False

        # Load TOC database
        with open(toc_db_path, 'r') as f:
            toc_database = json.load(f)

        indexed_wells = set(toc_database.keys())

        print(f"\nExpected wells: {self.EXPECTED_WELL_COUNT}")
        print(f"Wells in TOC database: {len(indexed_wells)}")
        print(f"\nIndexed wells: {sorted(indexed_wells)}")

        # Check for missing wells
        missing_wells = self.EXPECTED_WELLS - indexed_wells
        if missing_wells:
            self.errors.append(f"Missing wells in TOC database: {sorted(missing_wells)}")
            print(f"\n[ERROR] Missing wells: {sorted(missing_wells)}")
            return False

        # Check for unexpected wells
        extra_wells = indexed_wells - self.EXPECTED_WELLS
        if extra_wells:
            self.warnings.append(f"Unexpected wells in TOC database: {sorted(extra_wells)}")
            print(f"\n[WARN] Unexpected wells: {sorted(extra_wells)}")

        # Check PDF counts per well
        print(f"\nPDF counts per well:")
        print("-"*80)
        for well in sorted(indexed_wells):
            pdf_count = len(toc_database[well])
            print(f"  {well:15s}: {pdf_count:2d} PDFs")

            if pdf_count == 0:
                self.errors.append(f"{well} has 0 PDFs")
                print(f"    [ERROR] No PDFs indexed")

        if not self.errors:
            print(f"\n[OK] All {self.EXPECTED_WELL_COUNT} wells present in TOC database")
            return True
        else:
            return False

    def validate_chromadb(self):
        """Validate ChromaDB has all expected wells"""
        print("\n" + "="*80)
        print("VALIDATING CHROMADB")
        print("="*80)

        try:
            from vector_store import TOCEnhancedVectorStore

            vector_store = TOCEnhancedVectorStore()
            collection = vector_store.collection

            # Get all metadata
            all_data = collection.get(include=['metadatas'])

            if not all_data or 'metadatas' not in all_data:
                self.errors.append("ChromaDB has no metadata")
                print("[ERROR] ChromaDB has no metadata")
                return False

            metadatas = all_data['metadatas']

            # Count chunks per well
            well_chunks = defaultdict(int)
            for metadata in metadatas:
                well_name = metadata.get('well_name', 'Unknown')
                well_chunks[well_name] += 1

            indexed_wells = set(well_chunks.keys()) - {'Unknown'}

            print(f"\nExpected wells: {self.EXPECTED_WELL_COUNT}")
            print(f"Wells in ChromaDB: {len(indexed_wells)}")
            print(f"Total chunks: {len(metadatas)}")

            print(f"\nChunks per well:")
            print("-"*80)
            for well in sorted(indexed_wells):
                chunk_count = well_chunks[well]
                print(f"  {well:15s}: {chunk_count:4d} chunks")

                if chunk_count < 50:
                    self.warnings.append(f"{well} has only {chunk_count} chunks (suspiciously low)")
                    print(f"    [WARN] Low chunk count")

            # Check for missing wells
            missing_wells = self.EXPECTED_WELLS - indexed_wells
            if missing_wells:
                self.errors.append(f"Missing wells in ChromaDB: {sorted(missing_wells)}")
                print(f"\n[ERROR] Missing wells: {sorted(missing_wells)}")
                return False

            # Check for unexpected wells
            extra_wells = indexed_wells - self.EXPECTED_WELLS
            if extra_wells:
                self.warnings.append(f"Unexpected wells in ChromaDB: {sorted(extra_wells)}")
                print(f"\n[WARN] Unexpected wells: {sorted(extra_wells)}")

            if not self.errors:
                print(f"\n[OK] All {self.EXPECTED_WELL_COUNT} wells present in ChromaDB")
                return True
            else:
                return False

        except Exception as e:
            self.errors.append(f"Failed to validate ChromaDB: {e}")
            print(f"[ERROR] Failed to validate ChromaDB: {e}")
            return False

    def validate_training_data_folder(self, base_dir="Training data-shared with participants"):
        """Validate training data folder structure"""
        print("\n" + "="*80)
        print("VALIDATING TRAINING DATA FOLDER")
        print("="*80)

        base_path = Path(base_dir)

        if not base_path.exists():
            self.errors.append(f"Training data folder not found: {base_dir}")
            print(f"[ERROR] Training data folder not found: {base_dir}")
            return False

        # Find all well folders
        well_folders = [p for p in base_path.iterdir() if p.is_dir() and p.name.startswith('Well ')]
        found_wells = {p.name for p in well_folders}

        print(f"\nExpected wells: {self.EXPECTED_WELL_COUNT}")
        print(f"Found well folders: {len(found_wells)}")
        print(f"\nWell folders: {sorted(found_wells)}")

        # Check for missing wells
        missing_wells = self.EXPECTED_WELLS - found_wells
        if missing_wells:
            self.errors.append(f"Missing well folders: {sorted(missing_wells)}")
            print(f"\n[ERROR] Missing well folders: {sorted(missing_wells)}")
            return False

        # Check for unexpected wells
        extra_wells = found_wells - self.EXPECTED_WELLS
        if extra_wells:
            self.warnings.append(f"Unexpected well folders: {sorted(extra_wells)}")
            print(f"\n[WARN] Unexpected well folders: {sorted(extra_wells)}")

        # Check each well has Well report folder
        print(f"\nWell report folders:")
        print("-"*80)
        for well_folder in sorted(well_folders, key=lambda x: x.name):
            well_report_path = well_folder / "Well report"
            has_report = well_report_path.exists()

            if has_report:
                pdf_count = len(list(well_report_path.glob("*.pdf")))
                print(f"  {well_folder.name:15s}: OK ({pdf_count} PDFs)")
            else:
                self.errors.append(f"{well_folder.name} missing 'Well report' folder")
                print(f"  {well_folder.name:15s}: [ERROR] Missing 'Well report' folder")

        if not self.errors:
            print(f"\n[OK] All {self.EXPECTED_WELL_COUNT} well folders present")
            return True
        else:
            return False

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)

        if not self.errors and not self.warnings:
            print("\n[SUCCESS] All validations passed!")
            print("  All 8 wells accounted for")
            print("  Safe to proceed with indexing")
            return True

        if self.warnings:
            print(f"\nWarnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  [WARN] {warning}")

        if self.errors:
            print(f"\nErrors: {len(self.errors)}")
            for error in self.errors:
                print(f"  [ERROR] {error}")

            print("\n[FAILED] Validation failed!")
            print("  DO NOT proceed with indexing")
            print("  Fix errors above first")
            return False

        if self.warnings and not self.errors:
            print("\n[WARNING] Validation passed with warnings")
            print("  Review warnings before proceeding")
            return True


def main():
    parser = argparse.ArgumentParser(description="Validate well inventory before indexing")
    parser.add_argument('--toc-database', help="Path to TOC database JSON file")
    parser.add_argument('--check-chromadb', action='store_true', help="Validate ChromaDB")
    parser.add_argument('--check-training-data', action='store_true', help="Validate training data folder")
    parser.add_argument('--check-all', action='store_true', help="Run all validations")
    parser.add_argument('--base-dir', default="Training data-shared with participants",
                        help="Base directory for training data")

    args = parser.parse_args()

    validator = WellInventoryValidator()

    results = []

    # Training data validation
    if args.check_all or args.check_training_data:
        result = validator.validate_training_data_folder(args.base_dir)
        results.append(result)

    # TOC database validation
    if args.toc_database:
        result = validator.validate_toc_database(args.toc_database)
        results.append(result)

    # ChromaDB validation
    if args.check_all or args.check_chromadb:
        result = validator.validate_chromadb()
        results.append(result)

    # Print summary
    success = validator.print_summary()

    print("\n" + "="*80)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
