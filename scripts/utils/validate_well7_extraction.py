"""
Validate Well 7 Enhanced Extraction Results
"""

import json
from pathlib import Path

print("=" * 80)
print("WELL 7 EXTRACTION VALIDATION")
print("=" * 80)

output_dir = Path("outputs/well7_enhanced")

# Files to validate
files = [
    "NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02_results.json",
    "NLOG_GS_PUB_BIR-GT-01_AWB_Rev A 1_WellpathReport_results.json",
    "NLOG_GS_PUB_Appendix III_Casing tallies BRI-GT-01_results.json",
]

total_tables = 0
total_pictures = 0
total_chunks = 0

for filename in files:
    filepath = output_dir / filename

    if not filepath.exists():
        print(f"\n[MISSING] {filename}")
        continue

    print(f"\n{'=' * 80}")
    print(f"FILE: {filename}")
    print("=" * 80)

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Summary stats
    print(f"\nSummary:")
    print(f"  Tables: {len(data['tables'])}")
    print(f"  Pictures: {len(data['pictures'])}")
    print(f"  Chunks: {len(data['chunks'])}")
    print(f"  Text: {data['metadata']['total_chars']:,} chars")

    total_tables += len(data['tables'])
    total_pictures += len(data['pictures'])
    total_chunks += len(data['chunks'])

    # Validate first table
    if data['tables']:
        table = data['tables'][0]
        print(f"\nFirst Table:")
        print(f"  Size: {table['num_rows']} rows x {table['num_cols']} cols")
        print(f"  Has data: {len(table['data']) > 0}")
        print(f"  Has markdown: {table['markdown'] is not None}")

        # Show first row if exists
        if table['data']:
            first_row = table['data'][0]
            print(f"  First row keys: {list(first_row.keys())[:5]}")

    # Validate first picture
    if data['pictures']:
        picture = data['pictures'][0]
        print(f"\nFirst Picture:")
        print(f"  Has image path: {picture['image_path'] is not None}")
        print(f"  Dimensions: {picture['width']}x{picture['height']}")
        print(f"  Has classification: {picture['classification'] is not None}")
        print(f"  Has VLM description: {picture['description'] is not None}")

        # Check if image file exists
        if picture['image_path']:
            img_path = Path(picture['image_path'])
            print(f"  Image file exists: {img_path.exists()}")
            if img_path.exists():
                print(f"  Image size: {img_path.stat().st_size / 1024:.1f} KB")

        # Show description preview
        if picture['description']:
            desc_preview = picture['description'][:100]
            print(f"  Description preview: {desc_preview}...")

# Check extracted images
print(f"\n{'=' * 80}")
print("IMAGE EXTRACTION VALIDATION")
print("=" * 80)

images_dir = output_dir / "images" / "_" / "pictures"
if images_dir.exists():
    images = list(images_dir.glob("*.png"))
    print(f"\nTotal images saved: {len(images)}")

    if images:
        # Show first few
        print(f"\nSample images:")
        for img in images[:5]:
            size_kb = img.stat().st_size / 1024
            print(f"  {img.name}: {size_kb:.1f} KB")
else:
    print(f"\n[WARNING] Images directory not found: {images_dir}")

# Overall summary
print(f"\n{'=' * 80}")
print("OVERALL SUMMARY")
print("=" * 80)
print(f"Total tables extracted: {total_tables}")
print(f"Total pictures extracted: {total_pictures}")
print(f"Total chunks created: {total_chunks}")

# Validation checks
print(f"\nValidation Checks:")
print(f"  [{'OK' if total_tables >= 30 else 'WARN'}] Tables: {total_tables} (expected ~30)")
print(f"  [{'OK' if total_pictures >= 48 else 'WARN'}] Pictures: {total_pictures} (expected ~48)")
print(f"  [{'OK' if total_chunks >= 180 else 'WARN'}] Chunks: {total_chunks} (expected ~186)")

if images_dir.exists():
    actual_images = len(list(images_dir.glob("*.png")))
    print(f"  [{'OK' if actual_images > 0 else 'FAIL'}] Image files: {actual_images} saved")

print("\n" + "=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)
