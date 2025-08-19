"""
Conditional formatting implementation with enhanced error context and graceful degradation.

Handles conditional formatting tokens (?function_name) that control
whether sections or inline content should be shown or hidden based
on function results.
"""

from typing import Any, List, Optional
from .base import FormatterBase, FormatterError, FunctionExecutionError


class ConditionalFormatter(FormatterBase):
    """
    Handles conditional formatting tokens (?function_name) with enhanced error context
    and graceful degradation
    
    Conditionals work differently from color/text formatters:
    - They always require a function (no built-in conditionals)
    - Functions should return boolean-ish values
    - Results control visibility, not formatting
    - Used at both section level and inline level
    - Invalid functions gracefully degrade to 'hide' (safer default)
    
    Usage patterns:
    - Section level: {{?has_items;Found ;count; items}}
    - Inline level: {{Message{?is_urgent} - URGENT: ;text}}
    """
    
    def get_family_name(self) -> str:
        return 'conditional'
    
    def _get_valid_tokens(self) -> List[str]:
        """Get list of valid conditional tokens for error messages"""
        if self.function_registry:
            return [f"functions: {', '.join(sorted(self.function_registry.keys()))}"]
        else:
            return ["No conditional functions registered"]
    
    def parse_token(self, token_value: str, field_value: Optional[Any] = None) -> str:
        """
        Parse conditional token with graceful degradation
        
        Unlike color/text formatters, conditionals don't have built-in tokens.
        Every conditional token must map to a function that returns a boolean.
        
        Args:
            token_value: Function name for conditional logic
            field_value: Field value to pass to function
            
        Returns:
            'show' if function returns truthy, 'hide' if falsy or function missing/failed
            
        Note:
            Missing or failing functions return 'hide' instead of raising errors,
            allowing validation to warn but formatting to continue safely.
        """
        original_token = token_value
        
        # For conditionals, we always try function execution
        if not self.function_registry or original_token not in self.function_registry:
            # Graceful degradation: missing function defaults to 'hide' (safer)
            return 'hide'
        
        try:
            func = self.function_registry[original_token]
            
            # Try calling with field_value first, then without arguments
            try:
                if field_value is not None:
                    result = func(field_value)
                else:
                    result = func()
            except TypeError:
                # Function might not accept field_value parameter
                try:
                    result = func()
                except Exception:
                    # Function signature issues - gracefully degrade to hide
                    return 'hide'
            
            # For conditionals, we expect boolean-ish results, not strings
            # Convert the result to 'show' or 'hide' based on truthiness
            return 'show' if result else 'hide'
            
        except Exception:
            # Any function execution error - gracefully degrade to hide
            return 'hide'
    
    def apply_formatting(self, text: str, parsed_tokens: List[str], output_mode: str = 'console') -> str:
        """
        Apply conditional logic - show/hide text
        
        Note: This method shouldn't be called directly for conditionals.
        Conditional logic is handled during parsing by checking should_show_text().
        This is here for interface completeness.
        
        Args:
            text: Text to potentially show/hide
            parsed_tokens: List of conditional results ('show'/'hide')
            output_mode: Output mode (not used for conditionals)
            
        Returns:
            Original text (conditionals don't modify text, just control visibility)
        """
        return text
    
    def should_show_text(self, parsed_tokens: List[str]) -> bool:
        """
        Determine if text should be shown based on conditional tokens
        
        This is the main method used by the formatting system to determine
        if a conditional section or inline text should be visible.
        
        Args:
            parsed_tokens: List of conditional results from parse_token()
            
        Returns:
            False if any token says 'hide', True otherwise
        """
        # If any token says 'hide', hide the text
        # If all tokens say 'show' (or list is empty), show the text
        for token in parsed_tokens:
            if token == 'hide':
                return False
        return True