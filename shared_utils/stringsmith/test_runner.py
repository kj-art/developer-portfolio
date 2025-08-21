#!/usr/bin/env python3
"""
Simple test runner for StringSmith to debug import issues.
"""

import sys
import os

# Get the directory containing this script (should be the stringsmith package directory)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the stringsmith directory to Python path so we can import it as a package
sys.path.insert(0, script_dir)

# Also add the parent directory in case we're running from outside
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

print(f"Script directory: {script_dir}")
print(f"Python path: {sys.path[:3]}")  # Show first 3 entries

#!/usr/bin/env python3
"""
Simple test runner for StringSmith to debug import issues.
"""

import sys
import os

# Get the directory containing this script (the stringsmith package files are here)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add this directory to Python path so we can import the modules directly
sys.path.insert(0, script_dir)

print(f"Script directory: {script_dir}")
print(f"Python path: {sys.path[:3]}")  # Show first 3 entries

def test_import():
    """Test basic import functionality."""
    try:
        # Import directly from the local modules since they're in the same directory
        from formatter import TemplateFormatter
        print("✅ Successfully imported TemplateFormatter")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality."""
    try:
        from formatter import TemplateFormatter
        
        # Test 1: Simple variable
        print("Testing simple variable substitution...")
        formatter = TemplateFormatter("Hello {{name}}!")
        print(f"Template: 'Hello {{{{name}}}}!'")
        
        result = formatter.format(name="World")
        expected = "Hello World!"
        print(f"Result: '{result}'")
        print(f"Expected: '{expected}'")
        
        # Debug: Check what sections were parsed
        print(f"Parsed sections: {len(formatter.sections)}")
        for i, section in enumerate(formatter.sections):
            print(f"  Section {i}: {section}")
        
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print("✅ Basic variable substitution works")
        
        # Test 2: Missing optional variable
        print("\nTesting missing optional variable...")
        result = formatter.format()
        expected = "Hello !"
        print(f"Result: '{result}'")
        print(f"Expected: '{expected}'")
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print("✅ Missing optional variable works")
        
        # Test 3: Positional arguments
        print("\nTesting positional arguments...")
        formatter = TemplateFormatter("{{first}} {{second}}")
        print(f"Template: '{{{{first}}}} {{{{second}}}}'")
        
        # Debug: Check what sections were parsed for positional
        print(f"Parsed sections: {len(formatter.sections)}")
        for i, section in enumerate(formatter.sections):
            print(f"  Section {i}: {section}")
        
        result = formatter.format("Alpha", "Beta")
        expected = "Alpha Beta"
        print(f"Result: '{result}'")
        print(f"Expected: '{expected}'")
        print(f"Variables passed: {{'__pos_0__': 'Alpha', '__pos_1__': 'Beta'}}")
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print("✅ Positional arguments work")
        
        # Test 4: Mandatory section
        print("\nTesting mandatory sections...")
        from exceptions import MissingMandatoryFieldError
        formatter = TemplateFormatter("{{!name}}")
        try:
            formatter.format()
            assert False, "Should have raised MissingMandatoryFieldError"
        except MissingMandatoryFieldError:
            print("✅ Mandatory sections work")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_formatting():
    """Test formatting functionality."""
    try:
        from formatter import TemplateFormatter
        
        # Test color formatting
        formatter = TemplateFormatter("{{#red;message}}")
        result = formatter.format(message="test")
        # Should contain ANSI color codes
        assert "\033[31m" in result, f"Expected red color code in '{result}'"
        print("✅ Color formatting works")
        
        # Test emphasis formatting
        formatter = TemplateFormatter("{{@bold;message}}")
        result = formatter.format(message="test")
        assert "\033[1m" in result, f"Expected bold code in '{result}'"
        print("✅ Emphasis formatting works")
        
        return True
        
    except Exception as e:
        print(f"❌ Formatting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running StringSmith tests...")
    print()
    
    success = True
    success &= test_import()
    success &= test_basic_functionality() 
    success &= test_formatting()
    
    print()
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")
    
    sys.exit(0 if success else 1)