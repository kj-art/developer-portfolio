#!/usr/bin/env python3
"""
Template Validation Demo

Demonstrates the professional template validation system that catches
issues at creation time and provides helpful suggestions.

Run from project root: python shared_utils/dynamic_formatting/validation_demo.py
"""

import sys
import os
from pathlib import Path

# Ensure we can import from the project root
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

print(f"Script location: {script_dir}")
print(f"Project root: {project_root}")
print(f"Current working directory: {os.getcwd()}")

try:
    from shared_utils.dynamic_formatting import DynamicFormatter
    print("✓ Successfully imported dynamic formatting package!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you're running from the project root directory")
    print("2. Check that the shared_utils directory exists")
    print("3. Try: python -c 'from shared_utils.dynamic_formatting import DynamicFormatter'")
    
    # Show what we can see in the directory
    shared_utils_path = project_root / "shared_utils"
    if shared_utils_path.exists():
        print(f"\n✓ Found shared_utils at: {shared_utils_path}")
        dynamic_formatting_path = shared_utils_path / "dynamic_formatting"
        if dynamic_formatting_path.exists():
            print(f"✓ Found dynamic_formatting at: {dynamic_formatting_path}")
            init_file = dynamic_formatting_path / "__init__.py"
            if init_file.exists():
                print(f"✓ Found __init__.py")
            else:
                print(f"❌ Missing __init__.py")
        else:
            print(f"❌ dynamic_formatting directory not found")
    else:
        print(f"❌ shared_utils directory not found at: {shared_utils_path}")
    
    sys.exit(1)


def demo_validation_features():
    """Demonstrate various validation features"""
    
    print("\n🔍 TEMPLATE VALIDATION SYSTEM DEMO")
    print("=" * 50)
    print()
    
    # Demo 1: Syntax Errors
    print("📋 1. SYNTAX ERROR DETECTION")
    print("-" * 30)
    
    try:
        # Unclosed template section
        formatter = DynamicFormatter("{{Error: ;message")  # Missing }}
        print("❌ Should have caught unclosed section!")
    except Exception as e:
        print(f"✅ Caught syntax error: {type(e).__name__}: {e}")
    
    # Demo 2: Invalid Tokens with Suggestions
    print("\n📋 2. INVALID TOKEN DETECTION")
    print("-" * 30)
    
    # This will show validation warnings but still work
    print("Creating formatter with invalid color 'rd'...")
    formatter = DynamicFormatter("{{#rd;Error: ;message}}", validate=True)
    result = formatter.format(message="test")
    print(f"✅ Formatter still works with graceful degradation: '{result}'")
    print("(Note: Invalid color 'rd' was ignored, no color formatting applied)")
    
    # Demo 3: Performance Warnings
    print("\n📋 3. PERFORMANCE ANALYSIS")
    print("-" * 30)
    
    # Large template
    print("Creating large template with 60 sections...")
    large_template = " ".join([f"{{{{Field{i}: ;field{i}}}}}" for i in range(60)])
    formatter = DynamicFormatter(large_template, validate=True)
    print("✅ Large template created (check above for performance warnings)")
    
    # Demo 4: Best Practice Suggestions
    print("\n📋 4. BEST PRACTICE RECOMMENDATIONS")
    print("-" * 30)
    
    # Multiple colors (only last one applies)
    print("Creating template with multiple colors...")
    formatter = DynamicFormatter("{{#red#blue#green;Multi-color: ;text}}", validate=True)
    result = formatter.format(text="example")
    print(f"✅ Result: {result} (should be green only)")
    
    # Demo 5: Function Validation
    print("\n📋 5. FUNCTION VALIDATION")
    print("-" * 30)
    
    # Missing function - should work with graceful degradation
    print("Creating template with missing conditional function...")
    formatter = DynamicFormatter("{{?missing_func;Conditional: ;text}}", validate=True)
    result = formatter.format(text="test")
    print(f"✅ Result with missing function: '{result}' (section hidden due to missing function)")
    
    # Demo with a working function for comparison
    def test_function(value):
        return len(str(value)) > 3
    
    formatter_working = DynamicFormatter("{{?test_function;Conditional: ;text}}", 
                                        functions={"test_function": test_function}, validate=True)
    result_working = formatter_working.format(text="testing")
    result_short = formatter_working.format(text="hi")
    print(f"✅ With working function (long text): '{result_working}'")
    print(f"✅ With working function (short text): '{result_short}'")
    
    # Demo 6: Validation Report
    print("\n📋 6. DETAILED VALIDATION REPORT")
    print("-" * 30)
    
    # Complex template with multiple issues
    complex_template = "{{#invalidcolor@invalidstyle;Error: ;message}} {{?missing_function;Found ;count; items}} {{#red#blue#green;Multiple: ;colors}}"
    
    print("Creating complex template with multiple issues...")
    formatter = DynamicFormatter(complex_template, validate=True)
    print("\n📊 Full Validation Report:")
    print(formatter.get_validation_report())
    
    # Demo 7: Validation Levels
    print("\n📋 7. VALIDATION LEVELS")
    print("-" * 30)
    
    print("🔴 Error level only:")
    formatter = DynamicFormatter("{{#badcolor;Test: ;field}}", validate=True, validation_level='error')
    
    print("\n🟡 Warning level and above:")
    formatter = DynamicFormatter("{{#badcolor;Test: ;field}}", validate=True, validation_level='warning')
    
    print("\n🔵 All validation messages:")
    formatter = DynamicFormatter("{{#badcolor;Test: ;field}}", validate=True, validation_level='info')
    
    # Demo 8: Disable Validation
    print("\n📋 8. VALIDATION CONTROL")
    print("-" * 30)
    
    print("Validation disabled - no warnings:")
    formatter = DynamicFormatter("{{#badcolor;Test: ;field}}", validate=False)
    result = formatter.format(field="example")
    print(f"✅ Created formatter without validation: '{result}'")


def demo_professional_usage():
    """Show professional usage patterns"""
    
    print("\n\n🏢 PROFESSIONAL USAGE PATTERNS")
    print("=" * 50)
    
    # Development vs Production
    print("\n📋 DEVELOPMENT vs PRODUCTION")
    print("-" * 30)
    
    # Development: Full validation
    dev_template = "{{#level_color@bold;[;level;]}} {{message}} {{Duration: ;duration;s}}"
    print("Creating development formatter with full validation...")
    dev_formatter = DynamicFormatter(
        dev_template, 
        validate=True, 
        validation_level='info'
    )
    print("✅ Development formatter: Full validation enabled")
    
    # Production: Validation disabled for performance
    print("\nCreating production formatter without validation...")
    prod_formatter = DynamicFormatter(
        dev_template,
        validate=False
    )
    print("✅ Production formatter: Validation disabled for performance")
    
    # Test both formatters
    test_data = {"level": "INFO", "message": "System started", "duration": 1.25}
    dev_result = dev_formatter.format(**test_data)
    prod_result = prod_formatter.format(**test_data)
    print(f"\nDev result: {dev_result}")
    print(f"Prod result: {prod_result}")
    
    # Logging usage with validation
    print("\n📋 LOGGING WITH VALIDATION")
    print("-" * 30)
    
    try:
        from shared_utils.dynamic_formatting import DynamicLoggingFormatter
        
        # Development logging with validation
        print("Creating development logging formatter...")
        dev_log_formatter = DynamicLoggingFormatter(
            "{{#level_color;[;levelname;]}} {{message}} {{Duration: ;duration;s}}",
            validate=True,
            validation_level='warning'
        )
        print("✅ Development logging: Validation enabled")
        
        # Production logging without validation spam
        print("Creating production logging formatter...")
        prod_log_formatter = DynamicLoggingFormatter(
            "{{#level_color;[;levelname;]}} {{message}} {{Duration: ;duration;s}}",
            validate=False
        )
        print("✅ Production logging: Validation disabled")
        
    except Exception as e:
        print(f"Logging demo failed: {e}")


def demo_validation_benefits():
    """Show the benefits of validation"""
    
    print("\n\n💡 VALIDATION BENEFITS")
    print("=" * 50)
    
    print("""
🎯 CATCHES ISSUES EARLY:
   • Find template problems during development, not production
   • Prevent runtime errors before they happen
   • Faster development cycle with immediate feedback

🔧 BETTER DEVELOPER EXPERIENCE:
   • Helpful suggestions for fixing issues (e.g., "Did you mean 'red'?")
   • Performance warnings for large templates
   • Best practice recommendations

🏢 ENTERPRISE QUALITY:
   • Professional attention to developer productivity
   • Prevents common mistakes before they reach production
   • Shows engineering maturity and attention to quality

⚡ PROFESSIONAL FEATURES:
   • Configurable validation levels (error/warning/info)
   • Detailed validation reports
   • Easy to disable in production for performance
   • Integration with logging systems
    """)


if __name__ == "__main__":
    try:
        demo_validation_features()
        demo_professional_usage()
        demo_validation_benefits()
        
        print("\n" + "=" * 50)
        print("✅ Template validation demo completed!")
        print("\n🚀 Key Features Demonstrated:")
        print("• Proactive error prevention")
        print("• Helpful suggestions and corrections")
        print("• Performance and complexity analysis")
        print("• Professional development workflow")
        print("• Configurable validation levels")
        print("• Enterprise-grade quality checking")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()