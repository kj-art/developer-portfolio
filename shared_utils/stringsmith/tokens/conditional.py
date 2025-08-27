"""Conditional token handler for StringSmith."""

from typing import Any, Optional
from .base import BaseTokenHandler
from ..exceptions import StringSmithError
from ..core import TemplatePart

class ConditionalTokenHandler(BaseTokenHandler):
    """
    Handles conditional tokens (?function_name) that show/hide sections.
    
    Conditional tokens call user-defined functions with field values and show
    the section only if the function returns a truthy value.
    
    Examples:
        >>> def is_error(level):
        ...     return level.lower() == 'error'
        >>> handler = ConditionalTokenHandler('?', {'is_error': is_error})
        >>> # Template: {{?is_error;[ERROR] ;level}}
        >>> # Shows "[ERROR] " prefix only when level is 'error'
    """
    
    def _apply_sectional_formatting(self, token_value: str, field_value: Any, text: tuple[str, str, str]) -> Optional[tuple]:
        """Apply conditional logic to section visibility."""
        if token_value in self.functions: # the token's value is a call to one of the custom functions
            if field_value is None: # no field provided - this is a bake pass
                return None
            else:
                token_value = self._call_function(token_value, field_value)
        else:
            raise StringSmithError(f"Error applying function '{token_value}'")
        return text if token_value else ('', '', '')
    
    def apply_inline_formatting(self, text_segment: str, position: int, token_value: str, field_value: Any = None) -> tuple[str, bool]:
        """Mark position for conditional processing during finalization."""

        is_bake = field_value is None  # Baking phase
        if is_bake:
            return text_segment, False
        if token_value not in self.functions:
            raise StringSmithError(f"Error applying function '{token_value}'")

        # Insert marker for finalization processing
        return f"{text_segment[:position]}\uE000{text_segment[position:]}", False        

    def _set_reset_ansi(self):
        """Conditional tokens don't use ANSI codes."""
        self._reset_ansi = ''

    def get_ansi_code(self, token_value: str) -> str:
        """Conditional tokens don't generate ANSI codes."""
        return ''
    
    def finalize(self, template_part: TemplatePart, field_value: Any) -> str:
        """Process conditional markers and show/hide content accordingly."""
        template_part = template_part.copy()
        pieces = template_part.content.split('\uE000')
        result = pieces.pop(0)
        inline_formatting = [item for item in template_part.inline_formatting if item.type == self._token]
        if len(pieces) != len(inline_formatting):
            raise StringSmithError(f"Error finalizing text_segment '{template_part.content}': Mismatch between formatting length and number of conditional ANSI markers")
        for i, v in enumerate(pieces):
            token_value = inline_formatting[i].value
            if self.is_reset_token(token_value):
                result += v
            elif token_value not in self.functions:
                raise StringSmithError(f"Error applying function '{token_value}'")
            else:
                # Show piece only if function returns truthy value
                result += v if self._call_function(token_value, field_value) else ''
        return result