"""
Performance monitoring for dynamic formatting operations.

Provides comprehensive performance tracking with timing, memory usage monitoring,
and regression detection for production observability.
"""

import time
import logging
import threading
import json
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class PerformanceMetrics:
    """Individual operation performance metrics"""
    operation_name: str
    duration_ms: float
    memory_usage_mb: float
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return asdict(self)


@dataclass
class PerformanceStats:
    """Aggregated performance statistics"""
    operation_name: str
    total_calls: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    total_memory_usage_mb: float = 0.0
    avg_memory_usage_mb: float = 0.0
    min_memory_usage_mb: float = float('inf')
    max_memory_usage_mb: float = 0.0
    
    def update(self, metrics: PerformanceMetrics) -> None:
        """Update statistics with new metrics"""
        self.total_calls += 1
        self.total_duration_ms += metrics.duration_ms
        self.avg_duration_ms = self.total_duration_ms / self.total_calls
        self.min_duration_ms = min(self.min_duration_ms, metrics.duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, metrics.duration_ms)
        
        self.total_memory_usage_mb += metrics.memory_usage_mb
        self.avg_memory_usage_mb = self.total_memory_usage_mb / self.total_calls
        self.min_memory_usage_mb = min(self.min_memory_usage_mb, metrics.memory_usage_mb)
        self.max_memory_usage_mb = max(self.max_memory_usage_mb, metrics.memory_usage_mb)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary"""
        return asdict(self)


class PerformanceMonitor:
    """
    Thread-safe performance monitor for dynamic formatting operations.
    
    Tracks timing, memory usage, call counts, and provides performance
    regression detection with configurable alerting thresholds.
    """
    
    def __init__(
        self, 
        enabled: bool = True,
        log_threshold_ms: float = 100.0,
        memory_threshold_mb: float = 10.0,
        regression_threshold: float = 2.0,
        auto_log_stats: bool = True,
        log_stats_interval: int = 1000
    ):
        """
        Initialize performance monitor.
        
        Args:
            enabled: Whether monitoring is active
            log_threshold_ms: Log operations slower than this (milliseconds)
            memory_threshold_mb: Log operations using more memory than this (MB)
            regression_threshold: Alert when performance degrades by this multiplier
            auto_log_stats: Automatically log aggregated stats periodically
            log_stats_interval: Log stats every N operations
        """
        self.enabled = enabled
        self.log_threshold_ms = log_threshold_ms
        self.memory_threshold_mb = memory_threshold_mb
        self.regression_threshold = regression_threshold
        self.auto_log_stats = auto_log_stats
        self.log_stats_interval = log_stats_interval
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._stats: Dict[str, PerformanceStats] = {}
        self._operation_count = 0
        
        # Performance regression tracking
        self._baseline_performance: Dict[str, float] = {}
        
        # Logger for performance metrics
        self.logger = logging.getLogger(f"{__name__}.PerformanceMonitor")
    
    def set_baseline(self, operation_name: str, baseline_duration: float) -> None:
        """Set baseline performance for regression detection."""
        with self._lock:
            self._baseline_performance[operation_name] = baseline_duration
    
    @contextmanager
    def track(self, operation_name: str):
        """
        Context manager for tracking operation performance.
        
        Usage:
            with monitor.track('format_operation'):
                result = formatter.format(**data)
        """
        if not self.enabled:
            yield
            return
        
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()
            
            # Calculate metrics
            duration_ms = (end_time - start_time) * 1000
            memory_usage_mb = max(0, end_memory - start_memory)  # Memory increase
            
            # Create metrics object
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                duration_ms=duration_ms,
                memory_usage_mb=memory_usage_mb,
                timestamp=time.time()
            )
            
            # Update statistics
            self._update_stats(metrics)
            
            # Check thresholds and log if necessary
            self._check_thresholds(metrics)
            
            # Auto-log aggregated stats if enabled
            if self.auto_log_stats:
                self._operation_count += 1
                if self._operation_count % self.log_stats_interval == 0:
                    self._log_aggregated_stats()
    
    def get_stats(self, operation_name: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get performance statistics."""
        with self._lock:
            if operation_name:
                return self._stats.get(operation_name, PerformanceStats(operation_name)).to_dict()
            return [stats.to_dict() for stats in self._stats.values()]
    
    def reset_stats(self, operation_name: Optional[str] = None) -> None:
        """Reset performance statistics."""
        with self._lock:
            if operation_name:
                if operation_name in self._stats:
                    del self._stats[operation_name]
            else:
                self._stats.clear()
                self._operation_count = 0
    
    def export_stats(self, filepath: Union[str, Path]) -> None:
        """Export performance statistics to JSON file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            stats_data = {
                'timestamp': time.time(),
                'total_operations': self._operation_count,
                'statistics': [stats.to_dict() for stats in self._stats.values()]
            }
        
        with open(filepath, 'w') as f:
            json.dump(stats_data, f, indent=2)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB (simplified implementation)."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            # Fallback if psutil not available
            return 0.0
    
    def _update_stats(self, metrics: PerformanceMetrics) -> None:
        """Update aggregated statistics with new metrics."""
        with self._lock:
            if metrics.operation_name not in self._stats:
                self._stats[metrics.operation_name] = PerformanceStats(metrics.operation_name)
            
            self._stats[metrics.operation_name].update(metrics)
    
    def _check_thresholds(self, metrics: PerformanceMetrics) -> None:
        """Check if metrics exceed configured thresholds."""
        # Check duration threshold
        if metrics.duration_ms > self.log_threshold_ms:
            self.logger.warning(
                f"Slow operation detected: {metrics.operation_name} "
                f"took {metrics.duration_ms:.2f}ms (threshold: {self.log_threshold_ms}ms)"
            )
        
        # Check memory threshold
        if metrics.memory_usage_mb > self.memory_threshold_mb:
            self.logger.warning(
                f"High memory usage detected: {metrics.operation_name} "
                f"used {metrics.memory_usage_mb:.2f}MB (threshold: {self.memory_threshold_mb}MB)"
            )
        
        # Check for performance regression
        if metrics.operation_name in self._baseline_performance:
            baseline = self._baseline_performance[metrics.operation_name]
            if metrics.duration_ms > baseline * self.regression_threshold:
                self.logger.error(
                    f"Performance regression detected: {metrics.operation_name} "
                    f"duration {metrics.duration_ms:.2f}ms vs baseline {baseline:.2f}ms "
                    f"(regression factor: {metrics.duration_ms / baseline:.2f}x)"
                )
    
    def _log_aggregated_stats(self) -> None:
        """Log aggregated performance statistics."""
        with self._lock:
            if not self._stats:
                return
            
            self.logger.info(f"Performance stats after {self._operation_count} operations:")
            for stats in self._stats.values():
                self.logger.info(
                    f"  {stats.operation_name}: "
                    f"{stats.total_calls} calls, "
                    f"avg {stats.avg_duration_ms:.2f}ms, "
                    f"range {stats.min_duration_ms:.2f}-{stats.max_duration_ms:.2f}ms"
                )


def create_production_monitor(
    baseline_duration_ms: float = 50.0,
    baseline_memory_mb: float = 10.0,
    regression_threshold: float = 2.0,
    log_slow_operations: bool = True,
    log_memory_usage: bool = True,
    detect_regressions: bool = True,
    export_stats_path: Optional[str] = None
) -> PerformanceMonitor:
    """
    Create a performance monitor configured for production use.
    
    Args:
        baseline_duration_ms: Expected baseline operation duration
        baseline_memory_mb: Expected baseline memory usage
        regression_threshold: Multiplier for regression detection
        log_slow_operations: Log operations slower than baseline
        log_memory_usage: Log operations using more memory than baseline
        detect_regressions: Enable performance regression detection
        export_stats_path: Optional path to export stats periodically
        
    Returns:
        Configured PerformanceMonitor instance
    """
    monitor = PerformanceMonitor(
        enabled=True,
        log_threshold_ms=baseline_duration_ms if log_slow_operations else float('inf'),
        memory_threshold_mb=baseline_memory_mb if log_memory_usage else float('inf'),
        regression_threshold=regression_threshold if detect_regressions else float('inf'),
        auto_log_stats=True,
        log_stats_interval=500  # More frequent logging in production
    )
    
    # Set baseline for common operations
    monitor.set_baseline('format_operation', baseline_duration_ms)
    monitor.set_baseline('template_compilation', baseline_duration_ms * 10)  # Compilation is slower
    
    if export_stats_path:
        # In production, you'd set up periodic export (e.g., every hour)
        # This is just a demonstration
        import atexit
        atexit.register(lambda: monitor.export_stats(export_stats_path))
    
    return monitor


def create_development_monitor() -> PerformanceMonitor:
    """
    Create a performance monitor configured for development use.
    
    More verbose logging and stricter thresholds for catching issues early.
    """
    return PerformanceMonitor(
        enabled=True,
        log_threshold_ms=10.0,  # Lower threshold for development
        memory_threshold_mb=1.0,  # Stricter memory monitoring
        regression_threshold=1.2,  # Tighter regression detection
        auto_log_stats=True,
        log_stats_interval=100  # More frequent stats in development
    )