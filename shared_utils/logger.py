"""
Professional logging system powered by StringSmith template formatting

This module provides enterprise-grade logging capabilities with StringSmith's
conditional formatting system, delivering rich visual output with automatic
graceful degradation for missing data.

StringSmith Integration Features:
- Conditional sections that disappear when data is missing
- Rich ANSI formatting with colors and text emphasis  
- Multi-parameter functions for complex conditional logic
- High-performance template caching for production workloads
- Thread-safe formatters for concurrent logging operations

Usage:
    from shared_utils.logger import set_up_logging, get_logger, log_performance
    
    set_up_logging(level='INFO', log_file='app.log', enable_colors=True)
    logger = get_logger(__name__)
    
    with log_performance("file_processing"):
        logger.info("Processing files", file_count=100, duration=2.5)
        # Output: "[INFO] Processing files (100 files) in 2.50s"
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

from .stringsmith import TemplateFormatter


class PerformanceTracker:
    """Thread-safe performance monitoring with StringSmith-powered reporting"""
    
    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()
        
    def start_operation(self, operation_name: str) -> str:
        """Start tracking an operation with unique ID"""
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        with self.lock:
            self.metrics[operation_id] = {
                'name': operation_name,
                'start_time': time.time(),
                'start_memory': self._get_memory_usage(),
            }
        return operation_id
        
    def end_operation(self, operation_id: str, **extra_metrics):
        """End tracking and return metrics"""
        with self.lock:
            if operation_id not in self.metrics:
                return None
                
            start_data = self.metrics[operation_id]
            duration = time.time() - start_data['start_time']
            memory_delta = self._get_memory_usage() - start_data['start_memory']
            
            metrics = {
                'operation': start_data['name'],
                'duration': duration,
                'memory_delta_mb': memory_delta,
                **extra_metrics
            }
            
            # Log performance metrics
            perf_logger = logging.getLogger('performance')
            perf_logger.info(f"Operation completed: {start_data['name']}", 
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


class StringSmithLoggingFormatter(logging.Formatter):
    """
    Logging formatter powered by StringSmith conditional templating
    
    Automatically handles missing log fields using StringSmith's graceful degradation.
    Sections disappear when their data is missing, eliminating manual null checking.
    """
    
    def __init__(self, template: str = None, enable_colors: bool = True):
        super().__init__()
        
        # Set up fallback formatter FIRST
        self.fallback_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Default professional log template showcasing StringSmith features
        if template is None:
            template = (
                "{{#level_color;[;levelname;]}} {{@italic#111111;asctime}} {{name}} "
                "{{?has_user_context;(User: ;user_id;) }}"
                "{{?has_request_id;[Req: ;request_id;] }}"
                "{{message}}"
                "{{?has_duration; in ;{$format_duration}duration}}"
                "{{?has_file_count; ;file_count; files)}}"
                "{{?has_error_count; - ;{$format_errors}error_count}}"
                "{{?has_memory_usage;;memory_usage_mb;MB]}}"
                "{{?is_slow_operation; ⚠️ SLOW ;duration;}}"
            )
        
        # StringSmith functions for dynamic log formatting
        def level_color(level):
            """Map log levels to colors"""
            colors = {
                'DEBUG': 'FFA500',
                'INFO': 'blue', 
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'magenta'
            }
            return colors.get(level, 'white')
        
        def format_duration(duration_val):
            """Format duration with appropriate units"""
            if isinstance(duration_val, str):
                try:
                    duration_val = float(duration_val)
                except ValueError:
                    return duration_val
                    
            if duration_val < 0.001:
                return f"{duration_val*1000000:.0f}μs"
            elif duration_val < 1:
                return f"{duration_val*1000:.1f}ms"
            elif duration_val < 60:
                return f"{duration_val:.2f}s"
            else:
                minutes = int(duration_val // 60)
                seconds = duration_val % 60
                return f"{minutes}m{seconds:.1f}s"
        
        def format_errors(error_count):
            """Format error count with appropriate emphasis"""
            try:
                count = int(error_count)
                if count == 1:
                    return "1 error"
                else:
                    return f"{count} errors"
            except (ValueError, TypeError):
                return str(error_count)
        
        # Conditional functions
        def has_user_context(user_id):
            return user_id is not None and str(user_id).strip() != ''
        
        def has_request_id(request_id):
            return request_id is not None and str(request_id).strip() != ''
            
        def has_duration(duration):
            return duration is not None
            
        def has_file_count(file_count):
            return file_count is not None and file_count > 0
            
        def has_error_count(error_count):
            return error_count is not None and error_count > 0
            
        def has_memory_usage(memory_usage_mb):
            return memory_usage_mb is not None
            
        def is_slow_operation(duration):
            try:
                return duration is not None and float(duration) > 5.0
            except (ValueError, TypeError):
                return False
            
        def has_file_name(file_name):
            return file_name is not None and str(file_name).strip() != ''
        
        def has_error(error):
            return error is not None and str(error).strip() != ''
        
        # Create StringSmith formatter with logging functions
        functions = [
            level_color,
            format_duration,
            format_errors,
            has_user_context,
            has_request_id,
            has_duration,
            has_file_count,
            has_error_count,
            has_memory_usage,
            is_slow_operation,
            has_file_name,
            has_error
        ]
        
        try:
            self.formatter = TemplateFormatter(template, functions=functions)
        except Exception as e:
            logging.getLogger(__name__).error(f"StringSmith formatter setup failed: {e}")
            self.formatter = None
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record using StringSmith conditional templating"""
        # Fallback to basic formatting if StringSmith failed to initialize
        if self.formatter is None:
            return self.fallback_formatter.format(record)
        
        # Build comprehensive log data dictionary
        log_data = {
            'message': record.getMessage(),
            'levelname': record.levelname,
            'name': record.name,
            'funcName': record.funcName,
            'lineno': record.lineno,
            'asctime': self.formatTime(record),
        }
        
        # Add extra data if present
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Add other record attributes (excluding private/system ones)
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_') and key not in ('msg', 'args'):
                log_data[key] = value
        
        try:
            # StringSmith handles missing fields gracefully - sections disappear automatically
            return self.formatter.format(**log_data)
        except Exception as e:
            # Robust fallback preserves logging functionality
            return self.fallback_formatter.format(record) + f" [STRINGSMITH ERROR: {e}]"


class JSONFormatter(logging.Formatter):
    """Standard JSON formatter for structured logging"""
    
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


class EnterpriseLogger:
    """Enhanced logger with StringSmith-powered formatting"""
    
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
        """Internal logging with StringSmith extra data support"""
        # Handle exception parameter specially
        exc_info = kwargs.get('exc_info')
        if 'exception' in kwargs and exc_info is None:
            # Convert exception object to exc_info tuple
            exception = kwargs.pop('exception')
            exc_info = (type(exception), exception, exception.__traceback__)
        
        # Filter out logging-specific parameters from extra data
        extra_data = {k: v for k, v in kwargs.items() 
                     if k not in ['exc_info', 'stack_info', 'stacklevel', 'exception']}
        
        if extra_data:
            # Create LogRecord with StringSmith-compatible extra data and exception info
            record = self.logger.makeRecord(
                self.logger.name, level, '', 0, message, (), 
                exc_info, extra={'extra_data': extra_data}
            )
            self.logger.handle(record)
        else:
            # Remove exc_info from kwargs to avoid passing it twice
            filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'exc_info'}
            self.logger.log(level, message, exc_info=exc_info, **filtered_kwargs)


def set_up_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    json_file: Optional[str] = None,
    enable_colors: bool = True,
    max_file_size: str = '10MB',
    backup_count: int = 5,
    console_template: Optional[str] = None,
    file_template: Optional[str] = None,
):
    """
    Setup enterprise logging with StringSmith-powered formatting
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to text log file  
        json_file: Path to JSON log file for structured logging
        enable_colors: Whether to use colored console output via StringSmith
        max_file_size: Maximum size of log files before rotation
        backup_count: Number of backup files to keep
        console_template: Custom StringSmith template for console output
        file_template: Custom StringSmith template for file output
        
    StringSmith Template Examples:
        Basic: "{{#level_color;[;levelname;]}} {{message}}"
        Rich: "{{#level_color;[;levelname;]}} {{message}}{{?has_duration; in ;duration;$format_duration}}{{?has_errors; (;error_count; errors)}}"
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with StringSmith formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = StringSmithLoggingFormatter(
        template=console_template,
        enable_colors=enable_colors
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with detailed StringSmith template (no colors for files)
    if log_file:
        if file_template is None:
            # Rich file template showcasing StringSmith conditional sections
            file_template = (
                "{{asctime}} - {{name}} - {{levelname}} - {{funcName}}:{{lineno}} - {{message}}"
                "{{ (;file_count; files)}}"
                "{{ - duration: ;{$format_duration}duration}}"  
                "{{ - size: ;file_size_mb;MB}}"
                "{{ - error: ;error_code;}}"
                "{{ - memory: ;memory_delta_mb;MB}}"
            )
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=_parse_file_size(max_file_size),
            backupCount=backup_count
        )
        
        # File formatter without colors but with rich conditional sections
        file_formatter = StringSmithLoggingFormatter(file_template, enable_colors=False)
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


def get_logger(name: Optional[str] = None) -> EnterpriseLogger:
    """Get an enhanced logger with StringSmith formatting capabilities"""
    if name is None:
        # Get the calling module's name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return EnterpriseLogger(name)


@contextmanager
def log_performance(operation_name: str, logger: Optional[EnterpriseLogger] = None, **extra_metrics):
    """Context manager for automatic performance logging with StringSmith formatting"""
    if logger is None:
        logger = get_logger('performance')
    
    logger.info(f"Starting operation: {operation_name}")
    operation_id = _performance_tracker.start_operation(operation_name)
    
    try:
        yield
        metrics = _performance_tracker.end_operation(operation_id, **extra_metrics)
        if metrics:
            logger.info(f"Operation successful: {operation_name}", **metrics)
    except Exception as e:
        _performance_tracker.end_operation(operation_id, success=False, error=str(e))
        logger.error(f"Operation failed: {operation_name}", exception=e, **extra_metrics)
        raise


def log_processing_stats(
    operation: str,
    files_processed: int,
    rows_processed: int = 0,
    duration: float = 0,
    errors: int = 0,
    **extra_stats
):
    """Log standardized processing statistics"""
    # Calculate derived statistics
    files_per_second = files_processed / duration if duration > 0 else 0
    success_rate = ((files_processed - errors) / files_processed * 100) if files_processed > 0 else 0
    
    stats = {
        'operation': operation,
        'files_processed': files_processed,
        'rows_processed': rows_processed,
        'duration': duration,
        'files_per_second': files_per_second,
        'success_rate': success_rate,
        'errors': errors,
        **extra_stats
    }
    
    logger = get_logger('stats')
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
def quick_setup(level='INFO', log_file=None, enable_colors=True):
    """Quick logging setup showcasing StringSmith's capabilities"""
    set_up_logging(
        level=level,
        log_file=log_file,
        json_file=f"{log_file}.json" if log_file else None,
        enable_colors=enable_colors
    )