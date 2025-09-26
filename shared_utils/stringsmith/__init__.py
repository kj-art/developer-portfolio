"""
StringSmith - Professional template formatting with conditional sections and rich styling.

StringSmith provides advanced template formatting capabilities that eliminate manual null
checking and conditional string building. Templates automatically adapt based on available
data, with rich formatting options including colors, text emphasis, and custom functions.

Core Features:
    - **Conditional Sections**: Template sections disappear when variables are missing
    - **Mandatory Field Validation**: Required fields (marked with `!`) enforce data presence  
    - **Rich Formatting**: ANSI colors, text emphasis, hex codes, and custom styling
    - **Custom Functions**: User-defined functions for dynamic formatting and conditionals
    - **Multi-Parameter Functions**: Functions can access multiple template fields
    - **Performance Optimized**: Templates parsed once, formatted many times efficiently
    - **Thread Safe**: Immutable formatters safe for concurrent use
    - **Extensible**: Custom token handlers for specialized formatting needs

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
    - Application logging with context that varies by log level
    - Data reporting with sparse or missing datasets  
    - CLI interfaces with dynamic status messages
    - Business intelligence with formatted reports
    - Monitoring systems with context-sensitive alerts

Token Types:
    - #: Colors (named, hex codes, or custom functions)
    - @: Text emphasis (bold, italic, underline, etc.)
    - ?: Conditionals (section shown only if function returns True)
    - $: Literal transforms (replace content with function result)

Thread Safety:
    All StringSmith components are thread-safe after initialization.
    TemplateFormatter instances are immutable and can be used safely
    across multiple concurrent threads without synchronization.

Performance:
    Templates are parsed and optimized during initialization for fast
    runtime formatting. Recommended usage is to create formatters once
    and reuse them for multiple format operations.

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
__description__ = "Professional template formatting with conditional sections and rich styling"

# Public API - main classes and functions for user import
__all__ = [
    # Core formatter class
    "TemplateFormatter",
    
    # Exception hierarchy for error handling
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

def _check_rich_available() -> bool:
    """Check if Rich library is available for extended color support."""
    try:
        import rich
        return True
    except ImportError:
        return False

# Package-level feature detection
HAS_RICH = _check_rich_available()

def get_capabilities() -> dict:
    """
    Get StringSmith capabilities and feature availability.
    
    Returns comprehensive information about available features, performance
    characteristics, and optional dependencies for system integration.
    
    Returns:
        dict: Dictionary of available features and their status
        
    Example:
        >>> from stringsmith import get_capabilities
        >>> caps = get_capabilities()
        >>> print(f"Rich colors available: {caps['rich_colors']}")
        >>> print(f"Version: {caps['version']}")
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
        "multi_parameter_functions": True,
        "positional_args": True,
        "thread_safe": True,
        "performance_optimized": True,
        "extensible_tokens": True,
    }