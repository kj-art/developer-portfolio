"""
Enterprise-grade logging system for portfolio projects

This module provides comprehensive logging capabilities including:
- Family-based dynamic formatting with color and text formatting families
- Colored console output with proper reset handling
- JSON structured logging
- Performance monitoring
- Progress bar integration
- Context management
- Log rotation and filtering

Usage:
    from shared_utils.logger import set_up_logging, get_logger, log_performance
    
    set_up_logging(level='INFO', log_file='app.log', enable_json=True)
    logger = get_logger(__name__)
    
    with log_performance("file_processing"):
        logger.info("Processing files", file_count=100, duration=2.5)
        # Output: "Processing files (100 files) in 2.5s"
"""

import logging
import logging.handlers
import json
import time
import functools
import sys
import traceback
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Union, Callable
from contextlib import contextmanager
from datetime import datetime

try:
    import psutil  # For memory monitoring
except ImportError:
    psutil = None

from .dynamic_formatting import DynamicLoggingFormatter, DynamicFormattingError


class JSONFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_entry, default=str)


class ProgressAwareHandler(logging.StreamHandler):
    """Handler that doesn't interfere with progress bars"""
    
    def emit(self, record):
        try:
            # Check if tqdm is available and active
            try:
                import tqdm
                if tqdm.tqdm._instances:
                    # Clear progress bars, emit log, redraw progress bars
                    for instance in tqdm.tqdm._instances:
                        instance.clear()
                    super().emit(record)
                    for instance in tqdm.tqdm._instances:
                        instance.refresh()
                    return
            except ImportError:
                pass
                
            # Normal emission if no progress bars
            super().emit(record)
        except Exception:
            self.handleError(record)


class PerformanceTracker:
    """Tracks performance metrics and logs statistics"""
    
    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()
        
    def start_operation(self, operation_name: str) -> str:
        """Start tracking an operation"""
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        with self.lock:
            self.metrics[operation_id] = {
                'name': operation_name,
                'start_time': time.time(),
                'start_memory': self._get_memory_usage(),
            }
        return operation_id
        
    def end_operation(self, operation_id: str, **extra_metrics):
        """End tracking an operation and log results"""
        with self.lock:
            if operation_id not in self.metrics:
                return
                
            start_data = self.metrics[operation_id]
            duration = time.time() - start_data['start_time']
            memory_delta = self._get_memory_usage() - start_data['start_memory']
            
            metrics = {
                'operation': start_data['name'],
                'duration_seconds': round(duration, 3),
                'memory_delta_mb': round(memory_delta, 2),
                **extra_metrics
            }
            
            # Log performance metrics
            logger = logging.getLogger('performance')
            logger.info(f"Operation completed: {start_data['name']}", 
                       extra={'extra_data': metrics})
            
            del self.metrics[operation_id]
            return metrics
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        if psutil is None:
            return 0.0
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0


# Global performance tracker
_performance_tracker = PerformanceTracker()


class EnterpriseLogger:
    """Main logger class with enterprise features"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
        
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
        
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
        
    def error(self, message: str, exception: Exception = None, **kwargs):
        if exception:
            kwargs['exc_info'] = (type(exception), exception, exception.__traceback__)
        self._log(logging.ERROR, message, **kwargs)
        
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)
        
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with extra data handling"""
        extra_data = {k: v for k, v in kwargs.items() 
                     if k not in ['exc_info', 'stack_info', 'stacklevel']}
        
        if extra_data:
            # Create a LogRecord with extra data
            record = self.logger.makeRecord(
                self.logger.name, level, '', 0, message, (), 
                kwargs.get('exc_info'), extra={'extra_data': extra_data}
            )
            self.logger.handle(record)
        else:
            self.logger.log(level, message, **kwargs)


def create_default_format_functions() -> Dict[str, Callable]:
    """Create default formatting functions for family-based logging scenarios"""
    
    def duration_format(seconds):
        """Format duration with appropriate units"""
        if seconds < 0.001:
            return f"{seconds*1000000:.0f}μs"
        elif seconds < 1:
            return f"{seconds*1000:.1f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        else:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m{secs:.1f}s"
    
    def file_size_format(size_bytes):
        """Format file size with appropriate units"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f}KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f}MB"
        else:
            return f"{size_bytes/(1024**3):.2f}GB"
    
    def performance_indicator(duration):
        """Add performance indicators based on duration"""
        if duration < 0.1:
            return "⚡"
        elif duration < 1.0:
            return "✓"
        elif duration < 5.0:
            return "⏳"
        else:
            return "🐌"
    
    def error_severity(error_code):
        """Format error severity based on error code"""
        if isinstance(error_code, str):
            if error_code.startswith('E0'):
                return "CRITICAL"
            elif error_code.startswith('W'):
                return "WARNING"
            else:
                return "ERROR"
        return "ERROR"
    
    def level_color_map(level_name):
        """Map log levels to colors for family-based formatting"""
        color_map = {
            'DEBUG': 'cyan',
            'INFO': 'green', 
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'magenta'
        }
        return color_map.get(level_name, 'white')
    
    def has_items(count):
        """Check if count is greater than 0 (for conditional formatting)"""
        return count > 0
    
    def is_slow(duration):
        """Check if operation is slow (for conditional formatting)"""
        return duration > 5.0
    
    def has_errors(error_count):
        """Check if there are errors (for conditional formatting)"""
        return error_count > 0
    
    return {
        'duration_format': duration_format,
        'file_size_format': file_size_format,
        'performance_indicator': performance_indicator,
        'error_severity': error_severity,
        'level_color_map': level_color_map,
        'has_items': has_items,
        'is_slow': is_slow,
        'has_errors': has_errors,
    }


def set_up_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    json_file: Optional[str] = None,
    enable_colors: bool = True,
    enable_performance: bool = True,
    max_file_size: str = '10MB',
    backup_count: int = 5,
    console_format: Optional[str] = None,
    file_format: Optional[str] = None,
    format_functions: Optional[Dict[str, Callable]] = None
):
    """
    Set up enterprise logging configuration with family-based dynamic formatting
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to text log file
        json_file: Path to JSON log file for structured logging
        enable_colors: Whether to use colored console output
        enable_performance: Whether to enable performance tracking
        max_file_size: Maximum size of log files before rotation
        backup_count: Number of backup files to keep
        console_format: Custom console log format string (family-based formatting syntax)
        file_format: Custom file log format string (family-based formatting syntax)
        format_functions: Custom formatting functions for dynamic formatting
        
    Family-Based Format Examples:
        # Level-based coloring with function fallback
        "{{#level_color_map@bold;Level: ;levelname}} - {{message}}"
        
        # Conditional sections with function fallback
        "{{$has_items;(;file_count; files)}}{{ in ;duration;$duration_format}}"
        
        # Complex formatting with inline spans
        "{{message}}{{ with {#blue}important{#normal} data}}"
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Merge default format functions with custom ones
    default_functions = create_default_format_functions()
    if format_functions:
        default_functions.update(format_functions)
    
    # Default console format using family-based dynamic formatting with function fallback
    if console_format is None:
        console_format = ('{{#level_color_map@bold;[;levelname;]}} {{message}}'
                         '{{$has_items; (;file_count; files)}}'
                         '{{ in ;duration;$duration_format}}'
                         '{{$has_errors; [;error_count; errors]}}')
    
    # Console handler with family-based formatting
    console_handler = ProgressAwareHandler(sys.stdout)
    console_formatter = DynamicLoggingFormatter(
        console_format, 
        functions=default_functions, 
        output_mode='console' if enable_colors else 'file'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with detailed info but no colors
    if log_file:
        if file_format is None:
            file_format = ('{{asctime}} - {{name}} - {{levelname}} - {{funcName}}:{{lineno}} - {{message}}'
                          '{{ (;file_count; files)}}'
                          '{{ duration: ;duration;$duration_format}}'
                          '{{ size: ;file_size;$file_size_format}}'
                          '{{ error: ;error_code}}'
                          '{{ memory: ;memory_delta_mb;MB}}')
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=_parse_file_size(max_file_size),
            backupCount=backup_count
        )
        file_formatter = DynamicLoggingFormatter(file_format, functions=default_functions, output_mode='file')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # JSON handler for structured logging
    if json_file:
        json_handler = logging.handlers.RotatingFileHandler(
            json_file,
            maxBytes=_parse_file_size(max_file_size),
            backupCount=backup_count
        )
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)
    
    # Performance logger
    if enable_performance:
        perf_logger = logging.getLogger('performance')
        perf_logger.setLevel(logging.INFO)


def get_logger(name: Optional[str] = None) -> EnterpriseLogger:
    """Get an enterprise logger instance"""
    if name is None:
        # Get the calling module's name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return EnterpriseLogger(name)


@contextmanager
def log_performance(operation_name: str, logger: Optional[EnterpriseLogger] = None, **extra_metrics):
    """Context manager for automatic performance logging"""
    if logger is None:
        logger = get_logger('performance')
    
    logger.info(f"Starting operation: {operation_name}")
    operation_id = _performance_tracker.start_operation(operation_name)
    
    try:
        yield
        metrics = _performance_tracker.end_operation(operation_id, **extra_metrics)
        logger.info(f"Operation successful: {operation_name}", **metrics)
    except Exception as e:
        _performance_tracker.end_operation(operation_id, success=False, error=str(e))
        logger.error(f"Operation failed: {operation_name}", exception=e, **extra_metrics)
        raise


def log_function_performance(func):
    """Decorator for automatic function performance logging"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        with log_performance(f"{func.__name__}", logger):
            return func(*args, **kwargs)
    return wrapper


def log_processing_stats(
    operation: str,
    files_processed: int,
    rows_processed: int,
    duration: float,
    errors: int = 0,
    **extra_stats
):
    """Log standardized processing statistics using family-based dynamic formatting"""
    logger = get_logger('stats')
    
    stats = {
        'operation': operation,
        'files_processed': files_processed,
        'rows_processed': rows_processed,
        'duration': duration,
        'files_per_second': round(files_processed / duration, 2) if duration > 0 else 0,
        'rows_per_second': round(rows_processed / duration, 2) if duration > 0 else 0,
        'errors': errors,
        'success_rate': round((files_processed - errors) / files_processed * 100, 1) if files_processed > 0 else 0,
        **extra_stats
    }
    
    logger.info(f"Processing complete: {operation}", **stats)
    return stats


def _parse_file_size(size_str: str) -> int:
    """Parse file size string like '10MB' to bytes"""
    size_str = size_str.upper()
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


# Convenience function for quick setup
def quick_setup(level='INFO', log_file=None):
    """Quick logging setup for simple use cases"""
    set_up_logging(
        level=level,
        log_file=log_file,
        json_file=f"{log_file}.json" if log_file else None,
        enable_colors=True,
        enable_performance=True
    )


# Example usage demonstrating family-based dynamic formatting
if __name__ == "__main__":
    print("=== Enterprise Logger with Function Fallback Demo ===")
    
    # Set up logging with corrected format syntax
    set_up_logging(
        level='DEBUG',
        log_file='demo.log',
        console_format=('{{#level_color_map@bold;[;levelname;]}} {{message}}'
                       '{{$has_items; (;file_count; files)}}'
                       '{{ in ;duration;$duration_format}}'
                       '{{$has_errors; [;error_count; ERRORS]}}')
    )
    
    logger = get_logger('demo')
    
    # Demonstrate various logging scenarios
    logger.info("Application started")
    
    logger.info("Processing files", file_count=150, duration=2.45)
    
    logger.warning("Slow operation detected", duration=8.2)
    
    logger.error("Processing failed", error_count=5, file_count=100)
    
    # Demonstrate performance logging
    with log_performance("demo_operation"):
        import time
        time.sleep(0.1)  # Simulate work
        logger.info("Work completed", file_count=1000, duration=0.095)
    
    # Demonstrate processing stats
    log_processing_stats(
        operation="batch_process",
        files_processed=100,
        rows_processed=50000,
        duration=12.5,
        errors=2
    )
    
    print("\n✅ Function fallback integration complete!")
    print("Features now working:")
    print("• Color functions: #level_color_map maps levels to colors")
    print("• Conditional functions: $has_items shows/hides sections")
    print("• Format functions: $duration_format for time display")
    print("• Proper formatting isolation and resets")
    print("\nCheck demo.log and console output for results!")