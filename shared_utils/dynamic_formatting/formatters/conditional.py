"""
Conditional formatting implementation.

Handles conditional formatting tokens (?function_name) that control
whether sections or inline content should be shown or hidden based
on function results.
"""

from typing import Any, List, Optional
from .base import FormatterBase, FormatterError, FunctionExecutionError


class ConditionalFormatter(FormatterBase):
    """
    Handles conditional formatting tokens (?function_name)
    
    Conditionals work differently from color/text formatters:
    - They always require a function (no built-in conditionals)
    - Functions should return boolean-ish values
    - Results control visibility, not formatting
    - Used at both section level and inline level
    
    Usage patterns:
    - Section level: {{?has_items;Found ;count; items}}
    - Inline level: {{Message{?is_urgent} - URGENT: ;text}}
    """
    
    def get_family_name(self) -> str:
        return 'conditional'
    
    def parse_token(self, token_value: str, field_value: Optional[Any] = None) -> str:
        """
        Parse conditional token - always requires function fallback
        
        Unlike color/text formatters, conditionals don't have built-in tokens.
        Every conditional token must map to a function that returns a boolean.
        
        Args:
            token_value: Function name for conditional logic
            field_value: Field value to pass to function
            
        Returns:
            'show' if function returns truthy, 'hide' if falsy
            
        Raises:
            FormatterError: If function is not provided
            FunctionExecutionError: If function execution fails
        """
        original_token = token_value
        
        # For conditionals, we always try function execution
        if not self.function_registry or original_token not in self.function_registry:
            raise FormatterError(f"Conditional token '{original_token}' requires a valid function name.")
        
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
                result = func()
            
            # For conditionals, we expect boolean-ish results, not strings
            # Convert the result to 'show' or 'hide' based on truthiness
            return 'show' if result else 'hide'
            
        except Exception as e:
            raise FunctionExecutionError(f"Conditional function '{original_token}' failed: {e}")
    
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