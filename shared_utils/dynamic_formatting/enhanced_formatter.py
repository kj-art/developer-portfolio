"""
Enhanced formatter with additional convenience methods and production-ready features.

This module extends the base DynamicFormatter with helper methods for common
deployment scenarios and enhanced functionality.
"""

from typing import Dict, Any, Optional, Tuple
from .dynamic_formatting import DynamicFormatter as BaseDynamicFormatter
from .config import FormatterConfig


class DynamicFormatter(BaseDynamicFormatter):
    """
    Enhanced dynamic formatter with convenience methods and monitoring
    
    Extends the base formatter with additional methods for production use,
    monitoring, and common formatting patterns.
    """
    
    def __init__(self, format_string: str, config: Optional[FormatterConfig] = None,
                 functions: Optional[Dict[str, Any]] = None, performance_monitor=None, **kwargs):
        """
        Initialize enhanced formatter
        
        Args:
            format_string: Template string with {{...}} sections
            config: Configuration object
            functions: Custom functions for formatting
            performance_monitor: Optional performance monitoring instance
            **kwargs: Additional configuration parameters
        """
        super().__init__(format_string, config, functions, **kwargs)
        self.performance_monitor = performance_monitor
    
    def format(self, *args, **kwargs) -> str:
        """
        Enhanced format method with optional performance monitoring
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Formatted string
        """
        if self.performance_monitor and self.performance_monitor.enabled:
            with self.performance_monitor.track("format_operation"):
                return super().format(*args, **kwargs)
        else:
            return super().format(*args, **kwargs)
    
    def format_with_detailed_tracking(self, **kwargs) -> Tuple[str, Optional[Any]]:
        """
        Format with detailed performance tracking
        
        Args:
            **kwargs: Keyword arguments for formatting
            
        Returns:
            Tuple of (formatted_result, performance_metrics)
        """
        if not self.performance_monitor:
            return self.format(**kwargs), None
        
        # This would need the actual performance monitor implementation
        # For now, return None for metrics
        result = self.format(**kwargs)
        return result, None
    
    @classmethod
    def from_config(cls, template: str, config, **kwargs):
        """
        Create formatter from configuration object
        
        Args:
            template: Template string
            config: Configuration object or file path
            **kwargs: Additional parameters
            
        Returns:
            Configured DynamicFormatter instance
        """
        if isinstance(config, str):
            # Assume it's a file path
            formatter_config = FormatterConfig.from_config_file(config)
        elif hasattr(config, 'from_config_file'):
            # It's already a FormatterConfig
            formatter_config = config
        else:
            # Assume it's a dict
            formatter_config = FormatterConfig.from_config_dict(config)
        
        return cls(template, config=formatter_config, **kwargs)


def create_production_formatter(template: str, monitor_slow_operations: bool = False,
                               monitor_memory_usage: bool = False, **kwargs) -> DynamicFormatter:
    """
    Create a formatter optimized for production use
    
    Args:
        template: Template string
        monitor_slow_operations: Enable slow operation monitoring
        monitor_memory_usage: Enable memory usage monitoring
        **kwargs: Additional configuration parameters
        
    Returns:
        Production-ready DynamicFormatter instance
    """
    # FIXED: Handle performance monitoring override properly
    enable_monitoring = monitor_slow_operations or monitor_memory_usage
    if enable_monitoring:
        kwargs['enable_performance_monitoring'] = True
    
    # Set up production configuration
    config = FormatterConfig.production(**kwargs)
    
    performance_monitor = None
    if enable_monitoring:
        # Would initialize performance monitor here
        # For now, pass None
        pass
    
    return DynamicFormatter(
        template,
        config=config,
        performance_monitor=performance_monitor
    )


def create_development_formatter(template: str, **kwargs) -> DynamicFormatter:
    """
    Create a formatter optimized for development use
    
    Args:
        template: Template string
        **kwargs: Additional configuration parameters
        
    Returns:
        Development-ready DynamicFormatter instance
    """
    # FIXED: Handle performance monitoring properly - development defaults to enabled
    if 'enable_performance_monitoring' not in kwargs:
        kwargs['enable_performance_monitoring'] = True
    
    # Set up development configuration
    config = FormatterConfig.development(**kwargs)
    
    performance_monitor = None
    # Would initialize performance monitor for development
    
    return DynamicFormatter(
        template,
        config=config,
        performance_monitor=performance_monitor
    )


def create_console_formatter(template: str, **kwargs) -> DynamicFormatter:
    """
    Create a formatter optimized for console output
    
    Args:
        template: Template string
        **kwargs: Additional configuration parameters
        
    Returns:
        Console-optimized DynamicFormatter instance
    """
    config = FormatterConfig(
        output_mode="console",
        enable_colors=True,
        **kwargs
    )
    
    return DynamicFormatter(template, config=config)


def create_file_formatter(template: str, **kwargs) -> DynamicFormatter:
    """
    Create a formatter optimized for file output
    
    Args:
        template: Template string
        **kwargs: Additional configuration parameters
        
    Returns:
        File-optimized DynamicFormatter instance
    """
    config = FormatterConfig(
        output_mode="file",
        enable_colors=False,
        **kwargs
    )
    
    return DynamicFormatter(template, config=config)