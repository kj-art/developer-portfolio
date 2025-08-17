"""
Dynamic Formatting Package

A string formatting system that supports conditional sections with graceful handling of missing data,
plus extensible token-based formatting for colors and text formatting with function fallback support.

Key Features:
- Conditional formatting sections that gracefully handle missing data
- Token-based formatting (#red, @bold, etc.) with function fallback
- Case-insensitive color and text style names
- Proper error handling with meaningful error messages
- Inline formatting support within text spans
- Family-based formatting state management with stacking control
- Integration with logging systems

Example Usage:
    from shared_utils.dynamic_formatting import DynamicFormatter
    
    def get_level_color(level):
        return {'ERROR': 'red', 'INFO': 'green'}.get(level, 'white')
    
    formatter = DynamicFormatter(
        "{{#get_level_color@bold;Level: ;level}} - {{message}}",
        functions={'get_level_color': get_level_color}
    )
    
    result = formatter.format(level="ERROR", message="Something went wrong")
    # Result: colored and bold "Level: ERROR - Something went wrong"
"""

# Import the main classes that users will actually need
try:
    # Try relative imports first (when used as package)
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

    from .formatting_state import (
        FormattingState,
        StackingError
    )

    from .token_parsing import (
        TemplateParser,
        ParseError
    )

    from .span_structures import (
        FormattedSpan,
        FormatSection
    )
except ImportError:
    # Fall back to absolute imports (when files are in same directory)
    from dynamic_formatting import (
        DynamicFormatter,
        DynamicLoggingFormatter,
        DynamicFormattingError,
        RequiredFieldError,
        FunctionNotFoundError
    )

    from formatters import (
        TOKEN_FORMATTERS,
        FormatterError,
        FunctionExecutionError
    )

    from formatting_state import (
        FormattingState,
        StackingError
    )

    from token_parsing import (
        TemplateParser,
        ParseError
    )

    from span_structures import (
        FormattedSpan,
        FormatSection
    )

__all__ = [
    # Main user-facing classes
    'DynamicFormatter',
    'DynamicLoggingFormatter',
    
    # Exception classes
    'DynamicFormattingError',
    'RequiredFieldError', 
    'FunctionNotFoundError',
    'FormatterError',
    'FunctionExecutionError',
    'StackingError',
    'ParseError',
    
    # Advanced classes for extension
    'TOKEN_FORMATTERS',
    'FormattingState',
    'TemplateParser',
    'FormattedSpan',
    'FormatSection'
]

__version__ = '2.0.0'
#python -m shared_utils.dynamic_formatting.dynamic_formatting