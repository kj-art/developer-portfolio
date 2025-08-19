"""
Text style formatting implementation.

Handles text formatting tokens (@bold, @italic, etc.) with function fallback
support. Supports multiple text styles that can be combined naturally.
"""

from typing import Any, List, Dict, Optional
from .base import FormatterBase, FormatterError


class TextFormatter(FormatterBase):
    """
    Handles text formatting tokens (@bold, @italic, etc.) with function fallback
    
    Supported styles:
    - bold: Makes text bold
    - italic: Makes text italic  
    - underline: Underlines text
    - reset/normal/default: Clears all text formatting
    
    Text style behavior:
    - Multiple styles combine naturally (bold + italic = bold italic)
    - Reset tokens clear all text formatting
    - File output mode strips all formatting codes
    - Function fallback allows dynamic style selection
    """
    
    # Valid text formatting styles
    VALID_STYLES: Dict[str, str] = {
        'bold': '\033[1m',
        'italic': '\033[3m', 
        'underline': '\033[4m'
    }
    
    def get_family_name(self) -> str:
        return 'text'
    
    def parse_token(self, token_value: str, field_value: Optional[Any] = None) -> str:
        """
        Parse text formatting token with function fallback and proper error handling
        
        Parsing order:
        1. Check for reset tokens (normal, default, reset)
        2. Try direct style lookup
        3. Try function fallback
        4. Raise error if nothing works
        
        Args:
            token_value: Text style token to parse
            field_value: Field value for function fallback
            
        Returns:
            Parsed style token (style name or 'reset')
            
        Raises:
            FormatterError: If token is invalid and no function fallback
        """
        original_token = token_value
        token_lower = token_value.lower()
        
        # Handle reset tokens
        if self.is_reset_token(token_lower):
            return 'reset'
        
        # Try direct style lookup
        if token_lower in self.VALID_STYLES:
            return token_lower
        
        # Function fallback - use original case for function names
        try:
            function_result = self._try_function_fallback(original_token, field_value)
            if function_result is not None:
                # Recursively parse the function result as a text style
                return self.parse_token(function_result, field_value)
        except Exception as e:
            # Re-raise function errors - they should not fail silently
            raise e
        
        # If we get here, the token is invalid
        valid_styles_list = ', '.join(sorted(self.VALID_STYLES.keys()))
        raise FormatterError(f"Invalid text style token: '{original_token}'. "
                           f"Expected: {valid_styles_list}, reset/normal/default, "
                           f"or valid function name.")
    
    def apply_formatting(self, text: str, parsed_tokens: List[str], output_mode: str = 'console') -> str:
        """
        Apply text formatting - multiple styles combine naturally
        
        Args:
            text: Text to format
            parsed_tokens: List of parsed style tokens
            output_mode: 'console' for ANSI codes, 'file' for plain text
            
        Returns:
            Formatted text with style codes (console) or plain text (file)
        """
        if output_mode != 'console' or not parsed_tokens:
            return text
        
        # Apply all style codes in sequence - they combine naturally
        style_codes: List[str] = []
        for token in parsed_tokens:
            if token == 'reset':
                style_codes = []  # Reset clears all previous styles
            elif token in self.VALID_STYLES:
                style_codes.append(self.VALID_STYLES[token])
        
        if not style_codes:
            return text
        
        prefix = ''.join(style_codes)
        return f"{prefix}{text}"