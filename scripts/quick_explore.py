"""
Quick Data Exploration Script
Alternative to Jupyter notebook for quick inspection
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import json

console = Console()


def scan_dataset(data_dir: Path):
    """Scan training data directory"""

    console.print("\n[bold cyan]Scanning training data...[/bold cyan]\n")

    wells = {}

    # Find all well folders
    well_folders = sorted([d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith('Well')])

    for well_folder in track(well_folders, description="Scanning wells..."):
        well_name = well_folder.name

        # Count files by type
        pdf_files = list(well_folder.rglob("*.pdf"))
        xlsx_files = list(well_folder.rglob("*.xlsx"))
        docx_files = list(well_folder.rglob("*.docx"))
        png_files = list(well_folder.rglob("*.png"))

        # Find well reports
        well_reports = [f for f in pdf_files if 'well report' in str(f.parent).lower()]
        eowr_files = [f for f in well_reports if 'eowr' in f.name.lower()]

        wells[well_name] = {
            "path": well_folder,
            "pdf_count": len(pdf_files),
            "xlsx_count": len(xlsx_files),
            "docx_count": len(docx_files),
            "png_count": len(png_files),
            "well_reports": well_reports,
            "eowr_files": eowr_files,
            "subfolders": [d.name for d in well_folder.iterdir() if d.is_dir()]
        }

    return wells


def display_summary(wells_data):
    """Display dataset summary"""

    # Create summary table
    summary_table = Table(title="Training Data Summary", show_lines=True)
    summary_table.add_column("Well", style="cyan", no_wrap=True)
    summary_table.add_column("PDFs", justify="right")
    summary_table.add_column("Excel", justify="right")
    summary_table.add_column("Word", justify="right")
    summary_table.add_column("Images", justify="right")
    summary_table.add_column("EOWR", justify="right", style="green")
    summary_table.add_column("Quality", justify="center")

    for well_name, data in wells_data.items():
        # Assess quality
        has_eowr = len(data['eowr_files']) > 0
        has_tech_logs = 'Technical log' in data['subfolders'] or 'Technical Log' in data['subfolders']

        if has_eowr and has_tech_logs and data['pdf_count'] > 5:
            quality = "High"
        elif has_eowr:
            quality = "Medium"
        else:
            quality = "Low"

        summary_table.add_row(
            well_name,
            str(data['pdf_count']),
            str(data['xlsx_count']),
            str(data['docx_count']),
            str(data['png_count']),
            str(len(data['eowr_files'])),
            quality
        )

    console.print(summary_table)

    # Total statistics
    total_pdfs = sum(d['pdf_count'] for d in wells_data.values())
    total_excel = sum(d['xlsx_count'] for d in wells_data.values())
    total_eowr = sum(len(d['eowr_files']) for d in wells_data.values())

    console.print(Panel(
        f"""[bold green]Dataset Statistics:[/bold green]

Total Wells: {len(wells_data)}
Total PDF Files: {total_pdfs}
Total Excel Files: {total_excel}
Total EOWR Reports: {total_eowr}

[bold yellow]Recommended Starting Wells:[/bold yellow]
1. Well 5 (NLW-GT-03) - Most comprehensive
2. Well 7 (BRI-GT-01) - Well organized
3. Well 1 (ADK-GT-01) - Good quality
""",
        title="Overall Summary"
    ))


def show_well_details(wells_data, well_name):
    """Show detailed information for a specific well"""

    if well_name not in wells_data:
        console.print(f"[red]Well '{well_name}' not found[/red]")
        return

    data = wells_data[well_name]

    console.print(f"\n[bold cyan]=== {well_name} Details ===[/bold cyan]\n")

    # Show folder structure
    console.print(f"[bold]Path:[/bold] {data['path']}")
    console.print(f"[bold]Subfolders:[/bold] {', '.join(data['subfolders'])}\n")

    # Show EOWR files
    if data['eowr_files']:
        console.print("[bold green]EOWR Reports:[/bold green]")
        for eowr in data['eowr_files']:
            size_mb = eowr.stat().st_size / 1024 / 1024
            console.print(f"  • {eowr.name} ({size_mb:.2f} MB)")
    else:
        console.print("[yellow]No EOWR reports found[/yellow]")

    console.print()


def main():
    """Main exploration script"""

    console.print(Panel.fit(
        "[bold cyan]GeoHackathon 2025[/bold cyan]\n"
        "[bold]Quick Data Exploration[/bold]",
        border_style="cyan"
    ))

    # Set paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "Training data-shared with participants"

    if not data_dir.exists():
        console.print(f"[red]Error: Training data not found at {data_dir}[/red]")
        console.print("[yellow]Please ensure the training data folder is in the correct location[/yellow]")
        return

    # Scan dataset
    wells_data = scan_dataset(data_dir)

    # Display summary
    console.print()
    display_summary(wells_data)

    # Show details for high-quality wells
    console.print("\n[bold cyan]=== High-Quality Wells Detail ===[/bold cyan]")
    for well in ['Well 5', 'Well 7', 'Well 1']:
        show_well_details(wells_data, well)

    # Save summary
    output_dir = project_root / "outputs" / "exploration"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_file = output_dir / "quick_scan_summary.json"

    # Convert to JSON-serializable format
    summary_data = {}
    for well_name, data in wells_data.items():
        summary_data[well_name] = {
            "pdf_count": data['pdf_count'],
            "xlsx_count": data['xlsx_count'],
            "docx_count": data['docx_count'],
            "png_count": data['png_count'],
            "eowr_count": len(data['eowr_files']),
            "eowr_files": [str(f) for f in data['eowr_files']],
            "subfolders": data['subfolders']
        }

    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)

    console.print(f"\n[green]Summary saved to:[/green] {summary_file}")

    # Next steps
    console.print(Panel(
        """[bold yellow]Next Steps:[/bold yellow]

1. Open Jupyter notebook for detailed exploration:
   [cyan]cd notebooks && jupyter notebook[/cyan]

2. Or start Day 1 implementation:
   [cyan]python src/document_parser.py[/cyan]

3. Focus on Well 5 (NLW-GT-03) - best quality data

[bold]Key Files to Extract:[/bold]
• MD (Measured Depth)
• TVD (True Vertical Depth)
• ID (Inner Diameter)

From: [green]Well Report/EOWR PDFs[/green]
""",
        title="Ready to Start!",
        border_style="green"
    ))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
