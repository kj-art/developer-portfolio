"""
Formatters module for dynamic formatting system.

This module provides token formatters for colors, text styles, and conditionals.
"""

from .base import FormatterError, FunctionExecutionError, BaseFormatter
from .color import ColorFormatter
from .text import TextFormatter
from .conditional import ConditionalFormatter

# Registry of all token formatters
TOKEN_FORMATTERS = {
    '#': ColorFormatter(),
    '@': TextFormatter(),
    '?': ConditionalFormatter(),
}

__all__ = [
    'TOKEN_FORMATTERS',
    'FormatterError',
    'FunctionExecutionError',
    'BaseFormatter',
    'ColorFormatter',
    'TextFormatter',
    'ConditionalFormatter',
]