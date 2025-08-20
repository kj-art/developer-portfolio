"""
Enhanced DynamicFormatter with integrated performance monitoring.

This extends the base DynamicFormatter to add optional performance tracking
for production observability without changing the core API.
"""

from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from .dynamic_formatting import DynamicFormatter as BaseDynamicFormatter
from .config import FormatterConfig


class DynamicFormatter(BaseDynamicFormatter):
    """
    Enhanced DynamicFormatter with integrated performance monitoring.
    
    Extends the base DynamicFormatter to add optional performance tracking
    for production observability without changing the core API.
    
    This is the main entry point that users should import.
    """
    
    def __init__(
        self, 
        template: str, 
        functions: Optional[Dict[str, Any]] = None,
        config: Optional[FormatterConfig] = None,
        performance_monitor: Optional[Any] = None,
        # Backward compatibility parameters
        delimiter: Optional[str] = None,
        output_mode: Optional[str] = None,
        validate: Optional[bool] = None,
        validation_level: Optional[str] = None
    ):
        """
        Initialize formatter with optional performance monitoring.
        
        Args:
            template: Template string to parse
            functions: Optional function registry
            config: Optional formatter configuration
            performance_monitor: Optional performance monitor for tracking
            delimiter: Field separator (backward compatibility)
            output_mode: 'console' or 'file' (backward compatibility)
            validate: Enable validation (backward compatibility)
            validation_level: Validation strictness (backward compatibility)
        """
        # Initialize base formatter
        super().__init__(
            template, 
            functions=functions, 
            config=config,
            delimiter=delimiter,
            output_mode=output_mode,
            validate=validate,
            validation_level=validation_level
        )
        
        # Store performance monitor
        self.performance_monitor = performance_monitor
        
        # Track template compilation performance if monitor is enabled
        if self.performance_monitor:
            # The template was already compiled in super().__init__
            # In a real implementation, you'd wrap the compilation:
            # with self.performance_monitor.track('template_compilation'):
            #     # template compilation logic here
            pass
    
    def format(self, *args, **kwargs) -> str:
        """
        Format template with performance monitoring.
        
        Automatically tracks format operation performance if monitor is configured.
        """
        if self.performance_monitor:
            with self.performance_monitor.track('format_operation'):
                return super().format(*args, **kwargs)
        else:
            return super().format(*args, **kwargs)
    
    def format_with_detailed_tracking(self, *args, **kwargs) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        Format template and return both result and performance metrics.
        
        Useful for debugging performance issues or detailed monitoring.
        
        Returns:
            Tuple of (formatted_result, performance_metrics)
        """
        if self.performance_monitor:
            with self.performance_monitor.track('format_operation_detailed') as tracker:
                result = super().format(*args, **kwargs)
                return result, tracker.get_metrics()
        else:
            result = super().format(*args, **kwargs)
            return result, None


# Convenience functions for common monitoring scenarios
def create_production_formatter(
    template: str,
    functions: Optional[Dict[str, Any]] = None,
    config: Optional[FormatterConfig] = None,
    monitor_slow_operations: bool = True,
    monitor_memory_usage: bool = True,
    export_stats_path: Optional[str] = None
) -> DynamicFormatter:
    """
    Create a formatter configured for production monitoring.
    
    Args:
        template: Template string
        functions: Optional function registry
        config: Optional formatter configuration
        monitor_slow_operations: Enable slow operation detection
        monitor_memory_usage: Enable memory usage monitoring
        export_stats_path: Optional path for stats export
        
    Returns:
        DynamicFormatter with production-ready performance monitoring
    """
    from .performance_monitor import create_production_monitor
    
    monitor = create_production_monitor(
        log_slow_operations=monitor_slow_operations,
        log_memory_usage=monitor_memory_usage,
        export_stats_path=export_stats_path
    )
    
    return DynamicFormatter(
        template=template,
        functions=functions,
        config=config,
        performance_monitor=monitor
    )


def create_development_formatter(
    template: str,
    functions: Optional[Dict[str, Any]] = None,
    config: Optional[FormatterConfig] = None
) -> DynamicFormatter:
    """
    Create a formatter with development-friendly monitoring.
    
    More verbose logging and lower thresholds for catching performance
    issues during development.
    """
    from .performance_monitor import create_development_monitor
    
    monitor = create_development_monitor()
    
    return DynamicFormatter(
        template=template,
        functions=functions,
        config=config,
        performance_monitor=monitor
    )