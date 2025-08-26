"""
Token handlers for StringSmith inline formatting.

This module provides a base class for token handlers and specific implementations
for different token types (color, emphasis, conditions). The base class handles
common reset logic, eliminating repetitive code.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Any, Optional
import inspect

# Handle both relative and absolute imports
try:
    from .exceptions import StringSmithError
    from .template_ast import TemplateSection, TemplatePart
except ImportError:
    from exceptions import StringSmithError
    from template_ast import TemplateSection, TemplatePart

from rich.color import Color


class BaseTokenHandler(ABC):
    """Base class for all token handlers with common reset logic."""
    
    def __init__(self, functions: Dict[str, Callable] = None):
        self.functions = functions or {}
        self._token = self._determine_token_prefix()
        self._token_prefix = f'{self._token}_'
        self._set_reset_ansi()
    
    @abstractmethod
    def _set_reset_ansi(self):
        pass

    def get_reset_ansi(self):
        return self._reset_ansi
    
    def _call_function(self, token_value, field_value):
        func = self.functions[token_value]
        sig = inspect.signature(func)
        if len(sig.parameters) == 0:
            return func()
        return func(field_value)

    def _determine_token_prefix(self) -> str:
        for token, handler_class in TOKEN_REGISTRY.items():
            if handler_class == type(self):
                return f"{token}"
        raise ValueError(f"No token assigned to {type(self).__name__}")
    
    def get_token_prefix(self) -> str:
        return self._token_prefix
    
    @classmethod
    def get_token_char(cls) -> str:
        """Get the token character assigned to this handler class."""
        for token, handler_class in TOKEN_REGISTRY.items():
            if handler_class == cls:
                return token
        raise ValueError(f"No token assigned to {cls.__name__}")

    def is_reset_token(self, value: str) -> bool:
        """Check if this token value is a reset/default token."""
        return value.lower() in ('normal', 'default', 'reset')
    
    def apply_sectional_formatting(self, section: TemplateSection, field_value: Any = None) -> TemplateSection:
        """Default: apply formatting at beginning of each part (prefix, field, suffix)."""
        
        section = section.copy()
        section_formatting = section.section_formatting[self._token]
        text = (section.prefix.content, section.field.content, section.suffix.content, False)
        for f in range(len(section_formatting) - 1, -1, -1):
            c_text = self._apply_sectional_formatting(section_formatting[f], field_value, text)
            if c_text is not None:
                text = c_text
                section_formatting.pop(f)

        section.prefix.content, section.field.content, section.suffix.content, *_ = text
        return section
   
    def _apply_sectional_formatting(self, token_value: str, field_value: Any, text: tuple[str, str, str]) -> Optional[tuple]:
        if token_value in self.functions: # the token's value is a call to one of the custom functions
            if field_value is None: # no field provided - this is a bake pass
                return None
            token_value = str(self._call_function(token_value, field_value))
        
        ansi_code = self._reset_ansi if self.is_reset_token(token_value) else self.get_ansi_code(token_value)
        return f'{ansi_code}{text[0]}', f'{ansi_code}{text[1]}', f'{ansi_code}{text[2]}'
    
    def apply_inline_formatting(self, text_segment: str, position: int, token_value: str, field_value: Any = None) -> tuple[str, bool]:
        """Default: apply formatting to text segment."""

        is_bake = field_value == None
        if token_value in self.functions:
            if is_bake:
                return text_segment, False
            token_value = str(self._call_function(token_value, field_value))
        
        ansi_code = self._reset_ansi if self.is_reset_token(token_value) else self.get_ansi_code(token_value)

        if ansi_code:
            return f"{text_segment[:position]}{ansi_code}{text_segment[position:]}", True
        
        raise StringSmithError(f"Error applying function '{token_value}'")
        #return text_segment
        
    def finalize(self, template_part: TemplatePart, field_value: Any) -> str:
        return template_part.content

    @abstractmethod
    def get_ansi_code(self, token_value: str) -> str:
        """Get the ANSI code for this token value."""
        pass
    
    
class ColorTokenHandler(BaseTokenHandler):
    """Handles color formatting tokens (#red, #FF0000, etc.)."""
    
    def _set_reset_ansi(self):
        self._reset_ansi = '\033[39m'

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
            pass
        
        raise StringSmithError(f"Unknown color '{color_value}'. Valid colors: named colors (red, green, blue), hex codes (FF0000), or custom functions.")


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

    def _set_reset_ansi(self) -> str:
        reset_bold = '22'
        reset_italic = '23'
        reset_underline = '24'
        reset_strikethrough = '29'
        self._reset_ansi = f'\033[{";".join([reset_bold, reset_italic, reset_underline, reset_strikethrough])}m'
    
    def reset_formatting(self, current_formatting: List[str]) -> List[str]:
        """Remove all emphasis formatting from current_formatting."""
        return [f for f in current_formatting if not f.startswith(self.get_token_prefix())]
    
    def apply_formatting(self, value: str, current_formatting: List[str], field_value: Any = None) -> List[str]:
        """Apply emphasis formatting, emphasis can stack."""
        # Try custom function first
        if value in self.functions:
            try:
                function_result = self._call_function(value, field_value)
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
        code = self.emphasis_codes.get(emphasis_value, None)
        if code is None:
            raise StringSmithError(f"Unknown emphasis style '{emphasis_value}'. Valid styles: bold, italic, underline, strikethrough, dim, or custom functions.")
        return code

class ConditionalTokenHandler(BaseTokenHandler):
    """Handles conditional tokens (?function_name)."""
    
    def _apply_sectional_formatting(self, token_value: str, field_value: Any, text: tuple[str, str, str]) -> Optional[tuple]:
        if token_value in self.functions: # the token's value is a call to one of the custom functions
            if field_value is None: # no field provided - this is a bake pass
                return None
            else:
                token_value = self._call_function(token_value, field_value)
        else:
            raise StringSmithError(f"Error applying function '{token_value}'")
        return text if token_value else ('', '', '')
    
    def apply_inline_formatting(self, text_segment: str, position: int, token_value: str, field_value: Any = None) -> tuple[str, bool]:
        """Default: apply formatting to text segment."""

        is_bake = field_value is None
        if is_bake:
            return text_segment, False
        if token_value not in self.functions:
            raise StringSmithError(f"Error applying function '{token_value}'")

        return f"{text_segment[:position]}\uE000{text_segment[position:]}", False        

    def _set_reset_ansi(self):
        self._reset_ansi = ''

    def get_ansi_code(self, token_value: str) -> str:
        pass #return '\uE000'
    
    def finalize(self, template_part: TemplatePart, field_value: Any) -> str:
        template_part = template_part.copy()
        pieces = template_part.content.split('\uE000')
        result = pieces.pop(0)
        inline_formatting = [item for item in template_part.inline_formatting if item.type == self._token]
        if len(pieces) != len(inline_formatting):
            raise StringSmithError(f"Error finalizing text_segment '{template_part.content}': Mismatch between formatting length and number of conditional ANSI markers")
        for i, v in enumerate(pieces):
            token_value = inline_formatting[i].value
            if self.is_reset_token(token_value):
                result += v
            elif token_value not in self.functions:
                raise StringSmithError(f"Error applying function '{token_value}'")
            else:
                result += v if self._call_function(token_value, field_value) else ''
        return result

# Token handler registry
def create_token_handlers(functions: Dict[str, Callable] = None) -> Dict[str, BaseTokenHandler]:
    """Create a dictionary of token handlers."""
    handlers = {}
    for token in TOKEN_REGISTRY:
        handlers[token] = TOKEN_REGISTRY[token](functions)
    return handlers

# Single source of truth for token assignments
TOKEN_REGISTRY = {
    '?': ConditionalTokenHandler,
    '#': ColorTokenHandler,
    '@': EmphasisTokenHandler,
}

SORTED_TOKENS = sorted(TOKEN_REGISTRY.keys(), key=len, reverse=True)