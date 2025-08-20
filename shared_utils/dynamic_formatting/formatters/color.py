"""
Color formatting implementation with configurable graceful degradation.

Handles color formatting tokens (#red, #FF0000, etc.) with function fallback
support. Supports ANSI colors, hex colors, named colors, and dynamic color
selection through function calls.

Enhanced with configurable graceful degradation modes for professional deployment.
"""

from typing import Any, List, Dict, Optional, Union
import re
from .base import FormatterBase, FormatterError

try:
    import matplotlib.colors as mcolors
    NAMED_COLORS: Dict[str, str] = mcolors.CSS4_COLORS
except ImportError:
    # Fallback basic colors if matplotlib not available
    NAMED_COLORS = {
        'red': '#FF0000', 'green': '#00FF00', 'blue': '#0000FF',
        'yellow': '#FFFF00', 'cyan': '#00FFFF', 'magenta': '#FF00FF',
        'black': '#000000', 'white': '#FFFFFF', 'gray': '#808080'
    }


class ColorFormatter(FormatterBase):
    """
    Handles color formatting tokens (#red, #FF0000, etc.) with function fallback
    and configurable graceful degradation
    
    Supports multiple color formats:
    - ANSI color names: red, blue, green, etc.
    - Hex colors: FF0000, 0000FF, etc. (with or without #)
    - Named colors: Any color name from matplotlib's CSS4_COLORS
    - Function fallback: Any function that returns a valid color
    
    Graceful Degradation Modes:
    - STRICT: Invalid tokens raise FormatterError
    - GRACEFUL: Invalid tokens return 'invalid' (no formatting applied)
    - AUTO_CORRECT: Invalid tokens auto-correct to suggested alternatives
    
    Color behavior:
    - Later colors override earlier colors naturally via ANSI codes
    - Reset tokens clear all color formatting
    - File output mode strips all color codes
    """
    
    # ANSI color code mappings
    ANSI_COLORS: Dict[str, int] = {
        'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
        'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37,
        'bright_black': 90, 'bright_red': 91, 'bright_green': 92,
        'bright_yellow': 93, 'bright_blue': 94, 'bright_magenta': 95,
        'bright_cyan': 96, 'bright_white': 97
    }
    
    def get_family_name(self) -> str:
        return 'color'
    
    def _get_valid_tokens(self) -> List[str]:
        """Get list of valid color tokens for error messages"""
        tokens = list(self.ANSI_COLORS.keys())
        tokens.extend(['reset', 'normal', 'default'])
        tokens.extend(['hex colors (6 digits)', 'matplotlib color names'])
        if self.function_registry:
            tokens.append(f"functions: {', '.join(sorted(self.function_registry.keys()))}")
        return tokens
    
    def parse_token(self, token_value: str, field_value: Optional[Any] = None) -> str:
        """
        Parse color token with function fallback and configurable graceful degradation
        
        Parsing order:
        1. Check for reset tokens (normal, default, reset)
        2. Try direct ANSI color lookup
        3. Try hex color parsing
        4. Try named color lookup
        5. Try function fallback
        6. Handle failure based on validation mode
        """
        token_value = token_value.lower().strip()
        
        # Handle reset tokens
        if self.is_reset_token(token_value):
            return 'reset'
        
        # Try direct ANSI color lookup
        if token_value in self.ANSI_COLORS:
            return token_value
        
        # Try hex color parsing (with or without #)
        hex_match = re.match(r'^#?([0-9a-f]{6})$', token_value)
        if hex_match:
            return hex_match.group(1).upper()  # Return hex without #
        
        # Try named color lookup
        if token_value in NAMED_COLORS:
            # Convert named color to hex
            hex_color = NAMED_COLORS[token_value].lstrip('#')
            return hex_color.upper()
        
        # Try function fallback
        function_result = self._try_function_fallback(token_value, field_value)
        if function_result is not None:
            # Recursively parse the function result
            return self.parse_token(function_result, field_value)
        
        # Handle failure based on validation mode
        if self._is_graceful_mode():
            return 'invalid'  # Special marker for no formatting
        else:
            self._raise_formatter_error(
                f"Invalid color token: '{token_value}'",
                token=token_value
            )
    
    def apply_formatting(self, text: str, parsed_tokens: List[Union[str, int, bool]], output_mode: str = 'console') -> str:
        """
        Apply color formatting to text
        
        Args:
            text: Text to format
            parsed_tokens: List of parsed color tokens
            output_mode: 'console' for ANSI codes, 'file' for plain text
            
        Returns:
            Formatted text with ANSI color codes (console) or plain text (file)
        """
        if output_mode == 'file':
            return text  # No color formatting for file output
        
        if not parsed_tokens:
            return text
        
        # Get the last valid color token (later colors override earlier ones)
        final_color = None
        for token in parsed_tokens:
            if isinstance(token, str) and token != 'invalid':
                final_color = token
        
        if not final_color:
            return text
        
        # Handle reset
        if final_color == 'reset':
            return f"\033[0m{text}"
        
        # Apply ANSI color
        if final_color in self.ANSI_COLORS:
            color_code = self.ANSI_COLORS[final_color]
            return f"\033[{color_code}m{text}\033[0m"
        
        # Apply hex color (convert to ANSI 256-color if possible)
        if re.match(r'^[0-9A-F]{6}$', final_color):
            return f"\033[38;2;{int(final_color[:2], 16)};{int(final_color[2:4], 16)};{int(final_color[4:6], 16)}m{text}\033[0m"
        
        # Fallback to no formatting
        return text
    
    def strip_formatting(self, formatted_text: str) -> str:
        """Remove ANSI color codes from text"""
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', formatted_text)
