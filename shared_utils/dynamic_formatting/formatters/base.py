"""
Base formatter class and common formatting exceptions with enhanced error context.

This module provides the abstract base class that all formatters must
implement, along with enhanced exception types that provide detailed
context information for debugging.
"""

import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Callable, Optional, Union


class FormatterError(Exception):
    """Base exception for formatter errors with enhanced context"""
    def __init__(self, message: str, token: Optional[str] = None, 
                 formatter_family: Optional[str] = None,
                 template: Optional[str] = None, position: Optional[int] = None,
                 valid_tokens: Optional[List[str]] = None):
        self.token = token
        self.formatter_family = formatter_family
        self.template = template
        self.position = position
        self.valid_tokens = valid_tokens or []
        
        # Build enhanced error message
        enhanced_message = message
        if token and formatter_family:
            enhanced_message = f"Invalid {formatter_family} token: '{token}'"
            if self.valid_tokens:
                enhanced_message += f". Valid tokens: {', '.join(sorted(self.valid_tokens))}"
        
        if template and position is not None:
            # Add template context
            context_start = max(0, position - 15)
            context_end = min(len(template), position + 15)
            template_context = template[context_start:context_end]
            
            if context_start > 0:
                template_context = "..." + template_context
            if context_end < len(template):
                template_context = template_context + "..."
                
            enhanced_message += f"\nNear: {template_context}"
        
        super().__init__(enhanced_message)


class FunctionExecutionError(FormatterError):
    """Raised when a function fallback fails with enhanced context"""
    def __init__(self, message: str, function_name: Optional[str] = None,
                 original_error: Optional[Exception] = None,
                 template: Optional[str] = None, position: Optional[int] = None):
        self.function_name = function_name
        self.original_error = original_error
        
        enhanced_message = message
        if function_name:
            enhanced_message = f"Function '{function_name}' failed: {message}"
            if original_error:
                enhanced_message += f" (Original error: {type(original_error).__name__}: {original_error})"
        
        super().__init__(enhanced_message, template=template, position=position)


class FormatterBase(ABC):
    """
    Base class for all token formatters with enhanced error context
    
    Each formatter handles a specific family of formatting tokens (e.g., colors,
    text styles, conditionals) and provides both parsing and application logic.
    
    The formatter system supports function fallback - if a token like #level_color
    isn't a built-in formatter token, the system automatically tries to execute
    it as a function and re-parse the result.
    """
    
    def __init__(self) -> None:
        self.function_registry: Dict[str, Callable] = {}  # Will be set by DynamicFormatter
        self.current_template: Optional[str] = None  # For error context
        self.current_position: Optional[int] = None  # For error context
    
    def set_function_registry(self, functions: Dict[str, Callable]) -> None:
        """Set available functions for fallback execution"""
        self.function_registry = functions
    
    def set_error_context(self, template: Optional[str], position: Optional[int]) -> None:
        """Set current template and position for error context"""
        self.current_template = template
        self.current_position = position
    
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
                try:
                    result = func()
                except Exception as e:
                    raise FunctionExecutionError(
                        f"Function signature mismatch - function may require parameters",
                        function_name=token_value,
                        original_error=e,
                        template=self.current_template,
                        position=self.current_position
                    )
            
            if not isinstance(result, str):
                raise FunctionExecutionError(
                    f"Function must return a string, got {type(result).__name__}: {result}",
                    function_name=token_value,
                    template=self.current_template,
                    position=self.current_position
                )
            
            return result
            
        except FunctionExecutionError:
            # Re-raise function execution errors
            raise
        except Exception as e:
            raise FunctionExecutionError(
                f"Unexpected error during function execution: {e}",
                function_name=token_value,
                original_error=e,
                template=self.current_template,
                position=self.current_position
            )