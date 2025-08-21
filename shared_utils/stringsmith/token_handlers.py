"""
Token handlers for StringSmith inline formatting.

This module provides a base class for token handlers and specific implementations
for different token types (color, emphasis, conditions). The base class handles
common reset logic, eliminating repetitive code.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Any

# Handle both relative and absolute imports
try:
    from .exceptions import StringSmithError
except ImportError:
    from exceptions import StringSmithError

from rich.color import Color


class BaseTokenHandler(ABC):
    """Base class for all token handlers with common reset logic."""
    
    def __init__(self, functions: Dict[str, Callable] = None):
        self.functions = functions or {}
        self.reset_code = '\033[0m'
    
    def is_reset_token(self, value: str) -> bool:
        """Check if this token value is a reset/default token."""
        return value.lower() in ('normal', 'default', 'reset')
    
    def handle_token(self, value: str, current_formatting: List[str], field_value: Any = None) -> List[str]:
        """
        Handle a token value, applying reset or formatting as appropriate.
        
        Args:
            value: The token value (e.g., "red", "bold", "normal")
            current_formatting: Current list of formatting codes
            field_value: The field value for function evaluation
            
        Returns:
            Updated list of formatting codes
        """
        if self.is_reset_token(value):
            return self.reset_formatting(current_formatting)
        else:
            return self.apply_formatting(value, current_formatting, field_value)
    
    @abstractmethod
    def reset_formatting(self, current_formatting: List[str]) -> List[str]:
        """Remove all formatting of this type from current_formatting."""
        pass
    
    @abstractmethod
    def apply_formatting(self, value: str, current_formatting: List[str], field_value: Any = None) -> List[str]:
        """Apply this formatting token to current_formatting."""
        pass
    
    @abstractmethod
    def get_token_prefix(self) -> str:
        """Get the prefix used for this token type (e.g., '#_', '@_')."""
        pass


class ColorTokenHandler(BaseTokenHandler):
    """Handles color formatting tokens (#red, #FF0000, etc.)."""
    
    def get_token_prefix(self) -> str:
        return '#_'
    
    def reset_formatting(self, current_formatting: List[str]) -> List[str]:
        """Remove all color formatting from current_formatting."""
        return [f for f in current_formatting if not f.startswith(self.get_token_prefix())]
    
    def apply_formatting(self, value: str, current_formatting: List[str], field_value: Any = None) -> List[str]:
        """Apply color formatting, replacing any existing color."""
        # Try custom function first
        if value in self.functions:
            try:
                function_result = self.functions[value](field_value)
                # Recursively handle the function result
                return self.handle_token(str(function_result), current_formatting, field_value)
            except Exception as e:
                raise StringSmithError(f"Error applying color function '{value}': {e}")
        
        # Remove existing colors and add new one
        reset_formatting = self.reset_formatting(current_formatting)
        reset_formatting.append(f"{self.get_token_prefix()}{value}")
        return reset_formatting
    
    def get_ansi_code(self, color_value: str) -> str:
        """Get ANSI color code for a color value using Rich."""
        try:
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
            # Return empty string if color couldn't be parsed
            return ""
        
        return ""


class EmphasisTokenHandler(BaseTokenHandler):
    """Handles text emphasis tokens (@bold, @italic, etc.)."""
    
    def __init__(self, functions: Dict[str, Callable] = None):
        super().__init__(functions)
        self.emphasis_codes = {
            'bold': '\033[1m',
            'italic': '\033[3m',
            'underline': '\033[4m',
            'strikethrough': '\033[9m',
            'dim': '\033[2m',
        }
    
    def get_token_prefix(self) -> str:
        return '@_'
    
    def reset_formatting(self, current_formatting: List[str]) -> List[str]:
        """Remove all emphasis formatting from current_formatting."""
        return [f for f in current_formatting if not f.startswith(self.get_token_prefix())]
    
    def apply_formatting(self, value: str, current_formatting: List[str], field_value: Any = None) -> List[str]:
        """Apply emphasis formatting, emphasis can stack."""
        # Try custom function first
        if value in self.functions:
            try:
                function_result = self.functions[value](field_value)
                if isinstance(function_result, str) and function_result.strip():
                    # If function returns text, it's a custom formatter - handle specially
                    return current_formatting + [f"{self.get_token_prefix()}{value}"]
                else:
                    # Function returned emphasis name, recursively handle
                    return self.handle_token(str(function_result), current_formatting, field_value)
            except Exception as e:
                raise StringSmithError(f"Error applying emphasis function '{value}': {e}")
        
        # Apply standard emphasis (can stack)
        if value in self.emphasis_codes:
            return current_formatting + [f"{self.get_token_prefix()}{value}"]
        else:
            # Unknown emphasis, ignore silently
            return current_formatting
    
    def get_ansi_code(self, emphasis_value: str) -> str:
        """Get ANSI code for emphasis value."""
        return self.emphasis_codes.get(emphasis_value, "")


class ConditionalTokenHandler(BaseTokenHandler):
    """Handles conditional tokens (?function_name)."""
    
    def get_token_prefix(self) -> str:
        return '?_'
    
    def reset_formatting(self, current_formatting: List[str]) -> List[str]:
        """Conditionals don't have reset formatting, return as-is."""
        return current_formatting
    
    def apply_formatting(self, value: str, current_formatting: List[str], field_value: Any = None) -> List[str]:
        """Evaluate conditional function and return appropriate marker."""
        if value not in self.functions:
            raise StringSmithError(f"Unknown conditional function: {value}")
        
        try:
            func = self.functions[value]
            # Try calling with field_value first, then without arguments
            try:
                result = func(field_value) if field_value is not None else func()
            except TypeError:
                result = func()
            
            # Add conditional result marker
            conditional_marker = f"{self.get_token_prefix()}{'show' if result else 'hide'}"
            return current_formatting + [conditional_marker]
            
        except Exception as e:
            raise StringSmithError(f"Error evaluating conditional '{value}': {e}")
    
    def should_show_text(self, formatting_list: List[str]) -> bool:
        """Check if text should be shown based on conditional markers."""
        for fmt in formatting_list:
            if fmt.startswith(self.get_token_prefix()):
                return fmt.endswith('show')
        return True  # Default to show if no conditional markers


# Token handler registry
def create_token_handlers(functions: Dict[str, Callable] = None) -> Dict[str, BaseTokenHandler]:
    """Create a dictionary of token handlers."""
    return {
        'color': ColorTokenHandler(functions),
        'emphasis': EmphasisTokenHandler(functions),
        'condition': ConditionalTokenHandler(functions)
    }