"""
Core package for batch rename functionality.

Provides extractors, converters, filters, and processing logic.
"""

# Make key classes available at package level
from .processor import BatchRenameProcessor
from .config import RenameConfig, RenameResult

__all__ = [
    'BatchRenameProcessor',
    'RenameConfig', 
    'RenameResult'
]