"""
Dynamic Formatting Package with Enhanced Error Context and Performance Monitoring

A sophisticated string formatting system that gracefully handles missing data - template sections 
automatically disappear when their required data isn't provided, eliminating tedious manual null 
checking. Also supports conditional sections, plus extensible token-based formatting for colors 
and text formatting with function fallback support and positional argument support.

CORE VALUE: Sections automatically disappear when data is missing - no manual null checking required

ENHANCED: Detailed error messages with template context and position information for easier 
debugging and development.

NEW: Optional performance monitoring for production observability and development optimization.
"""

# Import the main classes that users will actually need
from .dynamic_formatting import (
    DynamicFormatter as BaseDynamicFormatter,
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

# Import configuration management
from .config import FormatterConfig, ValidationMode, ValidationLevel

# Import performance monitoring system
from .performance_monitor import (
    PerformanceMonitor, 
    PerformanceMetrics,
    PerformanceStats,
    create_production_monitor
)

# Import enhanced formatter with performance monitoring
from .enhanced_formatter import (
    DynamicFormatter,  # This is the enhanced version with monitoring
    create_production_formatter,
    create_development_formatter
)

# Keep the base formatter available for those who want it
BaseDynamicFormatter = BaseDynamicFormatter

__all__ = [
    # Main user-facing classes (enhanced versions)
    'DynamicFormatter',  # Enhanced version with performance monitoring
    'DynamicLoggingFormatter',
    
    # Configuration management
    'FormatterConfig',
    'ValidationMode', 
    'ValidationLevel',
    
    # Performance monitoring
    'PerformanceMonitor',
    'PerformanceMetrics',
    'PerformanceStats',
    'create_production_monitor',
    'create_production_formatter',
    'create_development_formatter',
    
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
    'FormatSection',
    
    # Base classes for advanced users
    'BaseDynamicFormatter',  # Original version without monitoring
]

__version__ = '2.2.0'  # Bumped for performance monitoring features

# Convenience imports for common use cases
def create_formatter(
    template: str, 
    mode: str = 'development',
    monitor_performance: bool = None,
    **kwargs
) -> DynamicFormatter:
    """
    Convenience function to create formatters for common scenarios.
    
    Args:
        template: Template string
        mode: 'development', 'production', or 'basic'
        monitor_performance: Override performance monitoring (auto-detected if None)
        **kwargs: Additional arguments passed to formatter
        
    Returns:
        Appropriately configured DynamicFormatter
    """
    if mode == 'production':
        return create_production_formatter(template, **kwargs)
    elif mode == 'development':
        return create_development_formatter(template, **kwargs)
    else:  # basic mode
        # Use base formatter without monitoring for simple use cases
        return BaseDynamicFormatter(template, **kwargs)