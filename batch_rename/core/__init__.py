"""
Core package for batch rename functionality.

Provides extractors, converters, templates, filters, and processing logic.
"""

# Make key classes available at package level
from .processor import BatchRenameProcessor
from .config import RenameConfig, RenameResult
from .templates import get_template, is_template_function
from .converters import get_converter, is_converter_function

__all__ = [
    'BatchRenameProcessor',
    'RenameConfig', 
    'RenameResult',
    'get_template',
    'is_template_function',
    'get_converter', 
    'is_converter_function'
]