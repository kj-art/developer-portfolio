"""
Enhanced DynamicFormatter with integrated performance monitoring.

This extends the base DynamicFormatter to add optional performance tracking
for production observability without changing the core API.
"""

from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from .performance_monitor import PerformanceMonitor
from .dynamic_formatting import DynamicFormatter as BaseDynamicFormatter
from .config import FormatterConfig


class DynamicFormatter(BaseDynamicFormatter):
    """
    Enhanced DynamicFormatter with integrated performance monitoring.
    
    Extends the base DynamicFormatter to add optional performance tracking
    for production observability without changing the core API.
    """
    
    def __init__(
        self, 
        template: str, 
        functions: Optional[Dict[str, Any]] = None,
        config: Optional[FormatterConfig] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """
        Initialize formatter with optional performance monitoring.
        
        Args:
            template: Template string to parse
            functions: Optional function registry
            config: Optional formatter configuration
            performance_monitor: Optional performance monitor for tracking
        """
        # Initialize base formatter
        super().__init__(template, functions, config)
        
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
        if not self.performance_monitor:
            return super().format(*args, **kwargs), None
        
        # Create a temporary monitor for detailed tracking
        temp_monitor = PerformanceMonitor(enabled=True)
        
        with temp_monitor.track('detailed_format_operation'):
            result = super().format(*args, **kwargs)
        
        metrics = temp_monitor.get_stats('detailed_format_operation')
        return result, metrics
    
    @classmethod
    def from_config(
        cls, 
        config_source: Union[str, Dict[str, Any], FormatterConfig],
        template: Optional[str] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ) -> 'DynamicFormatter':
        """
        Create formatter from configuration with optional performance monitoring.
        
        Args:
            config_source: Configuration file path, dict, or FormatterConfig object
            template: Optional template override
            performance_monitor: Optional performance monitor
            
        Returns:
            Configured DynamicFormatter with performance monitoring
        """
        # Use base class method to create formatter
        formatter = super().from_config(config_source, template)
        
        # Add performance monitoring
        formatter.performance_monitor = performance_monitor
        
        return formatter
    
    def get_performance_stats(self) -> Optional[List[Dict[str, Any]]]:
        """Get current performance statistics if monitoring is enabled."""
        if self.performance_monitor:
            return self.performance_monitor.get_stats()
        return None
    
    def export_performance_stats(self, filepath: str) -> bool:
        """
        Export performance statistics to file.
        
        Args:
            filepath: Path to export stats JSON file
            
        Returns:
            True if export successful, False if no monitor configured
        """
        if self.performance_monitor:
            self.performance_monitor.export_stats(filepath)
            return True
        return False


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
    monitor = PerformanceMonitor(
        enabled=True,
        log_threshold_ms=10.0,  # Lower threshold for development
        memory_threshold_mb=1.0,  # Stricter memory monitoring
        regression_threshold=1.2,  # Tighter regression detection
        auto_log_stats=True,
        log_stats_interval=100  # More frequent stats in development
    )
    
    return DynamicFormatter(
        template=template,
        functions=functions,
        config=config,
        performance_monitor=monitor
    )