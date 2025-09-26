"""
Extractor processing step implementation.

Handles data extraction from filenames and metadata.
"""

from pathlib import Path
from typing import Dict, Any, Callable

from .base import ProcessingStep, StepType, StepConfig
from ..processing_context import ProcessingContext
from ..validators import ValidationResult, validate_extractor_function
from ..built_ins.extractors import BUILTIN_EXTRACTORS
from ..function_loader import load_custom_function


class ExtractorStep(ProcessingStep):
    """Processing step for data extraction from filenames/metadata."""
    
    @property
    def step_type(self) -> StepType:
        return StepType.EXTRACTOR
    
    @property
    def is_stackable(self) -> bool:
        return False  # Only one extractor per pipeline
    
    @property
    def builtin_functions(self) -> Dict[str, Callable]:
        return BUILTIN_EXTRACTORS.copy()
    
    def get_help_text(self) -> str:
        """Return help text for extractor step."""
        help_lines = [
            "EXTRACTORS - Extract data from filenames and metadata",
            "",
            "Built-in extractors:"
        ]
        
        for name in self.builtin_functions.keys():
            help_lines.append(f"  {name}")
        
        help_lines.extend([
            "",
            "Custom extractors:",
            "  Load from .py files with functions that take ProcessingContext",
            "  Must return Dict[str, Any] with extracted field data",
            "",
            "Examples:",
            "  --extractor split,_,dept,type,date",
            "  --extractor regex,\"(?P<dept>\\w+)_(?P<num>\\d+)\"",
            "  --extractor my_extractors.py,custom_function"
        ])
        
        return "\n".join(help_lines)
    
    def validate_custom_function(self, function: Callable) -> ValidationResult:
        """Validate custom extractor function signature."""
        return validate_extractor_function(function)
    
    def get_gui_hints(self) -> Dict[str, Any]:
        """Return GUI hints for extractor panels."""
        return {
            'panel_title': "Data Extraction",
            'supports_custom': True,
            'add_remove_buttons': False,  # Not stackable
            'validation_style': 'expandable',
            'help_text': "Extract data from filenames and file metadata"
        }