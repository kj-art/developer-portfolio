"""
Pytest configuration for dynamic formatting tests.

This file helps pytest understand the package structure and sets up
proper import paths for testing.
"""

import sys
from pathlib import Path

# Add the project root to sys.path so imports work correctly
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Also add the shared_utils directory
shared_utils_path = Path(__file__).parent.parent
if str(shared_utils_path) not in sys.path:
    sys.path.insert(0, str(shared_utils_path))