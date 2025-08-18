"""
Real-world examples of dynamic formatting usage.

This module provides practical examples of how to use the dynamic formatting
system in various scenarios including logging, CLI tools, web applications,
and data processing pipelines.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List

from shared_utils.dynamic_formatting import (
    DynamicFormatter, 
    DynamicLoggingFormatter,
    DynamicFormattingError
)


# ============================================================================
# LOGGING EXAMPLES
# ============================================================================

def setup_advanced_logging():
    """
    Example: Advanced logging setup with dynamic formatting
    
    Demonstrates:
    - Function fallback for log levels
    - Conditional sections for optional data
    - Performance indicators
    - Memory usage formatting
    """
    
    def level_color(level_name):
        """Map log levels to colors"""
        colors = {
            'DEBUG': 'cyan',
            'INFO': 'green', 
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'magenta'
        }
        return colors.get(level_name.upper(), 'white')
    
    def performance_indicator(duration):
        """Add performance indicators based on duration"""
        if duration < 0.1:
            return "⚡"  # Fast
        elif duration < 1.0:
            return "✓"   # Normal
        elif duration < 5.0:
            return "⏳"  # Slow
        else:
            return "🐌"  # Very slow
    
    def has_duration(duration):
        """Check if duration should be displayed"""
        return duration and duration > 0
    
    def has_memory_info(memory_mb):
        """Check if memory info should be displayed"""
        return memory_mb and memory_mb > 0
    
    def has_file_count(count):
        """Check if file count should be displayed"""
        return count and count > 0
    
    # Create formatter with comprehensive features
    formatter = DynamicLoggingFormatter(
        "{{#level_color@bold;[;levelname;]}} {{asctime}} - {{name}} - {{message}}"
        "{{?has_file_count; (;file_count; files)}}"
        "{{?has_duration; in ;duration;s}}"
        "{{?has_memory_info; memory: ;memory_mb;MB}}"
        "{{?has_duration; ;performance_indicator;duration}}",
        functions={
            'level_color': level_color,
            'performance_indicator': performance_indicator,
            'has_duration': has_duration,
            'has_memory_info': has_memory_info,
            'has_file_count': has_file_count
        }
    )
    
    # Setup logger
    logger = logging.getLogger('example')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    return logger

def demo_logging():
    """Demonstrate advanced logging in action"""
    print("=== Advanced Logging Demo ===")
    
    logger = setup_advanced_logging()
    
    # Basic log messages
    logger.info("Application started")
    logger.debug("Loading configuration")
    
    # Logs with optional data
    logger.info("Processing files", extra={'extra_data': {
        'file_count': 150, 
        'duration': 2.45
    }})
    
    logger.warning("Slow operation detected", extra={'extra_data': {
        'duration': 8.2,
        'memory_mb': 45.6
    }})
    
    logger.error("Processing failed", extra={'extra_data': {
        'file_count': 25,
        'duration': 1.2,
        'memory_mb': 12.3
    }})


# ============================================================================
# CLI TOOL EXAMPLES  
# ============================================================================

def create_progress_formatter():
    """
    Example: CLI progress reporting with dynamic formatting
    
    Demonstrates:
    - Status-based coloring
    - Conditional error reporting
    - Rate calculations
    - Time formatting
    """
    
    def status_color(status):
        """Color based on operation status"""
        status_colors = {
            'running': 'yellow',
            'success': 'green',
            'error': 'red',
            'warning': 'yellow',
            'complete': 'blue'
        }
        return status_colors.get(status.lower(), 'white')
    
    def has_errors(error_count):
        """Check if errors should be displayed"""
        return error_count and error_count > 0
    
    def has_rate(rate):
        """Check if processing rate should be shown"""
        return rate and rate > 0
    
    def format_rate(rate):
        """Format processing rate with appropriate units"""
        if rate < 1:
            return f"{rate*1000:.0f}/s"
        elif rate < 100:
            return f"{rate:.1f}/s"
        else:
            return f"{rate:.0f}/s"
    
    return DynamicFormatter(
        "{{#status_color@bold;Status: ;status}} - {{processed}}/{{total}} "
        "{{?has_rate;at ;rate;$format_rate}} "
        "{{?has_errors;(;error_count; errors)}}",
        functions={
            'status_color': status_color,
            'has_errors': has_errors,
            'has_rate': has_rate,
            'format_rate': format_rate
        }
    )

def demo_cli_progress():
    """Demonstrate CLI progress reporting"""
    print("\n=== CLI Progress Demo ===")
    
    formatter = create_progress_formatter()
    
    # Simulate progress updates
    progress_data = [
        {'status': 'running', 'processed': 0, 'total': 100, 'rate': 0, 'error_count': 0},
        {'status': 'running', 'processed': 25, 'total': 100, 'rate': 12.5, 'error_count': 0},
        {'status': 'running', 'processed': 50, 'total': 100, 'rate': 15.2, 'error_count': 1},
        {'status': 'warning', 'processed': 75, 'total': 100, 'rate': 8.3, 'error_count': 3},
        {'status': 'complete', 'processed': 100, 'total': 100, 'rate': 10.1, 'error_count': 3}
    ]
    
    for data in progress_data:
        result = formatter.format(**data)
        print(f"Progress: {result}")
        time.sleep(0.5)


# ============================================================================
# DATA PROCESSING EXAMPLES
# ============================================================================

def create_data_summary_formatter():
    """
    Example: Data processing summary with comprehensive reporting
    
    Demonstrates:
    - Multiple conditional sections
    - Function-based calculations
    - Complex data relationships
    """
    
    def severity_color(error_count):
        """Color based on error severity"""
        if error_count == 0:
            return 'green'
        elif error_count < 5:
            return 'yellow'
        else:
            return 'red'
    
    def success_rate_color(rate):
        """Color based on success rate"""
        if rate >= 95:
            return 'green'
        elif rate >= 80:
            return 'yellow'
        else:
            return 'red'
    
    def has_warnings(count):
        return count > 0
    
    def has_skipped(count):
        return count > 0
    
    def has_duration(duration):
        return duration > 0
    
    def format_duration(seconds):
        """Format duration with appropriate units"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    def calculate_success_rate(processed, errors):
        """Calculate success rate percentage"""
        if processed == 0:
            return 0
        return ((processed - errors) / processed) * 100
    
    return DynamicFormatter(
        "{{@bold;Data Processing Summary:}}\n"
        "{{#blue;Processed:}} {{processed}} records\n"
        "{{#severity_color@bold;Errors: ;errors}} "
        "{{?has_warnings;(;warnings; warnings)}} "
        "{{?has_skipped;(;skipped; skipped)}}\n"
        "{{#success_rate_color;Success Rate: ;success_rate;%}}\n"
        "{{?has_duration;Duration: ;duration;$format_duration}}",
        functions={
            'severity_color': severity_color,
            'success_rate_color': success_rate_color,
            'has_warnings': has_warnings,
            'has_skipped': has_skipped,
            'has_duration': has_duration,
            'format_duration': format_duration,
            'success_rate': lambda x: calculate_success_rate(x.get('processed', 0), x.get('errors', 0))
        }
    )

def demo_data_processing():
    """Demonstrate data processing summary formatting"""
    print("\n=== Data Processing Summary Demo ===")
    
    formatter = create_data_summary_formatter()
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Perfect Run',
            'data': {
                'processed': 1000, 'errors': 0, 'warnings': 0, 
                'skipped': 0, 'duration': 45.2, 'success_rate': 100
            }
        },
        {
            'name': 'Some Issues',
            'data': {
                'processed': 850, 'errors': 12, 'warnings': 25, 
                'skipped': 5, 'duration': 67.8, 'success_rate': 98.6
            }
        },
        {
            'name': 'Major Problems',
            'data': {
                'processed': 500, 'errors': 45, 'warnings': 120, 
                'skipped': 30, 'duration': 123.4, 'success_rate': 91.0
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        result = formatter.format(**scenario['data'])
        print(result)


# ============================================================================
# WEB APPLICATION EXAMPLES
# ============================================================================

def create_api_response_formatter():
    """
    Example: API response formatting for web applications
    
    Demonstrates:
    - Status code coloring
    - Response time indicators
    - Conditional data display
    """
    
    def status_color(status_code):
        """Color HTTP status codes appropriately"""
        if 200 <= status_code < 300:
            return 'green'
        elif 300 <= status_code < 400:
            return 'blue'
        elif 400 <= status_code < 500:
            return 'yellow'
        else:
            return 'red'
    
    def response_time_color(ms):
        """Color response times based on performance"""
        if ms < 100:
            return 'green'
        elif ms < 500:
            return 'yellow'
        else:
            return 'red'
    
    def has_data(count):
        return count > 0
    
    def has_errors(errors):
        return errors and len(errors) > 0
    
    return DynamicFormatter(
        "{{#status_color@bold;HTTP ;status_code}} "
        "{{#response_time_color;(;response_time;ms)}} "
        "{{?has_data;- ;record_count; records}} "
        "{{?has_errors;- ;error_count; errors}}",
        functions={
            'status_color': status_color,
            'response_time_color': response_time_color,
            'has_data': has_data,
            'has_errors': has_errors
        }
    )

def demo_api_responses():
    """Demonstrate API response formatting"""
    print("\n=== API Response Demo ===")
    
    formatter = create_api_response_formatter()
    
    responses = [
        {'status_code': 200, 'response_time': 45, 'record_count': 150, 'error_count': 0},
        {'status_code': 201, 'response_time': 89, 'record_count': 1, 'error_count': 0},
        {'status_code': 400, 'response_time': 23, 'record_count': 0, 'error_count': 1},
        {'status_code': 500, 'response_time': 1250, 'record_count': 0, 'error_count': 3},
    ]
    
    for response in responses:
        result = formatter.format(**response)
        print(f"API Response: {result}")


# ============================================================================
# ERROR HANDLING EXAMPLES
# ============================================================================

def demo_error_handling():
    """
    Demonstrate proper error handling with dynamic formatting
    
    Shows best practices for:
    - Catching specific exceptions
    - Graceful degradation
    - Error logging
    """
    print("\n=== Error Handling Demo ===")
    
    def unreliable_function(value):
        """Function that sometimes fails"""
        if value == "fail":
            raise ValueError("Simulated failure")
        return "green" if value == "success" else "yellow"
    
    # Test cases for different error scenarios
    test_cases = [
        {
            'name': 'Valid Template + Valid Data',
            'template': "{{#blue;Status: ;status}}",
            'data': {'status': 'running'},
            'functions': {}
        },
        {
            'name': 'Missing Required Field',
            'template': "{{!#red;Critical: ;missing_field}}",
            'data': {'other_field': 'value'},
            'functions': {}
        },
        {
            'name': 'Function Execution Error',
            'template': "{{#unreliable_function;Status: ;status}}",
            'data': {'status': 'fail'},
            'functions': {'unreliable_function': unreliable_function}
        },
        {
            'name': 'Missing Function',
            'template': "{{#missing_function;Status: ;status}}",
            'data': {'status': 'test'},
            'functions': {}
        },
        {
            'name': 'Invalid Template Syntax',
            'template': "{{#red;Unclosed template",
            'data': {'status': 'test'},
            'functions': {}
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        
        try:
            formatter = DynamicFormatter(
                test_case['template'], 
                functions=test_case['functions']
            )
            result = formatter.format(**test_case['data'])
            print(f"✓ Success: {repr(result)}")
            
        except DynamicFormattingError as e:
            print(f"✗ Formatting Error: {type(e).__name__}: {e}")
            # In production, you might log this and use a fallback
            fallback = f"[FORMATTING ERROR] {test_case['data']}"
            print(f"  Fallback: {fallback}")
            
        except Exception as e:
            print(f"✗ Unexpected Error: {type(e).__name__}: {e}")


# ============================================================================
# PERFORMANCE EXAMPLES
# ============================================================================

def demo_performance_best_practices():
    """
    Demonstrate performance best practices
    
    Shows:
    - Formatter reuse vs recreation
    - Simple vs complex templates
    - Memory usage patterns
    """
    print("\n=== Performance Best Practices Demo ===")
    
    import time
    
    # Test data
    test_data = [
        {'level': 'INFO', 'message': f'Message {i}', 'count': i} 
        for i in range(1000)
    ]
    
    # BAD: Recreating formatter in loop
    print("❌ Bad Practice: Recreating formatter")
    start_time = time.time()
    results = []
    for data in test_data[:100]:  # Smaller sample for demo
        formatter = DynamicFormatter("{{#green;Level: ;level}} - {{message}}")
        results.append(formatter.format(**data))
    bad_time = time.time() - start_time
    print(f"   Time: {bad_time:.3f}s for 100 records")
    
    # GOOD: Reusing formatter
    print("✓ Good Practice: Reusing formatter")
    start_time = time.time()
    formatter = DynamicFormatter("{{#green;Level: ;level}} - {{message}}")
    results = []
    for data in test_data[:100]:
        results.append(formatter.format(**data))
    good_time = time.time() - start_time
    print(f"   Time: {good_time:.3f}s for 100 records")
    print(f"   Speedup: {bad_time/good_time:.1f}x faster")
    
    # Compare simple vs complex templates
    simple_formatter = DynamicFormatter("{{level}}: {{message}}")
    complex_formatter = DynamicFormatter(
        "{{#level_color@bold;[;level;]}} {{message}} {{?has_count;(;count; items)}}",
        functions={
            'level_color': lambda x: 'green',
            'has_count': lambda x: x > 0
        }
    )
    
    # Time simple formatting
    start_time = time.time()
    for data in test_data:
        simple_formatter.format(**data)
    simple_time = time.time() - start_time
    
    # Time complex formatting  
    start_time = time.time()
    for data in test_data:
        complex_formatter.format(**data)
    complex_time = time.time() - start_time
    
    print(f"\nTemplate Complexity Comparison (1000 records):")
    print(f"✓ Simple template: {simple_time:.3f}s")
    print(f"◐ Complex template: {complex_time:.3f}s")
    print(f"  Overhead: {complex_time/simple_time:.1f}x")


# ============================================================================
# MAIN DEMO RUNNER
# ============================================================================

def run_all_examples():
    """Run all example demonstrations"""
    print("Dynamic Formatting - Real-World Examples")
    print("=" * 50)
    
    try:
        demo_logging()
        demo_cli_progress()
        demo_data_processing()
        demo_api_responses()
        demo_error_handling()
        demo_performance_best_practices()
        
        print("\n" + "=" * 50)
        print("✅ All examples completed successfully!")
        print("\nKey Takeaways:")
        print("• Function fallback enables dynamic, context-aware formatting")
        print("• Conditional sections handle optional data gracefully")
        print("• Family-based architecture prevents formatting conflicts")
        print("• Proper error handling ensures robust production usage")
        print("• Formatter reuse is critical for performance")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()