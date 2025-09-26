"""
Converter processing step implementation.

Handles transformation of extracted data fields.
"""

from pathlib import Path
from typing import Dict, Any, Callable

from .base import ProcessingStep, StepType, StepConfig
from ..processing_context import ProcessingContext
from ..validators import ValidationResult, validate_converter_function
from ..built_ins.converters import BUILTIN_CONVERTERS
from ..function_loader import load_custom_function


class ConverterStep(ProcessingStep):
    """Processing step for data field transformation."""
    
    @property
    def step_type(self) -> StepType:
        return StepType.CONVERTER
    
    @property
    def is_stackable(self) -> bool:
        return True  # Multiple converters can be chained
    
    @property
    def builtin_functions(self) -> Dict[str, Callable]:
        return BUILTIN_CONVERTERS.copy()
    
    def get_help_text(self) -> str:
        """Return help text for converter step."""
        help_lines = [
            "CONVERTERS - Transform extracted data fields",
            "",
            "Built-in converters:"
        ]
        
        for name in self.builtin_functions.keys():
            help_lines.append(f"  {name}")
        
        help_lines.extend([
            "",
            "Custom converters:",
            "  Load from .py files with functions that take ProcessingContext",
            "  Must return Dict[str, Any] with transformed field data",
            "  Should preserve field structure (same keys in/out)",
            "",
            "Examples:",
            "  --converter pad_numbers,sequence,3",
            "  --converter case,dept,upper",
            "  --converter my_converters.py,custom_transform"
        ])
        
        return "\n".join(help_lines)
    
    def validate_custom_function(self, function: Callable) -> ValidationResult:
        """Validate custom converter function signature."""
        return validate_converter_function(function)
    
    def get_gui_hints(self) -> Dict[str, Any]:
        """Return GUI hints for converter panels."""
        return {
            'panel_title': "Data Transformation", 
            'supports_custom': True,
            'add_remove_buttons': True,  # Stackable
            'validation_style': 'expandable',
            'help_text': "Transform extracted data fields (can chain multiple)"
        }