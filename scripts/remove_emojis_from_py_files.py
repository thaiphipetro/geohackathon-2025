"""
Remove all emojis from Python source files for Windows compatibility
"""

import re
from pathlib import Path

# Emoji pattern (matches most common emojis)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE
)

# Emoji replacements
REPLACEMENTS = {
    '📚': '[LOAD]',
    '✅': '[OK]',
    '🔧': '[INIT]',
    '📁': '[DIR]',
    '📄': '[FILE]',
    'ℹ️': '[INFO]',
    'ℹ': '[INFO]',
    '⚠️': '[WARN]',
    '⚠': '[WARN]',
    '❌': '[ERROR]',
    '💾': '[SAVE]',
    '🎯': '[TARGET]',
    '📊': '[STATS]',
    '🚀': '[GO]',
}

def remove_emojis_from_file(file_path):
    """Remove emojis from a single file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # First, replace known emojis with ASCII
    for emoji, replacement in REPLACEMENTS.items():
        content = content.replace(emoji, replacement)

    # Then remove any remaining emojis
    content = EMOJI_PATTERN.sub('', content)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Files to process - all Python files in src/
src_dir = Path(__file__).parent.parent / 'src'
files_to_process = list(src_dir.glob('*.py'))

print("Removing emojis from Python files...")
for file_path in files_to_process:
    if file_path.exists():
        if remove_emojis_from_file(file_path):
            print(f"  [OK] {file_path.name}")
        else:
            print(f"  [SKIP] {file_path.name} (no emojis)")
    else:
        print(f"  [MISS] {file_path.name} (file not found)")

print("\nDone!")
