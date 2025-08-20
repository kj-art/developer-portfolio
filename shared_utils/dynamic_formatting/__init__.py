"""
Dynamic Formatting Package - Enterprise String Formatting System

An advanced string formatting system designed for production environments that eliminates
manual null checking through automatic section removal. When template sections reference
missing data, they automatically disappear from the output, dramatically simplifying
complex string construction logic throughout your codebase.

CORE VALUE PROPOSITION:
    Replace dozens of lines of conditional string building with simple templates.
    No more manual null checking, no more complex if-else chains for optional content.

ENTERPRISE FEATURES (v2.2.0):
    • Production Performance Monitoring: Built-in observability with memory tracking,
      duration measurement, and regression detection for production environments
      
    • Configuration Management: JSON configuration files with environment-specific
      deployment patterns (development/staging/production presets)
      
    • Thread-Safe Operations: Production-ready concurrency support with proper
      synchronization and graceful degradation
      
    • Professional Error Handling: Detailed error context with template position
      information and suggestions for easier debugging and development

ADVANCED CAPABILITIES:
    • Positional Arguments: Use {{}} syntax for sequential argument processing
    • Conditional Sections: Dynamic content based on function evaluation results  
    • Function Fallback: Custom formatting logic with extensible function registry
    • Token-Based Formatting: Colors, text styling, and custom transformations
    • Family-Based State: Consistent formatting behavior across related templates

REAL-WORLD EXAMPLE:
    # Traditional approach (error-prone, verbose)
    def format_log_entry(level, message, user_id=None, request_id=None, duration=None):
        parts = [f"[{level}] {message}"]
        if user_id:
            parts.append(f"User: {user_id}")
        if request_id:
            parts.append(f"Request: {request_id}")
        if duration:
            parts.append(f"Duration: {duration}ms")
        return " | ".join(parts)
    
    # Dynamic formatting approach (clean, maintainable)
    from shared_utils.dynamic_formatting import DynamicFormatter
    
    formatter = DynamicFormatter(
        "{{[;level;]}} {{message}}{{ | User: ;user_id}}{{ | Request: ;request_id}}{{ | Duration: ;duration;ms}}"
    )
    
    # Identical results, but much more maintainable and less error-prone
    result = formatter.format(level="ERROR", message="Connection failed", user_id="john_doe")

QUICK START:
    from shared_utils.dynamic_formatting import DynamicFormatter
    
    # Basic usage - sections auto-disappear when data missing
    formatter = DynamicFormatter("{{Hello ;name}}{{ from ;location}}")
    
    formatter.format(name="John", location="NYC")  # "Hello John from NYC"
    formatter.format(name="John")                  # "Hello John" (location section removed)
    formatter.format()                             # "" (both sections removed)

PRODUCTION DEPLOYMENT:
    # Environment-specific configurations
    dev_formatter = DynamicFormatter.from_config_file(template, "configs/development.json")
    prod_formatter = DynamicFormatter.from_config_file(template, "configs/production.json")
    
    # Built-in performance monitoring
    with formatter.monitor_performance() as monitor:
        results = [formatter.format(**data) for data in batch_data]
    
    metrics = monitor.get_metrics()  # Duration, memory usage, regression detection

TECHNICAL ACHIEVEMENTS:
    This package demonstrates enterprise-level Python engineering including complex parsing,
    production observability patterns, multi-environment deployment strategies, thread-safe
    programming, memory-efficient data structures, and comprehensive testing practices.
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
    # Main user-facing classes (enhanced versions with enterprise features)
    'DynamicFormatter',  # Enhanced version with performance monitoring and config management
    'DynamicLoggingFormatter',
    
    # Configuration management for enterprise deployment
    'FormatterConfig',
    'ValidationMode', 
    'ValidationLevel',
    
    # Performance monitoring and observability
    'PerformanceMonitor',
    'PerformanceMetrics',
    'PerformanceStats',
    'create_production_monitor',
    'create_production_formatter',
    'create_development_formatter',
    
    # Exception classes with enhanced error context
    'DynamicFormattingError',
    'RequiredFieldError', 
    'FunctionNotFoundError',
    'FormatterError',
    'FunctionExecutionError',
    'ParseError',
    
    # Advanced classes for extension and customization
    'TOKEN_FORMATTERS',
    'FormattingState',
    'TemplateParser',
    'FormattedSpan',
    'FormatSection',
    
    # Base classes for advanced users who need direct access
    'BaseDynamicFormatter',  # Original version without monitoring overhead
]

# Version reflects major enterprise features: config management and performance monitoring
__version__ = '2.2.0'

# Convenience factory functions for common enterprise deployment scenarios
def create_formatter(
    template: str, 
    mode: str = 'development',
    monitor_performance: bool = None,
    config_file: str = None,
    **kwargs
) -> DynamicFormatter:
    """
    Convenience function to create formatters for common enterprise scenarios.
    
    Args:
        template: Format string template to use
        mode: Deployment mode - 'development', 'production', or 'staging'
        monitor_performance: Enable performance monitoring (auto-detected if None)
        config_file: Path to JSON configuration file (optional)
        **kwargs: Additional configuration parameters
        
    Returns:
        DynamicFormatter configured for the specified environment
        
    Examples:
        # Development environment (strict validation, detailed errors)
        dev_formatter = create_formatter(template, mode='development')
        
        # Production environment (graceful degradation, minimal overhead)  
        prod_formatter = create_formatter(template, mode='production')
        
        # Custom configuration file
        custom_formatter = create_formatter(template, config_file='configs/custom.json')
    """
    if config_file:
        return DynamicFormatter.from_config_file(template, config_file)
    
    if mode == 'development':
        return create_development_formatter(template, **kwargs)
    elif mode == 'production':
        return create_production_formatter(template, **kwargs)
    elif mode == 'staging':
        # Staging uses assisted development mode with auto-correction
        config = FormatterConfig(
            validation_mode=ValidationMode.AUTO_CORRECT,
            validation_level=ValidationLevel.WARNING,
            enable_validation=True,
            **kwargs
        )
        return DynamicFormatter(template, config=config)
    else:
        # Default to development mode for safety
        return create_development_formatter(template, **kwargs)


def create_logging_formatter(
    template: str,
    mode: str = 'development',
    **kwargs
) -> DynamicLoggingFormatter:
    """
    Create a logging formatter with enterprise configuration.
    
    Args:
        template: Logging format template
        mode: Deployment mode for configuration
        **kwargs: Additional configuration parameters
        
    Returns:
        DynamicLoggingFormatter configured for the environment
        
    Example:
        import logging
        from shared_utils.dynamic_formatting import create_logging_formatter
        
        # Professional logging setup
        handler = logging.StreamHandler()
        handler.setFormatter(create_logging_formatter(
            "{{#level_color;[;levelname;]}} {{asctime}} {{name}} {{message}}{{ | ;extra_info}}",
            mode='production'
        ))
    """
    formatter_config = create_formatter(template, mode=mode, **kwargs)
    return DynamicLoggingFormatter(template, config=formatter_config.config)


# Enterprise deployment shortcuts
def development_formatter(template: str, **kwargs) -> DynamicFormatter:
    """Create formatter optimized for development (strict validation, detailed errors)"""
    return create_formatter(template, mode='development', **kwargs)


def production_formatter(template: str, **kwargs) -> DynamicFormatter:
    """Create formatter optimized for production (graceful degradation, monitoring)"""
    return create_formatter(template, mode='production', **kwargs)


def staging_formatter(template: str, **kwargs) -> DynamicFormatter:
    """Create formatter optimized for staging (auto-correction, assisted development)"""
    return create_formatter(template, mode='staging', **kwargs)