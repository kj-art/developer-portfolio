"""Text emphasis token handler for StringSmith."""

from typing import Dict, Callable
from .base import BaseTokenHandler
from ..exceptions import StringSmithError

class EmphasisTokenHandler(BaseTokenHandler):
    """
    Handles text emphasis tokens (@bold, @italic, @underline, etc.).
    
    Supported emphasis styles:
        - bold: Bold text
        - italic: Italic text  
        - underline: Underlined text
        - strikethrough: Strikethrough text
        - dim: Dimmed text
    
    Examples:
        >>> handler = EmphasisTokenHandler('@', {})
        >>> handler.get_ansi_code('bold')      # '\033[1m'
        >>> handler.get_ansi_code('italic')    # '\033[3m' 
        >>> handler.get_ansi_code('normal')    # Reset codes
    """

    RESET_ANSI = '\033[22;23;24;29m'
    
    def __init__(self, token: str, functions: Dict[str, Callable] = None):
        super().__init__(token, functions)
        self.emphasis_codes = {
            'bold': '\033[1m',
            'italic': '\033[3m',
            'underline': '\033[4m',
            'strikethrough': '\033[9m',
            'dim': '\033[2m',
        }
    
    def get_ansi_code(self, emphasis_value: str) -> str:
        """
        Generate ANSI code for emphasis style.
        
        Args:
            emphasis_value (str): Emphasis style name.
            
        Returns:
            str: ANSI escape sequence for text emphasis.
            
        Raises:
            StringSmithError: If emphasis style is not recognized.
        """
        code = self.emphasis_codes.get(emphasis_value, None)
        if code is None:
            raise StringSmithError(f"Unknown emphasis style '{emphasis_value}'. Valid styles: bold, italic, underline, strikethrough, dim, or custom functions.")
        return code