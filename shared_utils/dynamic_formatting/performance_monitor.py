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

# Optional psutil import for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class PerformanceMetrics:
    """Individual operation performance metrics"""
    operation_name: str
    duration_ms: float
    memory_usage_mb: float
    timestamp: float
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    memory_peak: Optional[float] = None
    
    def __post_init__(self):
        """Calculate derived values if not provided"""
        if self.start_time is not None and self.end_time is not None:
            self.duration = self.end_time - self.start_time
        if self.memory_before is not None and self.memory_after is not None:
            self.memory_used = self.memory_after - self.memory_before
        if self.memory_peak is not None and self.memory_before is not None:
            self.memory_peak_delta = self.memory_peak - self.memory_before
    
    @property
    def duration(self) -> float:
        """Duration in seconds"""
        return self.duration_ms / 1000.0
    
    @duration.setter
    def duration(self, value: float):
        """Set duration in seconds"""
        self.duration_ms = value * 1000.0
    
    @property
    def memory_used(self) -> float:
        """Memory used in MB"""
        return getattr(self, '_memory_used', 0.0)
    
    @memory_used.setter
    def memory_used(self, value: float):
        """Set memory used in MB"""
        self._memory_used = value
    
    @property
    def memory_peak_delta(self) -> float:
        """Peak memory delta in MB"""
        return getattr(self, '_memory_peak_delta', 0.0)
    
    @memory_peak_delta.setter
    def memory_peak_delta(self, value: float):
        """Set peak memory delta in MB"""
        self._memory_peak_delta = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        data = asdict(self)
        data['duration_s'] = self.duration
        data['memory_used_mb'] = self.memory_used
        data['memory_peak_delta_mb'] = self.memory_peak_delta
        data['thread_id'] = threading.get_ident()
        return data


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
    
    def add_metrics(self, metrics: PerformanceMetrics) -> None:
        """Add metrics to statistics (alias for update)"""
        self.update(metrics)
    
    @property
    def calls_per_second(self) -> float:
        """Calculate calls per second"""
        if self.total_duration_ms == 0:
            return 0.0
        return (self.total_calls * 1000.0) / self.total_duration_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary"""
        data = asdict(self)
        data['calls_per_second'] = self.calls_per_second
        return data


class OperationTracker:
    """Context manager for tracking individual operations"""
    
    def __init__(self, monitor: 'PerformanceMonitor', operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
        self.start_memory = None
        self.metrics = None
    
    def __enter__(self):
        if not self.monitor.enabled:
            return self
        
        self.start_time = time.time()
        self.start_memory = self.monitor._get_memory_usage()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.monitor.enabled:
            return
        
        end_time = time.time()
        end_memory = self.monitor._get_memory_usage()
        
        duration_ms = (end_time - self.start_time) * 1000
        memory_usage_mb = end_memory - self.start_memory if self.start_memory else 0.0
        
        self.metrics = PerformanceMetrics(
            operation_name=self.operation_name,
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            timestamp=end_time,
            start_time=self.start_time,
            end_time=end_time,
            memory_before=self.start_memory,
            memory_after=end_memory
        )
        
        self.monitor._record_metrics(self.metrics)
    
    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get metrics from this tracker"""
        if self.metrics:
            return self.metrics.to_dict()
        return None


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
                # your operation here
                pass
        """
        tracker = OperationTracker(self, operation_name)
        try:
            yield tracker
        finally:
            pass
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if not PSUTIL_AVAILABLE:
            return 0.0
        
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except Exception:
            return 0.0
    
    def _record_metrics(self, metrics: PerformanceMetrics) -> None:
        """Record metrics and update statistics."""
        with self._lock:
            self._operation_count += 1
            
            # Update statistics
            if metrics.operation_name not in self._stats:
                self._stats[metrics.operation_name] = PerformanceStats(metrics.operation_name)
            
            self._stats[metrics.operation_name].update(metrics)
            
            # Check thresholds
            self._check_thresholds(metrics)
            
            # Auto-log stats if configured
            if (self.auto_log_stats and 
                self.log_stats_interval > 0 and 
                self._operation_count % self.log_stats_interval == 0):
                self._log_aggregated_stats()
    
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
    
    def get_stats(self, operation_name: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get performance statistics.
        
        Args:
            operation_name: Specific operation to get stats for, or None for all
            
        Returns:
            Dictionary for specific operation or list of all stats
        """
        with self._lock:
            if operation_name:
                if operation_name in self._stats:
                    return self._stats[operation_name].to_dict()
                else:
                    return {}
            else:
                return [stats.to_dict() for stats in self._stats.values()]
    
    def export_stats(self, output_path: Union[str, Path]) -> None:
        """
        Export statistics to JSON file.
        
        Args:
            output_path: Path to write JSON file
        """
        output_path = Path(output_path)
        
        export_data = {
            'timestamp': time.time(),
            'total_operations': self._operation_count,
            'statistics': self.get_stats()
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def reset_stats(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self._stats.clear()
            self._operation_count = 0


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
        regression_threshold: Factor that indicates performance regression
        log_slow_operations: Whether to log slow operations
        log_memory_usage: Whether to log high memory usage
        detect_regressions: Whether to detect performance regressions
        export_stats_path: Path to export stats to (optional)
        
    Returns:
        Configured PerformanceMonitor instance
    """
    monitor = PerformanceMonitor(
        enabled=True,
        log_threshold_ms=baseline_duration_ms * 2,  # Alert at 2x baseline
        memory_threshold_mb=baseline_memory_mb * 2,  # Alert at 2x baseline
        regression_threshold=regression_threshold,
        auto_log_stats=True,
        log_stats_interval=10000  # Less frequent logging in production
    )
    
    # Set baseline for 'format_operation'
    monitor.set_baseline('format_operation', baseline_duration_ms)
    
    return monitor


def create_development_monitor(**kwargs) -> PerformanceMonitor:
    """
    Create a performance monitor configured for development use.
    
    Returns:
        Configured PerformanceMonitor instance with development-friendly settings
    """
    defaults = {
        'enabled': True,
        'log_threshold_ms': 10.0,  # More sensitive in development
        'memory_threshold_mb': 1.0,  # More sensitive in development
        'regression_threshold': 1.5,  # Catch smaller regressions
        'auto_log_stats': True,
        'log_stats_interval': 100  # More frequent logging in development
    }
    defaults.update(kwargs)
    
    return PerformanceMonitor(**defaults)