"""
Comprehensive examples of performance monitoring usage.

Demonstrates various monitoring scenarios from development to production,
including custom monitoring, performance regression detection, and
integration with existing logging systems.
"""

import logging
import time
import json
from pathlib import Path
import sys
import os

# Add project root to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared_utils.dynamic_formatting.enhanced_formatter import (
    DynamicFormatter, create_production_formatter, create_development_formatter
)
from shared_utils.dynamic_formatting.performance_monitor import (
    PerformanceMonitor, create_production_monitor
)


def basic_monitoring_example():
    """Basic performance monitoring example."""
    print("=== Basic Performance Monitoring ===")
    
    # Create monitor
    monitor = PerformanceMonitor(
        enabled=True,
        log_threshold_ms=5.0,  # Log operations slower than 5ms
        memory_threshold_mb=1.0,  # Log operations using more than 1MB
        auto_log_stats=True,
        log_stats_interval=10  # Log stats every 10 operations
    )
    
    # Create formatter with monitoring
    formatter = DynamicFormatter(
        "{{#level_color@bold;[;level;]}} {{message}} {{?duration;(;duration;s)}}",
        performance_monitor=monitor
    )
    
    # Simulate some operations
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    for i in range(25):
        level = levels[i % 4]
        duration = i * 0.1 if i % 3 == 0 else None
        
        result = formatter.format(
            level=level,
            message=f"Processing item {i}",
            duration=duration
        )
        print(f"  {result}")
        
        # Add some processing delay to make timing visible
        time.sleep(0.001)
    
    # Get final stats
    stats = monitor.get_stats()
    print(f"\nFinal Performance Stats:")
    for stat in stats:
        print(f"  Operation: {stat['operation_name']}")
        print(f"    Total calls: {stat['total_calls']}")
        print(f"    Avg duration: {stat['avg_duration_ms']:.2f}ms")
        print(f"    Memory usage: {stat['avg_memory_usage_mb']:.2f}MB")
        print()


def production_monitoring_example():
    """Production-ready monitoring with alerting and export."""
    print("=== Production Monitoring Example ===")
    
    # Set up logging to see performance alerts
    logging.basicConfig(level=logging.INFO)
    
    # Create production formatter
    formatter = create_production_formatter(
        template="{{timestamp}} - {{#severity_color;[;severity;]}} {{service}}: {{message}}",
        monitor_slow_operations=True,
        monitor_memory_usage=True,
        export_stats_path="performance_stats.json"
    )
    
    # Set performance baseline (would come from benchmarking)
    formatter.performance_monitor.set_baseline('format_operation', 0.001)  # 1ms baseline
    
    # Simulate production load
    services = ['auth-service', 'payment-service', 'notification-service']
    severities = ['INFO', 'WARN', 'ERROR']
    
    print("Simulating production load...")
    for i in range(100):
        service = services[i % 3]
        severity = severities[i % 3]
        
        # Simulate occasional slow operation
        if i % 23 == 0:
            time.sleep(0.01)  # Simulate slow operation
        
        result = formatter.format(
            timestamp=f"2024-01-{20 + i//50:02d}T10:{i//10:02d}:{i%60:02d}",
            severity=severity,
            service=service,
            message=f"Processed request {i}"
        )
        
        if i < 5:  # Show first few results
            print(f"  {result}")
    
    # Export and display stats
    print("\nExporting performance statistics...")
    formatter.export_performance_stats("production_stats.json")
    
    stats = formatter.get_performance_stats()
    for stat in stats:
        print(f"\nProduction Performance Summary:")
        print(f"  Total operations: {stat['total_calls']}")
        print(f"  Average duration: {stat['recent_avg_duration_ms']:.3f}ms")
        print(f"  Throughput: {stat['calls_per_second']:.1f} ops/sec")
        print(f"  Memory efficiency: {stat['avg_memory_usage_mb']:.3f}MB per operation")


def development_monitoring_example():
    """Development monitoring with detailed tracking."""
    print("=== Development Monitoring Example ===")
    
    # Set up detailed logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Create development formatter with strict monitoring
    formatter = create_development_formatter(
        template="{{#highlight;Processing:}} {{item}} {{#progress_bar;[;progress;%]}}"
    )
    
    # Demonstrate detailed tracking
    for i in range(10):
        progress = (i + 1) * 10
        
        # Use detailed tracking for debugging
        result, metrics = formatter.format_with_detailed_tracking(
            item=f"Dataset_{i:03d}",
            progress=progress
        )
        
        print(f"  {result}")
        
        if metrics:
            print(f"    ↳ Took {metrics['duration_ms']:.3f}ms, "
                  f"used {metrics['memory_used_mb']:.3f}MB")


def custom_monitoring_example():
    """Custom monitoring for specific use cases."""
    print("=== Custom Monitoring Example ===")
    
    # Create custom monitor for specific requirements
    monitor = PerformanceMonitor(
        enabled=True,
        log_threshold_ms=1.0,  # Very strict threshold
        memory_threshold_mb=0.5,  # Strict memory threshold
        regression_threshold=1.1,  # Catch even small regressions
        auto_log_stats=False  # Manual stats logging
    )
    
    # Multiple formatters sharing the same monitor
    formatters = {
        'log': DynamicFormatter("{{timestamp}} {{message}}", performance_monitor=monitor),
        'error': DynamicFormatter("{{#red@bold;ERROR:}} {{message}}", performance_monitor=monitor),
        'success': DynamicFormatter("{{#green@bold;✓}} {{message}}", performance_monitor=monitor)
    }
    
    # Track different operation types
    operations = [
        ('log', {'timestamp': '10:30:15', 'message': 'System startup complete'}),
        ('error', {'message': 'Database connection failed'}),
        ('success', {'message': 'Backup completed successfully'}),
        ('log', {'timestamp': '10:30:16', 'message': 'Processing user request'}),
        ('error', {'message': 'Invalid authentication token'}),
        ('success', {'message': 'User profile updated'})
    ]
    
    for fmt_type, data in operations:
        result = formatters[fmt_type].format(**data)
        print(f"  {result}")
    
    # Manual stats reporting
    print("\nCustom Performance Analysis:")
    all_stats = monitor.get_stats()
    for stat in all_stats:
        print(f"  {stat['operation_name']}: "
              f"{stat['total_calls']} calls, "
              f"avg {stat['avg_duration_ms']:.3f}ms")


def performance_regression_example():
    """Demonstrate performance regression detection."""
    print("=== Performance Regression Detection ===")
    
    monitor = PerformanceMonitor(
        enabled=True,
        regression_threshold=1.5,  # Alert when 50% slower
        log_threshold_ms=float('inf'),  # Don't log slow operations, just regressions
        auto_log_stats=False
    )
    
    formatter = DynamicFormatter(
        "{{processing}} {{item_name}} - {{status}}",
        performance_monitor=monitor
    )
    
    # Establish baseline performance
    baseline_times = []
    for i in range(10):
        start = time.perf_counter()
        result = formatter.format(
            processing="Processing",
            item_name=f"item_{i}",
            status="completed"
        )
        baseline_times.append(time.perf_counter() - start)
    
    baseline_avg = sum(baseline_times) / len(baseline_times)
    monitor.set_baseline('format_operation', baseline_avg)
    
    print(f"Baseline performance established: {baseline_avg*1000:.3f}ms average")
    
    # Simulate performance regression
    print("Simulating performance regression...")
    for i in range(5):
        # Add artificial delay to simulate regression
        time.sleep(0.002)  # 2ms delay
        
        result = formatter.format(
            processing="Processing",
            item_name=f"slow_item_{i}",
            status="completed"
        )
        print(f"  {result}")


def monitoring_integration_example():
    """Integration with existing logging and monitoring systems."""
    print("=== Monitoring Integration Example ===")
    
    # Set up structured logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create monitor that integrates with your logging
    monitor = create_production_monitor(
        log_slow_operations=True,
        log_memory_usage=True,
        detect_regressions=True
    )
    
    # Create formatter for application logs
    log_formatter = DynamicFormatter(
        "{{app_name}} [{{level}}] {{message}} {{?user_id;user=;user_id}} {{?duration;(;duration;ms)}}",
        performance_monitor=monitor
    )
    
    # Simulate application logging with performance tracking
    app_logs = [
        {'app_name': 'user-service', 'level': 'INFO', 'message': 'User login successful', 'user_id': '12345', 'duration': 45},
        {'app_name': 'payment-service', 'level': 'WARN', 'message': 'Payment processing slow', 'duration': 1200},
        {'app_name': 'notification-service', 'level': 'INFO', 'message': 'Email sent successfully', 'user_id': '67890'},
        {'app_name': 'user-service', 'level': 'ERROR', 'message': 'Database timeout', 'duration': 5000},
        {'app_name': 'analytics-service', 'level': 'INFO', 'message': 'Report generated', 'duration': 2300}
    ]
    
    for log_data in app_logs:
        formatted_log = log_formatter.format(**log_data)
        print(f"  {formatted_log}")
    
    # Show how performance data can be integrated with external monitoring
    performance_data = monitor.get_stats()
    
    print("\nIntegration with monitoring systems:")
    print("Metrics that could be sent to Prometheus, DataDog, etc.:")
    for stat in performance_data:
        print(f"  dynamic_formatter_duration_ms{{operation='{stat['operation_name']}'}} {stat['recent_avg_duration_ms']:.3f}")
        print(f"  dynamic_formatter_memory_mb{{operation='{stat['operation_name']}'}} {stat['avg_memory_usage_mb']:.3f}")
        print(f"  dynamic_formatter_calls_total{{operation='{stat['operation_name']}'}} {stat['total_calls']}")


def benchmark_comparison_example():
    """Compare performance with and without monitoring."""
    print("=== Performance Impact Benchmark ===")
    
    template = "{{#level_color@bold;[;level;]}} {{message}} {{?details;(;details;)}}"
    
    # Benchmark without monitoring
    formatter_no_monitor = DynamicFormatter(template)
    
    start_time = time.perf_counter()
    for i in range(1000):
        result = formatter_no_monitor.format(
            level='INFO',
            message=f'Message {i}',
            details=f'Detail {i}' if i % 3 == 0 else None
        )
    no_monitor_time = time.perf_counter() - start_time
    
    # Benchmark with monitoring
    monitor = PerformanceMonitor(enabled=True, auto_log_stats=False)
    formatter_with_monitor = DynamicFormatter(template, performance_monitor=monitor)
    
    start_time = time.perf_counter()
    for i in range(1000):
        result = formatter_with_monitor.format(
            level='INFO',
            message=f'Message {i}',
            details=f'Detail {i}' if i % 3 == 0 else None
        )
    with_monitor_time = time.perf_counter() - start_time
    
    # Calculate overhead
    overhead_percent = ((with_monitor_time - no_monitor_time) / no_monitor_time) * 100
    
    print(f"Performance Impact Analysis (1000 operations):")
    print(f"  Without monitoring: {no_monitor_time*1000:.2f}ms total ({no_monitor_time*1000000/1000:.2f}μs per operation)")
    print(f"  With monitoring:    {with_monitor_time*1000:.2f}ms total ({with_monitor_time*1000000/1000:.2f}μs per operation)")
    print(f"  Monitoring overhead: {overhead_percent:.1f}%")
    
    if overhead_percent < 5:
        print("  ✓ Low overhead - suitable for production use")
    elif overhead_percent < 15:
        print("  ⚠ Moderate overhead - consider for non-critical paths")
    else:
        print("  ⚠ High overhead - use only for debugging")


def memory_leak_detection_example():
    """Demonstrate memory leak detection capabilities."""
    print("=== Memory Leak Detection Example ===")
    
    monitor = PerformanceMonitor(
        enabled=True,
        memory_threshold_mb=0.1,  # Very sensitive to memory changes
        auto_log_stats=False
    )
    
    # Simulate a memory leak scenario
    formatter = DynamicFormatter(
        "{{data}} - {{timestamp}}",
        performance_monitor=monitor
    )
    
    # Simulate operations that might accumulate memory
    accumulated_data = []
    for i in range(20):
        # Simulate memory accumulation (intentional "leak" for demo)
        if i > 10:
            accumulated_data.append("x" * 1000)  # Add 1KB each iteration
        
        result = formatter.format(
            data=f"Processing batch {i}",
            timestamp=f"2024-01-20T10:{i:02d}:00"
        )
        
        if i < 5 or i > 15:  # Show beginning and end
            print(f"  {result}")
    
    # Analyze memory usage trends
    stats = monitor.get_stats('format_operation')
    print(f"\nMemory Usage Analysis:")
    print(f"  Average memory per operation: {stats['avg_memory_usage_mb']:.3f}MB")
    print("  Note: In production, trend analysis would detect gradual memory increases")


def stress_test_example():
    """Stress test the monitoring system itself."""
    print("=== Monitoring System Stress Test ===")
    
    monitor = PerformanceMonitor(
        enabled=True,
        auto_log_stats=True,
        log_stats_interval=1000  # Less frequent logging during stress test
    )
    
    formatter = DynamicFormatter(
        "{{id}}: {{status}} - {{message}}",
        performance_monitor=monitor
    )
    
    # High-volume formatting
    start_time = time.perf_counter()
    operation_count = 5000
    
    print(f"Performing {operation_count} operations...")
    for i in range(operation_count):
        result = formatter.format(
            id=f"REQ-{i:06d}",
            status="PROCESSED",
            message=f"Request processed successfully in batch {i//100}"
        )
    
    total_time = time.perf_counter() - start_time
    ops_per_second = operation_count / total_time
    
    print(f"Stress Test Results:")
    print(f"  Operations: {operation_count}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Throughput: {ops_per_second:.0f} ops/sec")
    
    # Verify monitoring data integrity
    stats = monitor.get_stats('format_operation')
    print(f"  Monitored operations: {stats['total_calls']}")
    print(f"  Data integrity: {'✓ PASS' if stats['total_calls'] == operation_count else '✗ FAIL'}")


if __name__ == "__main__":
    """Run all performance monitoring examples."""
    
    examples = [
        ("Basic Monitoring", basic_monitoring_example),
        ("Production Monitoring", production_monitoring_example),
        ("Development Monitoring", development_monitoring_example),
        ("Custom Monitoring", custom_monitoring_example),
        ("Regression Detection", performance_regression_example),
        ("System Integration", monitoring_integration_example),
        ("Performance Impact", benchmark_comparison_example),
        ("Memory Leak Detection", memory_leak_detection_example),
        ("Stress Testing", stress_test_example)
    ]
    
    print("Dynamic Formatter Performance Monitoring Examples")
    print("=" * 60)
    
    for name, example_func in examples:
        print(f"\n{name}")
        print("-" * len(name))
        try:
            example_func()
        except Exception as e:
            print(f"Error in {name}: {e}")
        print()
    
    print("Examples completed! Check generated files:")
    print("  - performance_stats.json")
    print("  - production_stats.json")