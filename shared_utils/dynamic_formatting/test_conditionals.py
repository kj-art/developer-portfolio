"""
Test the new conditional formatting features:
1. ? token for section-level conditionals (replacing $)
2. {?function} for inline conditionals within spans
"""

import sys
from pathlib import Path
import logging
from typing import Dict, Any, Callable, Optional, Union, List

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
    print("✓ Successfully imported DynamicFormatter with conditional support!")
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


def test_section_level_conditionals():
    """Test ?function at section level (whole section show/hide)"""
    print("\n=== Section-Level Conditionals (? token) ===")
    
    def has_items(count):
        return count > 0
    
    def is_slow(duration):
        return duration > 5.0
    
    def has_errors(error_count):
        return error_count > 0
    
    functions = {
        'has_items': has_items,
        'is_slow': is_slow, 
        'has_errors': has_errors
    }
    
    # Test format with multiple conditional sections
    formatter = DynamicFormatter(
        "{{Processing}} {{?has_items;(;file_count; files)}} {{?is_slow;SLOW: ;duration;s}} {{?has_errors;[;error_count; ERRORS]}}",
        functions=functions
    )
    
    # Test 1: All conditions true
    result1 = formatter.format(file_count=25, duration=8.2, error_count=3)
    print(f"1. All conditions true:")
    print(f"   Visual: {result1}")
    print(f"   Raw: {repr(result1)}")
    
    # Test 2: Some conditions false
    result2 = formatter.format(file_count=0, duration=2.1, error_count=0)
    print(f"2. All conditions false:")
    print(f"   Visual: {result2}")
    print(f"   Raw: {repr(result2)}")
    
    # Test 3: Mixed conditions
    result3 = formatter.format(file_count=50, duration=2.1, error_count=0)
    print(f"3. Only file count true:")
    print(f"   Visual: {result3}")
    print(f"   Raw: {repr(result3)}")


def test_inline_conditionals():
    """Test {?function} within spans (partial text show/hide)"""
    print("\n=== Inline Conditionals ({?function}) ===")
    
    # These functions will receive the field value (status) as parameter
    def has_files(status):
        # For demo, we'll check if status contains certain words
        return "files" in status.lower()
    
    def is_urgent(status):
        return "urgent" in status.lower()
    
    def has_errors(status):
        return "error" in status.lower()
    
    functions = {
        'has_files': has_files,
        'is_urgent': is_urgent,
        'has_errors': has_errors
    }
    
    # Test inline conditionals within prefix
    formatter = DynamicFormatter(
        "{{Processing{?has_files} files{?is_urgent} URGENT{?has_errors} - ERRORS: ;status}}",
        functions=functions
    )
    
    # Test 1: Status that triggers all conditions
    result1 = formatter.format(status="FILES_URGENT_ERROR")
    print(f"1. All inline conditions true:")
    print(f"   Visual: {result1}")
    print(f"   Raw: {repr(result1)}")
    
    # Test 2: Status that triggers no conditions
    result2 = formatter.format(status="COMPLETE")
    print(f"2. No inline conditions true:")
    print(f"   Visual: {result2}")
    print(f"   Raw: {repr(result2)}")
    
    # Test 3: Status that triggers only files condition
    result3 = formatter.format(status="FILES_COMPLETE")
    print(f"3. Only files condition true:")
    print(f"   Visual: {result3}")
    print(f"   Raw: {repr(result3)}")


def test_combined_conditionals():
    """Test mixing section-level and inline conditionals"""
    print("\n=== Combined Conditionals ===")
    
    def has_items(count):
        return count > 0
    
    def is_important(level):
        return level in ['ERROR', 'CRITICAL']
    
    def is_slow(duration):
        return duration > 3.0
    
    functions = {
        'has_items': has_items,
        'is_important': is_important,
        'is_slow': is_slow
    }
    
    # FIXED: Simplified format mixing both types
    formatter = DynamicFormatter(
        "{{#red@bold;Status{?is_important} - IMPORTANT: ;status}} {{?has_items;Found{?is_slow} (SLOW) ;file_count; items}}",
        functions=functions
    )
    
    # Test different combinations
    test_cases = [
        {"status": "ERROR", "file_count": 25, "duration": 5.2, "level": "ERROR"},
        {"status": "INFO", "file_count": 0, "duration": 1.0, "level": "INFO"}, 
        {"status": "WARNING", "file_count": 10, "duration": 1.5, "level": "WARNING"}
    ]
    
    for i, data in enumerate(test_cases, 1):
        result = formatter.format(**data)
        print(f"{i}. Data: {data}")
        print(f"   Visual: {result}")
        print(f"   Raw: {repr(result)}")


def test_conditional_with_colors():
    """Test conditionals combined with color functions"""
    print("\n=== Conditionals + Color Functions ===")
    
    def level_color(level):
        return {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'green'}.get(level, 'white')
    
    def has_details(detail_text):
        return bool(detail_text and detail_text.strip())
    
    def is_error(level):
        return level == 'ERROR'
    
    functions = {
        'level_color': level_color,
        'has_details': has_details,
        'is_error': is_error
    }
    
    # FIXED: Use separate sections for complex conditional logic
    formatter = DynamicFormatter(
        "{{#level_color@bold;[;level;]}} {{message}} {{?has_details;- Details: ;details}} {{?is_error;⚠️ URGENT}}",
        functions=functions
    )
    
    # Test cases
    test_cases = [
        {"level": "ERROR", "message": "Failed", "details": "Network timeout"},
        {"level": "INFO", "message": "Success", "details": ""},
        {"level": "WARNING", "message": "Slow", "details": "High latency"}
    ]
    
    for i, data in enumerate(test_cases, 1):
        result = formatter.format(**data)
        print(f"{i}. Level: {data['level']}, Has details: {bool(data['details'])}")
        print(f"   Visual: {result}")
        print(f"   Raw: {repr(result)}")


def run_all_tests():
    """Run all conditional formatting tests"""
    print("Testing New Conditional Formatting Features")
    print("=" * 50)
    
    try:
        test_section_level_conditionals()
        test_inline_conditionals()
        test_combined_conditionals()
        test_conditional_with_colors()
        
        print("\n" + "=" * 50)
        print("✅ All conditional tests completed successfully!")
        print("\nKey features demonstrated:")
        print("• ?function - Section-level conditionals (show/hide whole sections)")
        print("• {?function} - Inline conditionals (show/hide parts of text)")
        print("• Mixed usage - Both types in same format string")
        print("• Integration with colors and other formatting")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()

#python shared_utils/dynamic_formatting/test_conditionals.py