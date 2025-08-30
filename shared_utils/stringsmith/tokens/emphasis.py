"""Text emphasis token handler for StringSmith."""

from typing import Dict, Callable, List
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
        >>> handler.get_replacement_text('bold')      # '\033[1m'
        >>> handler.get_replacement_text('italic')    # '\033[3m' 
        >>> handler.get_replacement_text('normal')    # Reset codes
    """

    RESET_ANSI = '\033[22;23;24;29m'
    
    def __init__(self, token: str, escape_char: str, tokens: List[str], functions: Dict[str, Callable] = None):
        super().__init__(token, escape_char, tokens, functions)
        self.emphasis_codes = {
            'bold': '\033[1m',
            'italic': '\033[3m',
            'underline': '\033[4m',
            'strikethrough': '\033[9m',
            'dim': '\033[2m',
        }
    
    def get_replacement_text(self, token_value: str, field_value: str = None) -> str:
        """
        Generate ANSI code for emphasis style.
        
        Args:
            emphasis_value (str): Emphasis style name.
            
        Returns:
            str: ANSI escape sequence for text emphasis.
            
        Raises:
            StringSmithError: If emphasis style is not recognized.
        """
        code = self.emphasis_codes.get(token_value, None)
        if code is None:
            raise StringSmithError(f"Unknown emphasis style '{token_value}'. Valid styles: bold, italic, underline, strikethrough, dim, or custom functions.")
        return code