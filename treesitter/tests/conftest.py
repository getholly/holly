"""
Pytest configuration for the project.
"""

import sys
from pathlib import Path

# Add the src directory to sys.path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))
