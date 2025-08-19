from .base import FormatterBase, FormatterError, FunctionExecutionError
from .color import ColorFormatter
from .text import TextFormatter
from .conditional import ConditionalFormatter

TOKEN_FORMATTERS = {
    '#': ColorFormatter(),
    '@': TextFormatter(), 
    '?': ConditionalFormatter(),
}

__all__ = [
    'FormatterBase',
    'FormatterError',
    'FunctionExecutionError', 
    'ColorFormatter', 
    'TextFormatter',
    'ConditionalFormatter',
    'TOKEN_FORMATTERS',
]