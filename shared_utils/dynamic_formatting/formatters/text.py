"""
Text formatting implementation with configurable graceful degradation.

Handles text style formatting tokens (@bold, @italic, etc.) with function fallback
support. Supports ANSI text styles and dynamic style selection through function calls.

Enhanced with configurable graceful degradation modes for professional deployment.
"""

from typing import Any, List, Dict, Optional, Union
import re
from .base import FormatterBase, FormatterError


class TextFormatter(FormatterBase):
    """
    Handles text style formatting tokens (@bold, @italic, etc.) with function fallback
    and configurable graceful degradation
    
    Supports multiple text styles:
    - Basic styles: bold, italic, underline, strikethrough
    - Reset tokens: normal, default, reset
    - Function fallback: Any function that returns a valid style
    
    Graceful Degradation Modes:
    - STRICT: Invalid tokens raise FormatterError
    - GRACEFUL: Invalid tokens return 'invalid' (no formatting applied)
    - AUTO_CORRECT: Invalid tokens auto-correct to suggested alternatives
    
    Text style behavior:
    - Multiple styles can be combined (bold + italic)
    - Reset tokens clear all text formatting
    - File output mode strips all formatting codes
    """
    
    # ANSI text style code mappings
    ANSI_STYLES: Dict[str, int] = {
        'bold': 1,
        'dim': 2,
        'italic': 3,
        'underline': 4,
        'blink': 5,
        'reverse': 7,
        'strikethrough': 9,
        'normal': 0  # Reset
    }
    
    def get_family_name(self) -> str:
        return 'text'
    
    def _get_valid_tokens(self) -> List[str]:
        """Get list of valid text style tokens for error messages"""
        tokens = list(self.ANSI_STYLES.keys())
        tokens.extend(['reset', 'default'])
        if self.function_registry:
            tokens.append(f"functions: {', '.join(sorted(self.function_registry.keys()))}")
        return tokens
    
    def parse_token(self, token_value: str, field_value: Optional[Any] = None) -> str:
        """
        Parse text style token with function fallback and configurable graceful degradation
        
        Parsing order:
        1. Check for reset tokens (normal, default, reset)
        2. Try direct ANSI style lookup
        3. Try function fallback
        4. Handle failure based on validation mode
        """
        token_value = token_value.lower().strip()
        
        # Handle reset tokens
        if self.is_reset_token(token_value):
            return 'reset'
        
        # Try direct ANSI style lookup
        if token_value in self.ANSI_STYLES:
            return token_value
        
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
                f"Invalid text style token: '{token_value}'",
                token=token_value
            )
    
    def apply_formatting(self, text: str, parsed_tokens: List[Union[str, int, bool]], output_mode: str = 'console') -> str:
        """
        Apply text style formatting to text
        
        Args:
            text: Text to format
            parsed_tokens: List of parsed text style tokens
            output_mode: 'console' for ANSI codes, 'file' for plain text
            
        Returns:
            Formatted text with ANSI style codes (console) or plain text (file)
        """
        if output_mode == 'file':
            return text  # No style formatting for file output
        
        if not parsed_tokens:
            return text
        
        # Collect all valid style tokens
        valid_styles = []
        has_reset = False
        
        for token in parsed_tokens:
            if isinstance(token, str):
                if token == 'reset':
                    has_reset = True
                elif token != 'invalid' and token in self.ANSI_STYLES:
                    valid_styles.append(token)
        
        # Handle reset
        if has_reset:
            return f"\033[0m{text}"
        
        if not valid_styles:
            return text
        
        # Build ANSI escape sequence for combined styles
        style_codes = [str(self.ANSI_STYLES[style]) for style in valid_styles]
        if style_codes:
            return f"\033[{';'.join(style_codes)}m{text}\033[0m"
        
        return text
    
    def strip_formatting(self, formatted_text: str) -> str:
        """Remove ANSI text style codes from text"""
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', formatted_text)