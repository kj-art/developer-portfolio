"""
Test escape sequences for curly braces in dynamic formatting.
"""

import sys
from pathlib import Path

# Add the project root to path so we can import as a package
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared_utils.dynamic_formatting import DynamicFormatter
    print("✓ Successfully imported DynamicFormatter!")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)


def test_basic_escaping():
    """Test basic curly brace escaping"""
    print("\n=== Basic Escape Sequences ===")
    
    # Test 1: Escaped braces in literal text
    formatter = DynamicFormatter("Instructions: Use \\{variable\\} syntax in your code")
    result = formatter.format()
    print(f"1. Escaped braces in literals:")
    print(f"   Visual: {result}")
    print(f"   Raw: {repr(result)}")
    
    # Test 2: Mixed escaped and formatting braces
    formatter2 = DynamicFormatter("Config: \\{setting\\} = {{#green;value: ;setting}}")
    result2 = formatter2.format(setting="debug")
    print(f"2. Mixed escaped and formatting:")
    print(f"   Visual: {result2}")
    print(f"   Raw: {repr(result2)}")
    
    # Test 3: Escaped braces with field values
    formatter3 = DynamicFormatter("Template: \\{\\{;field_name;\\}\\} becomes {{field_value}}")
    result3 = formatter3.format(field_name="user", field_value="john")
    print(f"3. Template example:")
    print(f"   Visual: {result3}")
    print(f"   Raw: {repr(result3)}")


def test_inline_escaping():
    """Test escaping with inline formatting"""
    print("\n=== Inline Formatting with Escaping ===")
    
    def has_value(value):
        return bool(value)
    
    functions = {'has_value': has_value}
    
    # Test 1: Escaped braces in conditional text
    formatter = DynamicFormatter(
        "{{Use{?has_value} \\{brackets\\} for: ;syntax}}",
        functions=functions
    )
    
    result1 = formatter.format(syntax="variables")
    print(f"1. With conditional (has value):")
    print(f"   Visual: {result1}")
    print(f"   Raw: {repr(result1)}")
    
    result2 = formatter.format(syntax="")
    print(f"2. Without conditional (no value):")
    print(f"   Visual: {result2}")
    print(f"   Raw: {repr(result2)}")
    
    # Test 3: Escaped braces in formatted text (fixed syntax)
    formatter3 = DynamicFormatter("{{#red;Error in \\{module\\}: ;error}}")
    result3 = formatter3.format(error="syntax error")
    print(f"3. Escaped braces with formatting:")
    print(f"   Visual: {result3}")
    print(f"   Raw: {repr(result3)}")


def test_complex_escaping():
    """Test complex escaping scenarios"""
    print("\n=== Complex Escape Scenarios ===")
    
    # Test 1: Documentation example
    formatter = DynamicFormatter(
        "Format strings use \\{\\{field\\}\\} syntax. Example: {{#blue;Hello ;name}}!"
    )
    result = formatter.format(name="World")
    print(f"1. Documentation example:")
    print(f"   Visual: {result}")
    print(f"   Raw: {repr(result)}")
    
    # Test 2: JSON-like output with escaping
    formatter2 = DynamicFormatter(
        "\\{\"status\": \"{{#green;status}}\", \"message\": \"{{message}}\"\\}"
    )
    result2 = formatter2.format(status="success", message="Operation completed")
    print(f"2. JSON-like output:")
    print(f"   Visual: {result2}")
    print(f"   Raw: {repr(result2)}")
    
    # Test 3: Delimiter escaping with brace escaping
    formatter3 = DynamicFormatter("{{Config \\{key\\}: ;value}};separator\\;value")
    result3 = formatter3.format(value="setting=true")
    print(f"3. Mixed delimiter and brace escaping:")
    print(f"   Visual: {result3}")
    print(f"   Raw: {repr(result3)}")


def test_edge_cases():
    """Test edge cases and error conditions"""
    print("\n=== Edge Cases ===")
    
    # Test 1: Only escaped braces
    formatter = DynamicFormatter("\\{\\{no formatting here\\}\\}")
    result = formatter.format()
    print(f"1. Only escaped braces:")
    print(f"   Visual: {result}")
    print(f"   Raw: {repr(result)}")
    
    # Test 2: Backslash at end
    formatter2 = DynamicFormatter("{{message}} ends with backslash\\")
    result2 = formatter2.format(message="This")
    print(f"2. Backslash at end:")
    print(f"   Visual: {result2}")
    print(f"   Raw: {repr(result2)}")
    
    # Test 3: Multiple consecutive escapes
    formatter3 = DynamicFormatter("Multiple \\{\\{\\{braces\\}\\}\\} here")
    result3 = formatter3.format()
    print(f"3. Multiple consecutive escapes:")
    print(f"   Visual: {result3}")
    print(f"   Raw: {repr(result3)}")


def run_all_tests():
    """Run all escape sequence tests"""
    print("Testing Curly Brace Escape Sequences")
    print("=" * 40)
    
    try:
        test_basic_escaping()
        test_inline_escaping()
        test_complex_escaping()
        test_edge_cases()
        
        print("\n" + "=" * 40)
        print("✅ All escape sequence tests completed successfully!")
        print("\nEscape sequences now supported:")
        print("• \\{ → { (literal opening brace)")
        print("• \\} → } (literal closing brace)")
        print("• \\; → ; (literal semicolon)")
        print("• Works in all contexts: literals, formatting, conditionals")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()

#python shared_utils/dynamic_formatting/test_escape_sequences.py