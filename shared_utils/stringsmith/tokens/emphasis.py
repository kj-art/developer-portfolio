from typing import Dict, Callable
from .base import BaseTokenHandler
from ..exceptions import StringSmithError

class EmphasisTokenHandler(BaseTokenHandler):
    """Handles text emphasis tokens (@bold, @italic, etc.)."""
    
    def __init__(self, token: str, functions: Dict[str, Callable] = None):
        super().__init__(token, functions)
        self.emphasis_codes = {
            'bold': '\033[1m',
            'italic': '\033[3m',
            'underline': '\033[4m',
            'strikethrough': '\033[9m',
            'dim': '\033[2m',
        }

    def _set_reset_ansi(self) -> str:
        reset_bold = '22'
        reset_italic = '23'
        reset_underline = '24'
        reset_strikethrough = '29'
        self._reset_ansi = f'\033[{";".join([reset_bold, reset_italic, reset_underline, reset_strikethrough])}m'
    
    def get_ansi_code(self, emphasis_value: str) -> str:
        """Get ANSI code for emphasis value."""
        code = self.emphasis_codes.get(emphasis_value, None)
        if code is None:
            raise StringSmithError(f"Unknown emphasis style '{emphasis_value}'. Valid styles: bold, italic, underline, strikethrough, dim, or custom functions.")
        return code