"""
Color formatter for ANSI colors and hex colors.
"""

import re
from typing import Any, Dict, List, Optional
from .base import BaseFormatter, FormatterError, FunctionExecutionError


class ColorFormatter(BaseFormatter):
    """Formatter for color tokens (#red, #ff0000, etc.)"""
    
    # ANSI color codes
    ANSI_COLORS = {
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'bright_black': '\033[90m',
        'bright_red': '\033[91m',
        'bright_green': '\033[92m',
        'bright_yellow': '\033[93m',
        'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m',
        'bright_cyan': '\033[96m',
        'bright_white': '\033[97m',
    }
    
    RESET_CODE = '\033[0m'
    
    def __init__(self):
        super().__init__()
        self.hex_pattern = re.compile(r'^[0-9a-fA-F]{6}$')
    
    def parse_token(self, token: str, field_value: Any) -> Dict[str, Any]:
        """
        Parse a color token
        
        Args:
            token: Color token (e.g., 'red', 'ff0000', or function name)
            field_value: Field value for function calls
            
        Returns:
            Dictionary with color information
        """
        # Check if it's a function call
        if token in self.function_registry:
            try:
                func = self.function_registry[token]
                result = func(field_value)
                if isinstance(result, str):
                    return self.parse_token(result, field_value)  # Recursive parse
                else:
                    raise FormatterError(f"Color function '{token}' must return a string")
            except Exception as e:
                raise FunctionExecutionError(
                    f"Color function '{token}' failed: {e}",
                    function_name=token,
                    original_error=e
                )
        
        # Check if it's a hex color
        if self.hex_pattern.match(token):
            return {
                'type': 'hex',
                'value': token,
                'ansi': self._hex_to_ansi(token)
            }
        
        # Check if it's an ANSI color name
        if token.lower() in self.ANSI_COLORS:
            return {
                'type': 'ansi',
                'value': token.lower(),
                'ansi': self.ANSI_COLORS[token.lower()]
            }
        
        # If we're in strict mode, this is an error
        if self.config and self.config.is_strict_mode():
            raise FormatterError(f"Unknown color: '{token}'")
        
        # In graceful mode, just return a no-op
        return {
            'type': 'unknown',
            'value': token,
            'ansi': ''
        }
    
    def apply_formatting(self, text: str, parsed_tokens: List[Dict[str, Any]], output_mode: str) -> str:
        """
        Apply color formatting to text
        
        Args:
            text: Text to colorize
            parsed_tokens: List of parsed color tokens
            output_mode: 'console' or 'file'
            
        Returns:
            Formatted text with color codes (if console mode)
        """
        if output_mode == 'file' or not parsed_tokens:
            return text
        
        # Use the last color token (later ones override earlier ones)
        color_token = parsed_tokens[-1]
        ansi_code = color_token.get('ansi', '')
        
        if ansi_code:
            return f"{ansi_code}{text}{self.RESET_CODE}"
        else:
            return text
    
    def _hex_to_ansi(self, hex_color: str) -> str:
        """
        Convert hex color to ANSI escape sequence
        
        Args:
            hex_color: 6-character hex color (without #)
            
        Returns:
            ANSI escape sequence
        """
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f'\033[38;2;{r};{g};{b}m'
        except ValueError:
            return ''