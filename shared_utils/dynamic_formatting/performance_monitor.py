"""
Performance monitoring system for DynamicFormatter.

Provides comprehensive performance tracking including timing, memory usage,
call counts, and performance regression detection for production environments.
"""

import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
from collections import defaultdict, deque
import json
import logging
from pathlib import Path
from statistics import mean, median, stdev


@dataclass
class PerformanceMetrics:
    """Container for performance measurement data."""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_before: float
    memory_after: float
    memory_peak: float
    call_count: int = 1
    thread_id: int = field(default_factory=lambda: threading.get_ident())
    
    @property
    def memory_used(self) -> float:
        """Memory used during operation (MB)."""
        return self.memory_after - self.memory_before
    
    @property
    def memory_peak_delta(self) -> float:
        """Peak memory above starting point (MB)."""
        return self.memory_peak - self.memory_before
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            'operation_name': self.operation_name,
            'duration_ms': self.duration * 1000,
            'memory_used_mb': self.memory_used,
            'memory_peak_delta_mb': self.memory_peak_delta,
            'call_count': self.call_count,
            'timestamp': self.start_time,
            'thread_id': self.thread_id
        }


@dataclass
class PerformanceStats:
    """Aggregated statistics for an operation type."""
    operation_name: str
    total_calls: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    durations: deque = field(default_factory=lambda: deque(maxlen=1000))  # Keep last 1000
    memory_usage: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def add_metrics(self, metrics: PerformanceMetrics) -> None:
        """Add new metrics to the aggregated stats."""
        self.total_calls += metrics.call_count
        self.total_duration += metrics.duration
        self.min_duration = min(self.min_duration, metrics.duration)
        self.max_duration = max(self.max_duration, metrics.duration)
        self.durations.append(metrics.duration)
        self.memory_usage.append(metrics.memory_used)
    
    @property
    def avg_duration(self) -> float:
        """Average duration per call."""
        return self.total_duration / self.total_calls if self.total_calls > 0 else 0.0
    
    @property
    def recent_avg_duration(self) -> float:
        """Average duration of recent calls."""
        return mean(self.durations) if self.durations else 0.0
    
    @property
    def duration_std(self) -> float:
        """Standard deviation of recent durations."""
        return stdev(self.durations) if len(self.durations) > 1 else 0.0
    
    @property
    def avg_memory_usage(self) -> float:
        """Average memory usage per call."""
        return mean(self.memory_usage) if self.memory_usage else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for reporting."""
        return {
            'operation_name': self.operation_name,
            'total_calls': self.total_calls,
            'avg_duration_ms': self.avg_duration * 1000,
            'recent_avg_duration_ms': self.recent_avg_duration * 1000,
            'min_duration_ms': self.min_duration * 1000 if self.min_duration != float('inf') else 0,
            'max_duration_ms': self.max_duration * 1000,
            'duration_std_ms': self.duration_std * 1000,
            'avg_memory_usage_mb': self.avg_memory_usage,
            'calls_per_second': self.total_calls / self.total_duration if self.total_duration > 0 else 0
        }


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for DynamicFormatter.
    
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
        stats_data = {
            'timestamp': time.time(),
            'total_operations': self._operation_count,
            'operations': self.get_stats()
        }
        
        with open(filepath, 'w') as f:
            json.dump(stats_data, f, indent=2)
        
        self.logger.info(f"Performance stats exported to {filepath}")
    
    @contextmanager
    def track(self, operation_name: str):
        """
        Context manager for tracking operation performance.
        
        Usage:
            with monitor.track('format_operation'):
                result = formatter.format(...)
        """
        if not self.enabled:
            yield
            return
        
        # Memory tracking with error handling
        try:
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            memory_peak = memory_before
        except Exception:
            # Fallback if memory monitoring fails
            memory_before = 0.0
            memory_peak = 0.0
        
        start_time = time.perf_counter()
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            
            # Get final memory and peak during operation
            try:
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                # Peak memory is approximated - in production, you'd use more sophisticated monitoring
                memory_peak = max(memory_before, memory_after)
            except Exception:
                # Fallback if process monitoring fails
                memory_after = memory_before
                memory_peak = memory_before
            
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=memory_peak
            )
            
            self._record_metrics(metrics)
    
    def _record_metrics(self, metrics: PerformanceMetrics) -> None:
        """Record performance metrics and check for issues."""
        with self._lock:
            # Update aggregated stats
            if metrics.operation_name not in self._stats:
                self._stats[metrics.operation_name] = PerformanceStats(metrics.operation_name)
            
            self._stats[metrics.operation_name].add_metrics(metrics)
            self._operation_count += 1
            
            # Check for performance issues
            self._check_thresholds(metrics)
            self._check_regression(metrics)
            
            # Auto-log stats periodically
            if self.auto_log_stats and self._operation_count % self.log_stats_interval == 0:
                self._log_aggregated_stats()
    
    def _check_thresholds(self, metrics: PerformanceMetrics) -> None:
        """Check if operation exceeded performance thresholds."""
        duration_ms = metrics.duration * 1000
        memory_mb = metrics.memory_used
        
        if duration_ms > self.log_threshold_ms:
            self.logger.warning(
                f"Slow operation detected: {metrics.operation_name} "
                f"took {duration_ms:.1f}ms (threshold: {self.log_threshold_ms}ms)"
            )
        
        if memory_mb > self.memory_threshold_mb:
            self.logger.warning(
                f"High memory usage: {metrics.operation_name} "
                f"used {memory_mb:.1f}MB (threshold: {self.memory_threshold_mb}MB)"
            )
    
    def _check_regression(self, metrics: PerformanceMetrics) -> None:
        """Check for performance regression against baseline."""
        operation_name = metrics.operation_name
        
        if operation_name in self._baseline_performance:
            baseline = self._baseline_performance[operation_name]
            current = metrics.duration
            
            if current > baseline * self.regression_threshold:
                self.logger.error(
                    f"Performance regression detected: {operation_name} "
                    f"is {current/baseline:.1f}x slower than baseline "
                    f"({current*1000:.1f}ms vs {baseline*1000:.1f}ms)"
                )
    
    def _log_aggregated_stats(self) -> None:
        """Log aggregated performance statistics."""
        with self._lock:
            stats_summary = []
            for stats in self._stats.values():
                stats_summary.append(
                    f"{stats.operation_name}: "
                    f"{stats.total_calls} calls, "
                    f"avg {stats.recent_avg_duration*1000:.1f}ms, "
                    f"{stats.avg_memory_usage:.1f}MB"
                )
            
            if stats_summary:
                self.logger.info(
                    f"Performance Summary (after {self._operation_count} operations): "
                    f"{'; '.join(stats_summary)}"
                )
    
    def log_current_stats(self) -> None:
        """Manually trigger logging of current statistics."""
        self._log_aggregated_stats()


# Convenience function for creating production-ready monitor
def create_production_monitor(
    log_slow_operations: bool = True,
    log_memory_usage: bool = True,
    detect_regressions: bool = True,
    export_stats_path: Optional[str] = None
) -> PerformanceMonitor:
    """
    Create a performance monitor configured for production use.
    
    Args:
        log_slow_operations: Log operations slower than 50ms
        log_memory_usage: Log operations using more than 5MB
        detect_regressions: Enable performance regression detection
        export_stats_path: Optional path to export stats periodically
        
    Returns:
        Configured PerformanceMonitor instance
    """
    monitor = PerformanceMonitor(
        enabled=True,
        log_threshold_ms=50.0 if log_slow_operations else float('inf'),
        memory_threshold_mb=5.0 if log_memory_usage else float('inf'),
        regression_threshold=1.5 if detect_regressions else float('inf'),
        auto_log_stats=True,
        log_stats_interval=500  # More frequent logging in production
    )
    
    if export_stats_path:
        # In production, you'd set up periodic export (e.g., every hour)
        # This is just a demonstration
        import atexit
        atexit.register(lambda: monitor.export_stats(export_stats_path))
    
    return monitor