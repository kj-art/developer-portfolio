"""
StringSmith - Advanced template formatting with conditional sections and inline formatting.

A Python package that provides f-string-like functionality with conditional sections
that are completely omitted when variables aren't provided, plus rich formatting options.
"""

# Handle both relative and absolute imports
try:
    from .formatter import TemplateFormatter
except ImportError:
    from formatter import TemplateFormatter

__version__ = "0.1.0"
__all__ = ["TemplateFormatter"]