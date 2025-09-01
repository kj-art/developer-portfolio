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
        
        for fmt in section.section_formatting.get(self.get_token()):
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
        token = self.get_token()
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

    '''def bake_inline_formatting(self, parts: SectionParts) -> bool:
        """
        Pre-process static inline formatting tokens during template baking phase.
        
        Finds and applies all static formatting tokens (colors, emphasis styles) that
        don't require runtime data. Static tokens are resolved to ANSI codes and
        removed from the text, while dynamic tokens (custom functions) are left
        untouched for the format phase.
        
        Args:
            parts: Section parts containing potential inline tokens
            
        Returns:
            bool: True if any dynamic/live tokens remain and format phase is needed,
                False if all tokens were static and fully processed during baking
                
        Performance Note:
            This method optimizes runtime formatting by pre-processing everything
            possible during template initialization, reducing format() overhead.
        """
        static_bank = {}
        has_live_tokens = False
        for k, part in parts.iter_fields():
            static = defaultdict(str)
            for start, end, token_value in self.find_token(part):
                if token_value in self.functions:
                    has_live_tokens = True
                    continue

                if self._is_reset_token(token_value):
                    static[token_value] = self.RESET_ANSI
                else:
                    if token_value not in static_bank:
                        replacement_text = self.get_replacement_text(token_value)
                        if not replacement_text:
                            raise StringSmithError(f"Error applying function '{token_value}'")
                    static_bank[token_value] = static[token_value] = replacement_text
                    
            parts[k] = self._replace_static_tokens(parts[k], static)
        return has_live_tokens
    
    def apply_inline_formatting(self, parts: SectionParts, field_value: Any = None, kwargs: Dict = None) -> bool:
        """
    Apply dynamic inline formatting tokens during format phase with runtime data.
    
    Processes only the dynamic tokens (custom functions) that were deferred during
    baking. This method is only called if bake_inline_formatting() returned True,
    ensuring no unnecessary work for sections with only static tokens.
    
    Args:
        parts: Section parts containing dynamic tokens to process
        field_value: Runtime field value for function evaluation
        kwargs: All format() arguments for multi-parameter function support
        
    Returns:
        bool: True if the field value should be included in output,
              False if conditional tokens determined it should be hidden
              
    Note:
        This method assumes bake_inline_formatting() was already called and
        only dynamic tokens remain in the text.
    """
        
        for k, part in parts.iter_fields():
            dynamic = set()
            for start, end, token_value in self.find_token(part):
                if token_value in self.functions:    
                    dynamic.add(token_value)
                    
            parts[k] = self._replace_dynamic_tokens(parts[k], dynamic, field_value, kwargs)
        return True

    def _replace_dynamic_tokens(self, part: str, tokens: set[str], field_value: Any, kwargs: Dict) -> str:
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
            ansi_codes = [self.get_replacement_text(str(self._call_function(token, field_value, kwargs))) for _ in range(len(parts_list) - 1)]
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
        return f'{{{self.get_token()}{token_value}}}'
    '''
    def get_token(self) -> str:
        if hasattr(self.__class__, '_REGISTERED_TOKEN'):
            return self.__class__._REGISTERED_TOKEN
        
    @property
    def reset_ansi(self):
        return self.__class__._RESET_ANSI
    
    @abstractmethod
    def get_replacement_text(self, token_value: str) -> str:
        """Generate ANSI code for token value. Must be implemented by subclasses."""
        pass