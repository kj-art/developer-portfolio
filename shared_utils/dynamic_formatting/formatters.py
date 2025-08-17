"""
Token Formatters for Dynamic Formatting Library

This module contains all the token formatter classes that handle different
types of formatting (colors, text styles, etc.)
"""

import re
from abc import ABC, abstractmethod
from typing import Any

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
    
    @abstractmethod
    def parse_token(self, token_value: str) -> Any:
        """Parse the token value (e.g., 'red', 'FF0000', 'bold')"""
        pass
    
    @abstractmethod
    def apply_formatting(self, text: str, parsed_token: Any, output_mode: str = 'console') -> str:
        """Apply formatting to text, return formatted string"""
        pass
    
    def strip_formatting(self, formatted_text: str) -> str:
        """Remove formatting codes (default: return as-is)"""
        return formatted_text


class ColorFormatter(FormatterBase):
    """Handles color formatting tokens (#red, #FF0000, etc.)"""
    
    # ANSI color code mappings
    ANSI_COLORS = {
        'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
        'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37,
        'bright_black': 90, 'bright_red': 91, 'bright_green': 92,
        'bright_yellow': 93, 'bright_blue': 94, 'bright_magenta': 95,
        'bright_cyan': 96, 'bright_white': 97
    }
    
    def parse_token(self, token_value: str) -> str:
        """Parse color token - return color name or hex"""
        token_value = token_value.lower()
        
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
                'black': 'black', 'white': 'white'
            }
            if token_value in color_mapping:
                return color_mapping[token_value]
            else:
                return NAMED_COLORS[token_value]
        
        # Default fallback
        return 'white'
    
    def apply_formatting(self, text: str, parsed_token: str, output_mode: str = 'console') -> str:
        """Apply color formatting"""
        if output_mode != 'console':
            return text  # Strip colors for file output
        
        ansi_code = self._get_ansi_code(parsed_token)
        return f"\033[{ansi_code}m{text}\033[0m"
    
    def _get_ansi_code(self, color: str) -> int:
        """Convert color to ANSI code"""
        color_lower = color.lower().lstrip('#')
        
        # Direct ANSI color name mapping
        if color_lower in self.ANSI_COLORS:
            return self.ANSI_COLORS[color_lower]
        
        # Hex color mapping to closest ANSI
        hex_to_ansi = {
            '000000': 30, 'ff0000': 31, '00ff00': 32, 'ffff00': 33,
            '0000ff': 34, 'ff00ff': 35, '00ffff': 36, 'ffffff': 37
        }
        
        if color_lower in hex_to_ansi:
            return hex_to_ansi[color_lower]
        
        return 37  # Default to white


class TextFormatter(FormatterBase):
    """Handles text formatting tokens (@bold, @italic, etc.) - Future implementation"""
    
    def parse_token(self, token_value: str) -> str:
        """Parse text formatting token"""
        return token_value.lower()
    
    def apply_formatting(self, text: str, parsed_token: str, output_mode: str = 'console') -> str:
        """Apply text formatting"""
        if output_mode != 'console':
            return text
        
        format_codes = {
            'bold': '\033[1m',
            'italic': '\033[3m', 
            'underline': '\033[4m'
        }
        
        if parsed_token in format_codes:
            return f"{format_codes[parsed_token]}{text}\033[0m"
        
        return text


# Token Registry
TOKEN_FORMATTERS = {
    '#': ColorFormatter(),
    '@': TextFormatter(),
}