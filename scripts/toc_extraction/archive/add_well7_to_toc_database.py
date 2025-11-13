"""
Add Well 7 to TOC database with LLM-extracted TOC and publication date
"""

import json
from pathlib import Path
from datetime import datetime

# Load existing TOC database
toc_db_path = Path("outputs/exploration/toc_database_multi_doc_full.json")
with open(toc_db_path, 'r', encoding='utf-8') as f:
    toc_database = json.load(f)

# Well 7 EOWR with LLM-extracted TOC
well7_entry = {
    "filename": "NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf",
    "filepath": "Training data-shared with participants\\Well 7\\Well report\\NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf",
    "file_size": 0,  # Will be calculated
    "pub_date": "2015-11-27T00:00:00",
    "is_scanned": True,
    "parse_method": "LLM",
    "toc": [
        {
            "number": "1",
            "title": "General Project data",
            "page": 5,
            "type": "project_admin"
        },
        {
            "number": "2",
            "title": "Well summary",
            "page": 6,
            "type": "well_identification"
        },
        {
            "number": "2.1",
            "title": "Directional plots",
            "page": 7,
            "type": "technical"
        },
        {
            "number": "2.2",
            "title": "Technical summary",
            "page": 8,
            "type": "technical"
        },
        {
            "number": "3",
            "title": "Drilling fluid summary",
            "page": 9,
            "type": "drilling"
        },
        {
            "number": "4",
            "title": "Well schematic",
            "page": 10,
            "type": "technical"
        },
        {
            "number": "5",
            "title": "Geology",
            "page": 12,
            "type": "geology"
        },
        {
            "number": "6",
            "title": "HSE performance",
            "page": 13,
            "type": "hse"
        },
        {
            "number": "6.1",
            "title": "General",
            "page": 14,
            "type": "hse"
        },
        {
            "number": "6.2",
            "title": "Incident",
            "page": 0,
            "type": "hse"
        },
        {
            "number": "6.3",
            "title": "Drills/Emergency exercises, inspections & audits",
            "page": 0,
            "type": "hse"
        }
    ],
    "key_sections": {
        "project_admin": [
            {
                "number": "1",
                "title": "General Project data",
                "page": 5,
                "type": "project_admin"
            }
        ],
        "well_identification": [
            {
                "number": "2",
                "title": "Well summary",
                "page": 6,
                "type": "well_identification"
            }
        ],
        "technical": [
            {
                "number": "2.1",
                "title": "Directional plots",
                "page": 7,
                "type": "technical"
            },
            {
                "number": "2.2",
                "title": "Technical summary",
                "page": 8,
                "type": "technical"
            },
            {
                "number": "4",
                "title": "Well schematic",
                "page": 10,
                "type": "technical"
            }
        ],
        "drilling": [
            {
                "number": "3",
                "title": "Drilling fluid summary",
                "page": 9,
                "type": "drilling"
            }
        ],
        "geology": [
            {
                "number": "5",
                "title": "Geology",
                "page": 12,
                "type": "geology"
            }
        ],
        "hse": [
            {
                "number": "6",
                "title": "HSE performance",
                "page": 13,
                "type": "hse"
            },
            {
                "number": "6.1",
                "title": "General",
                "page": 14,
                "type": "hse"
            },
            {
                "number": "6.2",
                "title": "Incident",
                "page": 0,
                "type": "hse"
            },
            {
                "number": "6.3",
                "title": "Drills/Emergency exercises, inspections & audits",
                "page": 0,
                "type": "hse"
            }
        ]
    }
}

# Calculate file size
pdf_path = Path("Training data-shared with participants/Well 7/Well report/NLOG_GS_PUB_BRI-GT-01 SodM EOWR v1.02.pdf")
if pdf_path.exists():
    well7_entry["file_size"] = pdf_path.stat().st_size

# Add Well 7 to database
toc_database["Well 7"] = [well7_entry]

# Save updated database
with open(toc_db_path, 'w', encoding='utf-8') as f:
    json.dump(toc_database, f, indent=2, ensure_ascii=False)

print("="*80)
print("ADDED WELL 7 TO TOC DATABASE")
print("="*80)
print(f"\nFile: {well7_entry['filename']}")
print(f"Publication date: {well7_entry['pub_date']}")
print(f"Scanned: {well7_entry['is_scanned']}")
print(f"Parse method: {well7_entry['parse_method']}")
print(f"TOC sections: {len(well7_entry['toc'])}")
print(f"\nDatabase now contains: {len(toc_database)} wells")
print(f"Wells: {', '.join(sorted(toc_database.keys()))}")
print("\n" + "="*80)
