"""
Base formatter class and common formatting exceptions.

This module provides the abstract base class that all formatters must
implement, along with common exception types used throughout the
formatting system.
"""

import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Callable, Optional, Union


class FormatterError(Exception):
    """Base exception for formatter errors"""
    pass


class FunctionExecutionError(FormatterError):
    """Raised when a function fallback fails"""
    pass


class FormatterBase(ABC):
    """
    Base class for all token formatters
    
    Each formatter handles a specific family of formatting tokens (e.g., colors,
    text styles, conditionals) and provides both parsing and application logic.
    
    The formatter system supports function fallback - if a token like #level_color
    isn't a built-in formatter token, the system automatically tries to execute
    it as a function and re-parse the result.
    """
    
    def __init__(self) -> None:
        self.function_registry: Dict[str, Callable] = {}  # Will be set by DynamicFormatter
    
    def set_function_registry(self, functions: Dict[str, Callable]) -> None:
        """Set available functions for fallback execution"""
        self.function_registry = functions
    
    @abstractmethod
    def parse_token(self, token_value: str, field_value: Optional[Any] = None) -> Union[str, int, bool]:
        """
        Parse the token value with optional function fallback
        
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
    
    def _try_function_fallback(self, token_value: str, field_value: Optional[Any] = None) -> Optional[str]:
        """
        Try to execute token_value as a function name
        
        This is the core of the function fallback system. When a token like
        #level_color isn't a built-in color, this method tries to call a
        function named 'level_color' and use its return value.
        
        Args:
            token_value: Function name to try
            field_value: Field value to pass to function
            
        Returns:
            Function result if successful, None if function doesn't exist
            
        Raises:
            FunctionExecutionError: If function exists but fails
        """
        if not self.function_registry or token_value not in self.function_registry:
            return None
        
        try:
            func = self.function_registry[token_value]
            
            # Try calling with field_value first, then without arguments
            try:
                if field_value is not None:
                    result = func(field_value)
                else:
                    result = func()
            except TypeError:
                # Function might not accept field_value parameter
                result = func()
            
            if not isinstance(result, str):
                raise FunctionExecutionError(
                    f"Function '{token_value}' must return a string, got {type(result).__name__}: {result}"
                )
            
            return result
            
        except Exception as e:
            raise FunctionExecutionError(f"Function '{token_value}' failed: {e}")