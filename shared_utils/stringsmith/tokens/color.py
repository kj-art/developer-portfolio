from rich.color import Color
from .base import BaseTokenHandler
from ..exceptions import StringSmithError

class ColorTokenHandler(BaseTokenHandler):
    """Handles color formatting tokens (#red, #FF0000, etc.)."""
    
    def _set_reset_ansi(self):
        self._reset_ansi = '\033[39m'

    def get_ansi_code(self, color_value: str) -> str:
        """Get ANSI color code for a color value using Rich."""
        try:
            # Check if it looks like hex and add # prefix if needed
            if (len(color_value) == 6 and 
                all(c.lower() in '0123456789abcdef' for c in color_value)):
                color_value = f"#{color_value}"
            color = Color.parse(color_value)
            ansi_codes = color.get_ansi_codes()
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