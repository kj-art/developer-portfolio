"""
Template processing step implementation.

Handles final filename formatting from extracted/converted data.
"""

from typing import Dict, Any, Callable

from .base import ProcessingStep, StepType, StepConfig
from ..processing_context import ProcessingContext
from ..validators import ValidationResult, validate_template_function
from ..built_ins.templates import BUILTIN_TEMPLATES


class TemplateStep(ProcessingStep):
    """Processing step for final filename formatting."""
    
    @property
    def step_type(self) -> StepType:
        return StepType.TEMPLATE
    
    @property
    def is_stackable(self) -> bool:
        return False  # Only one template per pipeline
    
    @property
    def builtin_functions(self) -> Dict[str, Callable]:
        return BUILTIN_TEMPLATES.copy()
    
    def get_help_text(self) -> str:
        """Return help text for template step."""
        help_lines = [
            "TEMPLATES - Format final filename from extracted data",
            "",
            "Built-in templates:"
        ]
        
        for name in self.builtin_functions.keys():
            help_lines.append(f"  {name}")
        
        help_lines.extend([
            "",
            "Custom templates:",
            "  Load from .py files with functions that take ProcessingContext",
            "  Must return str (formatted filename without extension)",
            "",
            "Examples:",
            "  --template template,\"{dept}_{type}_{date}\"",
            "  --template stringsmith,\"{dept|upper}_{sequence:03d}\"",
            "  --template my_templates.py,custom_format"
        ])
        
        return "\n".join(help_lines)
    
    def validate_custom_function(self, function: Callable) -> ValidationResult:
        """Validate custom template function signature."""
        return validate_template_function(function)
    
    def get_gui_hints(self) -> Dict[str, Any]:
        """Return GUI hints for template panels."""
        return {
            'panel_title': "Filename Formatting",
            'supports_custom': True,
            'add_remove_buttons': False,  # Not stackable
            'validation_style': 'expandable',
            'help_text': "Format final filename from extracted/converted data"
        }