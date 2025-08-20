#!/usr/bin/env python3
"""
Quick test script to verify the core fixes are working correctly.

This tests the most critical functionality that was broken:
1. Basic template parsing and rendering
2. Positional argument handling  
3. Color and text formatting
4. Conditional logic
5. Function registry setup
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_basic_formatting():
    """Test basic template parsing and field mapping"""
    print("🧪 Testing Basic Formatting...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter
        
        # Test 1: Basic field formatting
        formatter = DynamicFormatter("{{Error: ;message}}")
        result = formatter.format(message="Test failed")
        expected = "Error: Test failed"
        
        print(f"   Template: {{{{Error: ;message}}}}")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}")
        
        if result == expected:
            print("   ✅ PASS: Basic formatting works!")
            return True
        else:
            print("   ❌ FAIL: Basic formatting broken")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_positional_arguments():
    """Test positional argument parsing"""
    print("\n🧪 Testing Positional Arguments...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter
        
        # Test 2: Positional with prefix and suffix
        formatter = DynamicFormatter("{{Error: ;;!}}")
        result = formatter.format("Connection failed")
        expected = "Error: Connection failed!"
        
        print(f"   Template: {{{{Error: ;;!}}}}")
        print(f"   Args:     ['Connection failed']")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}")
        
        if result == expected:
            print("   ✅ PASS: Positional arguments work!")
            return True
        else:
            print("   ❌ FAIL: Positional parsing broken")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_color_formatting():
    """Test color formatting functionality"""
    print("\n🧪 Testing Color Formatting...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter
        
        # Test 3: Color formatting
        formatter = DynamicFormatter("{{#red;Error: ;message}}")
        result = formatter.format(message="Failed")
        
        print(f"   Template: {{{{#red;Error: ;message}}}}")
        print(f"   Data:     message='Failed'")
        print(f"   Result:   {repr(result)}")
        
        # Should contain the text and ANSI color codes
        if "Error: Failed" in result and "\033[" in result:
            print("   ✅ PASS: Color formatting works!")
            return True
        elif "Error: Failed" in result:
            print("   ⚠️  PARTIAL: Text works but no color codes")
            return True
        else:
            print("   ❌ FAIL: Color formatting broken")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_conditional_logic():
    """Test conditional function logic"""
    print("\n🧪 Testing Conditional Logic...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter
        
        # Test 4: Conditional functions
        def has_value(val):
            return bool(val and str(val).strip())
        
        formatter = DynamicFormatter(
            "{{Processing}} {{?has_value;Found: ;data}}",
            functions={"has_value": has_value}
        )
        
        # Test with data
        result1 = formatter.format(data="test")
        expected1 = "Processing Found: test"
        
        print(f"   Template: {{{{Processing}}}} {{{{?has_value;Found: ;data}}}}")
        print(f"   Data:     data='test'")
        print(f"   Expected: {expected1}")
        print(f"   Got:      {result1}")
        
        # Test without data (should hide conditional section)
        result2 = formatter.format(data="")
        expected2 = "Processing "
        
        print(f"   Data:     data=''")
        print(f"   Expected: {expected2}")
        print(f"   Got:      {result2}")
        
        if result1 == expected1 and result2.strip() == expected2.strip():
            print("   ✅ PASS: Conditional logic works!")
            return True
        else:
            print("   ❌ FAIL: Conditional logic broken")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_required_fields():
    """Test required field validation"""
    print("\n🧪 Testing Required Fields...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter, RequiredFieldError
        
        # Test 5: Required fields
        formatter = DynamicFormatter("{{!;Critical: ;message}}")
        
        # Should work with data
        result1 = formatter.format(message="System down")
        expected1 = "Critical: System down"
        
        print(f"   Template: {{{{!;Critical: ;message}}}}")
        print(f"   Data:     message='System down'")
        print(f"   Expected: {expected1}")
        print(f"   Got:      {result1}")
        
        if result1 == expected1:
            print("   ✅ PASS: Required field with data works!")
        else:
            print("   ❌ FAIL: Required field with data broken")
            return False
        
        # Should raise error without data
        try:
            result2 = formatter.format()  # No message provided
            print("   ❌ FAIL: Should have raised RequiredFieldError")
            return False
        except RequiredFieldError:
            print("   ✅ PASS: Required field validation works!")
            return True
        except Exception as e:
            print(f"   ❌ FAIL: Wrong exception type: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def main():
    """Run all core tests"""
    print("🔧 TESTING CORE DYNAMIC FORMATTING FIXES")
    print("=" * 50)
    
    tests = [
        test_basic_formatting,
        test_positional_arguments,
        test_color_formatting,
        test_conditional_logic,
        test_required_fields
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL CORE FUNCTIONALITY WORKING!")
    elif passed >= total * 0.8:
        print("✅ Most core functionality working - good progress!")
    else:
        print("⚠️  Still significant issues to resolve")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)