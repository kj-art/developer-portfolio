"""
Conditional formatter for ?function conditionals.
"""

from typing import Any, Dict, List
from .base import BaseFormatter, FormatterError, FunctionExecutionError


class ConditionalFormatter(BaseFormatter):
    """Formatter for conditional tokens (?function)"""
    
    def parse_token(self, token: str, field_value: Any) -> Dict[str, Any]:
        """
        Parse a conditional token
        
        Args:
            token: Function name for conditional
            field_value: Field value to pass to function
            
        Returns:
            Dictionary with conditional result
        """
        # Check if function exists
        if token not in self.function_registry:
            if self.config and self.config.is_strict_mode():
                raise FormatterError(f"Conditional function not found: '{token}'")
            else:
                # In graceful mode, return False (hide section)
                return {
                    'type': 'missing_function',
                    'function_name': token,
                    'result': False
                }
        
        # Execute the conditional function
        try:
            func = self.function_registry[token]
            result = func(field_value)
            
            return {
                'type': 'conditional',
                'function_name': token,
                'result': bool(result)
            }
            
        except Exception as e:
            if self.config and self.config.is_strict_mode():
                raise FunctionExecutionError(
                    f"Conditional function '{token}' failed: {e}",
                    function_name=token,
                    original_error=e
                )
            else:
                # In graceful mode, return False (hide section)
                return {
                    'type': 'function_error',
                    'function_name': token,
                    'result': False,
                    'error': str(e)
                }
    
    def apply_formatting(self, text: str, parsed_tokens: List[Dict[str, Any]], output_mode: str) -> str:
        """
        Apply conditional formatting (show/hide section based on result)
        
        Args:
            text: Text to potentially show/hide
            parsed_tokens: List of parsed conditional tokens
            output_mode: Output mode ('console' or 'file')
            
        Returns:
            Text if condition is true, empty string if false
        """
        if not parsed_tokens:
            return text
        
        # Use the last conditional result (if multiple conditionals)
        conditional_token = parsed_tokens[-1]
        result = conditional_token.get('result', False)
        
        if result:
            return text
        else:
            return ""  # Hide the section