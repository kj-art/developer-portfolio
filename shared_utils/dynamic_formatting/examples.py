"""
Comprehensive examples showcasing all dynamic formatting features.

This module demonstrates every capability of the dynamic formatting system
including function fallback, all token types, escape sequences, custom
delimiters, and real-world usage patterns.

Run this file directly to see all features in action:
    python examples.py
"""

import logging
import time
import random
import sys
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add the project root to path so we can import as a package
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared_utils.dynamic_formatting import (
        DynamicFormatter, 
        DynamicLoggingFormatter,
        DynamicFormattingError,
        FunctionExecutionError,
        FormatterError
    )
    print("✓ Successfully imported dynamic formatting package!")
except ImportError:
    # Fallback: try importing from current directory (if modules are here)
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        # Import individual modules directly to avoid relative import issues
        import formatters
        import dynamic_formatting as df_module
        import formatting_state
        
        DynamicFormatter = df_module.DynamicFormatter
        DynamicLoggingFormatter = df_module.DynamicLoggingFormatter
        DynamicFormattingError = df_module.DynamicFormattingError
        FunctionExecutionError = formatters.FunctionExecutionError
        FormatterError = formatters.FormatterError
        
        print("✓ Successfully imported via fallback method!")
        
    except ImportError as e:
        print(f"Could not import dynamic formatting modules: {e}")
        print("Make sure you've saved all the artifact files in this directory:")
        print("- dynamic_formatting.py")
        print("- formatters.py") 
        print("- formatting_state.py")
        print("- token_parsing.py")
        print("- span_structures.py")
        print("- __init__.py")
        sys.exit(1)


# ============================================================================
# COMPREHENSIVE FEATURE SHOWCASE
# ============================================================================

def demo_all_color_features():
    """Demonstrate all color formatting capabilities"""
    print("=== Color Features ===")
    
    # 1. Built-in ANSI colors
    formatter = DynamicFormatter("{{#red;ANSI Red: ;message}} {{#blue;ANSI Blue: ;message}}")
    result = formatter.format(message="test")
    print(f"1. ANSI colors: {result}")
    
    # 2. Hex colors
    formatter = DynamicFormatter("{{#ff0000;Hex Red: ;message}} {{#0000ff;Hex Blue: ;message}}")
    result = formatter.format(message="test")
    print(f"2. Hex colors: {result}")
    
    # 3. Named colors (matplotlib)
    formatter = DynamicFormatter("{{#crimson;Named Red: ;message}} {{#navy;Named Blue: ;message}}")
    result = formatter.format(message="test")
    print(f"3. Named colors: {result}")
    
    # 4. Color override behavior
    formatter = DynamicFormatter("{{#red#green#blue;Multiple colors: ;message}}")
    result = formatter.format(message="should be blue")
    print(f"4. Color override: {result}")
    
    # 5. Color function fallback
    def status_color(status):
        return {'success': 'green', 'error': 'red', 'warning': 'yellow'}.get(status, 'white')
    
    formatter = DynamicFormatter("{{#status_color;Status: ;status}}", functions={'status_color': status_color})
    result = formatter.format(status="error")
    print(f"5. Color function: {result}")


def demo_function_fallback_mechanics():
    """Demonstrate exactly how function fallback works"""
    print("\n=== Function Fallback Mechanics ===")
    
    def field_based_color(field_value):
        """Function receives the actual field value, not other format data"""
        if 'error' in str(field_value).lower():
            return 'red'
        elif 'warning' in str(field_value).lower():
            return 'yellow'
        elif 'success' in str(field_value).lower():
            return 'green'
        else:
            return 'white'
    
    def field_based_style(field_value):
        """Text style based on field content"""
        if str(field_value).isupper():
            return 'bold'
        elif len(str(field_value)) > 10:
            return 'italic'
        else:
            return 'normal'
    
    functions = {
        'field_based_color': field_based_color,
        'field_based_style': field_based_style
    }
    
    # Function receives the field value it's applied to
    formatter = DynamicFormatter(
        "{{#field_based_color@field_based_style;Status: ;message}}",
        functions=functions
    )
    
    test_cases = [
        "ERROR: System down",
        "warning: slow response", 
        "SUCCESS",
        "normal operation status"
    ]
    
    for i, message in enumerate(test_cases, 1):
        result = formatter.format(message=message)
        print(f"{i}. Message '{message}' → {result}")
    
    print("\nFunction call details:")
    print("- field_based_color() receives: the value of 'message' field")
    print("- field_based_style() receives: the value of 'message' field")
    print("- Both functions operate on the same field value")


def demo_all_text_features():
    """Demonstrate all text formatting capabilities"""
    print("\n=== Text Style Features ===")
    
    # 1. Individual text styles
    styles = ['bold', 'italic', 'underline']
    for style in styles:
        formatter = DynamicFormatter(f"{{@{style};{style.title()}: ;message}}")
        result = formatter.format(message="text")
        print(f"1. {style}: {result}")
    
    # 2. Combined text styles
    formatter = DynamicFormatter("{{@bold@italic@underline;All styles: ;message}}")
    result = formatter.format(message="emphasized")
    print(f"2. Combined styles: {result}")
    
    # 3. Text style function fallback
    def emphasis_level(message):
        # Use message content to determine emphasis
        if len(message) > 10:
            return 'bold'
        elif len(message) > 5:
            return 'italic'
        return 'normal'
    
    formatter = DynamicFormatter("{{@emphasis_level;Priority: ;message}}", 
                                functions={'emphasis_level': emphasis_level})
    result = formatter.format(message="critical-alert-system-failure")
    print(f"3. Text function: {result}")
    
    # 4. Reset behavior
    formatter = DynamicFormatter("{{@bold@italic@reset;Reset test: ;message}}")
    result = formatter.format(message="should be normal")
    print(f"4. Reset styles: {result}")


def demo_conditional_features():
    """Demonstrate all conditional formatting capabilities"""
    print("\n=== Conditional Features ===")
    
    def has_items(count):
        return count > 0
    
    def is_urgent(priority):
        return priority > 7
    
    def has_errors(error_count):
        return error_count > 0
    
    functions = {
        'has_items': has_items,
        'is_urgent': is_urgent,
        'has_errors': has_errors
    }
    
    # 1. Section-level conditionals
    formatter = DynamicFormatter(
        "{{Processing}} {{?has_items;found ;item_count; items}} {{?has_errors;with ;error_count; errors}}",
        functions=functions
    )
    
    result1 = formatter.format(item_count=25, error_count=3)
    result2 = formatter.format(item_count=0, error_count=0)
    print(f"1. Section conditionals (with data): '{result1}'")
    print(f"2. Section conditionals (no data): '{result2}'")
    
    # 3. Inline conditionals
    formatter = DynamicFormatter(
        "{{Task{?is_urgent} - URGENT{?has_errors} - ERRORS: ;task_name}}",
        functions=functions
    )
    
    result3 = formatter.format(task_name="deployment", priority=9, error_count=2)
    result4 = formatter.format(task_name="cleanup", priority=3, error_count=0)
    print(f"3. Inline conditionals (urgent+errors): {result3}")
    print(f"4. Inline conditionals (normal): {result4}")
    
    # 5. Mixed section and inline conditionals
    formatter = DynamicFormatter(
        "{{Status{?is_urgent} URGENT: ;status}} {{?has_errors;Found ;error_count; issues}}",
        functions=functions
    )
    
    result5 = formatter.format(status="deploy", priority=8, error_count=1)
    print(f"5. Mixed conditionals: {result5}")


def demo_escape_sequences():
    """Demonstrate comprehensive escape sequence handling"""
    print("\n=== Escape Sequences ===")
    
    # 1. Basic brace escaping
    formatter = DynamicFormatter("{{Use \\{variable\\} syntax: ;example}}")
    result = formatter.format(example="name")
    print(f"1. Escaped braces: '{result}'")
    
    # 2. Delimiter escaping
    formatter = DynamicFormatter("{{Path: ;path}}", delimiter=';')
    result = formatter.format(path="C:\\Program Files\\app\\file.txt")
    print(f"2. Path with delimiters: '{result}'")
    
    # 3. Mixed escaping with formatting
    formatter = DynamicFormatter("{{#red;Error in \\{module\\}: ;error}}")
    result = formatter.format(error="syntax error")
    print(f"3. Escaping with formatting: {result}")
    
    # 4. Escaping with conditionals
    def has_value(value):
        return bool(value)
    
    formatter = DynamicFormatter(
        "{{Config{?has_value} \\{key\\}=\\{value\\}: ;setting}}",
        functions={'has_value': has_value}
    )
    
    result4 = formatter.format(setting="debug=true")
    result5 = formatter.format(setting="")
    print(f"4. Escaping with conditionals (has value): '{result4}'")
    print(f"5. Escaping with conditionals (no value): '{result5}'")
    
    # 6. Multiple fields combined
    formatter1 = DynamicFormatter("{{Status: ;status}}")
    formatter2 = DynamicFormatter("{{Count: ;count}}")
    result1 = formatter1.format(status="success")
    result2 = formatter2.format(count=42)
    combined = f"{result1}, {result2}"
    print(f"6. Multiple field output: {combined}")


def demo_custom_delimiters():
    """Demonstrate custom delimiter functionality"""
    print("\n=== Custom Delimiters ===")
    
    # 1. Pipe delimiter
    formatter = DynamicFormatter("{{#red|Error: |message}}", delimiter='|')
    result = formatter.format(message="Connection failed")
    print(f"1. Pipe delimiter: {result}")
    
    # 2. Double colon delimiter
    formatter = DynamicFormatter("{{@bold::Status: ::status}}", delimiter='::')
    result = formatter.format(status="Running")
    print(f"2. Double colon delimiter: {result}")
    
    # 3. Custom delimiter with paths
    formatter = DynamicFormatter("{{Path: |path}}", delimiter='|')
    result = formatter.format(path="file.txt|backup.txt")
    print(f"3. Custom delimiter with paths: '{result}'")


def demo_field_formatting():
    """Demonstrate inline field formatting"""
    print("\n=== Field Formatting ===")
    
    def importance_color(level):
        return {'low': 'cyan', 'medium': 'yellow', 'high': 'red'}[level]
    
    # 1. Field with inline formatting
    formatter = DynamicFormatter("{{Task: {#red}task_name}} priority: {{importance}}")
    result = formatter.format(task_name="Deploy", importance="high")
    print(f"1. Field formatting: {result}")
    
    # 2. Field with function formatting
    formatter = DynamicFormatter("{{Task: {#importance_color}task_name}} ({{importance}})", 
                                functions={'importance_color': importance_color})
    result = formatter.format(task_name="Deploy", importance="high")
    print(f"2. Field function formatting: {result}")
    
    # 3. Complex field combinations
    formatter = DynamicFormatter("{{Status: {#green@bold}status}} - {{message}}")
    result = formatter.format(status="RUNNING", message="All systems operational")
    print(f"3. Complex field formatting: {result}")


def demo_complex_combinations():
    """Demonstrate complex feature combinations"""
    print("\n=== Complex Combinations ===")
    
    def level_color(level):
        return {'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow', 
                'ERROR': 'red', 'CRITICAL': 'magenta'}[level]
    
    def level_style(level):
        return 'bold' if level in ['ERROR', 'CRITICAL'] else 'normal'
    
    def has_duration(duration):
        return duration > 0
    
    def has_memory(memory):
        return memory > 0
    
    functions = {
        'level_color': level_color,
        'level_style': level_style,
        'has_duration': has_duration,
        'has_memory': has_memory
    }
    
    # Complex logging-style formatter
    formatter = DynamicFormatter(
        "{{#level_color@level_style;[;levelname;]}} {{message}} "
        "{{?has_duration;in ;duration;s}} {{?has_memory;using ;memory;MB}}",
        functions=functions
    )
    
    # Test various scenarios
    scenarios = [
        {'levelname': 'ERROR', 'message': 'Database connection failed', 'duration': 2.5, 'memory': 45},
        {'levelname': 'INFO', 'message': 'Process completed', 'duration': 0.1, 'memory': 0},
        {'levelname': 'WARNING', 'message': 'Slow query detected', 'duration': 8.3, 'memory': 0},
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        result = formatter.format(**scenario)
        print(f"{i}. Complex scenario: {result}")


def demo_fun_examples():
    """Demonstrate fun and creative uses"""
    print("\n=== Fun Examples ===")
    
    # 1. Random color chaos
    def random_color(field):
        return random.choice(['red', 'green', 'blue', 'yellow', 'cyan', 'magenta'])
    
    rc = "{#random_color}"
    formatter = DynamicFormatter(
        f"{{{{A{rc}B{rc}C ;{rc}field; {rc}X{rc}Y{rc}Z}}}}",
        functions={'random_color': random_color}
    )
    
    def same_code_different_colors():
        return formatter.format(field="FIELD_VALUE")
    results = [same_code_different_colors(), same_code_different_colors(), same_code_different_colors()]
    print(f"1. Random character colors: \n\ta. {results[0]} \n\tb. {results[1]} \n\tc. {results[2]}")
    print(f"   Raw: \n\ta. {repr(results[0])} \n\tb. {repr(results[1])} \n\tc. {repr(results[2])}")
    
    # 2. Progress bar simulation
    def progress_color(percentage):
        if percentage < 30:
            return 'red'
        elif percentage < 70:
            return 'yellow'
        else:
            return 'green'
    
    def show_bar(bar_field):
        return bool(bar_field and bar_field.strip())
    
    formatter = DynamicFormatter(
        "{{#progress_color@bold;Progress: ;percentage;%}} {{?show_bar;[;bar;]}}",
        functions={'progress_color': progress_color, 'show_bar': show_bar}
    )
    
    for pct in [15, 45, 85]:
        bar = '█' * (pct // 10) + '░' * (10 - pct // 10)
        result = formatter.format(percentage=pct, bar=bar)
        print(f"2. Progress {pct}%: {result}")
    
    # 3. Dynamic emphasis based on content
    def content_emphasis(text):
        if 'ERROR' in text.upper():
            return 'bold'
        elif 'WARNING' in text.upper():
            return 'italic'
        else:
            return 'normal'
    
    def content_color(text):
        if 'SUCCESS' in text.upper():
            return 'green'
        elif 'ERROR' in text.upper():
            return 'red'
        elif 'WARNING' in text.upper():
            return 'yellow'
        else:
            return 'white'
    
    formatter = DynamicFormatter(
        "{{#content_color@content_emphasis;Message: ;message}}",
        functions={'content_emphasis': content_emphasis, 'content_color': content_color}
    )
    
    messages = ["Task completed successfully", "Warning: Low disk space", "Error: Connection timeout"]
    for i, msg in enumerate(messages, 1):
        result = formatter.format(message=msg)
        print(f"3. Dynamic emphasis {i}: {result}")


def demo_real_world_patterns():
    """Demonstrate real-world usage patterns"""
    print("\n=== Real-World Patterns ===")
    
    # 1. API Response Formatting
    def status_color(code):
        if 200 <= code < 300:
            return 'green'
        elif 400 <= code < 500:
            return 'yellow'
        else:
            return 'red'
    
    def has_data(count):
        return count > 0
    
    def has_errors(errors):
        return errors > 0
    
    api_formatter = DynamicFormatter(
        "{{#status_color@bold;HTTP ;status_code}} {{?has_data;- ;record_count; records}} {{?has_errors;- ;error_count; errors}}",
        functions={'status_color': status_color, 'has_data': has_data, 'has_errors': has_errors}
    )
    
    responses = [
        {'status_code': 200, 'record_count': 150, 'error_count': 0},
        {'status_code': 404, 'record_count': 0, 'error_count': 1},
        {'status_code': 500, 'record_count': 0, 'error_count': 3}
    ]
    
    for i, response in enumerate(responses, 1):
        result = api_formatter.format(**response)
        print(f"1. API Response {i}: {result}")
    
    # 2. Build System Output
    def build_status_color(status):
        return {'SUCCESS': 'green', 'FAILED': 'red', 'BUILDING': 'yellow'}[status]
    
    def show_duration(duration):
        return duration > 0
    
    def show_tests(test_count):
        return test_count > 0
    
    build_formatter = DynamicFormatter(
        "{{#build_status_color@bold;Build ;status}} {{?show_duration;in ;duration;s}} {{?show_tests;- ;test_count; tests passed}}",
        functions={'build_status_color': build_status_color, 'show_duration': show_duration, 'show_tests': show_tests}
    )
    
    builds = [
        {'status': 'SUCCESS', 'duration': 45, 'test_count': 127},
        {'status': 'FAILED', 'duration': 12, 'test_count': 0},
        {'status': 'BUILDING', 'duration': 0, 'test_count': 0}
    ]
    
    for i, build in enumerate(builds, 1):
        result = build_formatter.format(**build)
        print(f"2. Build Status {i}: {result}")
    
    # 3. File Processing Status
    def processing_color(status):
        if '/' in status:
            processed, total = map(int, status.split('/'))
            percentage = (processed / total) * 100 if total > 0 else 0
            if percentage >= 100:
                return 'green'
            elif percentage >= 50:
                return 'yellow'
            else:
                return 'red'
        return 'white'
    
    def has_rate(rate):
        return rate > 0
    
    def has_failures(failures):
        return failures > 0
    
    file_formatter = DynamicFormatter(
        "{{#processing_color;Processing: ;status}} {{?has_rate;at ;rate; files/sec}} {{?has_failures;(;failures; failed)}}",
        functions={'processing_color': processing_color, 'has_rate': has_rate, 'has_failures': has_failures}
    )
    
    progress_updates = [
        {'status': '450/1000', 'rate': 125, 'failures': 0},
        {'status': '750/1000', 'rate': 85, 'failures': 3},
        {'status': '1000/1000', 'rate': 0, 'failures': 8}
    ]
    
    for i, update in enumerate(progress_updates, 1):
        result = file_formatter.format(**update)
        print(f"3. File Processing {i}: {result}")


def demo_edge_cases():
    """Demonstrate edge cases and error handling"""
    print("\n=== Edge Cases & Error Handling ===")
    
    # 1. Empty fields with conditionals
    def is_present(value):
        return bool(value and str(value).strip())
    
    formatter = DynamicFormatter(
        "{{Status}} {{?is_present;: ;optional_field}}",
        functions={'is_present': is_present}
    )
    
    result1 = formatter.format(optional_field="active")
    result2 = formatter.format(optional_field="")
    result3 = formatter.format()  # Missing field
    print(f"1. Optional field (present): '{result1}'")
    print(f"2. Optional field (empty): '{result2}'")
    print(f"3. Optional field (missing): '{result3}'")
    
    # 2. Function chaining example
    def get_level(priority):
        if priority > 8:
            return 'CRITICAL'
        elif priority > 5:
            return 'WARNING'
        else:
            return 'INFO'
    
    def level_color(level):
        return {'CRITICAL': 'red', 'WARNING': 'yellow', 'INFO': 'green'}[level]
    
    formatter = DynamicFormatter(
        "{{Priority: ;priority}} → {{#level_color@bold;Level: ;level}}",
        functions={'get_level': get_level, 'level_color': level_color}
    )
    
    # Manually chain the functions for this example
    for priority in [3, 7, 9]:
        level = get_level(priority)
        result = formatter.format(priority=priority, level=level)
        print(f"4. Chained functions (priority {priority}): {result}")
    
    # 3. Output mode switching
    console_formatter = DynamicFormatter("{{#red@bold;Console: ;message}}", output_mode='console')
    file_formatter = DynamicFormatter("{{#red@bold;File: ;message}}", output_mode='file')
    
    console_result = console_formatter.format(message="test")
    file_result = file_formatter.format(message="test")
    print(f"5. Console mode: {repr(console_result)}")
    print(f"6. File mode: {repr(file_result)}")


def run_comprehensive_demo():
    """Run all feature demonstrations"""
    print("Dynamic Formatting System - Comprehensive Feature Demo")
    print("=" * 60)
    print("This demo showcases every feature of the dynamic formatting system.\n")
    
    demo_functions = [
        demo_all_color_features,
        demo_function_fallback_mechanics,
        demo_all_text_features,
        demo_conditional_features,
        demo_escape_sequences,
        demo_custom_delimiters,
        demo_field_formatting,
        demo_complex_combinations,
        demo_fun_examples,
        demo_real_world_patterns,
        demo_edge_cases
    ]
    
    for demo_func in demo_functions:
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ Demo {demo_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Comprehensive demo complete!")
    print("\nKey features demonstrated:")
    print("• All color types: ANSI, hex, named, function fallback")
    print("• All text styles: bold, italic, underline, combinations")
    print("• All conditionals: section-level and inline")
    print("• Escape sequences: braces, delimiters, complex patterns")
    print("• Custom delimiters: pipe, double-colon, etc.")
    print("• Field formatting: inline formatting within field values")
    print("• Function fallback: dynamic token resolution")
    print("• Real-world patterns: APIs, builds, file processing")
    print("• Edge cases: empty fields, output modes, chaining")
    print("• Creative uses: random colors, progress bars, dynamic emphasis")


# ============================================================================
# LEGACY EXAMPLES (Preserved for Reference)
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


if __name__ == "__main__":
    run_comprehensive_demo()