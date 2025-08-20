#!/usr/bin/env python3
"""
Test script to verify all dynamic formatting fixes.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_formatting():
    """Test basic formatting functionality"""
    print("Testing basic formatting...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter
        
        # Test basic formatting
        formatter = DynamicFormatter("{{Status: ;status}}")
        result = formatter.format(status="Success")
        print(f"  Basic test: '{result}'")
        assert "Status: Success" in result
        
        # Test missing data handling
        formatter = DynamicFormatter("{{Status: ;status}} {{Code: ;code}}")
        result = formatter.format(status="Success")
        print(f"  Missing data test: '{result}'")
        assert "Status: Success" in result
        assert "Code:" not in result
        
        print("  ✅ Basic formatting tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Basic formatting failed: {e}")
        return False

def test_configuration():
    """Test configuration system"""
    print("Testing configuration system...")
    
    try:
        from shared_utils.dynamic_formatting import FormatterConfig, ValidationMode
        
        # Test configuration creation
        config = FormatterConfig(
            validation_mode=ValidationMode.STRICT,
            enable_performance_monitoring=True
        )
        print(f"  Config creation: {config.validation_mode}")
        
        # Test factory methods
        dev_config = FormatterConfig.development()
        prod_config = FormatterConfig.production()
        print(f"  Factory methods: dev={dev_config.validation_mode}, prod={prod_config.validation_mode}")
        
        # Test config file loading
        config_path = project_root / "shared_utils" / "dynamic_formatting" / "configs" / "minimal.json"
        if config_path.exists():
            loaded_config = FormatterConfig.from_config_file(config_path)
            print(f"  Config file loading: {loaded_config.validation_mode}")
        
        print("  ✅ Configuration tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_monitoring():
    """Test performance monitoring"""
    print("Testing performance monitoring...")
    
    try:
        from shared_utils.dynamic_formatting import PerformanceMonitor
        
        # Test monitor creation
        monitor = PerformanceMonitor(enabled=True)
        
        # Test context manager
        with monitor.track("test_operation"):
            # Simulate some work
            result = "test" * 100
        
        stats = monitor.get_stats()
        print(f"  Monitor stats: {len(stats)} operations tracked")
        
        print("  ✅ Performance monitoring tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Performance monitoring failed: {e}")
        return False

def test_color_formatting():
    """Test color and text formatting"""
    print("Testing color and text formatting...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter
        
        # Test color formatting
        formatter = DynamicFormatter("{{#red;Error: ;message}}")
        result = formatter.format(message="Failed")
        print(f"  Color test: '{result}'")
        assert "Error: Failed" in result
        
        # Test text formatting
        formatter = DynamicFormatter("{{@bold;Warning: ;message}}")
        result = formatter.format(message="Important")
        print(f"  Text style test: '{result}'")
        assert "Warning: Important" in result
        
        print("  ✅ Color and text formatting tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Color and text formatting failed: {e}")
        return False

def test_positional_arguments():
    """Test positional argument support"""
    print("Testing positional arguments...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter
        
        # Test basic positional
        formatter = DynamicFormatter("{{}}")
        result = formatter.format("test")
        print(f"  Basic positional: '{result}'")
        assert result == "test"
        
        # Test positional with prefix/suffix
        formatter = DynamicFormatter("{{Status: ;}}")
        result = formatter.format("Success")
        print(f"  Positional with prefix: '{result}'")
        assert result == "Status: Success"
        
        print("  ✅ Positional argument tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Positional arguments failed: {e}")
        return False

def test_function_fallback():
    """Test function fallback system"""
    print("Testing function fallback...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter, FormatterConfig
        
        def level_color(level):
            return {"ERROR": "red", "INFO": "green"}[level]
        
        config = FormatterConfig(functions={"level_color": level_color})
        formatter = DynamicFormatter("{{#level_color;[;level;]}}", config=config)
        result = formatter.format(level="ERROR")
        print(f"  Function fallback: '{result}'")
        assert "[ERROR]" in result
        
        print("  ✅ Function fallback tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Function fallback failed: {e}")
        return False

def test_conditional_logic():
    """Test conditional logic"""
    print("Testing conditional logic...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter, FormatterConfig
        
        def has_value(val):
            return bool(val)
        
        config = FormatterConfig(functions={"has_value": has_value})
        formatter = DynamicFormatter("{{Processing}} {{?has_value;Found: ;}}", config=config)
        
        # Test with value
        result = formatter.format(25)
        print(f"  Conditional with value: '{result}'")
        assert "Processing" in result and "Found: 25" in result
        
        # Test without value
        result = formatter.format(None)
        print(f"  Conditional without value: '{result}'")
        assert result.strip() == "Processing"
        
        # Test conditional token format specifically
        formatter2 = DynamicFormatter("{{Status: ;status}} {{?has_value;Count: ;count}}", config=config)
        result2 = formatter2.format(status="OK", count=5)
        print(f"  Named field conditional: '{result2}'")
        assert "Status: OK" in result2 and "Count: 5" in result2
        
        result3 = formatter2.format(status="OK", count=None)
        print(f"  Named field conditional (no count): '{result3}'")
        assert "Status: OK" in result3 and "Count:" not in result3
        
        print("  ✅ Conditional logic tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Conditional logic failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_output_modes():
    """Test different output modes"""
    print("Testing output modes...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter, FormatterConfig
        
        # Test console mode (with colors)
        console_config = FormatterConfig(output_mode="console", enable_colors=True)
        formatter = DynamicFormatter("{{#red;Error: ;message}}", config=console_config)
        console_result = formatter.format(message="Failed")
        print(f"  Console mode: '{console_result}'")
        
        # Test file mode (no colors)
        file_config = FormatterConfig(output_mode="file", enable_colors=False)
        formatter = DynamicFormatter("{{#red;Error: ;message}}", config=file_config)
        file_result = formatter.format(message="Failed")
        print(f"  File mode: '{file_result}'")
        assert file_result == "Error: Failed"
        
        print("  ✅ Output mode tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Output modes failed: {e}")
        return False

def test_escape_sequences():
    """Test escape sequence handling"""
    print("Testing escape sequences...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter
        
        # Test escaped braces
        formatter = DynamicFormatter("\\{\\{not a template\\}\\}")
        result = formatter.format()
        print(f"  Escaped braces: '{result}'")
        assert result == "{{not a template}}"
        
        # Test escaped delimiter
        formatter = DynamicFormatter("{{Value\\;with\\;semicolons: ;value}}")
        result = formatter.format(value="test")
        print(f"  Escaped delimiter: '{result}'")
        assert "Value;with;semicolons: test" in result
        
        print("  ✅ Escape sequence tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Escape sequences failed: {e}")
        return False

def test_required_fields():
    """Test required field functionality"""
    print("Testing required fields...")
    
    try:
        from shared_utils.dynamic_formatting import DynamicFormatter, RequiredFieldError
        
        # Test required field present
        formatter = DynamicFormatter("{{!;Critical: ;message}}")
        result = formatter.format(message="System down")
        print(f"  Required field present: '{result}'")
        assert "Critical: System down" in result
        
        # Test required field missing (should raise error)
        try:
            formatter.format()
            print("  ❌ Required field test failed - should have raised error")
            return False
        except RequiredFieldError:
            print("  Required field missing: correctly raised RequiredFieldError")
        
        print("  ✅ Required field tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Required fields failed: {e}")
        return False

def run_all_tests():
    """Run all test functions"""
    print("=" * 60)
    print("RUNNING DYNAMIC FORMATTING SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        test_basic_formatting,
        test_configuration,
        test_performance_monitoring,
        test_color_formatting,
        test_positional_arguments,
        test_function_fallback,
        test_conditional_logic,
        test_output_modes,
        test_escape_sequences,
        test_required_fields,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ Test {test_func.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! The dynamic formatting system is working correctly.")
        return True
    else:
        print(f"❌ {failed} tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)