"""
StringSmith - Advanced template formatting with conditional sections and inline formatting.

A professional Python library that provides f-string-like functionality with conditional 
sections that are completely omitted when variables aren't provided, plus rich formatting 
options including colors and text emphasis.

Core Features:
- Conditional sections that disappear when variables are missing
- Mandatory field validation with structured error handling
- Rich color formatting (matplotlib colors, hex codes, custom functions)
- Text emphasis formatting (bold, italic, underline, etc.)
- Custom function integration for formatting and conditionals
- Performance-optimized template parsing and caching
- Thread-safe immutable formatters
- Professional error handling with detailed context

Quick Start:
    >>> from stringsmith import TemplateFormatter
    >>> formatter = TemplateFormatter("{{Hello ;name;}}")
    >>> formatter.format(name="World")  # "Hello World"
    >>> formatter.format()              # "" (section disappears)

Professional Use Cases:
- Application logging with conditional context
- Data reporting with sparse datasets
- CLI user interfaces with dynamic status
- Template-based output generation
"""

# Handle both relative and absolute imports for flexible usage
try:
    from .formatter import TemplateFormatter
    from .exceptions import (
        StringSmithError,
        MissingMandatoryFieldError,
        ParseError,
        FormattingError,
    )
except ImportError:
    # Fallback for direct execution or development
    from formatter import TemplateFormatter
    from exceptions import (
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