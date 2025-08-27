"""
Base token handler for StringSmith formatting tokens.

Provides abstract interface and common functionality for all token handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Callable, Any, Optional
import inspect

from ..core import TemplateSection, TemplatePart
from ..exceptions import StringSmithError

class BaseTokenHandler(ABC):
    """
    Abstract base class for all StringSmith token handlers.
    
    Token handlers process specific formatting tokens (colors, emphasis, conditionals)
    and apply appropriate formatting operations. Each token type has a corresponding
    handler that inherits from this base class.
    
    Args:
        token (str): Token prefix this handler processes ('#', '@', '?', etc.).
        functions (Dict[str, Callable], optional): Custom user functions available
                                                 as token values.
    
    Thread Safety:
        Handlers are thread-safe after initialization for concurrent formatting.
    """
    
    def __init__(self, token: str, functions: Dict[str, Callable] = None):
        self.functions = functions or {}
        self._token = token
        self._set_reset_ansi()
        
    @abstractmethod
    def _set_reset_ansi(self):
        """Set appropriate ANSI reset code for this token type."""
        pass

    def get_reset_ansi(self):
        """Get ANSI reset code for this token type."""
        return self._reset_ansi
    
    def _call_function(self, token_value, field_value):
        """Call custom function with appropriate parameter handling."""
        if token_value not in self.functions:
            raise StringSmithError(f"Function '{token_value}' not found in function registry")
        
        func = self.functions[token_value]
        sig = inspect.signature(func)

        if len(sig.parameters) == 0:
            return func()
        return func(field_value)

    def is_reset_token(self, value: str) -> bool:
        """Check if token value is a reset token ('normal', 'default', 'reset')."""
        return value.lower() in ('normal', 'default', 'reset')
    
    def apply_sectional_formatting(self, section: TemplateSection, field_value: Any = None) -> TemplateSection:
        """Apply formatting to entire section (prefix, field, suffix)."""
        
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
        """Apply single sectional formatting token to text parts."""

        if token_value in self.functions:
            if field_value is None:  # Baking phase - defer to runtime
                return None
            token_value = str(self._call_function(token_value, field_value))
        
        ansi_code = self._reset_ansi if self.is_reset_token(token_value) else self.get_ansi_code(token_value)
        return f'{ansi_code}{text[0]}', f'{ansi_code}{text[1]}', f'{ansi_code}{text[2]}'
    
    def apply_inline_formatting(self, text_segment: str, position: int, token_value: str, field_value: Any = None) -> tuple[str, bool]:
        """Apply formatting to specific position within text segment."""

        is_bake = field_value == None

        if token_value in self.functions:
            if is_bake:
                return text_segment, False
            token_value = str(self._call_function(token_value, field_value))
        
        ansi_code = self._reset_ansi if self.is_reset_token(token_value) else self.get_ansi_code(token_value)

        if ansi_code:
            return f"{text_segment[:position]}{ansi_code}{text_segment[position:]}", True
        
        raise StringSmithError(f"Error applying function '{token_value}'")
        
    def finalize(self, template_part: TemplatePart, field_value: Any) -> str:
        """Finalize template part after all formatting applied."""
        return template_part.content

    @abstractmethod
    def get_ansi_code(self, token_value: str) -> str:
        """Generate ANSI code for token value. Must be implemented by subclasses."""
        pass