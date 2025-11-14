"""
Multi-Document TOC Adapter

Adapter for new multi-document TOC database format where each well has multiple PDFs.
Handles loading and accessing document metadata including filepath, publication date, and TOC.

New TOC format:
{
    "Well 1": [
        {
            "filename": "NLOG_GS_PUB_EOWR_v1.0.pdf",
            "filepath": "Training data-shared with participants/Well 1/...",
            "file_size": 528636,
            "pub_date": "2018-11-14T00:00:00",
            "is_scanned": false,
            "parse_method": "Docling",
            "toc": [...],
            "key_sections": {...}
        },
        ...
    ]
}
"""

from typing import Dict, List, Optional
import json
from pathlib import Path
from datetime import datetime


class MultiDocTOCAdapter:
    """
    Adapter for multi-document TOC database

    Each well now has multiple documents with:
    - filename: PDF filename
    - filepath: Absolute path to PDF
    - pub_date: Publication date (ISO format)
    - is_scanned: Whether document is scanned
    - toc: Table of contents entries
    - key_sections: Important sections extracted
    """

    def __init__(self, toc_database_path: str):
        """
        Initialize adapter with TOC database

        Args:
            toc_database_path: Path to toc_database_multi_doc_granite.json
        """
        self.toc_database_path = Path(toc_database_path)

        if not self.toc_database_path.exists():
            raise FileNotFoundError(f"TOC database not found: {toc_database_path}")

        # Load database
        with open(self.toc_database_path, 'r', encoding='utf-8') as f:
            self.database = json.load(f)

        print(f"[OK] Loaded TOC database from {toc_database_path}")
        print(f"  Wells: {len(self.database)}")

        # Count total documents
        total_docs = sum(len(docs) for docs in self.database.values())
        print(f"  Total documents: {total_docs}")

    def get_wells(self) -> List[str]:
        """
        Get list of all wells in database

        Returns:
            List of well names (e.g., ['Well 1', 'Well 2', ...])
        """
        return list(self.database.keys())

    def get_documents_for_well(self, well_name: str) -> List[Dict]:
        """
        Get all documents for a specific well

        Args:
            well_name: Well identifier (e.g., 'Well 5')

        Returns:
            List of document dictionaries with:
                - filename: str
                - filepath: str
                - pub_date: str (ISO format)
                - is_scanned: bool
                - toc: List[Dict]
                - key_sections: Dict

        Raises:
            KeyError: If well not found
        """
        if well_name not in self.database:
            available = ', '.join(self.get_wells())
            raise KeyError(f"Well '{well_name}' not found. Available wells: {available}")

        return self.database[well_name]

    def get_latest_document(self, well_name: str) -> Optional[Dict]:
        """
        Get most recent document for a well based on publication date

        Args:
            well_name: Well identifier

        Returns:
            Most recent document dict, or None if no documents with pub_date
        """
        docs = self.get_documents_for_well(well_name)

        # Filter documents with pub_date
        dated_docs = [doc for doc in docs if doc.get('pub_date')]

        if not dated_docs:
            return None

        # Sort by pub_date (descending) and return latest
        sorted_docs = sorted(
            dated_docs,
            key=lambda x: datetime.fromisoformat(x['pub_date']),
            reverse=True
        )

        return sorted_docs[0]

    def get_all_documents(self) -> List[Dict]:
        """
        Get all documents across all wells

        Returns:
            List of all document dictionaries with well_name added
        """
        all_docs = []

        for well_name in self.get_wells():
            docs = self.get_documents_for_well(well_name)

            # Add well_name to each document
            for doc in docs:
                doc_with_well = doc.copy()
                doc_with_well['well_name'] = well_name
                all_docs.append(doc_with_well)

        return all_docs

    def get_document_by_filename(self, well_name: str, filename: str) -> Optional[Dict]:
        """
        Get specific document by filename

        Args:
            well_name: Well identifier
            filename: PDF filename to find

        Returns:
            Document dict if found, None otherwise
        """
        docs = self.get_documents_for_well(well_name)

        for doc in docs:
            if doc.get('filename') == filename:
                return doc

        return None

    def get_statistics(self) -> Dict:
        """
        Get database statistics

        Returns:
            Dict with statistics:
                - total_wells: int
                - total_documents: int
                - scanned_documents: int
                - native_documents: int
                - documents_per_well: Dict[str, int]
        """
        all_docs = self.get_all_documents()

        scanned = sum(1 for doc in all_docs if doc.get('is_scanned', False))
        native = len(all_docs) - scanned

        docs_per_well = {
            well: len(self.get_documents_for_well(well))
            for well in self.get_wells()
        }

        return {
            'total_wells': len(self.database),
            'total_documents': len(all_docs),
            'scanned_documents': scanned,
            'native_documents': native,
            'documents_per_well': docs_per_well
        }


# Test
if __name__ == '__main__':
    # Test with actual database
    adapter = MultiDocTOCAdapter(
        "outputs/exploration/toc_database_multi_doc_granite.json"
    )

    print("\n" + "="*80)
    print("MULTI-DOC TOC ADAPTER TEST")
    print("="*80)

    # Test 1: Get wells
    print("\n[TEST 1] Get all wells:")
    wells = adapter.get_wells()
    print(f"  Found {len(wells)} wells: {wells}")

    # Test 2: Get documents for Well 5
    print("\n[TEST 2] Get documents for Well 5:")
    well5_docs = adapter.get_documents_for_well('Well 5')
    print(f"  Found {len(well5_docs)} documents for Well 5")
    for doc in well5_docs:
        print(f"    - {doc['filename']} (pub_date: {doc.get('pub_date', 'N/A')})")

    # Test 3: Get latest document
    print("\n[TEST 3] Get latest document for Well 5:")
    latest = adapter.get_latest_document('Well 5')
    if latest:
        print(f"  Latest: {latest['filename']}")
        print(f"  Pub date: {latest.get('pub_date')}")

    # Test 4: Get statistics
    print("\n[TEST 4] Database statistics:")
    stats = adapter.get_statistics()
    print(f"  Total wells: {stats['total_wells']}")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Native PDFs: {stats['native_documents']}")
    print(f"  Scanned PDFs: {stats['scanned_documents']}")
    print(f"  Documents per well:")
    for well, count in stats['documents_per_well'].items():
        print(f"    {well}: {count}")

    print("\n[OK] All tests passed!")
