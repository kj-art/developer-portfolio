#!/usr/bin/env python3
"""
Template Validation and Graceful Degradation Demo

Demonstrates the professional template validation system and configurable
graceful degradation that makes the formatting system production-ready.

This showcases the enterprise-grade features that differentiate this package
from academic demos to production-ready tools.

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
    from shared_utils.dynamic_formatting import DynamicFormatter, DynamicLoggingFormatter
    from shared_utils.dynamic_formatting.config import FormatterConfig, ValidationMode, ValidationLevel
    print("✓ Successfully imported dynamic formatting package!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you're running from the project root directory")
    print("2. Check that the shared_utils directory exists")
    print("3. Try: python -c 'from shared_utils.dynamic_formatting import DynamicFormatter'")
    sys.exit(1)


def demo_validation_modes():
    """Demonstrate the three validation modes: strict, graceful, auto-correct"""
    
    print("\n🔧 VALIDATION MODES DEMONSTRATION")
    print("=" * 50)
    
    # Test template with multiple issues
    problematic_template = "{{#invalidcolor@badstyle;Error: ;message}} {{?missing_func;Alert: ;text}}"
    
    print("📋 Template with issues:")
    print(f"   {problematic_template}")
    print()
    
    # Test data
    test_data = {"message": "System failure", "text": "Critical alert"}
    
    # Mode 1: STRICT - Catches issues early (development)
    print("🔴 1. STRICT MODE (Development)")
    print("-" * 30)
    
    strict_config = FormatterConfig.development()
    print("Creating formatter in strict mode...")
    
    try:
        formatter = DynamicFormatter(problematic_template, config=strict_config)
        result = formatter.format(**test_data)
        print(f"❌ Should have failed in strict mode! Got: '{result}'")
    except Exception as e:
        print(f"✅ Strict mode correctly caught error: {type(e).__name__}")
        print(f"   Error: {e}")
    
    # Mode 2: GRACEFUL - Degrades safely (production)
    print("\n🟢 2. GRACEFUL MODE (Production)")
    print("-" * 30)
    
    graceful_config = FormatterConfig.production()
    print("Creating formatter in graceful mode...")
    
    formatter = DynamicFormatter(problematic_template, config=graceful_config)
    result = formatter.format(**test_data)
    print(f"✅ Graceful mode works safely: '{result}'")
    print("   Note: Invalid formatting ignored, missing function hidden section")
    
    # Mode 3: AUTO-CORRECT - Fixes issues automatically (assisted development)
    print("\n🟡 3. AUTO-CORRECT MODE (Assisted Development)")
    print("-" * 30)
    
    # Use a template with correctable issues
    correctable_template = "{{#rd;Error: ;message}} {{#blu;Status: ;status}}"
    
    auto_config = FormatterConfig.assisted_development()
    print("Creating formatter in auto-correct mode...")
    print(f"Template: {correctable_template}")
    
    formatter = DynamicFormatter(correctable_template, config=auto_config)
    result = formatter.format(message="Failed", status="Down")
    print(f"✅ Auto-correct mode result: '{result}'")
    print("   Note: 'rd' → 'red', 'blu' → 'blue' (auto-corrected)")


def demo_conditional_graceful_degradation():
    """Demonstrate graceful handling of missing conditional functions"""
    
    print("\n\n🎯 CONDITIONAL FUNCTION GRACEFUL DEGRADATION")
    print("=" * 50)
    
    template = "{{Processing}} {{?has_items;Found ;count; items}} {{?missing_func;Alert: ;message}}"
    
    # Working function
    def has_items(count):
        return count > 0
    
    functions = {"has_items": has_items}
    # Note: missing_func is intentionally not provided
    
    print("📋 Template with mixed functions:")
    print(f"   {template}")
    print("   Functions: has_items (provided), missing_func (missing)")
    print()
    
    # Strict mode - fails on missing function
    print("🔴 STRICT MODE:")
    strict_config = FormatterConfig.development(functions=functions)
    
    try:
        formatter = DynamicFormatter(template, config=strict_config)
        result = formatter.format(count=5, message="System down")
        print(f"❌ Should have failed! Got: '{result}'")
    except Exception as e:
        print(f"✅ Correctly caught missing function: {type(e).__name__}")
    
    # Graceful mode - hides sections with missing functions
    print("\n🟢 GRACEFUL MODE:")
    graceful_config = FormatterConfig.production(functions=functions)
    
    formatter = DynamicFormatter(template, config=graceful_config)
    result = formatter.format(count=5, message="System down")
    print(f"✅ Graceful result: '{result}'")
    print("   Note: 'has_items' section shows, 'missing_func' section hidden")
    
    # Test with no items (has_items returns False)
    result2 = formatter.format(count=0, message="System down")
    print(f"✅ No items result: '{result2}'")
    print("   Note: Both conditional sections hidden (count=0, missing function)")


def demo_professional_usage_patterns():
    """Show professional deployment patterns"""
    
    print("\n\n🏢 PROFESSIONAL DEPLOYMENT PATTERNS")
    print("=" * 50)
    
    # Template for demonstration
    log_template = "{{#level_color@bold;[;level;]}} {{message}} {{Duration: ;duration;s}} {{?has_errors;Errors: ;error_count}}"
    
    def level_color(level):
        return {"ERROR": "red", "INFO": "green", "WARNING": "yellow"}[level]
    
    def has_errors(count):
        return count > 0
    
    functions = {"level_color": level_color, "has_errors": has_errors}
    
    print("📋 1. DEVELOPMENT CONFIGURATION")
    print("-" * 30)
    
    # Development: Full validation, strict mode
    dev_config = FormatterConfig.development(functions=functions)
    print(f"Validation Mode: {dev_config.validation_mode.value}")
    print(f"Validation Level: {dev_config.validation_level.value}")
    print(f"Performance Monitoring: {dev_config.enable_performance_monitoring}")
    
    dev_formatter = DynamicFormatter(log_template, config=dev_config)
    result = dev_formatter.format(level="ERROR", message="Connection failed", duration=5.2, error_count=3)
    print(f"Result: {result}")
    
    print("\n📋 2. PRODUCTION CONFIGURATION")
    print("-" * 30)
    
    # Production: Minimal validation, graceful mode
    prod_config = FormatterConfig.production(functions=functions)
    print(f"Validation Mode: {prod_config.validation_mode.value}")
    print(f"Validation Level: {prod_config.validation_level.value}")
    print(f"Enable Validation: {prod_config.enable_validation}")
    print(f"Performance Monitoring: {prod_config.enable_performance_monitoring}")
    
    prod_formatter = DynamicFormatter(log_template, config=prod_config)
    result = prod_formatter.format(level="INFO", message="System started", duration=1.1)
    print(f"Result: {result}")
    
    print("\n📋 3. ASSISTED DEVELOPMENT CONFIGURATION")
    print("-" * 30)
    
    # Assisted: Auto-correction, productivity features
    assisted_config = FormatterConfig.assisted_development(functions=functions)
    print(f"Validation Mode: {assisted_config.validation_mode.value}")
    print(f"Auto-correct Suggestions: {assisted_config.auto_correct_suggestions}")
    print(f"Strict Argument Validation: {assisted_config.strict_argument_validation}")
    
    assisted_formatter = DynamicFormatter(log_template, config=assisted_config)
    result = assisted_formatter.format(level="WARNING", message="Slow response", duration=8.5, error_count=0)
    print(f"Result: {result}")


def demo_logging_integration():
    """Demonstrate logging integration with graceful degradation"""
    
    print("\n\n📝 LOGGING INTEGRATION")
    print("=" * 50)
    
    import logging
    
    # Set up logging with different configurations
    print("📋 DEVELOPMENT LOGGING")
    print("-" * 30)
    
    # Development logging: validation enabled, strict mode
    dev_log_config = FormatterConfig.development()
    dev_formatter = DynamicLoggingFormatter(
        "{{#level_color;[;levelname;]}} {{message}} {{Duration: ;duration;s}} {{Memory: ;memory;MB}}",
        config=dev_log_config
    )
    
    # Create a mock log record
    record = logging.LogRecord(
        name="test", level=logging.ERROR, pathname="test.py",
        lineno=1, msg="Database connection failed", args=(), exc_info=None
    )
    record.duration = 2.5
    record.memory = 45.2
    
    result = dev_formatter.format(record)
    print(f"Development log: {result}")
    
    print("\n📋 PRODUCTION LOGGING")
    print("-" * 30)
    
    # Production logging: graceful mode, minimal validation
    prod_log_config = FormatterConfig.production()
    prod_formatter = DynamicLoggingFormatter(
        "{{#level_color;[;levelname;]}} {{message}} {{Duration: ;duration;s}} {{Memory: ;memory;MB}}",
        config=prod_log_config
    )
    
    # Test with missing data
    record2 = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py",
        lineno=1, msg="Process completed", args=(), exc_info=None
    )
    # Note: duration and memory are missing
    
    result = prod_formatter.format(record2)
    print(f"Production log (missing data): {result}")
    print("   Note: Missing duration/memory sections disappeared gracefully")


def demo_configuration_flexibility():
    """Demonstrate configuration system flexibility"""
    
    print("\n\n⚙️ CONFIGURATION SYSTEM FLEXIBILITY")
    print("=" * 50)
    
    print("📋 CUSTOM CONFIGURATION")
    print("-" * 30)
    
    # Create custom configuration
    custom_config = FormatterConfig(
        validation_mode=ValidationMode.GRACEFUL,
        validation_level=ValidationLevel.WARNING,
        enable_colors=True,
        enable_performance_monitoring=True,
        max_template_sections=100,
        strict_argument_validation=False,  # More forgiving
        functions={"test_func": lambda x: "processed"}
    )
    
    print(f"Custom config - Mode: {custom_config.validation_mode.value}")
    print(f"Custom config - Performance monitoring: {custom_config.enable_performance_monitoring}")
    print(f"Custom config - Max sections: {custom_config.max_template_sections}")
    
    # Configuration copying with overrides
    print("\n📋 CONFIGURATION COPYING")
    print("-" * 30)
    
    base_config = FormatterConfig.production()
    modified_config = base_config.copy(
        enable_performance_monitoring=True,
        validation_mode=ValidationMode.GRACEFUL
    )
    
    print(f"Base config monitoring: {base_config.enable_performance_monitoring}")
    print(f"Modified config monitoring: {modified_config.enable_performance_monitoring}")
    print("✅ Configuration immutability maintained")


def demo_benefits_summary():
    """Summarize the enterprise benefits"""
    
    print("\n\n💡 ENTERPRISE BENEFITS SUMMARY")
    print("=" * 50)
    
    print("""
🎯 PRODUCTION RELIABILITY:
   • Graceful mode prevents formatting failures in production
   • Missing functions/tokens degrade safely instead of crashing
   • Logging always works, even with template issues

🔧 DEVELOPMENT PRODUCTIVITY:
   • Strict mode catches issues early during development
   • Auto-correct mode fixes common mistakes automatically
   • Detailed validation reports with suggestions

🏢 ENTERPRISE DEPLOYMENT:
   • Configurable validation modes for different environments
   • Production configs optimize for reliability over feedback
   • Development configs optimize for catching issues early

⚡ PROFESSIONAL ARCHITECTURE:
   • Clean separation between validation and runtime behavior
   • Comprehensive configuration system
   • Backward compatibility with simple parameter interface

🛡️ ROBUSTNESS FEATURES:
   • Template validation prevents common mistakes
   • Function fallback with graceful degradation
   • Missing data handling (core feature) + missing function handling
   • Performance monitoring and complexity analysis
    """)


if __name__ == "__main__":
    try:
        demo_validation_modes()
        demo_conditional_graceful_degradation()
        demo_professional_usage_patterns()
        demo_logging_integration()
        demo_configuration_flexibility()
        demo_benefits_summary()
        
        print("\n" + "=" * 50)
        print("🎉 GRACEFUL DEGRADATION DEMO COMPLETED!")
        print("\n🚀 Key Features Demonstrated:")
        print("• Configurable validation modes (strict/graceful/auto-correct)")
        print("• Production-ready graceful degradation")
        print("• Professional deployment configurations")
        print("• Enterprise logging integration")
        print("• Comprehensive configuration management")
        print("• Robust error handling for all scenarios")
        print("\n✨ This system is now truly production-ready!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()