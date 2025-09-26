"""
GUI panels package.

Contains all the step configuration panels.
"""

from .base import ProcessingStepPanel, SingleStepPanel, StackableStepPanel
from .extractor import ExtractorPanel
from .converter import ConverterPanel
from .filter import FilterPanel
from .template import TemplatePanel
from .all_in_one import AllInOnePanel

__all__ = [
    'ProcessingStepPanel',
    'SingleStepPanel', 
    'StackableStepPanel',
    'ExtractorPanel',
    'ConverterPanel',
    'FilterPanel',
    'TemplatePanel',
    'AllInOnePanel'
]