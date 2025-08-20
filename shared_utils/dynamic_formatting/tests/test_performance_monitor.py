"""
Comprehensive test suite for performance monitoring system.

Tests cover monitoring functionality, integration with DynamicFormatter,
performance regression detection, and edge cases.
"""

import pytest
import time
import tempfile
import json
import threading
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add project root to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared_utils.dynamic_formatting.performance_monitor import (
    PerformanceMonitor, 
    PerformanceMetrics, 
    PerformanceStats,
    create_production_monitor
)
from shared_utils.dynamic_formatting.enhanced_formatter import (
    DynamicFormatter, create_production_formatter, create_development_formatter
)


class TestPerformanceMetrics:
    """Test the PerformanceMetrics dataclass."""
    
    def test_metrics_creation(self):
        """Test creating performance metrics."""
        metrics = PerformanceMetrics(
            operation_name="test_op",
            start_time=1.0,
            end_time=2.0,
            duration=1.0,
            memory_before=100.0,
            memory_after=105.0,
            memory_peak=110.0
        )
        
        assert metrics.operation_name == "test_op"
        assert metrics.duration == 1.0
        assert metrics.memory_used == 5.0
        assert metrics.memory_peak_delta == 10.0
    
    def test_metrics_serialization(self):
        """Test metrics to dictionary conversion."""
        metrics = PerformanceMetrics(
            operation_name="serialize_test",
            start_time=1000.0,
            end_time=1001.5,
            duration=1.5,
            memory_before=50.0,
            memory_after=55.0,
            memory_peak=60.0
        )
        
        data = metrics.to_dict()
        
        assert data['operation_name'] == "serialize_test"
        assert data['duration_ms'] == 1500.0
        assert data['memory_used_mb'] == 5.0
        assert data['memory_peak_delta_mb'] == 10.0
        assert 'timestamp' in data
        assert 'thread_id' in data


class TestPerformanceStats:
    """Test the PerformanceStats aggregation class."""
    
    def test_stats_aggregation(self):
        """Test adding metrics to stats."""
        stats = PerformanceStats("test_operation")
        
        # Add first metrics
        metrics1 = PerformanceMetrics(
            operation_name="test_operation",
            start_time=1.0,
            end_time=2.0,
            duration=1.0,
            memory_before=100.0,
            memory_after=105.0,
            memory_peak=110.0
        )
        stats.add_metrics(metrics1)
        
        assert stats.total_calls == 1
        assert stats.total_duration == 1.0
        assert stats.min_duration == 1.0
        assert stats.max_duration == 1.0
        assert stats.avg_duration == 1.0
        
        # Add second metrics
        metrics2 = PerformanceMetrics(
            operation_name="test_operation",
            start_time=3.0,
            end_time=5.0,
            duration=2.0,
            memory_before=100.0,
            memory_after=107.0,
            memory_peak=112.0
        )
        stats.add_metrics(metrics2)
        
        assert stats.total_calls == 2
        assert stats.total_duration == 3.0
        assert stats.min_duration == 1.0
        assert stats.max_duration == 2.0
        assert stats.avg_duration == 1.5
        assert stats.avg_memory_usage == 6.0  # (5 + 7) / 2
    
    def test_stats_serialization(self):
        """Test stats to dictionary conversion."""
        stats = PerformanceStats("serialize_op")
        
        metrics = PerformanceMetrics(
            operation_name="serialize_op",
            start_time=1.0,
            end_time=1.5,
            duration=0.5,
            memory_before=100.0,
            memory_after=103.0,
            memory_peak=105.0
        )
        stats.add_metrics(metrics)
        
        data = stats.to_dict()
        
        assert data['operation_name'] == "serialize_op"
        assert data['total_calls'] == 1
        assert data['avg_duration_ms'] == 500.0
        assert data['calls_per_second'] == 2.0  # 1 call / 0.5 seconds


class TestPerformanceMonitor:
    """Test the main PerformanceMonitor class."""
    
    def test_monitor_disabled(self):
        """Test that disabled monitor doesn't track anything."""
        monitor = PerformanceMonitor(enabled=False)
        
        with monitor.track("test_operation"):
            time.sleep(0.001)
        
        stats = monitor.get_stats()
        assert len(stats) == 0
    
    def test_basic_tracking(self):
        """Test basic operation tracking."""
        monitor = PerformanceMonitor(enabled=True, auto_log_stats=False)
        
        with monitor.track("basic_test"):
            time.sleep(0.01)  # 10ms delay
        
        stats = monitor.get_stats("basic_test")
        assert stats['operation_name'] == "basic_test"
        assert stats['total_calls'] == 1
        assert stats['avg_duration_ms'] >= 10.0  # Should be at least 10ms
    
    def test_multiple_operations(self):
        """Test tracking multiple different operations."""
        monitor = PerformanceMonitor(enabled=True, auto_log_stats=False)
        
        # Track different operations
        with monitor.track("operation_a"):
            time.sleep(0.005)
        
        with monitor.track("operation_b"):
            time.sleep(0.002)
        
        with monitor.track("operation_a"):
            time.sleep(0.003)
        
        all_stats = monitor.get_stats()
        assert len(all_stats) == 2
        
        op_a_stats = monitor.get_stats("operation_a")
        op_b_stats = monitor.get_stats("operation_b")
        
        assert op_a_stats['total_calls'] == 2
        assert op_b_stats['total_calls'] == 1
    
    def test_threshold_logging(self, caplog):
        """Test that slow operations are logged."""
        monitor = PerformanceMonitor(
            enabled=True,
            log_threshold_ms=5.0,  # 5ms threshold
            auto_log_stats=False
        )
        
        # Fast operation - shouldn't log
        with monitor.track("fast_operation"):
            pass
        
        # Slow operation - should log
        with monitor.track("slow_operation"):
            time.sleep(0.01)  # 10ms - above threshold
        
        # Check that warning was logged for slow operation
        assert any("Slow operation detected" in record.message for record in caplog.records)
        assert any("slow_operation" in record.message for record in caplog.records)
    
    def test_regression_detection(self, caplog):
        """Test performance regression detection."""
        monitor = PerformanceMonitor(
            enabled=True,
            regression_threshold=2.0,  # Alert if 2x slower
            auto_log_stats=False
        )
        
        # Set baseline
        monitor.set_baseline("regression_test", 0.001)  # 1ms baseline
        
        # Operation within baseline - shouldn't alert
        with monitor.track("regression_test"):
            time.sleep(0.001)
        
        # Operation that exceeds regression threshold - should alert
        with monitor.track("regression_test"):
            time.sleep(0.003)  # 3ms - 3x baseline
        
        # Check that regression was detected
        assert any("Performance regression detected" in record.message for record in caplog.records)
    
    def test_stats_export(self):
        """Test exporting stats to file."""
        monitor = PerformanceMonitor(enabled=True, auto_log_stats=False)
        
        # Generate some stats
        with monitor.track("export_test"):
            time.sleep(0.001)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            monitor.export_stats(export_path)
            
            # Read and verify exported data
            with open(export_path, 'r') as f:
                data = json.load(f)
            
            assert 'timestamp' in data
            assert 'total_operations' in data
            assert 'operations' in data
            assert len(data['operations']) == 1
            assert data['operations'][0]['operation_name'] == 'export_test'
        
        finally:
            Path(export_path).unlink()
    
    def test_thread_safety(self):
        """Test that monitor works correctly with multiple threads."""
        monitor = PerformanceMonitor(enabled=True, auto_log_stats=False)
        results = []
        
        def worker(worker_id):
            for i in range(10):
                with monitor.track(f"worker_{worker_id}"):
                    time.sleep(0.001)
            results.append(worker_id)
        
        # Run multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all workers completed
        assert sorted(results) == [0, 1, 2]
        
        # Verify stats were collected correctly
        all_stats = monitor.get_stats()
        assert len(all_stats) == 3  # One stat per worker
        
        for i in range(3):
            worker_stats = monitor.get_stats(f"worker_{i}")
            assert worker_stats['total_calls'] == 10


class TestDynamicFormatterIntegration:
    """Test integration of performance monitoring with DynamicFormatter."""
    
    def test_formatter_without_monitor(self):
        """Test that formatter works normally without monitor."""
        formatter = DynamicFormatter("{{Hello ;name}}")
        result = formatter.format(name="World")
        assert result == "Hello World"
        assert formatter.performance_monitor is None
    
    def test_formatter_with_monitor(self):
        """Test formatter with performance monitoring enabled."""
        monitor = PerformanceMonitor(enabled=True, auto_log_stats=False)
        formatter = DynamicFormatter("{{Hello ;name}}", performance_monitor=monitor)
        
        result = formatter.format(name="World")
        assert result == "Hello World"
        
        # Verify monitoring occurred
        stats = monitor.get_stats("format_operation")
        assert stats['total_calls'] == 1
    
    def test_detailed_tracking(self):
        """Test detailed performance tracking."""
        monitor = PerformanceMonitor(enabled=True, auto_log_stats=False)
        formatter = DynamicFormatter("{{Processing ;item}}", performance_monitor=monitor)
        
        result, metrics = formatter.format_with_detailed_tracking(item="test_data")
        
        assert result == "Processing test_data"
        assert metrics is not None
        assert metrics['operation_name'] == 'detailed_format_operation'
        assert metrics['total_calls'] == 1
    
    def test_production_formatter_creation(self):
        """Test creating production formatter with monitoring."""
        formatter = create_production_formatter(
            template="{{app}}: {{message}}",
            monitor_slow_operations=True,
            monitor_memory_usage=True
        )
        
        assert formatter.performance_monitor is not None
        assert formatter.performance_monitor.enabled is True
        
        result = formatter.format(app="test-app", message="test message")
        assert result == "test-app: test message"
        
        # Should have tracked the operation
        stats = formatter.get_performance_stats()
        assert len(stats) == 1
    
    def test_development_formatter_creation(self):
        """Test creating development formatter with monitoring."""
        formatter = create_development_formatter("{{Debug: ;value}}")
        
        assert formatter.performance_monitor is not None
        assert formatter.performance_monitor.log_threshold_ms == 10.0  # Stricter threshold
        
        result = formatter.format(value="test")
        assert result == "Debug: test"


class TestProductionScenarios:
    """Test real-world production scenarios."""
    
    def test_high_volume_operations(self):
        """Test monitoring under high operation volume."""
        monitor = PerformanceMonitor(
            enabled=True,
            auto_log_stats=True,
            log_stats_interval=100,
            log_threshold_ms=float('inf')  # Don't log individual slow ops
        )
        
        formatter = DynamicFormatter(
            "{{id}}: {{status}}",
            performance_monitor=monitor
        )
        
        # Simulate high volume
        operation_count = 1000
        for i in range(operation_count):
            result = formatter.format(id=f"REQ-{i:04d}", status="PROCESSED")
        
        stats = monitor.get_stats("format_operation")
        assert stats['total_calls'] == operation_count
        assert stats['calls_per_second'] > 100  # Should be quite fast
    
    def test_memory_monitoring_accuracy(self):
        """Test that memory monitoring detects actual memory usage."""
        monitor = PerformanceMonitor(
            enabled=True,
            memory_threshold_mb=0.1,  # Very low threshold
            auto_log_stats=False
        )
        
        # Create formatter that might use more memory
        large_functions = {f"func_{i}": lambda x: "x" * 1000 for i in range(100)}
        formatter = DynamicFormatter(
            "{{data}}",
            functions=large_functions,
            performance_monitor=monitor
        )
        
        # Format with large data
        large_data = "x" * 10000  # 10KB string
        result = formatter.format(data=large_data)
        
        stats = monitor.get_stats("format_operation")
        # Memory usage should be detected (though exact values depend on Python internals)
        assert 'avg_memory_usage_mb' in stats
    
    @patch('logging.Logger.warning')
    def test_alerting_integration(self, mock_logger):
        """Test integration with alerting systems."""
        monitor = PerformanceMonitor(
            enabled=True,
            log_threshold_ms=1.0,  # Very strict
            memory_threshold_mb=0.1,
            auto_log_stats=False
        )
        
        formatter = DynamicFormatter("{{test}}", performance_monitor=monitor)
        
        # Trigger slow operation alert
        with monitor.track("manual_slow_operation"):
            time.sleep(0.005)  # 5ms - above 1ms threshold
        
        # Verify logging was called
        mock_logger.assert_called()
        call_args = mock_logger.call_args[0][0]
        assert "Slow operation detected" in call_args


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_monitor_with_exceptions(self):
        """Test that monitor handles exceptions in tracked code."""
        monitor = PerformanceMonitor(enabled=True, auto_log_stats=False)
        
        with pytest.raises(ValueError):
            with monitor.track("exception_test"):
                raise ValueError("Test exception")
        
        # Should still record metrics even when exception occurs
        stats = monitor.get_stats("exception_test")
        assert stats['total_calls'] == 1
    
    def test_concurrent_access(self):
        """Test concurrent access to monitor doesn't cause issues."""
        monitor = PerformanceMonitor(enabled=True, auto_log_stats=False)
        
        def concurrent_worker():
            for _ in range(100):
                with monitor.track("concurrent_test"):
                    pass
        
        # Run multiple threads concurrently
        threads = [threading.Thread(target=concurrent_worker) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        stats = monitor.get_stats("concurrent_test")
        assert stats['total_calls'] == 500  # 5 threads * 100 operations each
    
    def test_very_fast_operations(self):
        """Test monitoring of very fast operations."""
        monitor = PerformanceMonitor(enabled=True, auto_log_stats=False)
        
        # Very fast operations
        for _ in range(1000):
            with monitor.track("fast_op"):
                pass  # Essentially instantaneous
        
        stats = monitor.get_stats("fast_op")
        assert stats['total_calls'] == 1000
        assert stats['avg_duration_ms'] >= 0  # Should be positive, even if very small
    
    @patch('psutil.Process')
    def test_memory_monitoring_failure(self, mock_process):
        """Test graceful handling when memory monitoring fails."""
        # Make memory monitoring fail
        mock_process.return_value.memory_info.side_effect = Exception("Memory access failed")
        
        monitor = PerformanceMonitor(enabled=True, auto_log_stats=False)
        
        # Should not raise exception, should gracefully handle failure
        with monitor.track("memory_fail_test"):
            pass
        
        stats = monitor.get_stats("memory_fail_test")
        assert stats['total_calls'] == 1
        # Memory stats should be 0 or not cause errors
        assert 'avg_memory_usage_mb' in stats


if __name__ == "__main__":
    """Run the test suite."""
    pytest.main([__file__, "-v"])