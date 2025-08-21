"""
Comprehensive examples showcasing all dynamic formatting features.

This module demonstrates every capability of the dynamic formatting system
including function fallback, all token types, escape sequences, custom
delimiters, positional arguments, and real-world usage patterns.

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
        FormatterError,
        RequiredFieldError
    )
    # Use ASCII-safe checkmark that works on all Windows terminals
    print("[OK] Successfully imported dynamic formatting package!")
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
        RequiredFieldError = formatters.RequiredFieldError
        print("[OK] Successfully imported via fallback method!")
        
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
# CORE FEATURE DEMONSTRATION
# ============================================================================

def demo_core_feature_graceful_missing_data():
    """
    THE CORE FEATURE: Graceful handling of missing data
    
    This is the fundamental value proposition - template sections automatically
    disappear when their required data isn't provided, eliminating the need for
    manual null checking and conditional string building.
    """
    print("\n=== CORE FEATURE: Graceful Missing Data Handling ===")
    print("This is the primary innovation - sections automatically disappear when data is missing\n")
    
    # Template with multiple optional sections
    formatter = DynamicFormatter("{{#green;Status: ;status}} {{#blue;User: ;user}} {{#yellow;Count: ;count}}")
    
    # Scenario 1: All data present
    result = formatter.format(status="OK", user="admin", count=42)
    print(f"1. All data present: {result}")
    
    # Scenario 2: Missing user - user section disappears 
    result = formatter.format(status="OK", count=42)
    print(f"2. Missing user: {result}")
    
    # Scenario 3: Only status - other sections disappear
    result = formatter.format(status="ERROR")
    print(f"3. Only status: {result}")
    
    # Scenario 4: No data - completely empty result
    result = formatter.format()
    print(f"4. No data: '{result}' (empty)")
    
    print("\nKey insight: No conditional logic needed in your code!")
    print("Before: if status: msg += f'Status: {status} '")
    print("After:  formatter.format(status=status)  # Section disappears if None")


def demo_positional_arguments():
    """
    NEW FEATURE: Positional arguments support
    
    Use empty field names {{}} for cleaner templates when you have ordered data.
    Missing positional arguments cause later sections to disappear gracefully.
    """
    print("\n=== NEW FEATURE: Positional Arguments ===")
    print("Use {{}} syntax for ordered data without field names\n")
    
    # Template with positional arguments
    formatter = DynamicFormatter("{{#red;Error: ;}} {{Code: ;}} {{#yellow;Details: ;}}")
    
    # Scenario 1: All arguments provided
    result = formatter.format("Connection failed", 500, "Timeout after 30s")
    print(f"1. All args: {result}")
    
    # Scenario 2: Missing details - details section disappears
    result = formatter.format("Connection failed", 500)
    print(f"2. Missing details: {result}")
    
    # Scenario 3: Only error message
    result = formatter.format("Connection failed")
    print(f"3. Only error: {result}")
    
    # Scenario 4: Mixed positional and named (in separate sections)
    mixed_formatter = DynamicFormatter("{{Alert: ;}} {{User: ;username}} {{Time: ;}}")
    result = mixed_formatter.format("System overload", "admin")  # username section disappears
    print(f"4. Mixed template: {result}")
    
    print("\nBenefit: Cleaner templates for ordered data, still graceful with missing args")


# ============================================================================
# COLOR FORMATTING DEMONSTRATIONS
# ============================================================================

def demo_all_color_features():
    """Demonstrate all color formatting capabilities"""
    print("\n=== Color Formatting Features ===")
    
    # 1. Basic ANSI colors
    basic_colors = ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'white', 'black']
    print("1. Basic ANSI colors:")
    for color in basic_colors:
        formatter = DynamicFormatter(f"{{{{#{color};{color.capitalize()}: ;message}}}}")
        result = formatter.format(message="sample")
        print(f"   {result}")
    
    # 2. Hex colors
    print("\n2. Hex colors:")
    hex_colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff']
    color_names = ['Red', 'Green', 'Blue', 'Yellow', 'Magenta', 'Cyan']
    for hex_color, name in zip(hex_colors, color_names):
        formatter = DynamicFormatter(f"{{{{#{hex_color};{name}: ;message}}}}")
        result = formatter.format(message="hex")
        print(f"   {result}")
    
    # 3. Function-generated colors
    def dynamic_color(field_value):
        """Generate color based on content"""
        if 'error' in str(field_value).lower():
            return 'red'
        elif 'warning' in str(field_value).lower():
            return 'yellow'
        elif 'success' in str(field_value).lower():
            return 'green'
        else:
            return 'blue'
    
    print("\n3. Function-generated colors:")
    formatter = DynamicFormatter("{{#dynamic_color;Log: ;message}}", functions={'dynamic_color': dynamic_color})
    
    messages = ["Error occurred", "Warning: disk space", "Success: completed", "Info: processing"]
    for msg in messages:
        result = formatter.format(message=msg)
        print(f"   {result}")


def demo_function_fallback_mechanics():
    """Demonstrate the function fallback system"""
    print("\n=== Function Fallback Mechanics ===")
    
    # Create functions that return different types
    def error_color(field):
        return '#ff4444'  # Returns hex color
    
    def warning_emphasis(field):
        return 'bold'  # Returns text style
    
    def status_formatter(field):
        if field == 'online':
            return 'green'
        elif field == 'offline':
            return 'red'
        else:
            return 'yellow'
    
    # 1. Color function fallback
    formatter = DynamicFormatter(
        "{{#error_color;Error: ;message}} {{#warning_emphasis@bold;Warning: ;warning}}", 
        functions={
            'error_color': error_color,
            'warning_emphasis': warning_emphasis
        }
    )
    
    result = formatter.format(message="Critical failure", warning="Low memory")
    print(f"1. Color/style functions: {result}")
    
    # 2. Field-value dependent formatting
    formatter = DynamicFormatter(
        "{{#status_formatter;Server: ;status}}",
        functions={'status_formatter': status_formatter}
    )
    
    for status in ['online', 'offline', 'maintenance']:
        result = formatter.format(status=status)
        print(f"2. Status '{status}': {result}")
    
    # 3. Chained function priority
    def priority_color(priority):
        priority_map = {1: 'red', 2: 'yellow', 3: 'green'}
        return priority_map.get(priority, 'white')
    
    formatter = DynamicFormatter(
        "{{#priority_color;Priority ;priority;: ;message}}",
        functions={'priority_color': priority_color}
    )
    
    for priority in [1, 2, 3]:
        result = formatter.format(priority=priority, message=f"Task level {priority}")
        print(f"3. Priority {priority}: {result}")


# ============================================================================
# TEXT FORMATTING DEMONSTRATIONS  
# ============================================================================

def demo_all_text_features():
    """Demonstrate all text formatting capabilities"""
    print("\n=== Text Formatting Features ===")
    
    # 1. Individual text styles
    print("1. Individual text styles:")
    styles = ['bold', 'italic', 'underline', 'strikethrough', 'dim']
    for style in styles:
        formatter = DynamicFormatter(f"{{{{@{style};{style.capitalize()}: ;text}}}}")
        result = formatter.format(text="sample")
        print(f"   {result}")
    
    # 2. Combined styles
    print("\n2. Combined text styles:")
    combinations = [
        'bold@italic',
        'bold@underline', 
        'italic@underline',
        'bold@italic@underline'
    ]
    for combo in combinations:
        formatter = DynamicFormatter(f"{{{{@{combo};Combined: ;text}}}}")
        result = formatter.format(text="sample")
        print(f"   {result}")
    
    # 3. Color + text style combinations
    print("\n3. Color + text style combinations:")
    color_style_combos = [
        '#red@bold',
        '#green@italic',
        '#blue@underline',
        '#yellow@bold@italic'
    ]
    for combo in color_style_combos:
        formatter = DynamicFormatter(f"{{{{@{combo};Styled: ;text}}}}")
        result = formatter.format(text="sample")
        print(f"   {result}")


# ============================================================================
# CONDITIONAL FORMATTING DEMONSTRATIONS
# ============================================================================

def demo_conditional_features():
    """Demonstrate conditional section visibility"""
    print("\n=== Conditional Features ===")
    
    # Define conditional functions
    def is_error(field_value):
        return 'error' in str(field_value).lower()
    
    def has_user(user_field):
        return user_field is not None and user_field.strip()
    
    def is_high_priority(priority):
        return priority and int(priority) <= 2
    
    # 1. Section-level conditionals
    print("1. Section-level conditionals:")
    formatter = DynamicFormatter(
        "{{Message: ;message}} {{?is_error;#red;ERROR FLAG}} {{?has_user;User: ;user}}",
        functions={
            'is_error': is_error,
            'has_user': has_user
        }
    )
    
    test_cases = [
        {'message': 'System running normally', 'user': 'admin'},
        {'message': 'Error in database connection', 'user': 'admin'},
        {'message': 'Error in database connection', 'user': ''},
        {'message': 'Task completed'},
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = formatter.format(**case)
        print(f"   Test {i}: {result}")
    
    # 2. Inline conditionals  
    print("\n2. Inline conditionals:")
    formatter = DynamicFormatter(
        "{{Task ;task_id;}} {{?is_high_priority;(#red@bold;HIGH PRIORITY;)}}",
        functions={'is_high_priority': is_high_priority}
    )
    
    priorities = [1, 3, 5]
    for priority in priorities:
        result = formatter.format(task_id=f"T{priority*100}", priority=priority)
        print(f"   Priority {priority}: {result}")


# ============================================================================
# ESCAPE SEQUENCES DEMONSTRATIONS
# ============================================================================

def demo_escape_sequences():
    """Demonstrate escape sequence handling"""
    print("\n=== Escape Sequences ===")
    
    # 1. Escaped braces
    print("1. Escaped braces:")
    formatter = DynamicFormatter("\\{\\{Not a template\\}\\} {{But this is: ;field}}")
    result = formatter.format(field="value")
    print(f"   Result: {result}")
    
    # 2. Escaped delimiters in templates
    print("\n2. Escaped delimiters:")
    formatter = DynamicFormatter("{{Field with \\; semicolon: ;field}}")
    result = formatter.format(field="test")
    print(f"   Result: {result}")
    
    # 3. Complex escaping
    print("\n3. Complex escaping:")
    formatter = DynamicFormatter("\\{\\{escaped\\}\\} {{Real: ;field}} \\{\\{more escaped\\}\\}")
    result = formatter.format(field="value")
    print(f"   Result: {result}")
    
    # 4. Literal formatting tokens
    print("\n4. Literal formatting tokens:")
    formatter = DynamicFormatter("{{Use \\#red and \\@bold for: ;field}}")
    result = formatter.format(field="formatting")
    print(f"   Result: {result}")


# ============================================================================
# CUSTOM DELIMITER DEMONSTRATIONS
# ============================================================================

def demo_custom_delimiters():
    """Demonstrate custom delimiter support"""
    print("\n=== Custom Delimiters ===")
    
    # 1. Pipe delimiter
    print("1. Pipe delimiter:")
    formatter = DynamicFormatter("{{#red|Error|field}} {{Status|status}}", delimiter='|')
    result = formatter.format(field="Critical failure", status="FAILED")
    print(f"   Result: {result}")
    
    # 2. Double colon delimiter  
    print("\n2. Double colon delimiter:")
    formatter = DynamicFormatter("{{#blue::Info::message}} {{Code::code}}", delimiter='::')
    result = formatter.format(message="Process completed", code=200)
    print(f"   Result: {result}")
    
    # 3. Custom delimiter with escaping
    print("\n3. Custom delimiter with escaping:")
    formatter = DynamicFormatter("{{Text with \\| pipe|field}}", delimiter='|')
    result = formatter.format(field="and value")
    print(f"   Result: {result}")


# ============================================================================
# FIELD FORMATTING DEMONSTRATIONS
# ============================================================================

def demo_field_formatting():
    """Demonstrate inline field formatting"""
    print("\n=== Field Formatting ===")
    
    # 1. Field-level color formatting
    print("1. Field-level formatting:")
    formatter = DynamicFormatter("{{Status: ;status}} {{User: ;{#blue}user}}")
    result = formatter.format(status="Active", user="admin")
    print(f"   Result: {result}")
    
    # 2. Field-level text formatting
    print("\n2. Field text formatting:")
    formatter = DynamicFormatter("{{Normal: ;normal}} {{Bold: ;{@bold}bold_field}}")
    result = formatter.format(normal="regular", bold_field="emphasized")
    print(f"   Result: {result}")
    
    # 3. Combined field formatting
    print("\n3. Combined field formatting:")
    formatter = DynamicFormatter("{{Error: ;{#red@bold}error_msg}} {{Info: ;{#blue@italic}info}}")
    result = formatter.format(error_msg="Critical", info="Details")
    print(f"   Result: {result}")


# ============================================================================
# COMPLEX COMBINATIONS
# ============================================================================

def demo_complex_combinations():
    """Demonstrate complex feature combinations"""
    print("\n=== Complex Feature Combinations ===")
    
    # Define helper functions
    def severity_color(severity):
        severity_map = {
            'critical': '#ff0000',  # Red
            'high': '#ff8800',      # Orange  
            'medium': '#ffff00',    # Yellow
            'low': '#88ff88',       # Light green
            'info': '#8888ff'       # Light blue
        }
        return severity_map.get(severity, '#ffffff')
    
    def has_details(details):
        return details and details.strip()
    
    def format_timestamp(timestamp):
        return timestamp.strftime("%H:%M:%S") if timestamp else ""
    
    # 1. Security alert formatter
    print("1. Security alert system:")
    formatter = DynamicFormatter(
        "{{#severity_color@bold;[;severity;] ;message}} "
        "{{?has_details;#888888;(;details;)}} "
        "{{#888888;at ;{@italic}timestamp}}",
        functions={
            'severity_color': severity_color,
            'has_details': has_details,
            'format_timestamp': format_timestamp
        }
    )
    
    alerts = [
        {'severity': 'critical', 'message': 'Unauthorized access attempt', 'details': 'Multiple failed logins', 'timestamp': datetime.now()},
        {'severity': 'medium', 'message': 'Disk space warning', 'timestamp': datetime.now()},
        {'severity': 'info', 'message': 'Backup completed successfully', 'details': '1.2GB archived', 'timestamp': datetime.now()},
    ]
    
    for alert in alerts:
        result = formatter.format(**alert)
        print(f"   {result}")
    
    # 2. Build status reporter
    print("\n2. Build status reporter:")
    def build_color(status):
        return {'success': 'green', 'failed': 'red', 'running': 'yellow'}.get(status, 'white')
    
    def has_artifacts(artifacts):
        return artifacts and len(artifacts) > 0
    
    formatter = DynamicFormatter(
        "{{#build_color@bold;Build ;build_id; ;status}} "
        "{{Duration: ;duration;s}} "
        "{{?has_artifacts;Artifacts: ;artifacts}}",
        functions={'build_color': build_color, 'has_artifacts': has_artifacts}
    )
    
    builds = [
        {'build_id': '#1234', 'status': 'success', 'duration': 45, 'artifacts': ['app.zip', 'docs.pdf']},
        {'build_id': '#1235', 'status': 'failed', 'duration': 12},
        {'build_id': '#1236', 'status': 'running', 'duration': 23},
    ]
    
    for build in builds:
        # Convert artifacts list to string for display
        if 'artifacts' in build:
            build['artifacts'] = ', '.join(build['artifacts'])
        result = formatter.format(**build)
        print(f"   {result}")


# ============================================================================
# FUN EXAMPLES
# ============================================================================

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


# ============================================================================
# REAL-WORLD PATTERNS
# ============================================================================

def demo_real_world_patterns():
    """Demonstrate real-world usage patterns"""
    print("\n=== Real-World Patterns ===")
    
    # 1. API response formatting
    print("1. API response formatting:")
    def status_color(code):
        if 200 <= code < 300:
            return 'green'
        elif 400 <= code < 500:
            return 'yellow'
        elif code >= 500:
            return 'red'
        else:
            return 'blue'
    
    formatter = DynamicFormatter(
        "{{#status_color@bold;HTTP ;status_code}} {{Method: ;method}} {{Path: ;path}} "
        "{{Duration: ;duration;ms}} {{?has_error;#red;Error: ;error}}",
        functions={'status_color': status_color, 'has_error': lambda e: bool(e)}
    )
    
    responses = [
        {'status_code': 200, 'method': 'GET', 'path': '/api/users', 'duration': 45},
        {'status_code': 404, 'method': 'GET', 'path': '/api/missing', 'duration': 12},
        {'status_code': 500, 'method': 'POST', 'path': '/api/data', 'duration': 2000, 'error': 'Database timeout'},
    ]
    
    for response in responses:
        result = formatter.format(**response)
        print(f"   {result}")
    
    # 2. File processing status
    print("\n2. File processing status:")
    def size_color(size_mb):
        if size_mb > 100:
            return 'red'
        elif size_mb > 10:
            return 'yellow'
        else:
            return 'green'
    
    formatter = DynamicFormatter(
        "{{Processing: ;filename}} {{#size_color;(;size_mb;MB)}} "
        "{{Status: ;status}} {{Records: ;record_count}}",
        functions={'size_color': size_color}
    )
    
    files = [
        {'filename': 'users.csv', 'size_mb': 2.5, 'status': 'Complete', 'record_count': 1500},
        {'filename': 'transactions.json', 'size_mb': 45.2, 'status': 'Processing'},
        {'filename': 'archive.zip', 'size_mb': 250.8, 'status': 'Error'},
    ]
    
    for file_info in files:
        result = formatter.format(**file_info)
        print(f"   {result}")


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

def demo_edge_cases():
    """Demonstrate edge case handling and error scenarios"""
    print("\n=== Edge Cases & Error Handling ===")
    
    # 1. Empty and None values
    print("1. Empty and None value handling:")
    formatter = DynamicFormatter("{{Name: ;name}} {{Age: ;age}} {{Email: ;email}}")
    
    test_data = [
        {'name': 'John', 'age': 30, 'email': 'john@test.com'},
        {'name': 'Jane', 'age': None, 'email': ''},
        {'name': '', 'age': 25},
        {}
    ]
    
    for i, data in enumerate(test_data, 1):
        result = formatter.format(**data)
        print(f"   Test {i}: '{result}'")
    
    # 2. Output mode differences
    print("\n2. Output mode differences:")
    template = "{{#red@bold;Error: ;message}}"
    console_formatter = DynamicFormatter(template, output_mode='console')
    file_formatter = DynamicFormatter(template, output_mode='file')
    
    console_result = console_formatter.format(message="test")
    file_result = file_formatter.format(message="test")
    print(f"   Console mode: {repr(console_result)}")
    print(f"   File mode: '{file_result}'")
    
    # 3. Function errors and fallbacks
    print("\n3. Function error handling:")
    def failing_function(field):
        raise ValueError("Function failed!")
    
    def fallback_color(field):
        return 'blue'  # Safe fallback
    
    # This should handle the function error gracefully
    formatter = DynamicFormatter(
        "{{#failing_function;Message: ;message}} {{#fallback_color;Backup: ;backup}}",
        functions={'failing_function': failing_function, 'fallback_color': fallback_color}
    )
    
    try:
        result = formatter.format(message="test", backup="works")
        print(f"   With function error: {result}")
    except Exception as e:
        print(f"   Function error: {e}")
    
    # 4. Positional argument edge cases
    print("\n4. Positional argument edge cases:")
    
    # Mixed arguments error
    try:
        formatter = DynamicFormatter("{{}} {{}}")
        formatter.format("pos", keyword="kw")
    except DynamicFormattingError as e:
        print(f"   Mixed args error: {e}")
    
    # Too many positional arguments
    try:
        formatter = DynamicFormatter("{{}}")
        formatter.format("first", "second")
    except DynamicFormattingError as e:
        print(f"   Too many args error: {e}")
    
    # Required field missing (positional)
    try:
        formatter = DynamicFormatter("{{!}}")
        formatter.format()
    except RequiredFieldError as e:
        print(f"   Required field error: {e}")


# ============================================================================
# COMPREHENSIVE DEMO RUNNER
# ============================================================================

def run_comprehensive_demo():
    """Run all feature demonstrations"""
    print("Dynamic Formatting System - Comprehensive Feature Demo")
    print("=" * 60)
    print("This demo showcases every feature of the dynamic formatting system.\n")
    
    demo_functions = [
        demo_core_feature_graceful_missing_data,  # CORE FEATURE FIRST
        demo_positional_arguments,  # NEW POSITIONAL ARGUMENTS FEATURE
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
            print(f"\n[ERROR] Demo {demo_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("[OK] Comprehensive demo complete!")
    print("\nKey features demonstrated:")
    print("• CORE: Graceful missing data handling - sections disappear when data is missing")
    print("• NEW: Positional arguments - simplified syntax for ordered data")
    print("• All color types: ANSI, hex, named, function fallback")
    print("• All text styles: bold, italic, underline, combinations")
    print("• All conditionals: section-level and inline")
    print("• Escape sequences: braces, delimiters, complex patterns")
    print("• Custom delimiters: pipe, double-colon, etc.")
    print("• Field formatting: inline formatting within field values")
    print("• Function fallback: dynamic token resolution")
    print("• Real-world patterns: APIs, builds, file processing")
    print("• Edge cases: empty fields, output modes, error handling")
    print("• Creative uses: random colors, progress bars, dynamic emphasis")


if __name__ == "__main__":
    run_comprehensive_demo()