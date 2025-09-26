"""
Core package for batch rename functionality.

Provides extractors, converters, templates, filters, and processing logic.
"""

# Make key classes available at package level
from .processor import BatchRenameProcessor
from .config import RenameConfig, RenameResult
from .processing_context import ProcessingContext
from .step_factory import StepFactory
from .steps.base import StepType

__all__ = [
    'BatchRenameProcessor',
    'RenameConfig', 
    'RenameResult',
    'ProcessingContext',
    'StepFactory',
    'StepType'
]