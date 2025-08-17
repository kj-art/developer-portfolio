"""
Dynamic Formatting Package

A string formatting system that supports conditional sections with graceful handling of missing data,
plus extensible token-based formatting for colors and future text formatting.
"""

# Import the main classes that users will actually need
from .dynamic_formatting import (
    DynamicFormatter,
    DynamicLoggingFormatter,
    DynamicFormattingError,
    RequiredFieldError,
    FunctionNotFoundError
)

from .formatters import TOKEN_FORMATTERS

__all__ = [
    'DynamicFormatter',
    'DynamicLoggingFormatter', 
    'DynamicFormattingError',
    'RequiredFieldError',
    'FunctionNotFoundError',
    'TOKEN_FORMATTERS'
]

__version__ = '1.0.0'
#python -m shared_utils.dynamic_formatting.dynamic_formatting