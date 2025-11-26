import sys
from pathlib import Path

# Add the parent directory to sys.path to make imports work correctly
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
