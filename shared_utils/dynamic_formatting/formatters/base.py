"""
Base formatter classes and exceptions.
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


class FormatterError(Exception):
    """Base exception for formatter-related errors"""
    pass


class FunctionExecutionError(FormatterError):
    """Exception raised when function execution fails"""
    
    def __init__(self, message: str, function_name: Optional[str] = None, 
                 original_error: Optional[Exception] = None, template: Optional[str] = None):
        super().__init__(message)
        self.function_name = function_name
        self.original_error = original_error
        self.template = template


class BaseFormatter(ABC):
    """Base class for all token formatters"""
    
    def __init__(self):
        self.function_registry: Dict[str, Any] = {}
        self.config = None
    
    def set_function_registry(self, functions: Dict[str, Any]) -> None:
        """Set the function registry for this formatter"""
        self.function_registry = functions
    
    def set_config(self, config) -> None:
        """Set the configuration for this formatter"""
        self.config = config
    
    def set_error_context(self, template: str, position: Optional[int]) -> None:
        """Set error context for debugging"""
        self.template = template
        self.position = position
    
    @abstractmethod
    def parse_token(self, token: str, field_value: Any) -> Any:
        """
        Parse a token and return parsed representation
        
        Args:
            token: The token string (without prefix)
            field_value: The field value for context
            
        Returns:
            Parsed token representation
        """
        pass
    
    @abstractmethod
    def apply_formatting(self, text: str, parsed_tokens: List[Any], output_mode: str) -> str:
        """
        Apply formatting to text using parsed tokens
        
        Args:
            text: Text to format
            parsed_tokens: List of parsed tokens
            output_mode: Output mode ('console' or 'file')
            
        Returns:
            Formatted text
        """
        pass