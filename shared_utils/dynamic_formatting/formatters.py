"""
Enhanced token formatters with function fallback support.

This module contains all the token formatter classes that handle different
types of formatting (colors, text styles, etc.) with proper error handling
and function fallback capabilities.
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Callable, Optional

try:
    import matplotlib.colors as mcolors
    NAMED_COLORS = mcolors.CSS4_COLORS
except ImportError:
    # Fallback basic colors if matplotlib not available
    NAMED_COLORS = {
        'red': '#FF0000', 'green': '#00FF00', 'blue': '#0000FF',
        'yellow': '#FFFF00', 'cyan': '#00FFFF', 'magenta': '#FF00FF',
        'black': '#000000', 'white': '#FFFFFF', 'gray': '#808080'
    }


class FormatterError(Exception):
    """Base exception for formatter errors"""
    pass


class FunctionExecutionError(FormatterError):
    """Raised when a function fallback fails"""
    pass


class FormatterBase(ABC):
    """Base class for all token formatters"""
    
    # Stacking configuration
    self_stacking = True  # Can this formatter stack with itself? (e.g., @bold@italic)
    
    def __init__(self):
        self.function_registry = {}  # Will be set by DynamicFormatter
    
    def set_function_registry(self, functions: Dict[str, Callable]):
        """Set available functions for fallback execution"""
        self.function_registry = functions
    
    @abstractmethod
    def parse_token(self, token_value: str, field_value: Any = None) -> Any:
        """Parse the token value with optional function fallback"""
        pass
    
    @abstractmethod
    def apply_formatting(self, text: str, parsed_tokens: List[Any], output_mode: str = 'console') -> str:
        """Apply formatting to text using a list of parsed tokens from this family"""
        pass
    
    @abstractmethod
    def get_family_name(self) -> str:
        """Return the family name for this formatter (e.g., 'color', 'text')"""
        pass
    
    def is_reset_token(self, token_value: str) -> bool:
        """Check if this token value is a reset/default token"""
        return token_value.lower() in ['normal', 'default', 'reset']
    
    def strip_formatting(self, formatted_text: str) -> str:
        """Remove formatting codes (default: return as-is)"""
        return formatted_text
    
    def _try_function_fallback(self, token_value: str, field_value: Any = None) -> Optional[str]:
        """
        Try to execute token_value as a function name
        
        Returns:
            str: Function result if successful
            None: If function doesn't exist or fails
            
        Raises:
            FunctionExecutionError: If function exists but fails
        """
        if not self.function_registry or token_value not in self.function_registry:
            return None
        
        try:
            func = self.function_registry[token_value]
            
            # Try calling with field_value first, then without arguments
            try:
                if field_value is not None:
                    result = func(field_value)
                else:
                    result = func()
            except TypeError:
                # Function might not accept field_value parameter
                result = func()
            
            if not isinstance(result, str):
                raise FunctionExecutionError(
                    f"Function '{token_value}' must return a string, got {type(result).__name__}: {result}"
                )
            
            return result
            
        except Exception as e:
            raise FunctionExecutionError(f"Function '{token_value}' failed: {e}")


class ColorFormatter(FormatterBase):
    """Handles color formatting tokens (#red, #FF0000, etc.) with function fallback"""
    
    # Stacking configuration
    self_stacking = False  # Colors don't stack: {#red#blue} should error
    
    # ANSI color code mappings
    ANSI_COLORS = {
        'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
        'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37,
        'bright_black': 90, 'bright_red': 91, 'bright_green': 92,
        'bright_yellow': 93, 'bright_blue': 94, 'bright_magenta': 95,
        'bright_cyan': 96, 'bright_white': 97
    }
    
    def get_family_name(self) -> str:
        return 'color'
    
    def parse_token(self, token_value: str, field_value: Any = None) -> str:
        """Parse color token with function fallback and proper error handling"""
        original_token = token_value
        token_value = token_value.lower()
        
        # Handle reset tokens
        if self.is_reset_token(token_value):
            return 'reset'
        
        # Try direct ANSI color lookup
        if token_value in self.ANSI_COLORS:
            return token_value
        
        # Try hex color
        if len(token_value) == 6 and all(c in '0123456789abcdef' for c in token_value):
            return f"#{token_value}"
        
        # Try named colors from matplotlib
        if token_value in NAMED_COLORS:
            return self._map_named_color_to_ansi(token_value)
        
        # Function fallback - use original case for function names
        try:
            function_result = self._try_function_fallback(original_token, field_value)
            if function_result is not None:
                # Recursively parse the function result as a color
                return self.parse_token(function_result, field_value)
        except FunctionExecutionError as e:
            # Re-raise function errors - they should not fail silently
            raise e
        
        # If we get here, the token is invalid
        raise FormatterError(f"Invalid color token: '{original_token}'. "
                           f"Expected: ANSI color name, hex color (6 digits), "
                           f"matplotlib color name, or valid function name.")
    
    def _map_named_color_to_ansi(self, color_name: str) -> str:
        """Map matplotlib color name to closest ANSI color"""
        # Direct mapping for common colors
        color_mapping = {
            'red': 'red', 'green': 'green', 'blue': 'blue', 
            'yellow': 'yellow', 'cyan': 'cyan', 'magenta': 'magenta',
            'black': 'black', 'white': 'white', 'gray': 'bright_black',
            'grey': 'bright_black'
        }
        
        if color_name in color_mapping:
            return color_mapping[color_name]
        
        # For other colors, convert through hex
        hex_color = NAMED_COLORS[color_name].lower()
        return self._hex_to_ansi_name(hex_color)
    
    def apply_formatting(self, text: str, parsed_tokens: List[str], output_mode: str = 'console') -> str:
        """Apply color formatting"""
        if output_mode != 'console' or not parsed_tokens:
            return text  # Strip colors for file output
        
        # Since colors don't stack, we should only have one active token
        active_color = None
        for token in parsed_tokens:
            if token == 'reset':
                active_color = None
            else:
                active_color = token
        
        if active_color is None:
            return text  # No active color
        
        ansi_code = self._get_ansi_code(active_color)
        return f"\033[{ansi_code}m{text}"
    
    def _get_ansi_code(self, color: str) -> int:
        """Convert color to ANSI code"""
        color_lower = color.lower().lstrip('#')
        
        # Direct ANSI color name mapping
        if color_lower in self.ANSI_COLORS:
            return self.ANSI_COLORS[color_lower]
        
        # Hex color mapping to closest ANSI
        return self._hex_to_ansi_code(color_lower)
    
    def _hex_to_ansi_name(self, hex_color: str) -> str:
        """Convert hex color to closest ANSI color name"""
        hex_color = hex_color.lstrip('#').lower()
        
        # Simple mapping of common hex values to ANSI names
        hex_to_ansi_name = {
            '000000': 'black', 'ff0000': 'red', '00ff00': 'green', 'ffff00': 'yellow',
            '0000ff': 'blue', 'ff00ff': 'magenta', '00ffff': 'cyan', 'ffffff': 'white',
            '008000': 'green',  # CSS 'green' 
            '800080': 'magenta', # CSS 'purple' -> magenta
            '808080': 'bright_black'  # CSS 'gray'
        }
        
        if hex_color in hex_to_ansi_name:
            return hex_to_ansi_name[hex_color]
        
        # Fallback to closest basic color (could be enhanced with color distance calculation)
        return 'white'
    
    def _hex_to_ansi_code(self, hex_color: str) -> int:
        """Convert hex color to ANSI code"""
        ansi_name = self._hex_to_ansi_name(hex_color)
        return self.ANSI_COLORS.get(ansi_name, 37)


class TextFormatter(FormatterBase):
    """Handles text formatting tokens (@bold, @italic, etc.) with function fallback"""
    
    # Stacking configuration  
    self_stacking = True  # Text styles can stack: {@bold@italic} makes sense
    
    # Valid text formatting styles
    VALID_STYLES = {
        'bold': '\033[1m',
        'italic': '\033[3m', 
        'underline': '\033[4m'
    }
    
    def get_family_name(self) -> str:
        return 'text'
    
    def parse_token(self, token_value: str, field_value: Any = None) -> str:
        """Parse text formatting token with function fallback and proper error handling"""
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
        except FunctionExecutionError as e:
            # Re-raise function errors - they should not fail silently
            raise e
        
        # If we get here, the token is invalid
        valid_styles_list = ', '.join(sorted(self.VALID_STYLES.keys()))
        raise FormatterError(f"Invalid text style token: '{original_token}'. "
                           f"Expected: {valid_styles_list}, reset/normal/default, "
                           f"or valid function name.")
    
    def apply_formatting(self, text: str, parsed_tokens: List[str], output_mode: str = 'console') -> str:
        """Apply text formatting with proper stacking"""
        if output_mode != 'console' or not parsed_tokens:
            return text
        
        # Build list of active formats, handling resets
        active_formats = []
        for token in parsed_tokens:
            if token == 'reset':
                active_formats.clear()  # Reset clears all text formatting
            elif token in self.VALID_STYLES:
                if token not in active_formats:  # Avoid duplicates
                    active_formats.append(token)
            # Note: Invalid tokens should have been caught during parsing
        
        if not active_formats:
            return text
        
        # Apply all active formats
        prefix = ''.join(self.VALID_STYLES[fmt] for fmt in active_formats)
        return f"{prefix}{text}"


# Token Registry - maps token characters to their formatter instances
TOKEN_FORMATTERS = {
    '#': ColorFormatter(),
    '@': TextFormatter(),
}