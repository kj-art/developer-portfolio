"""Conditional token handler for StringSmith."""

from typing import Any, Optional
from .base import BaseTokenHandler
from ..exceptions import StringSmithError
from ..core import SectionParts
import inspect
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

    RESET_ANSI = ''  # Conditional tokens don't produce ANSI escape codes
    
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
    

    def apply_inline_formatting(self, parts: SectionParts, field_value: Any = None) -> bool:
        """
        Apply conditional logic to inline tokens, showing/hiding text segments.
        
        Conditional tokens evaluate user functions at runtime to determine visibility.
        Text following conditional tokens appears only if the function returns truthy.
        During baking phase (field_value=None), validation is deferred to runtime.
        
        Args:
            parts: Section parts containing potential conditional tokens
            field_value: Runtime field value for function evaluation, None during baking
            
        Returns:
            bool: Whether the field value should be appended (True unless hidden by conditional)
        """
        if field_value is None: # Baking phase
            return False
        
        def apply_inline_formatting_to_part(p:str) -> bool:
            found = []

            for start, end, token_value in self.find_token(parts[p]):
                if token_value in self.functions:
                    obj = {
                        'show': self._call_function(token_value, field_value),
                        'start': start,
                        'end': end
                    }
                    found.append(obj)
                elif self._is_reset_token(token_value):
                    obj = {
                        'show': True,
                        'start': start,
                        'end': end
                    }
                    found.append(obj)
                else:
                    raise StringSmithError(f"Error applying function '{token_value}'")
            
            if not len(found):
                return True
            last_index = len(found) - 1
            show_field = found[last_index]['show']
            result = parts[p][found[last_index]['end']:] if show_field else ''
            for i in range(last_index - 1, -1, -1):
                if found[i]['show']:
                    result = parts[p][found[i]['end']:found[i+1]['start']] + result
            parts[p] = parts[p][:found[0]['start']] + result

            return show_field

        for p in ['prefix', 'suffix']:
            apply_inline_formatting_to_part(p)
        return apply_inline_formatting_to_part('field')
    
    def get_replacement_text(self, token_value: str, field_value: str = None) -> str:
        return ''