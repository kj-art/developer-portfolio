"""Color token handler for StringSmith color formatting."""

from rich.color import Color
from .base import BaseTokenHandler
from ..exceptions import StringSmithError
from .registry import register_token_handler
@register_token_handler('#', '\033[39m')
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
        >>> handler.get_replacement_text('red')  # '\033[31m'
        >>> handler.get_replacement_text('FF0000')  # RGB ANSI code
        >>> handler.get_replacement_text('normal')  # '\033[39m' (reset)
    """

    def _hex_to_ansi(self, hex_color: str) -> str:
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"\033[38;2;{r};{g};{b}m"


    def get_replacement_text(self, color_value: str) -> str:
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
            color_value = str(color_value)
            
            # Auto-detect hex codes
            if ((len(color_value) == 6 and 
                all(c.lower() in '0123456789abcdef' for c in color_value))) or color_value.startswith('#'):
                return self._hex_to_ansi(color_value)

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