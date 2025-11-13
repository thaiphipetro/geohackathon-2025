"""
Verify Well 7 TOC metadata quality
Check if TOC sections are properly extracted
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vector_store import TOCEnhancedVectorStore

print("="*80)
print("VERIFYING WELL 7 TOC METADATA QUALITY")
print("="*80)

# Connect to ChromaDB
vector_store = TOCEnhancedVectorStore()
collection = vector_store.collection

# Get all chunks for Well 7
results = collection.get(
    where={"well_name": "Well 7"},
    include=["metadatas"]
)

if not results['ids']:
    print("\n[ERROR] No Well 7 chunks found")
    exit(1)

print(f"\n[INFO] Found {len(results['ids'])} Well 7 chunks")

# Extract unique TOC sections
toc_sections = set()
chunks_with_toc = 0

for metadata in results['metadatas']:
    if 'section_number' in metadata and 'section_title' in metadata:
        chunks_with_toc += 1
        section_num = metadata.get('section_number', '')
        section_title = metadata.get('section_title', '')
        if section_num and section_title:
            toc_sections.add((section_num, section_title))

print(f"\n[INFO] {chunks_with_toc} chunks have TOC metadata")
print(f"[INFO] {len(toc_sections)} unique TOC sections found")

if toc_sections:
    print("\n" + "-"*80)
    print("EXTRACTED TOC SECTIONS:")
    print("-"*80)

    # Sort by section number
    sorted_sections = sorted(toc_sections, key=lambda x: (
        len(x[0].split('.')),  # Sort by depth first
        [int(p) if p.isdigit() else p for p in x[0].split('.')]  # Then numerically
    ))

    for i, (num, title) in enumerate(sorted_sections, 1):
        print(f"{i:2d}. {num:5s} - {title}")

    print("-"*80)

    # Check if it looks like the expected Well 7 TOC
    expected_sections = {
        '1': 'General Project data',
        '2': 'Well summary',
        '2.1': 'Directional plots',
        '2.2': 'Technical summary'
    }

    matches = 0
    for num, title in expected_sections.items():
        if any(s[0] == num and title.lower() in s[1].lower() for s in toc_sections):
            matches += 1

    print(f"\n[INFO] Matched {matches}/{len(expected_sections)} expected sections")

    if matches >= 3:
        print("[SUCCESS] TOC metadata appears to be correctly extracted!")
    else:
        print("[WARN] TOC metadata may need re-extraction")
else:
    print("\n[ERROR] No TOC sections found in metadata")

print("\n" + "="*80)
