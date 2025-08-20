"""
Base classes for all formatting implementations.

Provides the foundation for color, text style, and conditional formatters
with function fallback support and enhanced error context.
"""

from abc import ABC, abstractmethod
from typing import Dict, Callable, List, Optional, Any, Union
import inspect


class FormatterError(Exception):
    """
    Comprehensive formatter error with enhanced debugging context
    
    Provides detailed information about formatting failures including
    the specific token that failed, available alternatives, and
    template context for easier debugging.
    """
    def __init__(self, message: str, token: Optional[str] = None,
                 formatter_family: Optional[str] = None,
                 template: Optional[str] = None, position: Optional[int] = None,
                 valid_tokens: Optional[List[str]] = None):
        self.token = token
        self.formatter_family = formatter_family
        self.template = template
        self.position = position
        self.valid_tokens = valid_tokens or []
        
        # Build comprehensive error message
        full_message = message
        if token:
            full_message += f"\nToken: '{token}'"
        if formatter_family:
            full_message += f"\nFormatter: {formatter_family}"
        if self.valid_tokens:
            full_message += f"\nValid tokens: {', '.join(self.valid_tokens[:10])}"
            if len(self.valid_tokens) > 10:
                full_message += f" (and {len(self.valid_tokens) - 10} more)"
        if template:
            full_message += f"\nTemplate: '{template}'"
        if position is not None:
            full_message += f"\nPosition: {position}"
            
        super().__init__(full_message)


class FunctionExecutionError(Exception):
    """Raised when function execution fails during formatting"""
    def __init__(self, message: str, function_name: Optional[str] = None,
                 original_error: Optional[Exception] = None,
                 template: Optional[str] = None, position: Optional[int] = None):
        self.function_name = function_name
        self.original_error = original_error
        self.template = template
        self.position = position
        
        full_message = message
        if function_name:
            full_message += f"\nFunction: '{function_name}'"
        if original_error:
            full_message += f"\nOriginal error: {original_error}"
        if template:
            full_message += f"\nTemplate: '{template}'"
        if position is not None:
            full_message += f"\nPosition: {position}"
            
        super().__init__(full_message)


class FormatterBase(ABC):
    """
    Abstract base class for all formatting implementations
    
    Formatters are organized by "family" (color, text, conditional) and support
    function fallback - if a token like #level_color isn't a built-in formatter
    token, the system automatically tries to execute it as a function and 
    re-parse the result.
    """
    
    def __init__(self) -> None:
        self.function_registry: Dict[str, Callable] = {}  # Will be set by DynamicFormatter
        self.current_template: Optional[str] = None  # For error context
        self.current_position: Optional[int] = None  # For error context
        self.config = None  # Will be set by DynamicFormatter
    
    def set_function_registry(self, functions: Dict[str, Callable]) -> None:
        """Set available functions for fallback execution"""
        self.function_registry = functions or {}
    
    def set_error_context(self, template: Optional[str], position: Optional[int]) -> None:
        """Set current template and position for error context"""
        self.current_template = template
        self.current_position = position
    
    def set_config(self, config) -> None:
        """Set formatter configuration"""
        self.config = config
    
    @abstractmethod
    def parse_token(self, token_value: str, field_value: Optional[Any] = None) -> Union[str, int, bool]:
        """
        Parse the token value with optional function fallback and enhanced error context
        
        Args:
            token_value: The token value to parse (e.g., "red", "bold", "has_items")
            field_value: The field value being formatted (for function fallback)
            
        Returns:
            Parsed token that can be used by apply_formatting()
            
        Raises:
            FormatterError: If token is invalid and no function fallback available
            FunctionExecutionError: If function fallback fails
        """
        pass
    
    @abstractmethod
    def apply_formatting(self, text: str, parsed_tokens: List[Union[str, int, bool]], output_mode: str = 'console') -> str:
        """
        Apply formatting to text using a list of parsed tokens from this family
        
        Args:
            text: Text to format
            parsed_tokens: List of parsed tokens from parse_token()
            output_mode: Either 'console' (with ANSI codes) or 'file' (plain text)
            
        Returns:
            Formatted text string
        """
        pass
    
    @abstractmethod
    def get_family_name(self) -> str:
        """
        Return the family name for this formatter (e.g., 'color', 'text')
        
        Used for organizing formatting state and ensuring formatters within
        the same family interact correctly (e.g., later colors override earlier ones).
        """
        pass
    
    def is_reset_token(self, token_value: str) -> bool:
        """Check if this token value is a reset/default token"""
        return token_value.lower() in ['normal', 'default', 'reset']
    
    def strip_formatting(self, formatted_text: str) -> str:
        """Remove formatting codes (default: return as-is)"""
        return formatted_text
    
    def _get_valid_tokens(self) -> List[str]:
        """Get list of valid tokens for this formatter (for error messages)"""
        # Override in subclasses to provide specific valid tokens
        return []
    
    def _raise_formatter_error(self, message: str, token: Optional[str] = None) -> None:
        """Raise a FormatterError with enhanced context"""
        raise FormatterError(
            message=message,
            token=token,
            formatter_family=self.get_family_name(),
            template=self.current_template,
            position=self.current_position,
            valid_tokens=self._get_valid_tokens()
        )
    
    def _try_function_fallback(self, token_value: str, field_value: Optional[Any] = None) -> Optional[str]:
        """
        Try to execute token_value as a function name with enhanced error context
        
        This is the core of the function fallback system. When a token like
        #level_color isn't a built-in color, this method tries to call a
        function named 'level_color' and use its return value.
        
        Args:
            token_value: Function name to try
            field_value: Value to pass to the function
            
        Returns:
            Function result as string, or None if function not found
            
        Raises:
            FunctionExecutionError: If function exists but execution fails
        """
        if not self.function_registry or token_value not in self.function_registry:
            return None
        
        func = self.function_registry[token_value]
        
        try:
            # Inspect function signature to determine how to call it
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            
            if len(params) == 0:
                # Function takes no parameters
                result = func()
            elif len(params) == 1:
                # Function takes one parameter (the field value)
                result = func(field_value)
            else:
                # Function takes multiple parameters - pass the field value and 
                # any other context we might have available
                # For now, just pass the field value to the first parameter
                result = func(field_value)
            
            return str(result) if result is not None else None
            
        except Exception as e:
            raise FunctionExecutionError(
                f"Function '{token_value}' execution failed",
                function_name=token_value,
                original_error=e,
                template=self.current_template,
                position=self.current_position
            )
    
    def _is_graceful_mode(self) -> bool:
        """Check if we're in graceful degradation mode"""
        if self.config and hasattr(self.config, 'validation_mode'):
            from ..config import ValidationMode
            return self.config.validation_mode == ValidationMode.GRACEFUL
        return False
    
    def _is_strict_mode(self) -> bool:
        """Check if we're in strict mode"""
        if self.config and hasattr(self.config, 'validation_mode'):
            from ..config import ValidationMode
            return self.config.validation_mode == ValidationMode.STRICT
        return True  # Default to strict if no config
