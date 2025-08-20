"""
Conditional formatter for handling ?function tokens.
"""

from typing import Any, Dict, List
from .base import BaseFormatter, FormatterError, FunctionExecutionError


class ConditionalFormatter(BaseFormatter):
    """Formatter for conditional tokens (?function_name)"""
    
    def parse_token(self, token: str, field_value: Any) -> Dict[str, Any]:
        """
        Parse a conditional token
        
        Args:
            token: Function name for conditional
            field_value: Field value to pass to function
            
        Returns:
            Dictionary with conditional information
        """
        if not token:
            if self.config and self.config.is_strict_mode():
                raise FormatterError("Empty conditional function name")
            return {'type': 'unknown', 'result': False}
        
        # Check if function exists
        if token not in self.function_registry:
            if self.config and self.config.is_strict_mode():
                available = list(self.function_registry.keys())
                raise FormatterError(
                    f"Conditional function '{token}' not found. "
                    f"Available functions: {available}"
                )
            # In graceful mode, assume false
            return {'type': 'missing', 'function_name': token, 'result': False}
        
        # Execute the function
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
            # In graceful mode, assume false
            return {
                'type': 'error',
                'function_name': token,
                'result': False,
                'error': str(e)
            }
    
    def apply_formatting(self, text: str, parsed_tokens: List[Dict[str, Any]], output_mode: str) -> str:
        """
        Apply conditional formatting (really just returns text or empty based on condition)
        
        Args:
            text: Text to conditionally show
            parsed_tokens: List of parsed conditional tokens
            output_mode: Output mode (not used for conditionals)
            
        Returns:
            Text if all conditions are true, empty string otherwise
        """
        # All conditional tokens must be true for text to be shown
        for token in parsed_tokens:
            if not token.get('result', False):
                return ""  # Hide the text if any condition is false
        
        return text  # Show the text if all conditions are true