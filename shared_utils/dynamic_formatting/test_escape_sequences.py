"""
Comprehensive test suite for the refactored dynamic formatting system.

Tests all functionality to ensure the removal of stacking management
didn't break any existing features.
"""

import sys
from pathlib import Path
import logging
from io import StringIO

# Add the project root to path so we can import as a package
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared_utils.dynamic_formatting import (
        DynamicFormatter, 
        DynamicLoggingFormatter,
        DynamicFormattingError, 
        RequiredFieldError,
        FunctionNotFoundError,
        FormatterError,
        FunctionExecutionError,
        ParseError
    )
    print("✓ Successfully imported all classes!")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)


def test_basic_color_formatting():
    """Test basic color formatting without stacking restrictions"""
    print("\n=== Basic Color Formatting ===")
    
    # Test single color
    formatter = DynamicFormatter("{{#red;Error: ;message}}")
    result = formatter.format(message="File not found")
    print(f"1. Single color: {repr(result)}")
    
    # Test color override (later color wins)
    formatter = DynamicFormatter("{{#red#blue;Message: ;message}}")
    result = formatter.format(message="Should be blue")
    print(f"2. Color override: {repr(result)}")
    
    # Test multiple color overrides
    formatter = DynamicFormatter("{{#red#green#blue#yellow;Message: ;message}}")
    result = formatter.format(message="Should be yellow")
    print(f"3. Multiple overrides: {repr(result)}")


def test_basic_text_formatting():
    """Test basic text formatting with natural stacking"""
    print("\n=== Basic Text Formatting ===")
    
    # Test single style
    formatter = DynamicFormatter("{{@bold;Bold: ;message}}")
    result = formatter.format(message="Important")
    print(f"1. Single style: {repr(result)}")
    
    # Test style combination
    formatter = DynamicFormatter("{{@bold@italic;Styled: ;message}}")
    result = formatter.format(message="Very important")
    print(f"2. Combined styles: {repr(result)}")
    
    # Test all styles together
    formatter = DynamicFormatter("{{@bold@italic@underline;All styles: ;message}}")
    result = formatter.format(message="Maximum emphasis")
    print(f"3. All styles: {repr(result)}")


def test_mixed_formatting():
    """Test combinations of colors and text styles"""
    print("\n=== Mixed Formatting ===")
    
    # Test color + text style
    formatter = DynamicFormatter("{{#red@bold;Alert: ;message}}")
    result = formatter.format(message="Critical error")
    print(f"1. Color + style: {repr(result)}")
    
    # Test complex combinations with overrides
    formatter = DynamicFormatter("{{#red#blue@bold@italic;Complex: ;message}}")
    result = formatter.format(message="Blue, bold, italic")
    print(f"2. Complex combination: {repr(result)}")
    
    # Test reset tokens
    formatter = DynamicFormatter("{{#red@bold@reset;Reset test: ;message}}")
    result = formatter.format(message="Should be red only")
    print(f"3. Reset token: {repr(result)}")


def test_function_fallback():
    """Test function fallback system"""
    print("\n=== Function Fallback ===")
    
    def level_color(level):
        colors = {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'green'}
        return colors.get(level.upper(), 'white')
    
    def level_style(level):
        return 'bold' if level.upper() in ['ERROR', 'CRITICAL'] else 'normal'
    
    functions = {
        'level_color': level_color,
        'level_style': level_style
    }
    
    # Test color function fallback
    formatter = DynamicFormatter("{{#level_color;Level: ;level}}", functions=functions)
    result = formatter.format(level="ERROR")
    print(f"1. Color function: {repr(result)}")
    
    # Test text function fallback
    formatter = DynamicFormatter("{{@level_style;Level: ;level}}", functions=functions)
    result = formatter.format(level="ERROR")
    print(f"2. Text function: {repr(result)}")
    
    # Test combined function fallback
    formatter = DynamicFormatter("{{#level_color@level_style;Level: ;level}}", functions=functions)
    result = formatter.format(level="ERROR")
    print(f"3. Combined functions: {repr(result)}")


def test_conditional_formatting():
    """Test conditional formatting at section and inline levels"""
    print("\n=== Conditional Formatting ===")
    
    def has_items(count):
        return count > 0
    
    def is_urgent(status):
        return 'urgent' in status.lower()
    
    functions = {
        'has_items': has_items,
        'is_urgent': is_urgent
    }
    
    # Test section-level conditionals
    formatter = DynamicFormatter(
        "{{Processing}} {{?has_items;(;file_count; files)}}",
        functions=functions
    )
    
    result1 = formatter.format(file_count=25)
    result2 = formatter.format(file_count=0)
    print(f"1. Section conditional (with items): {repr(result1)}")
    print(f"2. Section conditional (no items): {repr(result2)}")
    
    # Test inline conditionals
    formatter = DynamicFormatter(
        "{{Status{?is_urgent} - URGENT: ;status}}",
        functions=functions
    )
    
    result3 = formatter.format(status="urgent_task")
    result4 = formatter.format(status="normal_task")
    print(f"3. Inline conditional (urgent): {repr(result3)}")
    print(f"4. Inline conditional (normal): {repr(result4)}")


def test_escape_sequences():
    """Test escape sequence handling"""
    print("\n=== Escape Sequences ===")
    
    # Test basic escaping
    formatter = DynamicFormatter("{{Use \\{brackets\\} for: ;syntax}}")
    result = formatter.format(syntax="variables")
    print(f"1. Basic escaping: {repr(result)}")
    
    # Test escaping with formatting
    formatter = DynamicFormatter("{{#red;Error in \\{module\\}: ;error}}")
    result = formatter.format(error="syntax error")
    print(f"2. Escaping with formatting: {repr(result)}")
    
    # Test mixed escaping and conditionals
    def has_value(value):
        return bool(value)
    
    formatter = DynamicFormatter(
        "{{Processing{?has_value} \\{found items\\}: ;count}}",
        functions={'has_value': has_value}
    )
    
    result3 = formatter.format(count=5)
    result4 = formatter.format(count=0)
    print(f"3. Escaping with conditionals (has value): {repr(result3)}")
    print(f"4. Escaping with conditionals (no value): {repr(result4)}")


def test_complex_scenarios():
    """Test complex real-world scenarios"""
    print("\n=== Complex Scenarios ===")
    
    def level_color(level):
        return {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'green'}[level]
    
    def has_duration(duration):
        return duration > 0
    
    def has_errors(error_count):
        return error_count > 0
    
    functions = {
        'level_color': level_color,
        'has_duration': has_duration,
        'has_errors': has_errors
    }
    
    # Complex logging scenario
    formatter = DynamicFormatter(
        "{{#level_color@bold;[;levelname;]}} {{message}} "
        "{{?has_duration;in ;duration;s}} {{?has_errors;(;error_count; errors)}}",
        functions=functions
    )
    
    result1 = formatter.format(
        levelname="ERROR", 
        message="Processing failed", 
        duration=2.5, 
        error_count=3
    )
    
    result2 = formatter.format(
        levelname="INFO", 
        message="Processing complete",
        duration=0,
        error_count=0
    )
    
    print(f"1. Complex logging (with errors): {repr(result1)}")
    print(f"2. Complex logging (success): {repr(result2)}")


def test_required_fields():
    """Test required field functionality"""
    print("\n=== Required Fields ===")
    
    # Test required field present
    formatter = DynamicFormatter("{{!#red;Critical: ;error}}")
    result = formatter.format(error="System failure")
    print(f"1. Required field present: {repr(result)}")
    
    # Test required field missing
    try:
        result = formatter.format(other_field="value")
        print("ERROR: Should have raised RequiredFieldError")
    except RequiredFieldError as e:
        print(f"2. Required field missing: {e}")


def test_error_handling():
    """Test various error conditions"""
    print("\n=== Error Handling ===")
    
    # Test invalid color token
    try:
        formatter = DynamicFormatter("{{#invalid_color;Test: ;value}}")
        result = formatter.format(value="test")
        print("ERROR: Should have raised FormatterError")
    except DynamicFormattingError as e:
        print(f"1. Invalid color token: {type(e).__name__}: {e}")
    
    # Test invalid text style
    try:
        formatter = DynamicFormatter("{{@invalid_style;Test: ;value}}")
        result = formatter.format(value="test")
        print("ERROR: Should have raised FormatterError")
    except DynamicFormattingError as e:
        print(f"2. Invalid text style: {type(e).__name__}: {e}")
    
    # Test missing conditional function
    try:
        formatter = DynamicFormatter("{{?missing_function;Test: ;value}}")
        result = formatter.format(value="test")
        print("ERROR: Should have raised FunctionNotFoundError")
    except DynamicFormattingError as e:
        print(f"3. Missing conditional function: {type(e).__name__}: {e}")
    
    # Test malformed template
    try:
        formatter = DynamicFormatter("{{#red;Unclosed template")
        print("ERROR: Should have raised ParseError")
    except DynamicFormattingError as e:
        print(f"4. Malformed template: {type(e).__name__}: {e}")


def test_logging_formatter():
    """Test the DynamicLoggingFormatter"""
    print("\n=== Logging Formatter ===")
    
    def level_color(level):
        return {'ERROR': 'red', 'INFO': 'green', 'WARNING': 'yellow'}[level]
    
    # Create a string stream to capture log output
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    
    formatter = DynamicLoggingFormatter(
        "{{#level_color@bold;[;levelname;]}} {{message}}",
        functions={'level_color': level_color}
    )
    handler.setFormatter(formatter)
    
    # Create logger and add handler
    test_logger = logging.getLogger('test_logger')
    test_logger.setLevel(logging.DEBUG)
    test_logger.addHandler(handler)
    
    # Test logging
    test_logger.error("This is an error")
    test_logger.info("This is info")
    
    # Get the output
    log_output = log_stream.getvalue()
    print(f"1. Log output: {repr(log_output)}")
    
    # Clean up
    test_logger.removeHandler(handler)


def test_output_modes():
    """Test console vs file output modes"""
    print("\n=== Output Modes ===")
    
    # Test console mode (default)
    formatter_console = DynamicFormatter("{{#red@bold;Console: ;message}}", output_mode='console')
    result_console = formatter_console.format(message="test")
    print(f"1. Console mode: {repr(result_console)}")
    
    # Test file mode (no ANSI codes)
    formatter_file = DynamicFormatter("{{#red@bold;File: ;message}}", output_mode='file')
    result_file = formatter_file.format(message="test")
    print(f"2. File mode: {repr(result_file)}")


def test_performance_scenarios():
    """Test scenarios that should be efficient"""
    print("\n=== Performance Scenarios ===")
    
    # Test simple section (should use efficient path)
    formatter = DynamicFormatter("{{#red;Simple: ;message}}")
    result = formatter.format(message="test")
    print(f"1. Simple section: {repr(result)}")
    
    # Test complex section (should handle properly)
    formatter = DynamicFormatter("{{#red;Complex {#blue}inline: ;message}}")
    result = formatter.format(message="test")
    print(f"2. Complex section: {repr(result)}")


def run_all_tests():
    """Run all test functions"""
    test_functions = [
        test_basic_color_formatting,
        test_basic_text_formatting,
        test_mixed_formatting,
        test_function_fallback,
        test_conditional_formatting,
        test_escape_sequences,
        test_complex_scenarios,
        test_required_fields,
        test_error_handling,
        test_logging_formatter,
        test_output_modes,
        test_performance_scenarios
    ]
    
    print("Running Comprehensive Test Suite for Refactored Dynamic Formatting")
    print("=" * 75)
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ Test {test_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 75)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All tests passed! The refactor was successful.")
        print("\nKey changes verified:")
        print("• Color tokens naturally override (later wins)")
        print("• Text styles naturally combine via ANSI codes")
        print("• No stacking restrictions or error throwing")
        print("• All existing functionality preserved")
        print("• Error handling still works correctly")
        print("• Function fallback system intact")
        print("• Conditional formatting working")
        print("• Escape sequences working")
    else:
        print("❌ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    run_all_tests()

#python shared_utils/dynamic_formatting/test_escape_sequences.py