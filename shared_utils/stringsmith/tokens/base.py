"""
Base token handler for StringSmith formatting tokens.

Provides abstract interface and common functionality for all token handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Callable, Any, Optional
import inspect

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

    def __init__(self, functions: Dict[str, Callable] = None):
        self._static_cache = {}
        if functions:
            for f in functions.keys():
                if self._is_reset_token(f):
                    raise StringSmithError("Illegal custom function name '{f}'. Reserved token keywords are not allowed for use as function names.")
            self.functions = functions
        else:
            self.functions = {}
        
        self.functions = functions or {}

    def _call_function(self, function_name: str, field_value: Any, kwargs: Dict):
        """
        Call custom function with intelligent parameter matching.
        
        Matches function parameter names to format() arguments when possible,
        enabling multi-field functions. Falls back to single field_value for
        backward compatibility when no parameter names match.
        
        Parameter Matching Logic:
            1. If function has no parameters: call with no arguments
            2. If all function parameters match kwargs keys: call with matched values
            3. Otherwise: call with section's field_value (backward compatibility)
        
        Args:
            function_name: Name of function to call from function registry
            field_value: Value of current section's field (fallback argument)
            kwargs: All field values from format() call for parameter matching
            
        Returns:
            Function result for use in formatting operations
            
        Examples:
            # Multi-parameter function
            def is_profitable(revenue, costs): 
                return float(revenue) > float(costs)
            # Called as: is_profitable(revenue=150, costs=120)
            
            # Single-parameter function (legacy behavior)  
            def priority_color(level): 
                return 'red' if int(level) > 5 else 'green'
            # Called as: priority_color(field_value)
            
            # No-parameter function
            def random_color():
                return choice(['red', 'blue', 'green'])
            # Called as: random_color()
            
        Raises:
            StringSmithError: If function not found in registry
        """
        if function_name not in self.functions:
            raise StringSmithError(f"Function '{function_name}' not found in function registry")

        func = self.functions[function_name]
        sig = inspect.signature(func)
        params = sig.parameters

        # Case 1: function has no parameters → call with nothing
        if not params:
            return func()

        # Case 2: all parameters match keys in kwargs → call with those
        if all(name in kwargs for name in params):
            return func(**{name: kwargs[name] for name in params})

        # Case 3: fall back to old behavior → pass field_value
        return func(field_value)


    def _is_reset_token(self, value: str) -> bool:
        """Check if token value is a reset token ('normal', 'default', 'reset')."""
        return value.lower() in self._RESET_TOKENS
    
    def apply_section_formatting(self, section: TemplateSection, field_value: Any, kwargs: Dict = None) -> bool:
        """Apply formatting to entire section (prefix, field, suffix)."""
        
        for fmt in section.section_formatting.get(self.token):
            token_value = self._call_function(fmt, field_value, kwargs)
            replacement_text = self.get_replacement_text(token_value)
            for k, v in section.parts.iter_fields():
                section.parts[k] = f'{replacement_text}{v}'

        return True
    
    def apply_inline_formatting(
            self,
            split_part: list[str | tuple[str, str]],
            part_type: str,
            field_value: Any,
            kwargs: Dict = None
            ) -> tuple[list[str | tuple[str, str]], bool]:
        token = self.token
        for i, value in enumerate(split_part):
            if isinstance(value, str):
                continue
            part_token, token_value = value
            if token != part_token:
                continue
            token_value = self.get_replacement_text(self._call_function(token_value, field_value, kwargs))
            split_part[i] = token_value
        return split_part, True

    def get_static_formatting(self, token_value: str) -> Optional[str]:
        if token_value in self._static_cache:
            return self._static_cache[token_value]
        if token_value in self.functions:
            return None
        if self._is_reset_token(token_value):
            return self.reset_ansi
        replacement_text = self.get_replacement_text(token_value)
        if not replacement_text:
            raise StringSmithError(f"Error applying function '{token_value}'")
        self._static_cache[token_value] = replacement_text
        return replacement_text

    @property
    def token(self) -> str:
        return self.__class__._REGISTERED_TOKEN
        
    @property
    def reset_ansi(self):
        return self.__class__._RESET_ANSI
    
    @abstractmethod
    def get_replacement_text(self, token_value: str) -> str:
        """Generate ANSI code for token value. Must be implemented by subclasses."""
        pass