"""
Filter processing step implementation.

Handles file filtering to determine which files to process.
"""

from typing import Dict, Any, Callable

from .base import ProcessingStep, StepType, StepConfig
from ..processing_context import ProcessingContext
from ..validators import ValidationResult, validate_filter_function
from ..built_ins.filters import BUILTIN_FILTERS


class FilterStep(ProcessingStep):
    """Processing step for file filtering."""
    
    @property
    def step_type(self) -> StepType:
        return StepType.FILTER
    
    @property
    def is_stackable(self) -> bool:
        return True  # Multiple filters can be chained (all must pass)
    
    @property
    def builtin_functions(self) -> Dict[str, Callable]:
        return BUILTIN_FILTERS.copy()
    
    def get_help_text(self) -> str:
        """Return help text for filter step."""
        help_lines = [
            "FILTERS - Determine which files to process",
            "",
            "Built-in filters:"
        ]
        
        for name in self.builtin_functions.keys():
            help_lines.append(f"  {name}")
        
        help_lines.extend([
            "",
            "Custom filters:",
            "  Load from .py files with functions that take ProcessingContext",
            "  Must return bool (True = process file, False = skip)",
            "",
            "Examples:",
            "  --filter extension,.pdf,.doc",
            "  --filter size_range,min=1024,max=10485760",
            "  --filter my_filters.py,custom_check"
        ])
        
        return "\n".join(help_lines)
    
    def validate_custom_function(self, function: Callable) -> ValidationResult:
        """Validate custom filter function signature."""
        return validate_filter_function(function)
    
    def get_gui_hints(self) -> Dict[str, Any]:
        """Return GUI hints for filter panels."""
        return {
            'panel_title': "File Filtering",
            'supports_custom': True,
            'add_remove_buttons': True,  # Stackable
            'validation_style': 'expandable',
            'help_text': "Filter which files to process (all filters must pass)"
        }