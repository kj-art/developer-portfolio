"""
All-in-one processing step implementation.

Handles extraction, conversion, and formatting in a single function.
"""

from typing import Dict, Any, Callable

from .base import ProcessingStep, StepType, StepConfig
from ..processing_context import ProcessingContext
from ..validators import ValidationResult, validate_allinone_function
from ..built_ins.all_in_ones import BUILTIN_ALL_IN_ONE


class AllInOneStep(ProcessingStep):
    """Processing step for all-in-one extraction, conversion, and formatting."""
    
    @property
    def step_type(self) -> StepType:
        return StepType.ALLINONE
    
    @property
    def is_stackable(self) -> bool:
        return False  # Only one all-in-one function per pipeline
    
    @property
    def builtin_functions(self) -> Dict[str, Callable]:
        return BUILTIN_ALL_IN_ONE.copy()
    
    def get_help_text(self) -> str:
        """Return help text for all-in-one step."""
        help_lines = [
            "ALL-IN-ONE - Handle extraction, conversion, and formatting in one function",
            "",
            "Built-in all-in-one functions:"
        ]
        
        for name in self.builtin_functions.keys():
            help_lines.append(f"  {name}")
        
        help_lines.extend([
            "",
            "Custom all-in-one functions:",
            "  Load from .py files with functions that take ProcessingContext",
            "  Must return str (complete formatted filename without extension)",
            "  Handle extraction, conversion, and formatting internally",
            "",
            "Examples:",
            "  --extract-and-convert replace,old_text,new_text",
            "  --extract-and-convert my_functions.py,process_filename",
            "  --extract-and-convert advanced_renamer.py,smart_rename"
        ])
        
        return "\n".join(help_lines)
    
    def validate_custom_function(self, function: Callable) -> ValidationResult:
        """Validate custom all-in-one function signature."""
        return validate_allinone_function(function)
    
    def get_gui_hints(self) -> Dict[str, Any]:
        """Return GUI hints for all-in-one panels."""
        return {
            'panel_title': "All-in-One Processing",
            'supports_custom': True,
            'add_remove_buttons': False,  # Not stackable
            'validation_style': 'expandable',
            'help_text': "Single function that handles extraction, conversion, and formatting"
        }