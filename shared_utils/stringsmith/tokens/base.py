"""
Base token handler for StringSmith formatting tokens.

Provides abstract interface and common functionality for all token handlers.
Token handlers process specific formatting tokens and apply appropriate
formatting operations during template rendering.
"""

from abc import ABC, abstractmethod
from typing import Dict, Callable, Any, Optional
import inspect

from ..core import TemplateSection
from ..exceptions import StringSmithError
class BaseTokenHandler(ABC):
    """
    Abstract base class for StringSmith token handlers.
    
    Token handlers process specific formatting tokens (colors, emphasis, conditionals)
    and apply appropriate formatting operations during template rendering. Each token
    type has a corresponding handler that inherits from this base class.
    
    The token handler system uses a multi-pass architecture where handlers are
    organized by priority and applied in sequence. This allows for complex formatting
    interactions and proper precedence handling.
    
    Args:
        functions (Dict[str, Callable], optional): Custom user functions available
                                                 for dynamic token processing.
    
    Thread Safety:
        Handlers are thread-safe after initialization for concurrent formatting
        operations. Function registry and static caches are immutable after setup.
    """
    _RESET_TOKENS = ('normal', 'default', 'reset')

    def __init__(self, functions: Dict[str, Callable] = None):
        """
        Initialize token handler with function registry and static cache.
        
        Sets up the handler's function registry for dynamic token processing and
        initializes caching systems for improved performance. Validates that custom
        functions don't conflict with reserved token keywords.
        
        Args:
            functions: Dictionary of custom functions for dynamic token processing
            
        Raises:
            StringSmithError: If custom function names conflict with reserved tokens
        """
        self._static_cache = {}

        # Validate custom function names don't conflict with reserved tokens
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
        
        Implements sophisticated parameter matching to enable both single-field and
        multi-field functions. Functions with parameter names matching format()
        arguments receive those specific values, while functions with no matches
        receive the section's field value for compatibility.
        
        Parameter Matching Logic:
            1. No parameters: call with no arguments
            2. All parameters match kwargs: call with matched parameter values
            3. Otherwise: call with section's field_value (single-field mode)
        
        Args:
            function_name: Name of function in the function registry
            field_value: Value of current section's field (fallback argument)
            kwargs: All field values from format() call for parameter matching
            
        Returns:
            Function result for use in formatting operations
            
        Examples:
            # Multi-parameter function receives matched values
            def is_profitable(revenue, costs): 
                return float(revenue) > float(costs)
            # Called as: is_profitable(revenue=150, costs=120)
            
            # Single-parameter function receives field value
            def priority_color(level): 
                return 'red' if int(level) > 5 else 'green'
            # Called as: priority_color(field_value)
            
            # No-parameter function receives nothing
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

        # Case 3: fallback to passing field_value for single-field compatibility
        return func(field_value)


    def _is_reset_token(self, value: str) -> bool:
        """
        Check if token value is a formatting reset token.
        
        Reset tokens ('normal', 'default', 'reset') clear formatting state
        and are handled specially by the formatting system.
        
        Args:
            value: Token value to check
            
        Returns:
            bool: True if value is a reset token
        """
        return value.lower() in self._RESET_TOKENS
    
    def apply_section_formatting(self, section: TemplateSection, field_value: Any, kwargs: Dict = None) -> bool:
        """
        Apply formatting to entire section (prefix, field, suffix).
        
        Processes section-level formatting tokens and applies their effects to all
        parts of the template section. This is called during the formatting phase
        to handle tokens that affect the entire section scope.
        
        Args:
            section: Template section to format (modified in place)
            field_value: Value of the section's field
            kwargs: All format() arguments for function parameter matching
            
        Returns:
            bool: True if section should be displayed, False to hide it
        """
        
        for fmt in section.section_formatting.get(self.token):
            token_value = self._call_function(fmt, field_value, kwargs)
            replacement_text = self.get_replacement_text(token_value)

            # Apply formatting to all section parts
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
        """
        Apply inline formatting to specific tokens within template parts.
        
        Processes inline formatting tokens that appear within template parts,
        replacing token sequences with appropriate formatting codes. This enables
        fine-grained formatting control within individual template sections.
        
        Args:
            split_part: List of text fragments and token tuples from token splitting
            part_type: Type of template part being processed ('prefix', 'field', 'suffix')
            field_value: Value of the section's field
            kwargs: All format() arguments for function parameter matching
            
        Returns:
            tuple: (processed_fragments, continue_display_flag)
                - processed_fragments: Updated list with tokens replaced by formatting
                - continue_display_flag: True if section should continue to be displayed
        """
        token = self.token

        for i, value in enumerate(split_part):
            if isinstance(value, str):
                continue

            part_token, token_value = value
            if token != part_token:
                continue

            # Process matching token
            token_value = self.get_replacement_text(self._call_function(token_value, field_value, kwargs))
            split_part[i] = token_value

        return split_part, True

    def get_static_formatting(self, token_value: str) -> Optional[str]:
        """
        Get pre-computed formatting for static tokens.
        
        Provides cached formatting codes for tokens that don't require runtime
        computation. Function-based tokens return None to indicate they need
        runtime processing. Reset tokens are handled specially.
        
        Args:
            token_value: Token value to process
            
        Returns:
            Optional[str]: Pre-computed formatting code, or None if runtime processing needed
        """
        # Return cached result if available
        if token_value in self._static_cache:
            return self._static_cache[token_value]
        
        # Function-based tokens need runtime processing
        if token_value in self.functions:
            return None
        
        # Handle reset tokens specially
        if self._is_reset_token(token_value):
            return self.reset_ansi
        
        # Compute and cache static formatting
        replacement_text = self.get_replacement_text(token_value)
        if not replacement_text:
            raise StringSmithError(f"Error applying function '{token_value}'")
        
        self._static_cache[token_value] = replacement_text
        return replacement_text

    @property
    def token(self) -> str:
        """Get the token prefix this handler processes."""
        return self.__class__._REGISTERED_TOKEN
        
    @property
    def reset_ansi(self):
        """Get the ANSI reset sequence for this token type."""
        return self.__class__._RESET_ANSI
    
    @abstractmethod
    def get_replacement_text(self, token_value: str) -> str:
        """
        Generate formatting code for token value.
        
        This is the core method that each token handler must implement to
        convert token values into appropriate formatting codes (usually ANSI
        escape sequences for terminal formatting).
        
        Args:
            token_value: The token value to process (e.g., 'red', 'bold', 'FF0000')
            
        Returns:
            str: Formatting code to insert into the output
            
        Raises:
            StringSmithError: If token value is invalid or cannot be processed
        """
        pass