"""
Dynamic Formatting Examples Package

Collection of comprehensive examples demonstrating all features
of the dynamic formatting system including basic usage, performance
monitoring, configuration management, and validation scenarios.

Available Examples:
- basic_examples: Core functionality demonstrations
- config_examples: Configuration file usage patterns  
- performance_examples: Performance monitoring scenarios
- validation_examples: Template validation and deployment modes

Usage:
    from shared_utils.dynamic_formatting.examples import basic_examples
    basic_examples.run_all_examples()
    
    # Or run specific example categories
    from shared_utils.dynamic_formatting.examples import performance_examples
    performance_examples.production_monitoring_example()
"""

# Import all example modules for easy access
from . import basic_examples
from . import config_examples
from . import performance_examples
from . import validation_examples

__all__ = [
    'basic_examples',
    'config_examples', 
    'performance_examples',
    'validation_examples'
]

def run_all_examples():
    """Run all example demonstrations."""
    print("Dynamic Formatting - Comprehensive Examples")
    print("=" * 50)
    
    print("\n🔧 Basic Examples:")
    try:
        basic_examples.run_all_examples()
    except Exception as e:
        print(f"Error running basic examples: {e}")
    
    print("\n⚙️ Configuration Examples:")
    try:
        config_examples.run_all_examples()
    except Exception as e:
        print(f"Error running config examples: {e}")
    
    print("\n📊 Performance Examples:")
    try:
        performance_examples.run_all_examples()
    except Exception as e:
        print(f"Error running performance examples: {e}")
    
    print("\n✅ Validation Examples:")
    try:
        validation_examples.run_all_examples()
    except Exception as e:
        print(f"Error running validation examples: {e}")
    
    print("\n🎉 All examples completed!")

if __name__ == "__main__":
    run_all_examples()