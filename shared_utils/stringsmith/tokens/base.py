from abc import ABC, abstractmethod
from typing import Dict, Callable, Any, Optional
import inspect

from ..core import TemplateSection, TemplatePart
from ..exceptions import StringSmithError

class BaseTokenHandler(ABC):
    """Base class for all token handlers with common reset logic."""
    
    def __init__(self, token: str, functions: Dict[str, Callable] = None):
        self.functions = functions or {}
        self._token = token
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