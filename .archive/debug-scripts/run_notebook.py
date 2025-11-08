"""Execute Jupyter notebook programmatically"""
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import sys
from pathlib import Path

# Paths
notebook_path = Path(__file__).parent / "01_data_exploration_v1.ipynb"
output_path = Path(__file__).parent / "01_data_exploration_v1_executed.ipynb"

print(f"Executing notebook: {notebook_path}")
print("This may take several minutes...")

try:
    # Read notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    # Execute notebook
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    ep.preprocess(nb, {'metadata': {'path': str(notebook_path.parent)}})

    # Save executed notebook
    with open(output_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)

    print(f"\n✓ Notebook executed successfully!")
    print(f"✓ Output saved to: {output_path}")

except Exception as e:
    print(f"\n✗ Error executing notebook: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
