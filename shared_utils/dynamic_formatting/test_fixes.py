#!/usr/bin/env python3
"""
Quick test script to verify that the major fixes are working.

This script tests the core functionality that was broken in the failing tests
to ensure the fixes are correct before running the full test suite.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared_utils.dynamic_formatting import DynamicFormatter, FormatterConfig, ValidationMode
    print("✓ Import successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)


def test_basic_formatting():
    """Test basic template parsing and formatting"""
    print("\n1. Basic Formatting Test")
    formatter = DynamicFormatter("{{Status: ;message}}")
    result = formatter.format(message="Success")
    expected = "Status: Success"
    print(f"   Template: {{{{Status: ;message}}}}")
    print(f"   Result: '{result}'")
    print(f"   Expected: '{expected}'")
    print(f"   ✓ PASS" if result == expected else f"   ✗ FAIL")
    return result == expected


def test_missing_data_handling():
    """Test that missing data causes sections to disappear"""
    print("\n2. Missing Data Handling Test")
    formatter = DynamicFormatter("{{Status: ;status}}{{ | Code: ;code}}")
    result = formatter.format(status="Success")
    expected = "Status: Success"
    print(f"   Template: {{{{Status: ;status}}}}{{{{ | Code: ;code}}}}")
    print(f"   Data: status='Success' (code missing)")
    print(f"   Result: '{result}'")
    print(f"   Expected: '{expected}'")
    print(f"   ✓ PASS" if result == expected else f"   ✗ FAIL")
    return result == expected


def test_none_value_handling():
    """Test that None values cause sections to disappear"""
    print("\n3. None Value Handling Test")
    formatter = DynamicFormatter("{{Value: ;field}}")
    result = formatter.format(field=None)
    expected = ""
    print(f"   Template: {{{{Value: ;field}}}}")
    print(f"   Data: field=None")
    print(f"   Result: '{result}'")
    print(f"   Expected: '{expected}'")
    print(f"   ✓ PASS" if result == expected else f"   ✗ FAIL")
    return result == expected


def test_positional_arguments():
    """Test positional argument support"""
    print("\n4. Positional Arguments Test")
    formatter = DynamicFormatter("{{}} {{}}")
    result = formatter.format("hello", "world")
    expected = "hello world"
    print(f"   Template: {{{{}}}} {{{{}}}}")
    print(f"   Args: 'hello', 'world'")
    print(f"   Result: '{result}'")
    print(f"   Expected: '{expected}'")
    print(f"   ✓ PASS" if result == expected else f"   ✗ FAIL")
    return result == expected


def test_function_fallback():
    """Test function fallback for dynamic formatting"""
    print("\n5. Function Fallback Test")
    
    def level_color(level):
        return "red" if level == "ERROR" else "green"
    
    config = FormatterConfig(functions={"level_color": level_color})
    formatter = DynamicFormatter("{{#level_color;[;level;]}}", config=config)
    result = formatter.format(level="ERROR")
    
    # Should contain the text with color formatting
    contains_text = "[ERROR]" in result
    print(f"   Template: {{{{#level_color;[;level;]}}}}")
    print(f"   Function: level_color('ERROR') -> 'red'")
    print(f"   Data: level='ERROR'")
    print(f"   Result: '{result}'")
    print(f"   Contains '[ERROR]': {contains_text}")
    print(f"   ✓ PASS" if contains_text else f"   ✗ FAIL")
    return contains_text


def test_conditional_logic():
    """Test conditional section logic"""
    print("\n6. Conditional Logic Test")
    
    def has_items(count):
        return count > 0
    
    config = FormatterConfig(functions={"has_items": has_items})
    formatter = DynamicFormatter("{{Processing}} {{?has_items;found ;count; items}}", config=config)
    
    # Test with items
    result1 = formatter.format(count=5)
    expected1 = "Processing found 5 items"
    
    # Test without items  
    result2 = formatter.format(count=0)
    expected2 = "Processing "
    
    print(f"   Template: {{{{Processing}}}} {{{{?has_items;found ;count; items}}}}")
    print(f"   Function: has_items(count) -> count > 0")
    print(f"   Test 1 - count=5:")
    print(f"     Result: '{result1}'")
    print(f"     Expected: '{expected1}'")
    test1_pass = result1 == expected1
    print(f"     ✓ PASS" if test1_pass else f"     ✗ FAIL")
    
    print(f"   Test 2 - count=0:")
    print(f"     Result: '{result2}'")
    print(f"     Expected: '{expected2}'")
    test2_pass = result2 == expected2
    print(f"     ✓ PASS" if test2_pass else f"     ✗ FAIL")
    
    return test1_pass and test2_pass


def test_output_modes():
    """Test console vs file output modes"""
    print("\n7. Output Mode Test")
    
    # Console mode (with ANSI codes)
    console_config = FormatterConfig(output_mode="console")
    console_formatter = DynamicFormatter("{{#red;Error: ;message}}", config=console_config)
    console_result = console_formatter.format(message="Failed")
    
    # File mode (without ANSI codes)
    file_config = FormatterConfig(output_mode="file")
    file_formatter = DynamicFormatter("{{#red;Error: ;message}}", config=file_config)
    file_result = file_formatter.format(message="Failed")
    
    console_has_ansi = "\033[" in console_result
    file_no_ansi = "\033[" not in file_result
    both_have_text = "Error: Failed" in console_result and "Error: Failed" in file_result
    
    print(f"   Template: {{{{#red;Error: ;message}}}}")
    print(f"   Console result: '{console_result}'")
    print(f"   File result: '{file_result}'")
    print(f"   Console has ANSI: {console_has_ansi}")
    print(f"   File has no ANSI: {file_no_ansi}")
    print(f"   Both contain text: {both_have_text}")
    
    success = console_has_ansi and file_no_ansi and both_have_text
    print(f"   ✓ PASS" if success else f"   ✗ FAIL")
    return success


def test_escape_sequences():
    """Test escape sequence handling"""
    print("\n8. Escape Sequences Test")
    formatter = DynamicFormatter(r"Text with \; semicolon and {{field}}")
    result = formatter.format(field="value")
    expected = "Text with ; semicolon and value"
    print(f"   Template: Text with \\; semicolon and {{{{field}}}}")
    print(f"   Result: '{result}'")
    print(f"   Expected: '{expected}'")
    print(f"   ✓ PASS" if result == expected else f"   ✗ FAIL")
    return result == expected


def main():
    """Run all tests and report results"""
    print("Dynamic Formatting Fix Verification")
    print("=" * 50)
    
    tests = [
        test_basic_formatting,
        test_missing_data_handling,
        test_none_value_handling,
        test_positional_arguments,
        test_function_fallback,
        test_conditional_logic,
        test_output_modes,
        test_escape_sequences,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ✗ EXCEPTION: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The fixes are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
