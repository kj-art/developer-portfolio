"""
Text style formatter for bold, italic, underline, etc.
"""

from typing import Any, Dict, List
from .base import BaseFormatter, FormatterError, FunctionExecutionError


class TextFormatter(BaseFormatter):
    """Formatter for text style tokens (@bold, @italic, etc.)"""
    
    # ANSI text formatting codes
    TEXT_STYLES = {
        'bold': '\033[1m',
        'dim': '\033[2m',
        'italic': '\033[3m',
        'underline': '\033[4m',
        'blink': '\033[5m',
        'reverse': '\033[7m',
        'strikethrough': '\033[9m',
        'normal': '\033[22m',
        'reset': '\033[0m',
    }
    
    RESET_CODE = '\033[0m'
    
    def parse_token(self, token: str, field_value: Any) -> Dict[str, Any]:
        """
        Parse a text style token
        
        Args:
            token: Style token (e.g., 'bold', 'italic', or function name)
            field_value: Field value for function calls
            
        Returns:
            Dictionary with style information
        """
        # Check if it's a function call
        if token in self.function_registry:
            try:
                func = self.function_registry[token]
                result = func(field_value)
                if isinstance(result, str):
                    return self.parse_token(result, field_value)  # Recursive parse
                else:
                    raise FormatterError(f"Text style function '{token}' must return a string")
            except Exception as e:
                raise FunctionExecutionError(
                    f"Text style function '{token}' failed: {e}",
                    function_name=token,
                    original_error=e
                )
        
        # Check if it's a known style
        if token.lower() in self.TEXT_STYLES:
            return {
                'type': 'style',
                'value': token.lower(),
                'ansi': self.TEXT_STYLES[token.lower()]
            }
        
        # If we're in strict mode, this is an error
        if self.config and self.config.is_strict_mode():
            raise FormatterError(f"Unknown text style: '{token}'")
        
        # In graceful mode, just return a no-op
        return {
            'type': 'unknown',
            'value': token,
            'ansi': ''
        }
    
    def apply_formatting(self, text: str, parsed_tokens: List[Dict[str, Any]], output_mode: str) -> str:
        """
        Apply text style formatting
        
        Args:
            text: Text to style
            parsed_tokens: List of parsed style tokens
            output_mode: 'console' or 'file'
            
        Returns:
            Formatted text with style codes (if console mode)
        """
        if output_mode == 'file' or not parsed_tokens:
            return text
        
        # Apply all style tokens
        prefix_codes = []
        has_reset = False
        
        for token in parsed_tokens:
            ansi_code = token.get('ansi', '')
            if ansi_code:
                if token.get('value') == 'reset':
                    has_reset = True
                    prefix_codes = [ansi_code]  # Reset clears all previous styles
                else:
                    prefix_codes.append(ansi_code)
        
        if prefix_codes:
            prefix = ''.join(prefix_codes)
            suffix = self.RESET_CODE if not has_reset else ''
            return f"{prefix}{text}{suffix}"
        else:
            return text