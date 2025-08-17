"""
Token Formatters for Dynamic Formatting Library

This module contains all the token formatter classes that handle different
types of formatting (colors, text styles, etc.)
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List

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


class FormatterBase(ABC):
    """Base class for all token formatters"""
    
    # Stacking configuration
    self_stacking = True  # Can this formatter stack with itself? (e.g., @bold@italic)
    
    # TODO: Add cross_stacking property for future use
    # cross_stacking = True  # Can this formatter stack with other families?
    # 
    # Cross-stacking controls whether a formatter can be combined with other formatter types.
    # Examples where cross_stacking=False might be needed:
    # - Position formatters (^superscript) might not work with size formatters (%large)
    # - Some terminal effects might conflict with text decorations
    # - Background/foreground color families might have complex interactions
    # 
    # For now, we assume all formatters can cross-stack and will add this property
    # when we encounter real-world conflicts between formatter families.
    
    @abstractmethod
    def parse_token(self, token_value: str) -> Any:
        """Parse the token value (e.g., 'red', 'FF0000', 'bold')"""
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


class ColorFormatter(FormatterBase):
    """Handles color formatting tokens (#red, #FF0000, etc.)"""
    
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
    
    def parse_token(self, token_value: str) -> str:
        """Parse color token - return color name or hex"""
        token_value = token_value.lower()
        
        # Handle reset tokens
        if self.is_reset_token(token_value):
            return 'reset'
        
        # Return basic ANSI colors as names for direct mapping
        if token_value in self.ANSI_COLORS:
            return token_value
        
        # Check if it's a 6-digit hex color
        if len(token_value) == 6 and all(c in '0123456789abcdef' for c in token_value):
            return f"#{token_value}"
        
        # Look up matplotlib colors
        if token_value in NAMED_COLORS:
            # Map common colors to ANSI names for better terminal support
            color_mapping = {
                'red': 'red', 'green': 'green', 'blue': 'blue', 
                'yellow': 'yellow', 'cyan': 'cyan', 'magenta': 'magenta',
                'black': 'black', 'white': 'white', 'gray': 'bright_black'
            }
            if token_value in color_mapping:
                return color_mapping[token_value]
            else:
                # For other matplotlib colors, try to find closest ANSI match
                hex_color = NAMED_COLORS[token_value].lower()
                return self._hex_to_ansi_name(hex_color)
        
        # Default fallback
        return 'white'
    
    def apply_formatting(self, text: str, parsed_tokens: List[str], output_mode: str = 'console') -> str:
        """Apply color formatting"""
        if output_mode != 'console' or not parsed_tokens:
            return text  # Strip colors for file output
        
        # Since colors don't stack, we should only have one token
        # But handle the case where reset might be involved
        active_color = None
        for token in parsed_tokens:
            if token == 'reset':
                active_color = None
            else:
                active_color = token
        
        if active_color is None:
            return text  # No active color
        
        ansi_code = self._get_ansi_code(active_color)
        # Don't add reset here - let the caller handle resets to avoid conflicts
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
        
        return 'white'  # Default fallback
    
    def _hex_to_ansi_code(self, hex_color: str) -> int:
        """Convert hex color to ANSI code"""
        ansi_name = self._hex_to_ansi_name(hex_color)
        return self.ANSI_COLORS.get(ansi_name, 37)


class TextFormatter(FormatterBase):
    """Handles text formatting tokens (@bold, @italic, etc.)"""
    
    # Stacking configuration  
    self_stacking = True  # Text styles can stack: {@bold@italic} makes sense
    
    def get_family_name(self) -> str:
        return 'text'
    
    def parse_token(self, token_value: str) -> str:
        """Parse text formatting token"""
        token_lower = token_value.lower()
        
        # Handle reset tokens
        if self.is_reset_token(token_lower):
            return 'reset'
        
        return token_lower
    
    def apply_formatting(self, text: str, parsed_tokens: List[str], output_mode: str = 'console') -> str:
        """Apply text formatting with proper stacking"""
        if output_mode != 'console' or not parsed_tokens:
            return text
        
        format_codes = {
            'bold': '\033[1m',
            'italic': '\033[3m', 
            'underline': '\033[4m'
        }
        
        # Build list of active formats, handling resets
        active_formats = []
        for token in parsed_tokens:
            if token == 'reset':
                active_formats.clear()  # Reset clears all text formatting
            elif token in format_codes:
                if token not in active_formats:  # Avoid duplicates
                    active_formats.append(token)
        
        if not active_formats:
            return text
        
        # Apply all active formats - don't add reset here
        prefix = ''.join(format_codes[fmt] for fmt in active_formats)
        return f"{prefix}{text}"


# Token Registry
TOKEN_FORMATTERS = {
    '#': ColorFormatter(),
    '@': TextFormatter(),
}