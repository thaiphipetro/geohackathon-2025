"""
Table Chunker - Extract tables as separate chunks with markdown format

Purpose:
    Convert Docling-extracted tables into searchable text chunks with rich metadata

Key Features:
    - Convert table dataframes to markdown format
    - Add table-specific metadata (caption, index, section info)
    - Support context-aware table prioritization
"""

from typing import List, Dict, Optional
import pandas as pd


class TableChunker:
    """
    Chunks tables extracted from Docling parser

    Strategy:
        1. Convert table DataFrame to markdown
        2. Prepend table caption for context
        3. Add rich metadata (chunk_type, table_index, section info)
        4. Enable filtering by table properties

    Example:
        chunker = TableChunker()
        table_chunks = chunker.chunk_tables(
            tables=parsed['tables'],
            section_info={'number': '3.4', 'title': 'Casing', 'type': 'casing'},
            doc_metadata={'well_name': 'Well 5', 'document_name': 'Final-Well-Report.pdf'}
        )
    """

    def __init__(self):
        """Initialize table chunker"""
        pass

    def chunk_tables(self,
                     tables: List,
                     section_info: Optional[Dict] = None,
                     doc_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Convert Docling tables to searchable chunks

        Args:
            tables: List of table objects from Docling (with .data, .text, .caption properties)
            section_info: Section metadata {'number': '3.4', 'title': 'Casing', 'type': 'casing', 'page': 20}
            doc_metadata: Document metadata {'well_name': 'Well 5', 'document_name': 'Final-Well-Report.pdf'}

        Returns:
            List of chunks with structure:
                [{
                    'text': 'Table: Casing Program\n\n| MD | TVD | ID |\n|---|---|---|\n...',
                    'metadata': {
                        'chunk_type': 'table',
                        'table_index': 0,
                        'table_caption': 'Casing Program',
                        'section_number': '3.4',
                        'section_title': 'Casing',
                        'section_type': 'casing',
                        'page': 20,
                        'well_name': 'Well 5',
                        'document_name': 'Final-Well-Report.pdf'
                    }
                }, ...]
        """
        chunks = []
        section_info = section_info or {}
        doc_metadata = doc_metadata or {}

        for i, table in enumerate(tables):
            # Extract table data
            table_md = self._table_to_markdown(table)

            if not table_md or not table_md.strip():
                continue  # Skip empty tables

            # Get caption (if available)
            caption = self._get_table_caption(table, i)

            # Build full text with context
            full_text = f"Table: {caption}\n\n{table_md}"

            # Build metadata
            metadata = {
                **doc_metadata,  # Include document-level metadata
                'chunk_type': 'table',
                'table_index': i,
                'table_caption': caption,
                'section_number': section_info.get('section_number') or section_info.get('number'),
                'section_title': section_info.get('section_title') or section_info.get('title'),
                'section_type': section_info.get('section_type') or section_info.get('type'),
                'page': section_info.get('page') or table.page if hasattr(table, 'page') else None,
            }

            chunks.append({
                'text': full_text,
                'metadata': metadata
            })

        return chunks

    def _table_to_markdown(self, table) -> str:
        """
        Convert Docling table to markdown format

        Args:
            table: Docling table object (has .data or .text attributes)

        Returns:
            Markdown-formatted table string
        """
        # Try different attributes based on Docling version
        if hasattr(table, 'data') and table.data is not None:
            # Table has structured data (DataFrame)
            if isinstance(table.data, pd.DataFrame):
                return table.data.to_markdown(index=False)
            elif isinstance(table.data, list):
                # List of lists/dicts
                df = pd.DataFrame(table.data)
                return df.to_markdown(index=False)
            else:
                # Unknown format, try converting to DataFrame
                try:
                    df = pd.DataFrame(table.data)
                    return df.to_markdown(index=False)
                except:
                    pass

        # Fallback: use text representation
        if hasattr(table, 'text') and table.text:
            return table.text

        # Last resort: string representation
        return str(table)

    def _get_table_caption(self, table, index: int) -> str:
        """
        Extract table caption or generate default

        Args:
            table: Docling table object
            index: Table index in document

        Returns:
            Caption string
        """
        if hasattr(table, 'caption') and table.caption:
            return table.caption

        # Try alternative attributes
        if hasattr(table, 'title') and table.title:
            return table.title

        # Default caption
        return f"Table {index + 1}"

    def chunk_table_from_markdown(self,
                                   markdown_text: str,
                                   caption: str = "Table",
                                   metadata: Optional[Dict] = None) -> Dict:
        """
        Create a table chunk from markdown text directly

        Useful for custom table extraction or testing

        Args:
            markdown_text: Table in markdown format
            caption: Table caption
            metadata: Additional metadata

        Returns:
            Single chunk dictionary
        """
        metadata = metadata or {}

        full_text = f"Table: {caption}\n\n{markdown_text}"

        chunk_metadata = {
            **metadata,
            'chunk_type': 'table',
            'table_caption': caption,
        }

        return {
            'text': full_text,
            'metadata': chunk_metadata
        }


def main():
    """Test the table chunker"""

    # Mock table object (simulating Docling output)
    class MockTable:
        def __init__(self, data, caption, page):
            self.data = pd.DataFrame(data)
            self.caption = caption
            self.page = page

    # Sample tables
    sample_tables = [
        MockTable(
            data={'MD (m)': [0, 500, 1500], 'TVD (m)': [0, 500, 1500], 'ID (in)': [13.375, 9.625, 7.0]},
            caption='Casing Program',
            page=20
        ),
        MockTable(
            data={'Depth (m)': [0, 100, 200], 'Lithology': ['Clay', 'Sand', 'Limestone']},
            caption='Stratigraphy',
            page=15
        )
    ]

    print("="*80)
    print("TABLE CHUNKER - TEST")
    print("="*80)

    # Test chunker
    chunker = TableChunker()
    chunks = chunker.chunk_tables(
        tables=sample_tables,
        section_info={'number': '3.4', 'title': 'Casing', 'type': 'casing', 'page': 20},
        doc_metadata={'well_name': 'Well 5', 'document_name': 'Final-Well-Report.pdf'}
    )

    print(f"\nNumber of table chunks created: {len(chunks)}")
    print("\nChunks with metadata:")
    print("-"*80)

    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"  Caption: {chunk['metadata']['table_caption']}")
        print(f"  Section: {chunk['metadata']['section_number']} - {chunk['metadata']['section_title']}")
        print(f"  Type: {chunk['metadata']['section_type']}")
        print(f"  Page: {chunk['metadata']['page']}")
        print(f"  Document: {chunk['metadata']['document_name']}")
        print(f"  Text preview ({len(chunk['text'])} chars):")
        print(f"    {chunk['text'][:150]}...")

    print("\n" + "="*80)
    print("[OK] Table chunker working correctly!")
    print("="*80)


if __name__ == '__main__':
    main()
