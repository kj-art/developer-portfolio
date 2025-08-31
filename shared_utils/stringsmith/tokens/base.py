"""
Base token handler for StringSmith formatting tokens.

Provides abstract interface and common functionality for all token handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Callable, Any, Iterator, Tuple, List
import inspect, re
from collections import defaultdict

from ..core import TemplateSection, SectionParts
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
    _RESET_TOKENS = ('normal', 'default', 'reset')

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'RESET_ANSI'):
            raise TypeError(f"{cls.__name__} must define RESET_ANSI class attribute")

    def __init__(self, token: str, escape_char: str, functions: Dict[str, Callable] = None):
        if functions:
            for f in functions.keys():
                if self._is_reset_token(f):
                    raise StringSmithError("Illegal custom function name '{f}'. Reserved token keywords are not allowed for use as function names.")
            self.functions = functions
        else:
            self.functions = {}
        
        self.functions = functions or {}
        self._token = token
        self._escape_char = escape_char
        self._escape_len = len(escape_char)

    def find_token(self, text: str, token: str = None) -> Iterator[Tuple[int, int, str]]:
        """
        Find unescaped {token ...} sequences in text.
        Yields (start_index, end_index, token_content)
        Only matches if the text immediately after { matches `token`.
        """
        # Match anything inside braces (candidate tokens)
        pattern = re.compile(r'\{(.*?)\}')
        token = token or self._token

        def is_unescaped(pos: int) -> bool:
            count = 0
            i = pos - self._escape_len
            while i >= 0 and text[i:i+self._escape_len] == self._escape_char:
                count += 1
                i -= self._escape_len
            return count % 2 == 0

        for m in pattern.finditer(text):
            start, end = m.start(), m.end()
            content = m.group(1)
            # Only consider it if unescaped and starts with the token
            if is_unescaped(start) and is_unescaped(end - 1) and content.startswith(token):
                yield start, end, content[len(token):]


    def _call_function(self, token_value, field_value):
        """Call custom function with appropriate parameter handling."""
        if token_value not in self.functions:
            raise StringSmithError(f"Function '{token_value}' not found in function registry")
        
        func = self.functions[token_value]
        sig = inspect.signature(func)

        if len(sig.parameters) == 0:
            return func()
        return func(field_value)

    def _is_reset_token(self, value: str) -> bool:
        """Check if token value is a reset token ('normal', 'default', 'reset')."""
        return value.lower() in self._RESET_TOKENS
    
    def has_inline_formatting(self, parts: SectionParts) -> bool:
        """Check if any inline formatting tokens exist for this handler."""
        for part_name, part_text in parts.iter_fields():
            for _ in self.find_token(part_text):
                return True
        return False
    
    def apply_sectional_formatting(self, section: TemplateSection, field_value: Any = None) -> TemplateSection:
        """Apply formatting to entire section (prefix, field, suffix)."""
        
        section = section.copy()
        section_formatting = section.section_formatting.get(self._token)

        if section_formatting:
            for f in range(len(section_formatting) - 1, -1, -1):
                if self._apply_sectional_formatting(section_formatting[f], field_value, section.parts):
                    section_formatting.pop(f)

        return section
   
    def _apply_sectional_formatting(self, token_value: str, field_value: Any, parts: SectionParts) -> bool:
        """Apply single sectional formatting token to text parts."""

        if token_value in self.functions:
            if field_value is None:  # Baking phase - defer to runtime
                return False
            token_value = str(self._call_function(token_value, field_value))
        
        replacement_text = self.RESET_ANSI if self._is_reset_token(token_value) else self.get_replacement_text(token_value, field_value)
        for k, v in parts.iter_fields():
            parts[k] = f'{replacement_text}{v}'
        return True
    
    def apply_inline_formatting(self, parts: SectionParts, field_value: Any = None) -> bool:
        """Apply formatting to specific position within text segment."""

        is_bake = field_value == None
        static_bank = {}

        for k, part in parts.iter_fields():
            dynamic = set()
            static = defaultdict(str)
            for start, end, token_value in self.find_token(part):
                if token_value in self.functions:    
                    dynamic.add(token_value)
                    continue

                if self._is_reset_token(token_value):
                    static[token_value] = self.RESET_ANSI
                else:
                    if token_value not in static_bank:
                        replacement_text = self.get_replacement_text(token_value, field_value)
                        if not replacement_text:
                            raise StringSmithError(f"Error applying function '{token_value}'")
                    static_bank[token_value] = static[token_value] = replacement_text
                    
            if not is_bake:
                parts[k] = self._replace_dynamic_tokens(parts[k], dynamic, field_value)
            parts[k] = self._replace_static_tokens(parts[k], static)
        return True

    def _replace_dynamic_tokens(self, part: str, tokens: set[str], field_value: Any) -> str:
        """
        Replace dynamic tokens with function results using string splitting approach.
        
        Dynamic tokens require field values to resolve, so they're processed during
        format() rather than baking. Each token is processed separately to handle
        multiple occurrences correctly.
        
        Args:
            part: Text containing dynamic tokens to replace
            tokens: Set of dynamic token names to process
            field_value: Runtime field value passed to token functions
            
        Returns:
            Text with dynamic tokens replaced by function results
        """
        for token in tokens:
            parts_list = part.split(self._get_token_bracket(token))
            ansi_codes = [self.get_replacement_text(str(self._call_function(token, field_value))) for _ in range(len(parts_list) - 1)]
            #print('|'.join(ansi_codes).encode('unicode_escape').decode())
            result = parts_list[0]
            for i, replacement_text in enumerate(ansi_codes):
                result += replacement_text + parts_list[i + 1]
            part = result
            
        return part

    def _replace_static_tokens(self, part: str, tokens: Dict[str, str]) -> str:
        """
        Replace static tokens with pre-computed replacement text.
        
        Static tokens (colors, emphasis styles) are resolved during baking phase
        since they don't depend on runtime field values. Uses simple string
        replacement for efficiency.
        
        Args:
            part: Text containing static tokens to replace  
            tokens: Mapping of token names to replacement ANSI codes
            
        Returns:
            Text with static tokens replaced by ANSI codes
        """
        for token, replacement_text in tokens.items():
            token = self._get_token_bracket(token)
            part = replacement_text.join(part.split(token))
        return part

    def _get_token_bracket(self, token_value: str):
        return f'{{{self._token}{token_value}}}'
    
    @abstractmethod
    def get_replacement_text(self, token_value: str, field_value: str = None) -> str:
        """Generate ANSI code for token value. Must be implemented by subclasses."""
        pass