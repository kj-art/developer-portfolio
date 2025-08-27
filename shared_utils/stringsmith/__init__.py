"""
StringSmith - Advanced template formatting with conditional sections and inline formatting.

StringSmith provides f-string-like functionality with conditional sections that automatically
disappear when variables aren't provided, plus rich formatting options including colors
and text emphasis. It eliminates manual null checking and conditional string building.

Core Features:
    - **Conditional Sections**: Template sections disappear when variables are missing
    - **Mandatory Field Validation**: Required fields (marked with `!`) enforce data presence  
    - **Rich Formatting**: ANSI colors, text emphasis, and custom styling functions
    - **Performance Optimized**: Templates parsed once, formatted many times efficiently
    - **Thread Safe**: Immutable formatters safe for concurrent use
    - **Extensible**: Custom formatting functions and conditional logic

Quick Start:
    Basic conditional formatting:
    >>> from stringsmith import TemplateFormatter
    >>> formatter = TemplateFormatter("{{Hello ;name;}}")
    >>> formatter.format(name="World")  # "Hello World"
    >>> formatter.format()              # "" (section disappears)

    Rich formatting with colors and emphasis:
    >>> formatter = TemplateFormatter("{{#red@bold;ERROR: ;message;}}")
    >>> formatter.format(message="Failed")  # Red bold "ERROR: Failed"

    Custom functions for dynamic behavior:
    >>> def priority_color(level):
    ...     return 'red' if int(level) > 5 else 'yellow'
    >>> formatter = TemplateFormatter(
    ...     "{{#priority_color;Level ;priority;: ;message;}}", 
    ...     functions={'priority_color': priority_color}
    ... )
    >>> formatter.format(priority=8, message="Critical")  # Red "Level 8: Critical"

Professional Use Cases:
    - Application logging with conditional context that varies by log level
    - Data reporting with sparse or missing datasets
    - CLI interfaces with dynamic status messages
    - Business intelligence with formatted reports
    - Monitoring systems with context-sensitive formatting

Thread Safety:
    All StringSmith components are thread-safe after initialization.
    TemplateFormatter instances are immutable and can be used safely
    across multiple concurrent threads.

Author: Krishna R Jain <krishna@krishnajain.com>
License: MIT
"""

from .core import TemplateFormatter
from .exceptions import (
    StringSmithError,
    MissingMandatoryFieldError,
    ParseError,
    FormattingError,
)

# Package metadata
__version__ = "0.1.0"
__author__ = "Krishna R Jain"
__email__ = "krishna@krishnajain.com"
__license__ = "MIT"
__description__ = "Advanced template formatting with conditional sections and inline formatting"

# Public API - these are the main classes/functions users should import
__all__ = [
    # Main formatter class
    "TemplateFormatter",
    
    # Exception hierarchy
    "StringSmithError",
    "MissingMandatoryFieldError", 
    "ParseError",
    "FormattingError",
    
    # Package metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__description__",
]

# Optional Rich integration check
def _check_rich_available() -> bool:
    """Check if Rich is available for extended color support."""
    try:
        import rich
        return True
    except ImportError:
        return False

# Package-level configuration
HAS_RICH = _check_rich_available()

# Convenience function for checking capabilities
def get_capabilities() -> dict:
    """
    Get StringSmith capabilities and feature availability.
    
    Returns:
        dict: Dictionary of available features and their status
        
    Example:
        >>> from stringsmith import get_capabilities
        >>> caps = get_capabilities()
        >>> print(f"Rich colors available: {caps['rich_colors']}")
    """
    import sys
    return {
        "version": __version__,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "rich_colors": HAS_RICH,
        "basic_colors": True,
        "text_emphasis": True,
        "conditional_sections": True,
        "custom_functions": True,
        "positional_args": True,
        "thread_safe": True,
    }