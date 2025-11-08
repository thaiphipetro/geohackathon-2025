"""
Section-Aware Chunker
Chunks text with section context for better retrieval accuracy
"""

from typing import List, Dict
import re


class SectionAwareChunker:
    """
    Chunks text while preserving section context

    Strategy:
        1. Split by markdown headers (## Section Title)
        2. Prepend section header to each chunk
        3. Add metadata (section_number, section_title, page)
        4. Use overlapping chunks for better retrieval

    Example:
        chunker = SectionAwareChunker(chunk_size=1000, overlap=200)
        chunks = chunker.chunk_with_section_headers(text, toc_sections)
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize chunker

        Args:
            chunk_size: Maximum characters per chunk
            overlap: Characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_with_section_headers(self,
                                     text: str,
                                     toc_sections: List[Dict]) -> List[Dict]:
        """
        Chunk text and prepend section headers for context

        Args:
            text: Full markdown text from Docling
            toc_sections: List of TOC sections with metadata
                [{
                    'number': '2.1',
                    'title': 'Depths',
                    'page': 6,
                    'type': 'depth'
                }, ...]

        Returns:
            List of chunks with metadata:
                [{
                    'text': 'Section 2.1 Depths\n\nMD: 2500m...',
                    'metadata': {
                        'section_number': '2.1',
                        'section_title': 'Depths',
                        'section_type': 'depth',
                        'page': 6,
                        'chunk_index': 0
                    }
                }, ...]
        """
        chunks = []

        # Split by markdown headers (## Section Title or # Section Title)
        # This regex captures the header and its content
        sections = re.split(r'(^#{1,2}\s+.+$)', text, flags=re.MULTILINE)

        # Process sections (header + content pairs)
        for i in range(1, len(sections), 2):
            if i >= len(sections):
                break

            header = sections[i].strip()
            content = sections[i+1].strip() if i+1 < len(sections) else ''

            if not content:
                continue

            # Find matching TOC entry for this header
            toc_match = self._find_toc_match(header, toc_sections)

            # Chunk the content with overlap
            content_chunks = self._split_text_with_overlap(content)

            # Add header to each chunk
            for chunk_idx, chunk_text in enumerate(content_chunks):
                # Prepend header to chunk for context
                full_chunk = f"{header}\n\n{chunk_text}"

                chunks.append({
                    'text': full_chunk,
                    'metadata': {
                        'section_number': toc_match.get('number') if toc_match else None,
                        'section_title': toc_match.get('title') if toc_match else self._extract_title(header),
                        'section_type': toc_match.get('type') if toc_match else None,
                        'page': toc_match.get('page') if toc_match else None,
                        'chunk_index': chunk_idx,
                    }
                })

        return chunks

    def _find_toc_match(self, header: str, toc_sections: List[Dict]) -> Dict:
        """
        Match markdown header to TOC entry

        Args:
            header: Markdown header (e.g., "## 2.1 Depths")
            toc_sections: List of TOC sections

        Returns:
            Matching TOC entry or None
        """
        # Extract section number from header (e.g., "## 2.1 Depths" -> "2.1")
        header_match = re.search(r'#{1,2}\s+(\d+\.?\d*\.?\d*)\s+(.+)', header)
        if not header_match:
            return None

        section_num = header_match.group(1)
        header_title = header_match.group(2).strip()

        # Find matching TOC entry
        for toc in toc_sections:
            if toc['number'] == section_num:
                return toc
            # Fuzzy match on title if number doesn't match
            if header_title.lower() in toc['title'].lower() or toc['title'].lower() in header_title.lower():
                return toc

        return None

    def _extract_title(self, header: str) -> str:
        """Extract title from markdown header"""
        # Remove markdown syntax (## or #)
        title = re.sub(r'^#{1,2}\s+', '', header)
        # Remove section numbers
        title = re.sub(r'^\d+\.?\d*\.?\d*\s+', '', title)
        return title.strip()

    def _split_text_with_overlap(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap

        Args:
            text: Text to chunk

        Returns:
            List of overlapping text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence boundary if possible
            if end < len(text):
                # Look for period, newline, or other break point
                break_points = ['.', '\n', '!', '?']
                for i in range(end, max(start, end - 100), -1):
                    if i < len(text) and text[i] in break_points:
                        end = i + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - self.overlap

        return chunks

    def chunk_simple(self, text: str, well_name: str = None) -> List[Dict]:
        """
        Simple chunking without section headers (fallback)

        Args:
            text: Text to chunk
            well_name: Optional well identifier for metadata

        Returns:
            List of chunks with basic metadata
        """
        chunks = []
        text_chunks = self._split_text_with_overlap(text)

        for idx, chunk_text in enumerate(text_chunks):
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    'well_name': well_name,
                    'chunk_index': idx,
                    'section_number': None,
                    'section_title': None,
                    'section_type': None,
                    'page': None,
                }
            })

        return chunks


def main():
    """Test the section-aware chunker"""

    # Sample markdown text (simulating Docling output)
    sample_text = """
## 2.1 Depths

The well has the following depth measurements:
- Measured Depth (MD): 2500 meters
- True Vertical Depth (TVD): 2300 meters
- Kick-off Point (KOP): 700 meters

Additional details about the well trajectory...

## 2.2 Casing

Casing specifications:
- 13 3/8" casing to 500m
- 9 5/8" casing to 1500m
- 7" liner to TD

The casing program was designed for...
"""

    # Sample TOC sections
    toc_sections = [
        {'number': '2.1', 'title': 'Depths', 'page': 6, 'type': 'depth'},
        {'number': '2.2', 'title': 'Casing', 'page': 6, 'type': 'casing'},
    ]

    print("="*80)
    print("SECTION-AWARE CHUNKER - TEST")
    print("="*80)

    # Test chunker
    chunker = SectionAwareChunker(chunk_size=200, overlap=50)
    chunks = chunker.chunk_with_section_headers(sample_text, toc_sections)

    print(f"\nOriginal text length: {len(sample_text)} chars")
    print(f"Number of chunks: {len(chunks)}")
    print(f"\nChunks with metadata:")
    print("-"*80)

    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"  Section: {chunk['metadata']['section_number']} - {chunk['metadata']['section_title']}")
        print(f"  Type: {chunk['metadata']['section_type']}")
        print(f"  Page: {chunk['metadata']['page']}")
        print(f"  Text ({len(chunk['text'])} chars):")
        print(f"    {chunk['text'][:100]}...")

    print("\n" + "="*80)
    print("[OK] Chunker working correctly!")
    print("="*80)


if __name__ == '__main__':
    main()
