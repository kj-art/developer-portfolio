"""
Comprehensive regression test suite for positional arguments feature.

This module ensures that the positional arguments implementation doesn't break
any existing functionality while properly implementing the new features.

Run with: python test_positional_regression.py
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Callable

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared_utils.dynamic_formatting import (
        DynamicFormatter, 
        DynamicLoggingFormatter,
        DynamicFormattingError,
        RequiredFieldError,
        FunctionNotFoundError,
        FormatterError
    )
except ImportError as e:
    print(f"Import failed: {e}")
    print("Make sure all dynamic formatting modules are available")
    sys.exit(1)


class TestRunner:
    """Simple test runner for regression testing"""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
    
    def run_test(self, test_name: str, test_func: Callable):
        """Run a single test and track results"""
        self.tests_run += 1
        try:
            test_func()
            self.tests_passed += 1
            print(f"✓ {test_name}")
        except Exception as e:
            self.failures.append((test_name, str(e)))
            print(f"✗ {test_name}: {e}")
    
    def print_summary(self):
        """Print test run summary"""
        print(f"\n{'='*60}")
        print(f"Test Summary: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failures:
            print(f"\nFailures ({len(self.failures)}):")
            for test_name, error in self.failures:
                print(f"  • {test_name}: {error}")
        else:
            print("\n🎉 All tests passed!")


def test_backward_compatibility_basic():
    """Ensure basic keyword argument functionality still works"""
    formatter = DynamicFormatter("{{Error: ;message}} {{Count: ;count}}")
    
    # Complete data
    result = formatter.format(message="Failed", count=42)
    expected = "Error: Failed Count: 42"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    # Partial data
    result = formatter.format(message="Failed")
    expected = "Error: Failed "  # Note: there will be a trailing space from missing section
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    # No data - should be empty but might have spaces from template structure
    result = formatter.format()
    expected = " "  # There's a space between the two template sections
    assert result == expected, f"Expected '{expected}', got '{result}'"


def test_backward_compatibility_colors():
    """Ensure color formatting still works with keyword args"""
    formatter = DynamicFormatter("{{#red@bold;Error: ;message}}")
    result = formatter.format(message="test")
    assert "Error: test" in result  # Should contain the text regardless of ANSI codes


def test_backward_compatibility_conditionals():
    """Ensure conditional functionality still works with keyword args"""
    def has_value(val):
        return bool(val)
    
    formatter = DynamicFormatter("{{?has_value;Found: ;data}}", functions={'has_value': has_value})
    
    result = formatter.format(data="test")
    assert result == "Found: test"
    
    result = formatter.format(data="")
    assert result == ""


def test_backward_compatibility_complex():
    """Ensure complex formatting still works with keyword args"""
    def level_color(level):
        return {'ERROR': 'red', 'INFO': 'green'}[level]
    
    formatter = DynamicFormatter(
        "{{#level_color@bold;[;level;]}} {{message}}",
        functions={'level_color': level_color}
    )
    
    result = formatter.format(level="ERROR", message="test")
    # The result should contain both the formatted text and might have ANSI codes
    # Let's check if the core components are present
    assert "[ERROR]" in result, f"Expected '[ERROR]' in result, got '{result}'"
    assert "test" in result, f"Expected 'test' in result, got '{result}'"


def test_positional_basic():
    """Test basic positional argument functionality"""
    # Single field
    formatter = DynamicFormatter("{{}}")
    result = formatter.format("test")
    assert result == "test"
    
    # Multiple fields
    formatter = DynamicFormatter("{{}} {{}}")
    result = formatter.format("hello", "world")
    assert result == "hello world"
    
    # Empty field with prefix/suffix
    formatter = DynamicFormatter("{{Error: ;}}")
    result = formatter.format("Failed")
    assert result == "Error: Failed"


def test_positional_with_formatting():
    """Test positional arguments with formatting"""
    # Basic color
    formatter = DynamicFormatter("{{#red;}}")
    result = formatter.format("test")
    assert "test" in result
    
    # Color and text style
    formatter = DynamicFormatter("{{#red@bold;}}")
    result = formatter.format("test")
    assert "test" in result
    
    # Multiple fields with different formatting
    formatter = DynamicFormatter("{{#red;}} {{#blue;}}")
    result = formatter.format("first", "second")
    assert "first" in result and "second" in result


def test_positional_with_conditionals():
    """Test positional arguments with conditional functions"""
    def has_value(val):
        return bool(val and str(val).strip())
    
    formatter = DynamicFormatter("{{?has_value;Found: ;}}", functions={'has_value': has_value})
    
    # Should show with valid value
    result = formatter.format("test")
    assert result == "Found: test"
    
    # Should hide with empty value
    result = formatter.format("")
    assert result == ""


def test_positional_complex_syntax():
    """Test complex positional syntax patterns"""
    # With prefix and suffix
    formatter = DynamicFormatter("{{Error: ;;!}}")
    result = formatter.format("Failed")
    assert result == "Error: Failed!"
    
    # With formatting, prefix, and suffix
    formatter = DynamicFormatter("{{#red@bold;Warning: ;;!}}")
    result = formatter.format("Low disk space")
    assert "Warning: Low disk space!" in result
    
    # Multiple complex sections
    formatter = DynamicFormatter("{{#red;Error: ;}} {{#green;Success: ;}}")
    result = formatter.format("Failed", "Completed")
    assert "Error: Failed" in result and "Success: Completed" in result


def test_positional_missing_data():
    """Test positional arguments with missing data (graceful handling)"""
    # More sections than arguments - extra sections should disappear
    formatter = DynamicFormatter("{{First: ;}} {{Second: ;}} {{Third: ;}}")
    
    result = formatter.format("A")
    expected = "First: A  "  # Note: there will be trailing spaces from missing sections
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    result = formatter.format("A", "B")
    expected = "First: A Second: B "  # Note: trailing space from missing third section
    assert result == expected, f"Expected '{expected}', got '{result}'"
    
    result = formatter.format("A", "B", "C")
    expected = "First: A Second: B Third: C"
    assert result == expected, f"Expected '{expected}', got '{result}'"


def test_positional_function_fallback():
    """Test positional arguments with function fallback"""
    def status_color(status):
        return {'error': 'red', 'success': 'green'}[status.lower()]
    
    formatter = DynamicFormatter("{{#status_color;}}", functions={'status_color': status_color})
    
    result = formatter.format("ERROR")
    assert "ERROR" in result
    
    result = formatter.format("SUCCESS")
    assert "SUCCESS" in result


def test_error_conditions_mixed_args():
    """Test error condition: mixed positional and keyword arguments"""
    formatter = DynamicFormatter("{{}} {{}}")
    
    try:
        formatter.format("pos", keyword="kw")
        assert False, "Should have raised DynamicFormattingError"
    except DynamicFormattingError as e:
        assert "Cannot mix positional and keyword arguments" in str(e)


def test_error_conditions_too_many_args():
    """Test error condition: too many positional arguments"""
    formatter = DynamicFormatter("{{}}")  # Only one positional section
    
    try:
        formatter.format("first", "second")
        assert False, "Should have raised DynamicFormattingError"
    except DynamicFormattingError as e:
        assert "Too many positional arguments: expected 1, got 2" in str(e)


def test_error_conditions_required_fields():
    """Test error condition: required fields with positional args"""
    formatter = DynamicFormatter("{{!}}")  # Required field
    
    try:
        formatter.format()  # No arguments
        assert False, "Should have raised RequiredFieldError"
    except RequiredFieldError as e:
        assert "position 1" in str(e)  # Should show user-friendly position


def test_error_conditions_missing_functions():
    """Test error condition: missing conditional functions with positional args"""
    formatter = DynamicFormatter("{{?missing_func;}}")
    
    try:
        formatter.format("test")
        assert False, "Should have raised FunctionNotFoundError"
    except FunctionNotFoundError as e:
        assert "missing_func" in str(e)


def test_edge_cases_empty_arguments():
    """Test edge cases with empty arguments"""
    formatter = DynamicFormatter("{{}} {{}}")
    
    # Empty string arguments should work
    result = formatter.format("", "test")
    assert result == " test"
    
    # None arguments should cause sections to disappear
    result = formatter.format(None, "test")
    assert result == " test"


def test_edge_cases_zero_positional_sections():
    """Test edge case: no positional sections in template"""
    formatter = DynamicFormatter("{{named_field}}")
    
    # Should work fine with keyword args
    result = formatter.format(named_field="test")
    assert result == "test"
    
    # Should fail with positional args - there are field sections, but using positional args should work
    # Actually, this should work because we map positional args to field sections in order
    result = formatter.format("test")
    assert result == "test", f"Expected 'test', got '{result}'"


def test_edge_cases_mixed_template():
    """Test edge case: template with both positional and named sections"""
    formatter = DynamicFormatter("{{}} {{named_field}}")
    
    # Should work with keyword args (positional section gets ignored, named section appears)
    result = formatter.format(named_field="test")
    assert result == " test", f"Expected ' test', got '{result}'"
    
    # Should work with positional args (named sections just disappear)
    result = formatter.format("pos")
    assert result == "pos ", f"Expected 'pos ', got '{result}'"


def test_logging_formatter_compatibility():
    """Test that DynamicLoggingFormatter still works properly"""
    import logging
    
    formatter = DynamicLoggingFormatter("{{#green;[;levelname;]}} {{message}}")
    
    # Create a mock log record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    result = formatter.format(record)
    # Check that the core components are present, might have ANSI codes
    assert "[INFO]" in result, f"Expected '[INFO]' in result, got '{result}'"
    assert "Test message" in result, f"Expected 'Test message' in result, got '{result}'"


def test_performance_large_positional():
    """Test performance with many positional arguments"""
    # Create template with 100 positional sections
    template = " ".join(["{{}}" for _ in range(100)])
    formatter = DynamicFormatter(template)
    
    # Create 100 arguments
    args = [f"arg{i}" for i in range(100)]
    
    result = formatter.format(*args)
    assert "arg0" in result and "arg99" in result


def test_all_syntax_patterns():
    """Test all documented syntax patterns work correctly"""
    patterns = [
        ("{{}}",                      ["test"],           "test"),
        ("{{#red}}",                  ["test"],           "test"),  # Content varies with color codes
        ("{{my_field}}",              ["test"],           "test"),  # Field name ignored for positional
        ("{{#red;my_field}}",         ["test"],           "test"),  # Field name ignored for positional  
        ("{{prefix;my_field}}",       ["test"],           "prefixtest"),  # No space between prefix and field
        ("{{prefix;my_field;suffix}}", ["test"],          "prefixtestsuffix"),  # No spaces
        ("{{#red@bold;prefix;my_field}}", ["test"],       "prefixtest"),  # Content varies with formatting
        ("{{#red@bold;prefix;my_field;suffix}}", ["test"], "prefixtestsuffix"),  # Content varies with formatting
    ]
    
    for pattern, args, expected_base in patterns:
        formatter = DynamicFormatter(pattern)
        result = formatter.format(*args)
        
        # For formatted text, just check that the base text is present
        if expected_base in result:
            continue  # Pass
        else:
            raise AssertionError(f"Pattern '{pattern}' with args {args} failed. Expected base '{expected_base}' in result '{result}'")


def run_all_tests():
    """Run all regression tests"""
    runner = TestRunner()
    
    # Backward compatibility tests
    runner.run_test("Backward Compatibility - Basic", test_backward_compatibility_basic)
    runner.run_test("Backward Compatibility - Colors", test_backward_compatibility_colors)
    runner.run_test("Backward Compatibility - Conditionals", test_backward_compatibility_conditionals)
    runner.run_test("Backward Compatibility - Complex", test_backward_compatibility_complex)
    
    # Positional argument tests
    runner.run_test("Positional Arguments - Basic", test_positional_basic)
    runner.run_test("Positional Arguments - With Formatting", test_positional_with_formatting)
    runner.run_test("Positional Arguments - With Conditionals", test_positional_with_conditionals)
    runner.run_test("Positional Arguments - Complex Syntax", test_positional_complex_syntax)
    runner.run_test("Positional Arguments - Missing Data", test_positional_missing_data)
    runner.run_test("Positional Arguments - Function Fallback", test_positional_function_fallback)
    
    # Error condition tests
    runner.run_test("Error Conditions - Mixed Args", test_error_conditions_mixed_args)
    runner.run_test("Error Conditions - Too Many Args", test_error_conditions_too_many_args)
    runner.run_test("Error Conditions - Required Fields", test_error_conditions_required_fields)
    runner.run_test("Error Conditions - Missing Functions", test_error_conditions_missing_functions)
    
    # Edge case tests
    runner.run_test("Edge Cases - Empty Arguments", test_edge_cases_empty_arguments)
    runner.run_test("Edge Cases - Zero Positional Sections", test_edge_cases_zero_positional_sections)
    runner.run_test("Edge Cases - Mixed Template", test_edge_cases_mixed_template)
    
    # Integration tests
    runner.run_test("Logging Formatter Compatibility", test_logging_formatter_compatibility)
    runner.run_test("Performance - Large Positional", test_performance_large_positional)
    runner.run_test("All Syntax Patterns", test_all_syntax_patterns)
    
    runner.print_summary()
    return runner.tests_passed == runner.tests_run


if __name__ == "__main__":
    print("Dynamic Formatting - Positional Arguments Regression Test Suite")
    print("=" * 70)
    
    success = run_all_tests()
    sys.exit(0 if success else 1)