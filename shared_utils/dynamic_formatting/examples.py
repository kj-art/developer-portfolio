"""
Comprehensive examples showcasing all dynamic formatting features.

This module demonstrates every capability of the dynamic formatting system
including function fallback, all token types, escape sequences, custom
delimiters, positional arguments, and real-world usage patterns.

Run with: python examples.py
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path for imports
# This handles both direct execution and package execution
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent

# Add project root to path if not already there
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    # Try importing as a package first
    from shared_utils.dynamic_formatting import (
        DynamicFormatter, 
        DynamicLoggingFormatter,
        DynamicFormattingError,
        RequiredFieldError,
        FunctionNotFoundError,
        FormatterError
    )
    print("✓ Successfully imported dynamic formatting package!")
except ImportError:
    try:
        # Fallback: try importing from current directory (if modules are here)
        # Add current directory to path
        sys.path.insert(0, str(current_dir))
        
        # Import individual modules directly
        from dynamic_formatting import (
            DynamicFormatter,
            DynamicLoggingFormatter, 
            DynamicFormattingError,
            RequiredFieldError,
            FunctionNotFoundError
        )
        from formatters.base import FormatterError
        print("✓ Successfully imported via fallback method!")
        
    except ImportError as e:
        print(f"❌ Could not import dynamic formatting modules: {e}")
        print("Make sure you have the following structure:")
        print("shared_utils/dynamic_formatting/")
        print("├── __init__.py")
        print("├── dynamic_formatting.py")
        print("├── formatters/")
        print("│   ├── __init__.py")
        print("│   ├── base.py")
        print("│   ├── color.py")
        print("│   ├── text.py")
        print("│   └── conditional.py")
        print("├── formatting_state.py")
        print("├── template_parser.py")
        print("├── span_structures.py")
        print("└── examples.py")
        print(f"Current directory: {os.getcwd()}")
        print(f"Script location: {current_dir}")
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
    print("=== Core Feature: Graceful Missing Data Handling ===")
    
    # Single section example - keyword arguments
    formatter = DynamicFormatter("{{Error: ;message}}")
    
    result1 = formatter.format(message="Connection failed")
    result2 = formatter.format()  # No message provided
    print(f"1. Keyword with data: '{result1}'")      # "Error: Connection failed"  
    print(f"2. Keyword without data: '{result2}'")   # "" (empty string)
    
    # Single section example - positional arguments (NEW)
    formatter = DynamicFormatter("{{Error: ;}}")
    
    result3 = formatter.format("Connection failed")
    result4 = formatter.format()  # No arguments provided
    print(f"3. Positional with data: '{result3}'")      # "Error: Connection failed"  
    print(f"4. Positional without data: '{result4}'")   # "" (empty string)
    
    # Multiple sections example - keyword arguments
    formatter = DynamicFormatter("{{Error: ;message}} {{Processing ;file_count; files}} {{Duration: ;seconds;s}}")
    
    # All data present
    result5 = formatter.format(message="Failed", file_count=25, seconds=12.5)
    print(f"5. Keyword all data: '{result5}'")
    
    # Some data missing
    result6 = formatter.format(file_count=25, seconds=12.5)  # No error message
    print(f"6. Keyword partial data: '{result6}'")
    
    # Only one piece of data
    result7 = formatter.format(message="Failed")  # Only error message
    print(f"7. Keyword minimal data: '{result7}'")
    
    # No data at all
    result8 = formatter.format()
    print(f"8. Keyword no data: '{result8}'")
    
    # Multiple sections example - positional arguments (NEW)
    formatter = DynamicFormatter("{{Error: ;}} {{Processing ; files}} {{Duration: ;s}}")
    
    # All data present
    result9 = formatter.format("Failed", 25, 12.5)
    print(f"9. Positional all data: '{result9}'")
    
    # Some data missing (fewer arguments)
    result10 = formatter.format("Failed")  # Only first argument
    print(f"10. Positional partial data: '{result10}'")
    
    print("\nKey insight: No manual null checking required!")
    print("Compare to manual approach:")
    print("  parts = []")
    print("  if message: parts.append(f'Error: {message}')")
    print("  if file_count: parts.append(f'Processing {file_count} files')")
    print("  if seconds: parts.append(f'Duration: {seconds}s')")
    print("  result = ' '.join(parts)")


def demo_positional_arguments():
    """Demonstrate the new positional arguments feature"""
    print("\n=== Positional Arguments Feature (NEW) ===")
    
    # 1. Basic positional syntax
    formatter = DynamicFormatter("{{}}")
    result = formatter.format("Hello")
    print(f"1. Single field: '{result}'")
    
    formatter = DynamicFormatter("{{}} {{}}")
    result = formatter.format("Hello", "World")
    print(f"2. Multiple fields: '{result}'")
    
    # 3. Positional with prefixes and suffixes
    formatter = DynamicFormatter("{{Error: ;}}")
    result = formatter.format("Connection failed")
    print(f"3. With prefix: '{result}'")
    
    formatter = DynamicFormatter("{{Count: ;;items}}")
    result = formatter.format(25)
    print(f"4. With prefix and suffix: '{result}'")
    
    # 5. Complex formatting with positional args
    formatter = DynamicFormatter("{{#red@bold;}}")
    result = formatter.format("URGENT")
    print(f"5. With formatting: {result}")
    
    formatter = DynamicFormatter("{{#red@bold;Alert: ;}}")
    result = formatter.format("System down")
    print(f"6. Formatting with prefix: {result}")
    
    # 7. Multiple formatted sections
    formatter = DynamicFormatter("{{#red;Error: ;}} {{#green;Status: ;}}")
    result = formatter.format("Failed", "Recovered")
    print(f"7. Multiple formatted: {result}")
    
    # 8. Positional with functions
    def priority_color(priority):
        return {'high': 'red', 'medium': 'yellow', 'low': 'green'}[priority.lower()]
    
    formatter = DynamicFormatter("{{#priority_color@bold;Priority: ;}}", 
                                functions={'priority_color': priority_color})
    result = formatter.format("HIGH")
    print(f"8. With function fallback: {result}")
    
    # 9. Positional with conditionals
    def is_urgent(priority):
        return priority.lower() in ['high', 'critical']
    
    formatter = DynamicFormatter("{{?is_urgent;URGENT: ;}}", 
                                functions={'is_urgent': is_urgent})
    result1 = formatter.format("HIGH")
    result2 = formatter.format("LOW")
    print(f"9. Conditional (urgent): '{result1}'")
    print(f"10. Conditional (normal): '{result2}'")
    
    # 11. Missing arguments demonstration
    formatter = DynamicFormatter("{{First: ;}} {{Second: ;}} {{Third: ;}}")
    result1 = formatter.format("A", "B", "C")
    result2 = formatter.format("A", "B")
    result3 = formatter.format("A")
    print(f"11. All arguments: '{result1}'")
    print(f"12. Two arguments: '{result2}'")
    print(f"13. One argument: '{result3}'")
    
    # 14. Comparison with keyword arguments
    print("\n--- Keyword vs Positional Comparison ---")
    
    # Same template content, different argument styles
    kw_formatter = DynamicFormatter("{{Error: ;message}} {{Code: ;code}}")
    pos_formatter = DynamicFormatter("{{Error: ;}} {{Code: ;}}")
    
    kw_result = kw_formatter.format(message="Failed", code=404)
    pos_result = pos_formatter.format("Failed", 404)
    
    print(f"Keyword style: '{kw_result}'")
    print(f"Positional style: '{pos_result}'")
    
    print("\nBenefits of positional arguments:")
    print("• Cleaner templates: {{}} vs {{field_name}}")
    print("• Simpler function calls: format('a', 'b') vs format(field1='a', field2='b')")
    print("• Good for fixed-order data like tuples or API responses")
    print("• Still supports all formatting features (colors, functions, conditionals)")


def demo_basic_formatting():
    """Demonstrate basic formatting capabilities"""
    print("\n=== Basic Formatting ===")
    
    # Colors
    formatter = DynamicFormatter("{{#red;Error: ;message}}")
    result = formatter.format(message="System failure")
    print(f"1. Red text: {result}")
    
    # Text styles
    formatter = DynamicFormatter("{{@bold;Important: ;message}}")
    result = formatter.format(message="Read this")
    print(f"2. Bold text: {result}")
    
    # Combined formatting
    formatter = DynamicFormatter("{{#blue@italic;Note: ;message}}")
    result = formatter.format(message="This is blue and italic")
    print(f"3. Blue italic: {result}")


def demo_function_fallback():
    """Demonstrate function fallback system"""
    print("\n=== Function Fallback System ===")
    
    def level_color(level):
        return {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'green'}[level]
    
    def has_items(count):
        return count > 0
    
    functions = {'level_color': level_color, 'has_items': has_items}
    
    # Color function - Fixed template to show the message
    formatter = DynamicFormatter("{{#level_color;[;level;] ;message}}", functions=functions)
    result = formatter.format(level="ERROR", message="System down")
    print(f"1. Color function: {result}")
    
    # Conditional function
    formatter = DynamicFormatter("{{?has_items;Found ;count; items}}", functions=functions)
    result1 = formatter.format(count=5)
    result2 = formatter.format(count=0)
    print(f"2. Conditional (has items): '{result1}'")
    print(f"3. Conditional (no items): '{result2}'")


def demo_error_scenarios():
    """Demonstrate error handling"""
    print("\n=== Error Handling ===")
    
    # Too many positional arguments
    try:
        formatter = DynamicFormatter("{{}}")
        formatter.format("first", "second")
    except DynamicFormattingError as e:
        print(f"1. Too many args: {e}")
    
    # Missing required field
    try:
        formatter = DynamicFormatter("{{!}}")
        formatter.format()
    except RequiredFieldError as e:
        print(f"2. Required field: {e}")
    
    # Invalid color - Catch the right exception type
    try:
        formatter = DynamicFormatter("{{#invalid_color;Text: ;field}}")
        formatter.format(field="test")
    except DynamicFormattingError as e:  # This catches the wrapped error
        print(f"3. Invalid color: {e}")
    except FormatterError as e:  # This catches the original error if not wrapped
        print(f"3. Invalid color: {e}")


def run_examples():
    """Run all example demonstrations"""
    print("Dynamic Formatting System - Examples")
    print("=" * 50)
    
    try:
        demo_core_feature_graceful_missing_data()
        demo_positional_arguments()
        demo_basic_formatting()
        demo_function_fallback()
        demo_error_scenarios()
        
        print("\n" + "=" * 50)
        print("✅ All examples completed successfully!")
        print("\nKey Features Demonstrated:")
        print("• Graceful missing data handling (core feature)")
        print("• Positional arguments (new feature)")
        print("• Color and text formatting")
        print("• Function fallback system")
        print("• Error handling and validation")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("This indicates an issue with the package that should be investigated.")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_examples()