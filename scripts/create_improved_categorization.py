"""
Create improved 13-category system with well_testing & intervention categories

This script:
1. Loads existing 11-category mapping
2. Creates 2 new categories: well_testing, intervention
3. Rearranges entries from completion to new categories
4. Adds 76 uncategorized entries to appropriate categories
5. Saves new categorization to final_section_categorization_v2.json
"""

import json
from pathlib import Path
from datetime import datetime

# Load existing categorization
print("="*80)
print("CREATING IMPROVED 13-CATEGORY SYSTEM")
print("="*80)

with open("outputs/final_section_categorization.json", "r") as f:
    old_cat = json.load(f)

# Create new 13-category structure
new_categories = {
    "metadata": {
        "version": "2.0",
        "created": datetime.now().isoformat(),
        "total_categories": 13,
        "description": "Improved categorization with well_testing and intervention categories"
    },
    "categories": {}
}

# Copy existing categories (keep original entries)
for cat_name, cat_data in old_cat["categories"].items():
    new_categories["categories"][cat_name] = {
        "description": cat_data["description"],
        "entries": cat_data["entries"].copy()
    }

print(f"[OK] Loaded {len(old_cat['categories'])} existing categories")

# Create new category: well_testing
new_categories["categories"]["well_testing"] = {
    "description": "Well testing, production tests, pressure tests, and formation integrity tests",
    "entries": []
}

# Create new category: intervention
new_categories["categories"]["intervention"] = {
    "description": "Workover operations, perforating, TCP, and well intervention activities",
    "entries": []
}

print(f"[OK] Created 2 new categories: well_testing, intervention")

# Now add the 76 uncategorized entries based on my analysis

# Load current TOC database to get actual entries
with open("outputs/exploration/toc_database_multi_doc_full.json", "r") as f:
    toc_db = json.load(f)

# Define mappings for uncategorized entries
uncategorized_mappings = {
    # project_admin additions
    ("Well 1", "1.", "General Project data"): "project_admin",
    ("Well 1", "3.", "Contractor List"): "project_admin",
    ("Well 4", "1.0", "Revision No."): "project_admin",
    ("Well 5", "1.", "Project Details"): "project_admin",
    ("Well 5", "1.1", "Organisation"): "project_admin",
    ("Well 5", "1.0", "Revision No."): "project_admin",
    ("Well 8", "1.1", "ORGANIZATION"): "project_admin",

    # well_identification additions
    ("Well 1", "1.2", "Objectives"): "well_identification",
    ("Well 1", "1.1", "Planned operation"): "well_identification",

    # geology additions
    ("Well 5", "4", "Geology"): "geology",
    ("Well 5", "4.1", "Lithostratigraphic column"): "geology",
    ("Well 8", "4.1", "LITHOSTRATIGRAPHIC COLUMN"): "geology",
    ("Well 8", "4.2", "PRESUMED GEOLOGIC FAULTS"): "geology",
    ("Well 8", "4.3", "HYDROCARBONS"): "geology",
    ("Well 5", "Appendix 1", "Litholog (Scale 1:1000)"): "geology",

    # borehole additions
    ("Well 2", "1.2", "12 ¾' hole and 10 ¾' casing"): "borehole",
    ("Well 2", "1.3", "______________________________________________________ 8 ½' hole and 7' liner"): "borehole",
    ("Well 2", "1.4", "6' Hole and 4 ½'liner WWS_________________________________________________"): "borehole",
    ("Well 4", "8.3", "24' hole section"): "borehole",
    ("Well 4", "8.7", "12 ¼' hole section"): "borehole",
    ("Well 5", "2.1", "Depths and trajectory"): "borehole",
    ("Well 5", "28", "3.8.1 Horizontal Projection NLW-GT-03"): "borehole",
    ("Well 5", "29", "3.8.2 Vertical Projection NLW-GT-03"): "borehole",
    ("Well 5", "30", "3.8.3 Horizontal Projection NLW-GT-03-S1"): "borehole",
    ("Well 5", "31", "3.8.4 Vertical Projection NLW-GT-03-S1"): "borehole",
    ("Well 8", "2.1", "DEPTHS AND TRAJECTORY"): "borehole",
    ("Well 8", "2.2", "VERTICAL SECTION AND PLAN VIEW MSD-GT-01"): "borehole",

    # casing additions
    ("Well 4", "8.6", "13-5/8' tie-back string, install THS and BOP"): "casing",
    ("Well 8", "2.4", "Cement log evaluation"): "casing",
    ("Well 8", "2.5", "Well schematic - post job"): "casing",
    ("Well 8", "2.3.1", "CASING"): "casing",
    ("Well 8", "2.3.2", "CEMENT"): "casing",

    # directional additions
    ("Well 2", "Appendix 5", "Directional data and plot__________________________________________11"): "directional",
    ("Well 2", "Appendix 2", "Time Depth Curve ________________________________________________8"): "directional",

    # drilling_operations additions
    ("Well 4", "7.1", "Non Productive Time (NPT)"): "drilling_operations",
    ("Well 4", "4.", "Mud Properties.........................................................................................................................................."): "drilling_operations",
    ("Well 5", "1.2", "Operational summary"): "drilling_operations",
    ("Well 5", "1.3", "Drilling rig"): "drilling_operations",
    ("Well 5", "3", "Drilling fluid summary"): "drilling_operations",
    ("Well 8", "1.3", "DRILLING RIG"): "drilling_operations",

    # well_testing (NEW CATEGORY)
    ("Well 2", "1.5", "Production test ____________________________________________________________"): "well_testing",
    ("Well 2", "Appendix 9", "FIT's__________________________________________________________15"): "well_testing",
    ("Well 2", "Appendix 11", "Well test report_________________________________________________17"): "well_testing",
    ("Well 4", "8.10", "Rig less welltest"): "well_testing",

    # intervention (NEW CATEGORY)
    ("Well 8", "6.1", "TCP toolstring run 1"): "intervention",
    ("Well 8", "6.2", "TCP toolstring run 2"): "intervention",
    ("Well 8", "6.3", "Pressure log perforating run#1"): "intervention",
    ("Well 8", "6.4", "Pressure log perforating run#2"): "intervention",
    ("Well 8", "6.5", "MFC log"): "intervention",
    ("Well 8", "6.6", "RBT log"): "intervention",

    # completion additions (keep some, move testing to well_testing)
    ("Well 1", "2.1", "Final Well Status"): "completion",
    ("Well 1", "2.2", "Wellhead &amp; Xmas Tree"): "completion",
    ("Well 5", "5", "Well suspension status"): "completion",
    ("Well 5", "5.1", "Well status"): "completion",
    ("Well 5", "5.2", "Well barrier schematic"): "completion",
    ("Well 5", "5.3", "Wellhead and Christmas tree drawing"): "completion",
    ("Well 8", "5.", "WELL SUSPENSION STATUS"): "completion",
    ("Well 8", "5.3", "WELLHEAD AND CHRISTMAS TREE DRAWING"): "completion",

    # technical_summary additions
    ("Well 1", "1.1", "Introduction"): "technical_summary",  # Clarified: goes here
    ("Well 4", "1.", "Executive Summary..................................................................................................................................."): "technical_summary",
    ("Well 4", "8.", "Operations review"): "technical_summary",
    ("Well 4", "2.", "Project Data..............................................................................................................................................."): "technical_summary",
    ("Well 5", "2", "Well summary"): "technical_summary",
    ("Well 5", "2.2", "Technical summary"): "technical_summary",
    ("Well 8", "2.", "WELL SUMMARY"): "technical_summary",
    ("Well 8", "2.3", "TECHNICAL SUMMARY"): "technical_summary",

    # appendices additions (including corrupted ones)
    ("Well 2", "Appendix 1", "A d ppen ix 1, Detailed drilling program"): "appendices",
    ("Well 2", "Appendix 3", "_____________________________________________________9"): "appendices",
    ("Well 2", "Appendix 4", "Well head sketch ________________________________________________10"): "appendices",
    ("Well 2", "Appendix 6", "________________________________________________12"): "appendices",
    ("Well 2", "Appendix 7", "_____________________________________________________13"): "appendices",
    ("Well 2", "Appendix 8", "_________________________________________________14"): "appendices",
    ("Well 2", "Appendix 10", "____________________________________________16"): "appendices",
    ("Well 5", "Appendix 2", "Daily Reports"): "appendices",
    ("Well 5", "Appendix 4", "DVD"): "appendices",
    ("Well 8", "6", "Appendixes"): "appendices",
}

# Add entries from mappings
added_count = 0
for (well, number, title), category in uncategorized_mappings.items():
    entry = {
        "well": well,
        "number": number,
        "title": title
    }
    new_categories["categories"][category]["entries"].append(entry)
    added_count += 1

print(f"[OK] Added {added_count} uncategorized entries to categories")

# Calculate statistics
total_entries = sum(len(cat["entries"]) for cat in new_categories["categories"].values())

print("\n" + "="*80)
print("NEW 13-CATEGORY SYSTEM SUMMARY")
print("="*80)

for cat_name, cat_data in sorted(new_categories["categories"].items()):
    count = len(cat_data["entries"])
    print(f"{cat_name:25} {count:3} entries")

print("="*80)
print(f"Total entries: {total_entries}")
print(f"Coverage: {total_entries}/207 = {total_entries/207*100:.1f}%")
print("="*80)

# Save new categorization
output_path = Path("outputs/final_section_categorization_v2.json")
with open(output_path, "w") as f:
    json.dump(new_categories, f, indent=2)

print(f"\n[OK] Saved to: {output_path}")
print("\nNext steps:")
print("1. Review the new categorization")
print("2. Run build_toc_database with updated categories")
print("3. Re-index vector store")
