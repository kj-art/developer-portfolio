"""
Dynamic Formatting Package

Professional string formatting with automatic missing data handling, function fallback,
and configurable validation modes for enterprise deployment.

Core Features:
- Automatic section removal for missing data (eliminates manual null checking)
- Function fallback for dynamic formatting logic
- Positional and keyword argument support
- Configurable validation modes (strict/graceful/auto-correct)
- Production-ready configuration management
- Enhanced error context for debugging

Quick Start:
    >>> from shared_utils.dynamic_formatting import DynamicFormatter
    >>> formatter = DynamicFormatter("{{Status: ;status}}{{ | Code: ;code}}")
    >>> result = formatter.format(status="Success", code=200)
    >>> print(result)  # "Status: Success | Code: 200"
    >>> 
    >>> # Missing data automatically handled
    >>> result = formatter.format(status="Success")
    >>> print(result)  # "Status: Success"
"""

# Import main classes for public API
from .enhanced_formatter import DynamicFormatter, create_production_formatter, create_development_formatter
from .dynamic_formatting import DynamicLoggingFormatter, DynamicFormattingError, RequiredFieldError, FunctionNotFoundError
from .config import FormatterConfig, ValidationMode, ValidationLevel, create_development_config, create_production_config, create_testing_config
from .performance_monitor import PerformanceMonitor, create_production_monitor, create_development_monitor

# Import formatter errors
try:
    from .formatters.base import FormatterError, FunctionExecutionError
except ImportError:
    # Define minimal versions if formatters module is missing
    class FormatterError(Exception):
        """Base formatter error"""
        pass
    
    class FunctionExecutionError(Exception):
        """Function execution error"""
        pass

# Version information
__version__ = "2.2.0"
__author__ = "Dynamic Formatting Team"

# Public API
__all__ = [
    # Main classes
    'DynamicFormatter',
    'DynamicLoggingFormatter',
    
    # Configuration
    'FormatterConfig',
    'ValidationMode', 
    'ValidationLevel',
    'create_development_config',
    'create_production_config',
    'create_testing_config',
    
    # Performance monitoring
    'PerformanceMonitor',
    'create_production_monitor',
    'create_development_monitor',
    'create_production_formatter',
    'create_development_formatter',
    
    # Exceptions
    'DynamicFormattingError',
    'RequiredFieldError',
    'FunctionNotFoundError',
    'FormatterError',
    'FunctionExecutionError',
    
    # Version
    '__version__',
]