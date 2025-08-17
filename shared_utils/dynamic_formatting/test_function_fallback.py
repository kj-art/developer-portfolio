"""
Test suite for function fallback functionality in dynamic formatting.

Run this file directly to test the new function fallback features.
"""

import sys
from pathlib import Path

# Add the project root to path so we can import as a package
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared_utils.dynamic_formatting import (
        DynamicFormatter, 
        DynamicFormattingError, 
        FunctionExecutionError,
        FormatterError
    )
except ImportError:
    # Fallback: try importing from current directory (if modules are here)
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        # Import individual modules directly to avoid relative import issues
        import formatters
        import dynamic_formatting as df_module
        import formatting_state
        
        DynamicFormatter = df_module.DynamicFormatter
        DynamicFormattingError = df_module.DynamicFormattingError
        FunctionExecutionError = formatters.FunctionExecutionError
        FormatterError = formatters.FormatterError
        
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


def test_color_function_fallback():
    """Test color function fallback functionality"""
    print("=== Color Function Fallback Tests ===")
    
    def level_color_map(level_name):
        """Function that returns color based on log level"""
        colors = {
            'DEBUG': 'cyan',
            'INFO': 'green', 
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'magenta'
        }
        return colors.get(level_name.upper(), 'white')
    
    def status_color(status):
        """Function that returns color based on status"""
        return 'green' if status == 'success' else 'red'
    
    functions = {
        'level_color_map': level_color_map,
        'status_color': status_color
    }
    
    # Test 1: Basic color function fallback
    formatter = DynamicFormatter("{{Le{#level_color_map}vel: ;levelname}}", functions=functions)
    result = formatter.format(levelname="ERROR")
    print(f"1. Color function fallback:")
    print(f"   Visual: {result}")
    print(f"   Raw: {repr(result)}")
    
    # Test 2: Color function with different case
    result2 = formatter.format(levelname="debug")
    print(f"2. Color function case handling:")
    print(f"   Visual: {result2}")
    print(f"   Raw: {repr(result2)}")
    
    # Test 3: Combined with static formatting (fixed syntax)
    formatter3 = DynamicFormatter("{{#level_color_map@bold;[;levelname;]}} {{message}}", functions=functions)
    result3 = formatter3.format(levelname="ERROR", message="Something failed")
    print(f"3. Combined color function + text:")
    print(f"   Visual: {result3}")
    print(f"   Raw: {repr(result3)}")
    
    # Test 4: Multiple function calls
    formatter4 = DynamicFormatter("{{#status_color;Status: ;status}} {{#level_color_map;Level: ;level}}", 
                                functions=functions)
    result4 = formatter4.format(status="success", level="INFO")
    print(f"4. Multiple color functions:")
    print(f"   Visual: {result4}")
    print(f"   Raw: {repr(result4)}")


def test_text_function_fallback():
    """Test text formatting function fallback"""
    print("\n=== Text Function Fallback Tests ===")
    
    def level_style_map(level_name):
        """Function that returns text style based on log level"""
        if level_name.upper() in ['ERROR', 'CRITICAL']:
            return 'bold'
        elif level_name.upper() == 'WARNING':
            return 'underline'
        return 'normal'
    
    def priority_style(priority):
        """Function that returns style based on priority"""
        if priority > 7:
            return 'bold'
        elif priority > 4:
            return 'italic'
        return 'normal'
    
    functions = {
        'level_style_map': level_style_map,
        'priority_style': priority_style
    }
    
    # Test 1: Basic text function fallback
    formatter = DynamicFormatter("{{@level_style_map;Level: ;levelname}}", functions=functions)
    result = formatter.format(levelname="ERROR")
    print(f"1. Text function fallback:")
    print(f"   Visual: {result}")
    print(f"   Raw: {repr(result)}")
    
    # Test 2: Text function with numeric input
    formatter2 = DynamicFormatter("{{@priority_style;Priority ;priority; task}}", functions=functions)
    result2 = formatter2.format(priority=8)
    print(f"2. Text function with numeric input:")
    print(f"   Visual: {result2}")
    print(f"   Raw: {repr(result2)}")
    
    # Test 3: Stacked text styles from function
    formatter3 = DynamicFormatter("{{@level_style_map@italic;Status: ;level}}", functions=functions)
    result3 = formatter3.format(level="WARNING")  # Should be underline + italic
    print(f"3. Stacked text function + static:")
    print(f"   Visual: {result3}")
    print(f"   Raw: {repr(result3)}")


def test_combined_function_fallback():
    """Test combined color and text function fallback"""
    print("\n=== Combined Function Fallback Tests ===")
    
    def get_level_color(level):
        return {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'green'}.get(level.upper(), 'white')
    
    def get_level_style(level):
        return 'bold' if level.upper() in ['ERROR', 'CRITICAL'] else 'normal'
    
    functions = {
        'get_level_color': get_level_color,
        'get_level_style': get_level_style
    }
    
    # Test combined color and text functions (fixed syntax)
    formatter = DynamicFormatter("{{#get_level_color@get_level_style;[;level;]}} {{message}}", 
                                functions=functions)
    result = formatter.format(level="ERROR", message="Critical failure")
    print(f"1. Combined color + text functions: {repr(result)}")


def test_inline_function_fallback():
    """Test function fallback in inline formatting"""
    print("\n=== Inline Function Fallback Tests ===")
    
    def highlight_color(text):
        """Return color based on text content"""
        if 'error' in text.lower():
            return 'red'
        elif 'success' in text.lower():
            return 'green'
        return 'blue'
    
    functions = {'highlight_color': highlight_color}
    
    # Test inline function fallback (fixed syntax)
    formatter = DynamicFormatter("{{@bold;Status: ;{#highlight_color}status}} reported", 
                                functions=functions)
    result = formatter.format(status="Error detected")
    print(f"1. Inline function fallback: {repr(result)}")


def test_error_handling():
    """Test error handling for function fallback"""
    print("\n=== Error Handling Tests ===")
    
    def broken_function(value):
        """Function that always raises an exception"""
        raise ValueError("This function is broken")
    
    def wrong_return_type(value):
        """Function that returns wrong type"""
        return 42  # Should return string
    
    functions = {
        'broken_function': broken_function,
        'wrong_return_type': wrong_return_type
    }
    
    # Test 1: Function that raises exception
    try:
        formatter = DynamicFormatter("{{#broken_function;Test: ;value}}", functions=functions)
        result = formatter.format(value="test")
        print("ERROR: Should have raised exception")
    except DynamicFormattingError as e:
        print(f"1. Exception handling: {e}")
    
    # Test 2: Function that returns wrong type
    try:
        formatter2 = DynamicFormatter("{{#wrong_return_type;Test: ;value}}", functions=functions)
        result2 = formatter2.format(value="test")
        print("ERROR: Should have raised exception")
    except DynamicFormattingError as e:
        print(f"2. Wrong return type handling: {e}")
    
    # Test 3: Unknown function
    try:
        formatter3 = DynamicFormatter("{{#unknown_function;Test: ;value}}")
        result3 = formatter3.format(value="test")
        print("ERROR: Should have raised exception")
    except DynamicFormattingError as e:
        print(f"3. Unknown function handling: {e}")
    
    # Test 4: Invalid color token
    try:
        formatter4 = DynamicFormatter("{{#invalid_color_name;Test: ;value}}")
        result4 = formatter4.format(value="test")
        print("ERROR: Should have raised exception")
    except DynamicFormattingError as e:
        print(f"4. Invalid color token handling: {e}")


def test_case_sensitivity():
    """Test case sensitivity handling"""
    print("\n=== Case Sensitivity Tests ===")
    
    # Test that color names are case insensitive
    formatter1 = DynamicFormatter("{{#RED;Red text: ;message}}")
    result1 = formatter1.format(message="test")
    print(f"1. Uppercase color name: {repr(result1)}")
    
    formatter2 = DynamicFormatter("{{#Red;Red text: ;message}}")
    result2 = formatter2.format(message="test")
    print(f"2. Mixed case color name: {repr(result2)}")
    
    # Test that text styles are case insensitive
    formatter3 = DynamicFormatter("{{@BOLD;Bold text: ;message}}")
    result3 = formatter3.format(message="test")
    print(f"3. Uppercase text style: {repr(result3)}")
    
    # Test that reset tokens are case insensitive
    formatter4 = DynamicFormatter("{{@bold;Bold}} {{@NORMAL;Normal}}")
    result4 = formatter4.format()
    print(f"4. Uppercase reset token: {repr(result4)}")


def run_all_tests():
    """Run all test functions"""
    test_functions = [
        test_color_function_fallback,
        test_text_function_fallback, 
        test_combined_function_fallback,
        test_inline_function_fallback,
        test_error_handling,
        test_case_sensitivity
    ]
    
    print("Running Function Fallback Tests")
    print("=" * 50)
    
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            print(f"Test {test_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    run_all_tests()
#python shared_utils/dynamic_formatting/test_function_fallback.py