#!/usr/bin/env python3
"""
Batch File Rename Tool - Main Entry Point

Professional batch file renaming with mixable extractors and converters.
"""

import sys
from pathlib import Path

# Add the parent directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from batch_rename.ui.cli import main

if __name__ == "__main__":
    main()