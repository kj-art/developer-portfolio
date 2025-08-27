"""Color token handler for StringSmith color formatting."""

from rich.color import Color
from .base import BaseTokenHandler
from ..exceptions import StringSmithError

class ColorTokenHandler(BaseTokenHandler):
    """
    Handles color formatting tokens (#red, #blue, #FF0000, etc.).
    
    Supports:
        - Named colors: 'red', 'green', 'blue'
        - Hex codes: 'FF0000', '#FF0000' 
        - Custom functions: User-defined functions that return color names
        - Reset tokens: 'normal', 'default', 'reset'
    
    Uses Rich library for comprehensive color parsing when available.
    
    Examples:
        >>> handler = ColorTokenHandler('#', {})
        >>> handler.get_ansi_code('red')  # '\033[31m'
        >>> handler.get_ansi_code('FF0000')  # RGB ANSI code
        >>> handler.get_ansi_code('normal')  # '\033[39m' (reset)
    """
    
    def _set_reset_ansi(self):
        """Set ANSI reset code for color formatting."""
        self._reset_ansi = '\033[39m'

    def get_ansi_code(self, color_value: str) -> str:
        """
        Generate ANSI color code for the specified color value.
        
        Args:
            color_value (str): Color specification (name, hex code, etc.).
        
        Returns:
            str: ANSI escape sequence for foreground color.
        
        Raises:
            StringSmithError: If color cannot be parsed or is invalid.
        """
        try:
            # Auto-detect hex codes and add # prefix if needed
            if (len(color_value) == 6 and 
                all(c.lower() in '0123456789abcdef' for c in color_value)):
                color_value = f"#{color_value}"

            # Use Rich library for color parsing
            color = Color.parse(color_value)
            ansi_codes = color.get_ansi_codes()

            # Handle different return formats from Rich
            if isinstance(ansi_codes, tuple) and len(ansi_codes) > 0:
                fg_code = ansi_codes[0]
                if fg_code and not fg_code.startswith('\033['):
                    return f'\033[{fg_code}m'
                return fg_code if fg_code else ""
            elif isinstance(ansi_codes, str):
                if ansi_codes and not ansi_codes.startswith('\033['):
                    return f'\033[{ansi_codes}m'
                return ansi_codes
        except Exception:
            pass
        
        raise StringSmithError(f"Unknown color '{color_value}'. Valid colors: named colors (red, green, blue), hex codes (FF0000), or custom functions.")