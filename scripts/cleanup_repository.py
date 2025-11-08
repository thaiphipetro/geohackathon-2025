"""
Repository Cleanup Script
Safely removes unnecessary files and organizes the repository structure
"""

import os
import shutil
from pathlib import Path
import sys

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_section(title):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_success(msg):
    print(f"{GREEN}[OK]{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}[WARN]{RESET} {msg}")

def print_error(msg):
    print(f"{RED}[ERROR]{RESET} {msg}")

def confirm(prompt):
    """Ask user for confirmation"""
    response = input(f"{YELLOW}{prompt} (y/n): {RESET}").strip().lower()
    return response == 'y'

def safe_remove_file(file_path):
    """Safely remove a file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print_error(f"Failed to remove {file_path}: {e}")
    return False

def safe_remove_dir(dir_path):
    """Safely remove a directory"""
    try:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            return True
    except Exception as e:
        print_error(f"Failed to remove {dir_path}: {e}")
    return False

def safe_move(src, dst):
    """Safely move a file"""
    try:
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return True
    except Exception as e:
        print_error(f"Failed to move {src} to {dst}: {e}")
    return False

def main():
    # Get project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print_section("REPOSITORY CLEANUP SCRIPT")
    print("This script will:")
    print("  1. Remove temporary/debug files")
    print("  2. Remove cache files")
    print("  3. Archive or remove old files")
    print("  4. Reorganize directory structure")
    print("")
    print(f"Working directory: {project_root}")
    print("")
    print("[AUTO] Proceeding with cleanup (non-interactive mode)")
    print("")

    # Statistics
    files_removed = 0
    files_archived = 0
    files_moved = 0

    # Phase 1: Create archive directory (safer option)
    print_section("Phase 1: Creating Archive Directory")

    archive_root = project_root / '.archive'
    archive_dirs = ['debug-scripts', 'session-logs', 'old-outputs', 'old-notebooks']

    for subdir in archive_dirs:
        archive_path = archive_root / subdir
        archive_path.mkdir(parents=True, exist_ok=True)
        print_success(f"Created: {archive_path}")

    # Phase 2: Remove cache files
    print_section("Phase 2: Removing Cache Files")

    cache_patterns = ['__pycache__', '.ipynb_checkpoints']
    for pattern in cache_patterns:
        for cache_dir in project_root.rglob(pattern):
            if safe_remove_dir(cache_dir):
                files_removed += 1
                print_success(f"Removed: {cache_dir}")

    # Remove .pyc files
    for pyc_file in project_root.rglob('*.pyc'):
        if safe_remove_file(pyc_file):
            files_removed += 1

    print_success(f"Removed all cache files")

    # Phase 3: Archive old debug scripts (keep useful ones)
    print_section("Phase 3: Archiving Old Debug Scripts")

    notebooks_dir = project_root / 'notebooks'

    # Scripts to keep (will be moved to scripts/ later)
    keep_scripts = ['debug_failing_wells.py']

    # Get all debug/test scripts
    all_debug_scripts = list(notebooks_dir.glob('debug_*.py')) + \
                       list(notebooks_dir.glob('test_*.py')) + \
                       [notebooks_dir / 'extract_toc_fixed.py',
                        notebooks_dir / 'run_notebook.py']

    # Archive only old scripts, skip ones we want to keep
    for script in all_debug_scripts:
        if script.exists() and script.name not in keep_scripts:
            dst = archive_root / 'debug-scripts' / script.name
            if safe_move(str(script), str(dst)):
                files_archived += 1
                print_success(f"Archived: {script.name}")
        elif script.name in keep_scripts:
            print_success(f"Keeping: {script.name} (will move to scripts/)")

    # Phase 4: Remove temporary files
    print_section("Phase 4: Removing Temporary Files")

    temp_files = [
        'emoji_lines.txt',
        'SESSION_SUMMARY_2025-11-07.md',
        'SESSION_SUMMARY_2025-11-08.md',
    ]

    for temp_file in temp_files:
        file_path = project_root / temp_file
        if safe_remove_file(file_path):
            files_removed += 1
            print_success(f"Removed: {temp_file}")

    # Phase 5: Archive old exploration outputs
    print_section("Phase 5: Archiving Old Exploration Outputs")

    outputs_exploration = project_root / 'outputs' / 'exploration'
    old_outputs = [
        'well_1_docling_markdown.txt',
        'well_1_pymupdf_text.txt',
        'well_2_docling_markdown.txt',
        'well_7_ocr_markdown.txt',
        'well_5_table_metadata.json',
    ]

    for output_file in old_outputs:
        src = outputs_exploration / output_file
        if src.exists():
            dst = archive_root / 'old-outputs' / output_file
            if safe_move(str(src), str(dst)):
                files_archived += 1
                print_success(f"Archived: {output_file}")

    # Phase 6: Remove duplicate notebooks
    print_section("Phase 6: Archiving Duplicate Notebooks")

    duplicate_notebooks = [
        'notebooks/01_data_exploration.ipynb',  # Keep v1 (newer, cleaner)
    ]

    for notebook in duplicate_notebooks:
        notebook_path = project_root / notebook
        if notebook_path.exists():
            dst = archive_root / 'old-notebooks' / notebook_path.name
            if safe_move(str(notebook_path), str(dst)):
                files_archived += 1
                print_success(f"Archived: {notebook}")

    # Phase 7: Remove old logs
    print_section("Phase 7: Removing Old Logs")

    old_logs = [
        'outputs/indexing_log.txt',  # Keep indexing_log_fixed.txt
    ]

    for log_file in old_logs:
        log_path = project_root / log_file
        if safe_remove_file(log_path):
            files_removed += 1
            print_success(f"Removed: {log_file}")

    # Phase 8: Move Python scripts from notebooks to scripts
    print_section("Phase 8: Reorganizing Scripts")

    scripts_to_move = [
        'build_toc_database.py',
        'analyze_all_tocs.py',
        'debug_failing_wells.py',
    ]

    for script in scripts_to_move:
        src = notebooks_dir / script
        if src.exists():
            dst = project_root / 'scripts' / script
            if safe_move(str(src), str(dst)):
                files_moved += 1
                print_success(f"Moved: {script} to scripts/")

    # Phase 9: Archive session logs
    print_section("Phase 9: Archiving Session Logs")

    session_logs_dir = project_root / '.claude' / 'tasks' / 'session-logs'
    if session_logs_dir.exists():
        print("[AUTO] Archiving session logs (non-interactive mode)")
        dst = archive_root / 'session-logs'
        if session_logs_dir.exists():
            for log_file in session_logs_dir.glob('*.md'):
                if safe_move(str(log_file), str(dst / log_file.name)):
                    files_archived += 1
                    print_success(f"Archived: {log_file.name}")

            # Remove empty directory
            if not any(session_logs_dir.iterdir()):
                safe_remove_dir(session_logs_dir)

    # Summary
    print_section("CLEANUP SUMMARY")

    print(f"Files removed: {files_removed}")
    print(f"Files archived: {files_archived}")
    print(f"Files moved: {files_moved}")
    print(f"\nArchive location: {archive_root}")

    # Check final sizes
    print("\n" + "-"*80)
    print("Final directory sizes:")
    print("-"*80)

    dirs_to_check = ['src', 'scripts', 'notebooks', 'outputs', '.claude', '.archive']
    for dir_name in dirs_to_check:
        dir_path = project_root / dir_name
        if dir_path.exists():
            size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
            size_kb = size / 1024
            print(f"{dir_name:20s}: {size_kb:>10.1f} KB")

    print("\n" + "="*80)
    print_success("Cleanup complete!")
    print("="*80)

    print("\nNext steps:")
    print("  1. Review the changes: git status")
    print("  2. Test the system: python scripts/check_chromadb_status.py")
    print("  3. Update .gitignore if needed")
    print("  4. Commit changes: git add . && git commit -m 'chore: repository cleanup'")
    print(f"\nTo restore archived files: cp .archive/*/* <destination>/")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCleanup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
