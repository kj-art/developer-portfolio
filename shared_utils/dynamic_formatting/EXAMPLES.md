# Dynamic Formatting Examples

This document provides comprehensive examples showcasing all features of the Dynamic Formatting system. Each example includes both the code and expected output to demonstrate real-world usage patterns.

## Table of Contents

1. [Core Feature: Automatic Section Removal](#core-feature-automatic-section-removal)
2. [Positional Arguments](#positional-arguments)
3. [Configuration Management](#configuration-management)
4. [Performance Monitoring](#performance-monitoring)
5. [Advanced Formatting](#advanced-formatting)
6. [Enterprise Logging](#enterprise-logging)
7. [Production Deployment Patterns](#production-deployment-patterns)
8. [Error Handling](#error-handling)
9. [Custom Functions](#custom-functions)
10. [Real-World Use Cases](#real-world-use-cases)

## Core Feature: Automatic Section Removal

The fundamental value of Dynamic Formatting is eliminating manual null checking through automatic section removal.

### Basic Section Removal

```python
from shared_utils.dynamic_formatting import DynamicFormatter

# Traditional approach (manual null checking)
def format_status_traditional(message, code=None, user=None):
    parts = [f"Status: {message}"]
    if code:
        parts.append(f"Code: {code}")
    if user:
        parts.append(f"User: {user}")
    return " | ".join(parts)

# Dynamic formatting approach (automatic handling)
formatter = DynamicFormatter("{{Status: ;message}}{{ | Code: ;code}}{{ | User: ;user}}")

# All data present
result1 = formatter.format(message="Success", code=200, user="john_doe")
print(result1)  # "Status: Success | Code: 200 | User: john_doe"

# Partial data (code missing)
result2 = formatter.format(message="Success", user="john_doe")
print(result2)  # "Status: Success | User: john_doe"

# Minimal data (only message)
result3 = formatter.format(message="Success")
print(result3)  # "Status: Success"

# No data
result4 = formatter.format()
print(result4)  # ""
```

### Complex Multi-Section Templates

```python
# Log entry formatter with optional fields
log_formatter = DynamicFormatter(
    "{{#level_color;[;level;]}} "
    "{{timestamp}} "
    "{{service_name}} "
    "{{message}}"
    "{{ | RequestID: ;request_id}}"
    "{{ | UserID: ;user_id}}"
    "{{ | Duration: ;duration;ms}}"
    "{{ | Error: ;error_code}}"
)

# Complete log entry
full_log = log_formatter.format(
    level="ERROR",
    timestamp="2024-01-15T10:30:00Z",
    service_name="auth-service",
    message="Authentication failed",
    request_id="req_12345",
    user_id="user_67890",
    duration=150,
    error_code=401
)
print(full_log)
# "[ERROR] 2024-01-15T10:30:00Z auth-service Authentication failed | RequestID: req_12345 | UserID: user_67890 | Duration: 150ms | Error: 401"

# Minimal log entry (only required fields)
minimal_log = log_formatter.format(
    level="INFO",
    timestamp="2024-01-15T10:30:00Z",
    service_name="auth-service",
    message="User login successful"
)
print(minimal_log)
# "[INFO] 2024-01-15T10:30:00Z auth-service User login successful"
```

## Positional Arguments

Use `{{}}` syntax for sequential argument processing without named parameters.

### Basic Positional Usage

```python
# Simple positional fields
formatter = DynamicFormatter("{{Error: ;}} {{Code: ;}}")

# All arguments provided
result1 = formatter.format("Connection failed", 500)
print(result1)  # "Error: Connection failed Code: 500"

# Partial arguments (second missing)
result2 = formatter.format("Connection failed")
print(result2)  # "Error: Connection failed"

# No arguments
result3 = formatter.format()
print(result3)  # ""
```

### Mixed Positional and Named Arguments

```python
# Combine positional and named fields
formatter = DynamicFormatter("{{Error: ;}} {{message}}{{ | User: ;user_id}}")

# Positional first, then named
result = formatter.format("Database error", message="Connection timeout", user_id="john")
print(result)  # "Error: Database error Connection timeout | User: john"
```

### Advanced Positional with Formatting

```python
# Positional arguments with color formatting
formatter = DynamicFormatter("{{#red@bold;Alert: ;}} {{#yellow;Warning: ;}}")

result1 = formatter.format("System down", "High CPU usage")
print(result1)  # Colored output: "Alert: System down Warning: High CPU usage"

result2 = formatter.format("System down")
print(result2)  # Colored output: "Alert: System down"
```

## Configuration Management

Enterprise-grade configuration management for different deployment environments.

### JSON Configuration Files

**configs/development.json**
```json
{
    "validation_mode": "STRICT",
    "validation_level": "ERROR",
    "enable_validation": true,
    "output_mode": "console",
    "performance_monitoring": {
        "enabled": true,
        "memory_tracking": true,
        "regression_detection": true,
        "baseline_duration_ms": 1.0,
        "baseline_memory_mb": 5.0
    },
    "functions": {
        "priority_color": "lambda p: 'red' if p == 'high' else 'green'"
    }
}
```

**configs/production.json**
```json
{
    "validation_mode": "GRACEFUL",
    "validation_level": "WARNING",
    "enable_validation": false,
    "output_mode": "file",
    "performance_monitoring": {
        "enabled": true,
        "memory_tracking": false,
        "regression_detection": false,
        "baseline_duration_ms": 0.5,
        "baseline_memory_mb": 2.0
    }
}
```

### Using Configuration Files

```python
from shared_utils.dynamic_formatting import DynamicFormatter

template = "{{#red;[ERROR];}} {{message}}{{ | Code: ;error_code}}"

# Load environment-specific configurations
dev_formatter = DynamicFormatter.from_config_file(template, "configs/development.json")
prod_formatter = DynamicFormatter.from_config_file(template, "configs/production.json")

# Same template, different behavior based on environment
error_data = {"message": "Database connection failed", "error_code": "DB_CONN_001"}

# Development: Strict validation, detailed errors, full monitoring
dev_result = dev_formatter.format(**error_data)
print(f"Development: {dev_result}")

# Production: Graceful degradation, minimal overhead
prod_result = prod_formatter.format(**error_data)
print(f"Production: {prod_result}")
```

### Environment Variable Configuration

```python
import os

# Set configuration via environment variables
os.environ['FORMATTER_VALIDATION_MODE'] = 'GRACEFUL'
os.environ['FORMATTER_OUTPUT_MODE'] = 'file'
os.environ['FORMATTER_PERFORMANCE_ENABLED'] = 'true'

# Load from environment
formatter = DynamicFormatter.from_environment(template)
```

### Programmatic Configuration

```python
from shared_utils.dynamic_formatting import FormatterConfig, ValidationMode

# Create custom configuration
config = FormatterConfig(
    validation_mode=ValidationMode.AUTO_CORRECT,
    enable_validation=True,
    output_mode="console",
    functions={
        'status_color': lambda status: 'green' if status == 'OK' else 'red',
        'is_error': lambda level: level.upper() in ['ERROR', 'CRITICAL']
    }
)

formatter = DynamicFormatter(template, config=config)
```

## Performance Monitoring

Built-in observability for production systems with detailed metrics and regression detection.

### Basic Performance Monitoring

```python
from shared_utils.dynamic_formatting import create_production_formatter

# Create formatter with performance monitoring
formatter = create_production_formatter(
    "{{#status_color;Status: ;status}} {{Response: ;response_time;ms}} {{Error: ;error_code}}"
)

# Monitor performance during operations
with formatter.monitor_performance() as monitor:
    results = []
    for data in batch_data:
        result = formatter.format(**data)
        results.append(result)

# Access detailed metrics
metrics = monitor.get_metrics()
print(f"Total operations: {metrics.operation_count}")
print(f"Average duration: {metrics.duration_ms:.2f}ms")
print(f"Peak memory usage: {metrics.peak_memory_mb:.2f}MB")
print(f"Total memory allocated: {metrics.total_memory_mb:.2f}MB")
```

### Production Monitoring with Regression Detection

```python
from shared_utils.dynamic_formatting import PerformanceMonitor, create_production_monitor

# Create monitor with baseline expectations
monitor = create_production_monitor(
    baseline_duration_ms=1.0,    # Expected baseline performance
    baseline_memory_mb=5.0,      # Expected memory usage
    regression_threshold=2.0      # Alert if performance degrades 2x
)

formatter = DynamicFormatter(template, monitor=monitor)

# Process large batch with monitoring
batch_size = 10000
with formatter.monitor_performance() as perf:
    for i in range(batch_size):
        result = formatter.format(
            status="processing",
            item_count=i,
            timestamp="2024-01-15T10:30:00Z"
        )

# Check for performance regressions
stats = perf.get_stats()
if stats.has_regression:
    print("⚠️  Performance regression detected!")
    print(f"Expected: {monitor.baseline_duration_ms}ms, Actual: {stats.avg_duration_ms:.2f}ms")
    
    # Export metrics for external monitoring
    metrics_json = monitor.export_metrics()
    # Send to monitoring system (Prometheus, DataDog, etc.)
```

### Memory Usage Tracking

```python
import psutil
from shared_utils.dynamic_formatting import PerformanceMonitor

# Monitor with detailed memory tracking
monitor = PerformanceMonitor(
    track_memory=True,
    memory_sample_interval=100  # Sample every 100 operations
)

formatter = DynamicFormatter(template, monitor=monitor)

# Long-running process with memory monitoring
with formatter.monitor_performance() as perf:
    for batch in large_dataset:
        batch_results = [formatter.format(**item) for item in batch]
        
        # Check memory usage periodically
        if perf.operation_count % 1000 == 0:
            current_memory = perf.get_current_memory_mb()
            print(f"Processed {perf.operation_count} items, Memory: {current_memory:.2f}MB")

# Final memory analysis
final_stats = perf.get_stats()
print(f"Peak memory: {final_stats.peak_memory_mb:.2f}MB")
print(f"Memory efficiency: {final_stats.memory_efficiency:.2%}")
```

## Advanced Formatting

Sophisticated formatting capabilities including colors, styles, and conditional logic.

### Color and Style Formatting

```python
# Color formatting with styles
formatter = DynamicFormatter(
    "{{#red@bold;ERROR: ;}} "
    "{{#yellow@italic;Warning: ;}} "
    "{{#green@underline;Success: ;}} "
    "{{#blue;Info: ;}}"
)

# Different message types
error_msg = formatter.format("System failure detected")
# Output: Bold red "ERROR: System failure detected"

warning_msg = formatter.format("", "High memory usage", "", "")
# Output: Italic yellow "Warning: High memory usage"

success_msg = formatter.format("", "", "Deployment complete", "")
# Output: Underlined green "Success: Deployment complete"
```

### Conditional Formatting

```python
# Functions for conditional logic
def is_critical(level):
    return level.upper() in ['ERROR', 'CRITICAL', 'FATAL']

def is_warning(level):
    return level.upper() in ['WARNING', 'WARN']

def get_priority_color(priority):
    color_map = {
        'high': 'red',
        'medium': 'yellow', 
        'low': 'green',
        'critical': 'magenta'
    }
    return color_map.get(priority.lower(), 'white')

# Conditional sections
formatter = DynamicFormatter(
    "{{?is_critical;🚨 CRITICAL: ;}} "
    "{{?is_warning;⚠️  WARNING: ;}} "
    "{{#get_priority_color@bold;Priority ;priority;: ;}} "
    "{{message}}",
    functions={
        'is_critical': is_critical,
        'is_warning': is_warning,
        'get_priority_color': get_priority_color
    }
)

# Critical message
critical_result = formatter.format(
    level="CRITICAL",
    priority="high", 
    message="Database server unreachable"
)
print(critical_result)
# Output: "🚨 CRITICAL: Priority high: Database server unreachable" (in red/bold)

# Warning message
warning_result = formatter.format(
    level="WARNING",
    priority="medium",
    message="Disk space low"
)
print(warning_result)
# Output: "⚠️  WARNING: Priority medium: Disk space low" (in yellow/bold)

# Normal message
info_result = formatter.format(
    level="INFO",
    priority="low",
    message="Backup completed successfully"
)
print(info_result)
# Output: "Priority low: Backup completed successfully" (in green/bold)
```

### Complex Function Integration

```python
from datetime import datetime
import json

# Advanced custom functions
def format_timestamp(ts):
    """Format timestamp with relative time"""
    if isinstance(ts, str):
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    else:
        dt = ts
    
    now = datetime.now(dt.tzinfo)
    diff = now - dt
    
    if diff.seconds < 60:
        return f"{diff.seconds}s ago"
    elif diff.seconds < 3600:
        return f"{diff.seconds // 60}m ago"
    else:
        return dt.strftime("%Y-%m-%d %H:%M")

def format_size(bytes_size):
    """Format byte size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}PB"

def format_json(data):
    """Format data as compact JSON"""
    if isinstance(data, dict):
        return json.dumps(data, separators=(',', ':'))
    return str(data)

# Complex formatter with multiple functions
formatter = DynamicFormatter(
    "{{#format_timestamp;Timestamp: ;timestamp}} "
    "{{Level: ;level}} "
    "{{Service: ;service}} "
    "{{Message: ;message}}"
    "{{ | Size: #format_size;size}}"
    "{{ | Data: #format_json;metadata}}"
    "{{ | Duration: ;duration;ms}}",
    functions={
        'format_timestamp': format_timestamp,
        'format_size': format_size,
        'format_json': format_json
    }
)

# Complex log entry
result = formatter.format(
    timestamp="2024-01-15T10:30:00Z",
    level="INFO",
    service="data-processor",
    message="File processed successfully",
    size=1048576,  # 1MB in bytes
    metadata={"file_type": "csv", "rows": 10000},
    duration=245
)
print(result)
# Output: "Timestamp: 2m ago Level: INFO Service: data-processor Message: File processed successfully | Size: 1.0MB | Data: {"file_type":"csv","rows":10000} | Duration: 245ms"
```

## Enterprise Logging

Professional logging integration with automatic formatting and performance monitoring.

### Structured Logging Setup

```python
import logging
from shared_utils.dynamic_formatting import DynamicLoggingFormatter, create_logging_formatter

# Create enterprise logging formatter
log_formatter = create_logging_formatter(
    template="{{#level_color;[;levelname;]}} "
             "{{asctime}} "
             "{{name}} "
             "{{message}}"
             "{{ | RequestID: ;request_id}}"
             "{{ | UserID: ;user_id}}"
             "{{ | Duration: ;duration;ms}}"
             "{{ | Error: ;error_code}}",
    mode='production'
)

# Configure logging handler
handler = logging.StreamHandler()
handler.setFormatter(log_formatter)

# Setup logger
logger = logging.getLogger('my_service')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Use structured logging with automatic section handling
logger.info(
    "User authentication successful",
    extra={
        'request_id': 'req_12345',
        'user_id': 'user_67890',
        'duration': 150
    }
)
# Output: "[INFO] 2024-01-15 10:30:00,123 my_service User authentication successful | RequestID: req_12345 | UserID: user_67890 | Duration: 150ms"

logger.error(
    "Database connection failed",
    extra={
        'request_id': 'req_12346',
        'error_code': 'DB_CONN_001'
    }
)
# Output: "[ERROR] 2024-01-15 10:30:01,456 my_service Database connection failed | RequestID: req_12346 | Error: DB_CONN_001"

# Minimal logging (optional fields auto-removed)
logger.info("Service started successfully")
# Output: "[INFO] 2024-01-15 10:30:02,789 my_service Service started successfully"
```

### Multi-Handler Logging Configuration

```python
import logging
from shared_utils.dynamic_formatting import create_logging_formatter

# Console handler (colored output for development)
console_handler = logging.StreamHandler()
console_formatter = create_logging_formatter(
    "{{#level_color@bold;[;levelname;]}} {{asctime}} {{#cyan;{;name;}}} {{message}}{{ | ;extra_info}}",
    mode='development'
)
console_handler.setFormatter(console_formatter)

# File handler (plain text for production logs)
file_handler = logging.FileHandler('application.log')
file_formatter = create_logging_formatter(
    "{{[;levelname;]}} {{asctime}} {{name}} {{message}}{{ | RequestID: ;request_id}}{{ | UserID: ;user_id}}{{ | Duration: ;duration;ms}}",
    mode='production'
)
file_handler.setFormatter(file_formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)
root_logger.setLevel(logging.INFO)

# Usage produces both console and file output
logger = logging.getLogger('api_service')
logger.info(
    "API request processed",
    extra={
        'request_id': 'api_12345',
        'user_id': 'user_67890',
        'duration': 45
    }
)
```

## Production Deployment Patterns

Real-world deployment strategies for different environments.

### Environment-Specific Formatters

```python
from shared_utils.dynamic_formatting import (
    development_formatter,
    staging_formatter, 
    production_formatter
)

# Template used across all environments
api_log_template = (
    "{{#level_color;[;level;]}} "
    "{{timestamp}} "
    "{{service}} "
    "{{endpoint}} "
    "{{message}}"
    "{{ | IP: ;client_ip}}"
    "{{ | User: ;user_id}}"
    "{{ | Duration: ;response_time;ms}}"
    "{{ | Status: ;status_code}}"
)

# Environment-specific configurations
dev_formatter = development_formatter(api_log_template)     # Strict validation, detailed errors
staging_formatter = staging_formatter(api_log_template)     # Auto-correction, assisted dev
prod_formatter = production_formatter(api_log_template)     # Graceful degradation, monitoring

# Deployment function
def get_formatter_for_environment(env: str):
    formatters = {
        'development': dev_formatter,
        'staging': staging_formatter,
        'production': prod_formatter
    }
    return formatters.get(env, dev_formatter)

# Usage in application
import os
current_env = os.getenv('ENVIRONMENT', 'development')
formatter = get_formatter_for_environment(current_env)
```

### Configuration File Management

```python
import os
from pathlib import Path
from shared_utils.dynamic_formatting import DynamicFormatter

def load_formatter_config(service_name: str, environment: str):
    """Load formatter configuration for specific service and environment"""
    
    config_dir = Path("configs/formatters")
    config_file = config_dir / f"{service_name}_{environment}.json"
    
    # Fallback to default environment config
    if not config_file.exists():
        config_file = config_dir / f"default_{environment}.json"
    
    # Final fallback to development config
    if not config_file.exists():
        config_file = config_dir / "default_development.json"
    
    return str(config_file)

# Load service-specific configurations
def create_service_formatter(service_name: str, template: str):
    environment = os.getenv('ENVIRONMENT', 'development')
    config_path = load_formatter_config(service_name, environment)
    
    return DynamicFormatter.from_config_file(template, config_path)

# Usage for different services
auth_formatter = create_service_formatter('auth', auth_template)
api_formatter = create_service_formatter('api', api_template)
worker_formatter = create_service_formatter('worker', worker_template)
```

### Health Check and Monitoring Integration

```python
from shared_utils.dynamic_formatting import create_production_formatter
import time

class FormatterHealthCheck:
    """Health check system for formatter performance"""
    
    def __init__(self, formatter, check_interval=60):
        self.formatter = formatter
        self.check_interval = check_interval
        self.last_check = time.time()
        self.health_status = "healthy"
        
    def perform_health_check(self):
        """Perform health check on formatter performance"""
        try:
            # Test formatting performance
            test_data = {
                "level": "INFO",
                "message": "Health check test",
                "timestamp": "2024-01-15T10:30:00Z"
            }
            
            with self.formatter.monitor_performance() as monitor:
                for _ in range(100):  # Test batch
                    self.formatter.format(**test_data)
            
            metrics = monitor.get_metrics()
            
            # Check performance thresholds
            if metrics.avg_duration_ms > 5.0:  # 5ms threshold
                self.health_status = "degraded"
                return {
                    "status": "degraded",
                    "reason": f"Slow performance: {metrics.avg_duration_ms:.2f}ms",
                    "metrics": metrics.__dict__
                }
            
            if metrics.peak_memory_mb > 50.0:  # 50MB threshold
                self.health_status = "warning"
                return {
                    "status": "warning", 
                    "reason": f"High memory usage: {metrics.peak_memory_mb:.2f}MB",
                    "metrics": metrics.__dict__
                }
            
            self.health_status = "healthy"
            return {
                "status": "healthy",
                "performance": f"{metrics.avg_duration_ms:.2f}ms avg",
                "memory": f"{metrics.peak_memory_mb:.2f}MB peak"
            }
            
        except Exception as e:
            self.health_status = "unhealthy"
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_health_status(self):
        """Get current health status with automatic periodic checks"""
        current_time = time.time()
        if current_time - self.last_check > self.check_interval:
            self.perform_health_check()
            self.last_check = current_time
        
        return self.health_status

# Usage in production application
formatter = create_production_formatter(template)
health_checker = FormatterHealthCheck(formatter)

# Integrate with application health endpoint
def health_endpoint():
    formatter_health = health_checker.get_health_status()
    return {
        "service": "healthy",
        "components": {
            "formatter": formatter_health
        }
    }
```

## Error Handling

Comprehensive error handling with detailed context for debugging and production resilience.

### Development Error Handling

```python
from shared_utils.dynamic_formatting import (
    DynamicFormatter,
    DynamicFormattingError,
    RequiredFieldError,
    ParseError
)

# Development mode with strict validation
formatter = DynamicFormatter(
    "{{#invalid_color;Message: ;message}}",  # Invalid color function
    config=FormatterConfig.development()
)

try:
    result = formatter.format(message="Test message")
except DynamicFormattingError as e:
    print(f"Error Type: {type(e).__name__}")
    print(f"Message: {e.message}")
    print(f"Template: {e.template}")
    print(f"Position: {e.position}")
    print(f"Context: {e.context}")
    
    # Detailed debugging information
    print("\nDebugging Information:")
    print(f"Available functions: {e.available_functions}")
    print(f"Suggested alternatives: {e.suggestions}")
```

### Production Error Handling

```python
# Production mode with graceful degradation
prod_formatter = DynamicFormatter(
    template,
    config=FormatterConfig.production()
)

def safe_format(formatter, **data):
    """Production-safe formatting with fallback"""
    try:
        return formatter.format(**data)
    except DynamicFormattingError as e:
        # Log error but continue operation
        logger.warning(f"Formatting error: {e.message}", extra={'template': e.template})
        
        # Fallback to simple string format
        return f"[{data.get('level', 'INFO')}] {data.get('message', 'No message')}"
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected formatting error: {e}")
        return f"[ERROR] Formatting failed: {data.get('message', 'Unknown error')}"

# Usage with guaranteed output
result = safe_format(prod_formatter, level="INFO", message="Operation completed")
```

### Error Recovery and Debugging

```python
def debug_formatter_issues(template, data):
    """Debug formatter issues with detailed analysis"""
    
    print(f"Template: {template}")
    print(f"Data: {data}")
    
    try:
        # Test with development mode for detailed errors
        debug_formatter = DynamicFormatter(template, config=FormatterConfig.development())
        result = debug_formatter.format(**data)
        print(f"Success: {result}")
        return result
        
    except ParseError as e:
        print(f"Template Parse Error at position {e.position}:")
        print(f"  {template}")
        print(f"  {' ' * e.position}^")
        print(f"  Issue: {e.message}")
        
    except RequiredFieldError as e:
        print(f"Missing Required Field: {e.field_name}")
        print(f"Available fields: {list(data.keys())}")
        print(f"Template context: {e.context}")
        
    except DynamicFormattingError as e:
        print(f"Formatting Error: {e.message}")
        if hasattr(e, 'suggestions'):
            print(f"Suggestions: {e.suggestions}")
        
    return None

# Debug problematic templates
debug_formatter_issues(
    "{{#invalid_function;Message: ;message}}",
    {"message": "Test"}
)
```

## Real-World Use Cases

Complete examples showing how to use Dynamic Formatting in real enterprise scenarios.

### API Gateway Logging

```python
# API Gateway request/response logging
api_gateway_formatter = DynamicFormatter(
    "{{#status_color;[;method;]}} "
    "{{endpoint}} "
    "{{#response_color;{;status_code;}}} "
    "{{duration;ms}}"
    "{{ | Client: ;client_ip}}"
    "{{ | User: ;user_id}}"
    "{{ | Size: ;response_size;B}}"
    "{{ | Error: ;error_message}}",
    functions={
        'status_color': lambda method: {
            'GET': 'blue', 'POST': 'green', 'PUT': 'yellow', 
            'DELETE': 'red', 'PATCH': 'magenta'
        }.get(method, 'white'),
        'response_color': lambda code: 'green' if 200 <= code < 300 else 'red' if code >= 400 else 'yellow'
    }
)

# Successful API request
success_log = api_gateway_formatter.format(
    method="GET",
    endpoint="/api/v1/users",
    status_code=200,
    duration=45,
    client_ip="192.168.1.100",
    user_id="user_123",
    response_size=1024
)

# Failed API request with error
error_log = api_gateway_formatter.format(
    method="POST",
    endpoint="/api/v1/orders",
    status_code=400,
    duration=12,
    client_ip="192.168.1.101",
    error_message="Invalid request payload"
)
```

### Database Query Monitoring

```python
# Database query performance monitoring
db_formatter = DynamicFormatter(
    "{{#query_type_color;[;query_type;]}} "
    "{{database}}.{{table}} "
    "{{#duration_color;{;duration;ms}}} "
    "{{rows_affected}} rows"
    "{{ | Query: ;query_hash}}"
    "{{ | User: ;db_user}}"
    "{{ | Connection: ;connection_id}}"
    "{{ | Error: ;error_message}}",
    functions={
        'query_type_color': lambda qt: {
            'SELECT': 'green', 'INSERT': 'blue', 'UPDATE': 'yellow', 
            'DELETE': 'red', 'CREATE': 'magenta', 'DROP': 'red'
        }.get(qt.upper(), 'white'),
        'duration_color': lambda d: 'green' if d < 100 else 'yellow' if d < 1000 else 'red'
    }
)

# Fast query log
fast_query = db_formatter.format(
    query_type="SELECT",
    database="ecommerce",
    table="products",
    duration=25,
    rows_affected=150,
    query_hash="a1b2c3d4",
    db_user="app_user",
    connection_id="conn_456"
)

# Slow query log with warning
slow_query = db_formatter.format(
    query_type="UPDATE",
    database="ecommerce", 
    table="orders",
    duration=1500,  # 1.5 seconds - will be red
    rows_affected=50000,
    query_hash="e5f6g7h8",
    db_user="batch_user"
)
```

### Microservice Communication Logging

```python
# Service-to-service communication logging
service_comm_formatter = DynamicFormatter(
    "{{#service_color;[;source_service;]}} → {{#service_color;[;target_service;]}} "
    "{{operation}} "
    "{{#status_color;{;status;}}} "
    "{{duration;ms}}"
    "{{ | Trace: ;trace_id}}"
    "{{ | Span: ;span_id}}"
    "{{ | Retry: ;retry_count}}"
    "{{ | Circuit: ;circuit_breaker_state}}"
    "{{ | Error: ;error_details}}",
    functions={
        'service_color': lambda s: hash(s) % 6 + 31,  # Consistent color per service
        'status_color': lambda s: 'green' if s == 'SUCCESS' else 'red' if s == 'ERROR' else 'yellow'
    }
)

# Successful service call
success_call = service_comm_formatter.format(
    source_service="order-service",
    target_service="payment-service",
    operation="process_payment",
    status="SUCCESS",
    duration=250,
    trace_id="trace_abc123",
    span_id="span_def456"
)

# Failed service call with circuit breaker
failed_call = service_comm_formatter.format(
    source_service="order-service",
    target_service="inventory-service", 
    operation="check_availability",
    status="ERROR",
    duration=5000,  # Timeout
    trace_id="trace_xyz789",
    span_id="span_uvw012",
    retry_count=3,
    circuit_breaker_state="OPEN",
    error_details="Connection timeout after 5000ms"
)
```

### CI/CD Pipeline Logging

```python
# CI/CD pipeline step logging
pipeline_formatter = DynamicFormatter(
    "{{#stage_color;[;stage;]}} {{#step_color;{;step;}}} "
    "{{#status_color@bold;[;status;]}} "
    "{{duration}}"
    "{{ | Job: ;job_id}}"
    "{{ | Branch: ;branch}}"
    "{{ | Commit: ;commit_hash}}"
    "{{ | Artifacts: ;artifact_count}}"
    "{{ | Error: ;error_message}}",
    functions={
        'stage_color': lambda s: {
            'build': 'blue', 'test': 'yellow', 'deploy': 'green', 
            'security': 'magenta', 'cleanup': 'cyan'
        }.get(s.lower(), 'white'),
        'step_color': lambda s: 'cyan',
        'status_color': lambda s: 'green' if s == 'PASSED' else 'red' if s == 'FAILED' else 'yellow'
    }
)

# Successful build step
build_success = pipeline_formatter.format(
    stage="build",
    step="compile",
    status="PASSED",
    duration="2m 15s",
    job_id="job_123",
    branch="feature/new-api",
    commit_hash="a1b2c3d",
    artifact_count=3
)

# Failed test step
test_failure = pipeline_formatter.format(
    stage="test",
    step="unit_tests",
    status="FAILED", 
    duration="45s",
    job_id="job_124",
    branch="feature/new-api",
    commit_hash="a1b2c3d",
    error_message="TestUserService.test_create_user failed: assertion error"
)
```

This comprehensive examples document demonstrates every major feature of the Dynamic Formatting system in real-world contexts, showing both the technical capabilities and practical business value for enterprise development scenarios.