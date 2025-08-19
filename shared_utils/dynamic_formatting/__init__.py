"""
Dynamic Formatting Package with Enhanced Error Context

A sophisticated string formatting system that gracefully handles missing data - template sections 
automatically disappear when their required data isn't provided, eliminating tedious manual null 
checking. Also supports conditional sections, plus extensible token-based formatting for colors 
and text formatting with function fallback support and positional argument support.

CORE VALUE: Sections automatically disappear when data is missing - no manual null checking required

ENHANCED: Detailed error messages with template context and position information for easier 
debugging and development.
"""

# Import the main classes that users will actually need
from .dynamic_formatting import (
    DynamicFormatter,
    DynamicLoggingFormatter,
    DynamicFormattingError,
    RequiredFieldError,
    FunctionNotFoundError
)

from .formatters import (
    TOKEN_FORMATTERS,
    FormatterError,
    FunctionExecutionError
)

from .formatting_state import FormattingState
from .template_parser import TemplateParser, ParseError
from .span_structures import FormattedSpan, FormatSection

__all__ = [
    # Main user-facing classes
    'DynamicFormatter',
    'DynamicLoggingFormatter',
    
    # Exception classes with enhanced context
    'DynamicFormattingError',
    'RequiredFieldError', 
    'FunctionNotFoundError',
    'FormatterError',
    'FunctionExecutionError',
    'ParseError',
    
    # Advanced classes for extension
    'TOKEN_FORMATTERS',
    'FormattingState',
    'TemplateParser',
    'FormattedSpan',
    'FormatSection'
]

__version__ = '2.1.0'