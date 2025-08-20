"""
Enhanced dynamic formatter with performance monitoring and factory functions.

This module extends the core DynamicFormatter with optional performance
monitoring and provides factory functions for common deployment scenarios.
"""

import time
from typing import Dict, Any, Optional, Tuple, Union
from pathlib import Path

from .dynamic_formatting import DynamicFormatter as BaseDynamicFormatter
from .config import FormatterConfig
from .performance_monitor import PerformanceMonitor, create_production_monitor, create_development_monitor


class DynamicFormatter(BaseDynamicFormatter):
    """
    Enhanced DynamicFormatter with optional performance monitoring
    
    Extends the base formatter with optional performance tracking for
    production observability and development debugging.
    """
    
    def __init__(self, format_string: str, config: Optional[FormatterConfig] = None, 
                 performance_monitor: Optional[PerformanceMonitor] = None, **kwargs):
        """
        Initialize enhanced formatter
        
        Args:
            format_string: Template string
            config: Configuration object
            performance_monitor: Optional performance monitor
            **kwargs: Legacy parameters for backward compatibility
        """
        super().__init__(format_string, config, **kwargs)
        self.performance_monitor = performance_monitor
    
    def format(self, *args, **kwargs) -> str:
        """
        Format with optional performance monitoring
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Formatted string
        """
        if self.performance_monitor and self.performance_monitor.enabled:
            with self.performance_monitor.track('format_operation'):
                return super().format(*args, **kwargs)
        else:
            return super().format(*args, **kwargs)
    
    def format_with_detailed_tracking(self, *args, **kwargs) -> Tuple[str, Optional[Dict[str, Any]]]:
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
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get current performance statistics
        
        Returns:
            Dictionary of performance statistics
        """
        if self.performance_monitor:
            return self.performance_monitor.get_stats('format_operation')
        return {}


def create_production_formatter(
    template: str,
    functions: Optional[Dict[str, Any]] = None,
    monitor_slow_operations: bool = False,
    monitor_memory_usage: bool = False,
    baseline_duration_ms: float = 50.0,
    **config_overrides
) -> DynamicFormatter:
    """
    Create a formatter optimized for production use
    
    Args:
        template: Format template string
        functions: Optional function registry
        monitor_slow_operations: Enable performance monitoring
        monitor_memory_usage: Enable memory usage tracking
        baseline_duration_ms: Expected baseline performance
        **config_overrides: Additional configuration options
        
    Returns:
        Production-ready DynamicFormatter instance
    """
    # Create production configuration
    config = FormatterConfig.production(
        functions=functions or {},
        enable_performance_monitoring=monitor_slow_operations or monitor_memory_usage,
        **config_overrides
    )
    
    # Create performance monitor if requested
    performance_monitor = None
    if monitor_slow_operations or monitor_memory_usage:
        performance_monitor = create_production_monitor(
            baseline_duration_ms=baseline_duration_ms,
            log_slow_operations=monitor_slow_operations,
            log_memory_usage=monitor_memory_usage
        )
    
    return DynamicFormatter(
        template, 
        config=config, 
        performance_monitor=performance_monitor
    )


def create_development_formatter(
    template: str,
    functions: Optional[Dict[str, Any]] = None,
    enable_monitoring: bool = True,
    **config_overrides
) -> DynamicFormatter:
    """
    Create a formatter optimized for development use
    
    Args:
        template: Format template string
        functions: Optional function registry
        enable_monitoring: Enable performance monitoring
        **config_overrides: Additional configuration options
        
    Returns:
        Development-ready DynamicFormatter instance
    """
    # Create development configuration
    config = FormatterConfig.development(
        functions=functions or {},
        enable_performance_monitoring=enable_monitoring,
        **config_overrides
    )
    
    # Create performance monitor for development
    performance_monitor = None
    if enable_monitoring:
        performance_monitor = create_development_monitor()
    
    return DynamicFormatter(
        template, 
        config=config, 
        performance_monitor=performance_monitor
    )