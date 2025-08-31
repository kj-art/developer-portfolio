"""Conditional token handler for StringSmith."""

from typing import Any
from .base import BaseTokenHandler
from ..exceptions import StringSmithError
from ..core import SectionParts
from .registry import register_token_handler
@register_token_handler('?')
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
    
    def _apply_sectional_formatting(self, token_value: str, parts: SectionParts, field_value: Any = None, kwargs: dict = None) -> bool:
        """Apply conditional logic to section visibility."""
        if token_value in self.functions: # the token's value is a call to one of the custom functions
            if field_value is None: # no field provided - this is a bake pass
                return False
            else:
                token_value = self._call_function(token_value, field_value, kwargs)
        else:
            raise StringSmithError(f"Error applying function '{token_value}'")
        if not token_value:
            for k, v in parts.iter_fields():
                parts[k] = ''
        return True
    
    def bake_inline_formatting(self, parts: SectionParts) -> bool:
        """
        Validate conditional function names during baking phase.
        
        Scans for conditional tokens and validates that referenced functions exist
        in the function registry. Since conditional logic depends on runtime field
        values, no tokens are processed during baking - all are deferred to format.
        
        Args:
            parts: Section parts to scan for conditional tokens
            
        Returns:
            bool: True if any conditional tokens found (format phase needed),
                False if no conditional tokens exist in this section
                
        Raises:
            StringSmithError: If conditional token references unknown function
        """
        for p, part in parts.iter_fields():
            for start, end, token_value in self.find_token(part):
                if token_value in self.functions or self._is_reset_token(token_value):
                    return True
                else:
                    raise StringSmithError(f"Error applying function '{token_value}'")
        return False

    def apply_inline_formatting(self, parts: SectionParts, field_value: Any = None, kwargs: dict = None) -> bool:
        """
        Apply conditional logic to inline tokens, controlling text segment visibility.
        
        Evaluates conditional functions with runtime data to determine which text
        segments should appear. Text following conditional tokens is shown only
        if the function returns a truthy value.
        
        Args:
            parts: Section parts containing conditional tokens
            field_value: Runtime field value passed to conditional functions
            kwargs: All format() arguments for multi-parameter function support
            
        Returns:
            bool: False if any conditional determined the field should be hidden,
                True if field should be included in output
                
        Processing:
            Conditional tokens are processed right-to-left, with the rightmost
            token determining final field visibility.
        """
        def apply_inline_formatting_to_part(p:str) -> bool:
            found = []

            for start, end, token_value in self.find_token(parts[p]):
                if token_value in self.functions:
                    obj = {
                        'show': self._call_function(token_value, field_value, kwargs),
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
    
    def get_replacement_text(self, token_value: str) -> str:
        return ''