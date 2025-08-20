"""
Configuration File Examples for Dynamic Formatting Package

Demonstrates professional deployment patterns using JSON configuration files
for different environments and use cases.
"""

import os
from pathlib import Path
from shared_utils.dynamic_formatting import DynamicFormatter, FormatterConfig


def example_config_file_usage():
    """Demonstrate loading formatter from configuration files"""
    
    print("=== Configuration File Usage Examples ===\n")
    
    # Sample template for all examples
    template = "{{#red;[ERROR];}} {{#yellow;Code: ;code}} {{Message: ;message}}"
    sample_data = {"code": 500, "message": "Internal server error"}
    
    # Example 1: Load from development config
    print("1. Development Configuration (strict validation):")
    try:
        dev_formatter = DynamicFormatter.from_config_file(
            template, 
            "configs/development.json"
        )
        result = dev_formatter.format(**sample_data)
        print(f"   Result: {result}")
        print(f"   Mode: {dev_formatter.config.validation_mode.value}")
    except FileNotFoundError:
        print("   Config file not found - using fallback")
        dev_formatter = DynamicFormatter(template, config=FormatterConfig.development())
        result = dev_formatter.format(**sample_data)
        print(f"   Result: {result}")
    
    print()
    
    # Example 2: Load from production config
    print("2. Production Configuration (graceful degradation):")
    try:
        prod_formatter = DynamicFormatter.from_config_file(
            template,
            "configs/production.json"  
        )
        result = prod_formatter.format(**sample_data)
        print(f"   Result: {result}")
        print(f"   Validation enabled: {prod_formatter.config.enable_validation}")
    except FileNotFoundError:
        print("   Config file not found - using fallback")
        prod_formatter = DynamicFormatter(template, config=FormatterConfig.production())
        result = prod_formatter.format(**sample_data)
        print(f"   Result: {result}")
    
    print()
    
    # Example 3: File output configuration (no colors)
    print("3. File Output Configuration (no ANSI colors):")
    try:
        file_formatter = DynamicFormatter.from_config_file(
            template,
            "configs/file_output.json"
        )
        result = file_formatter.format(**sample_data)
        print(f"   Result: {result}")
        print(f"   Output mode: {file_formatter.config.output_mode}")
    except FileNotFoundError:
        print("   Config file not found - using fallback")
        file_config = FormatterConfig(output_mode='file', enable_colors=False)
        file_formatter = DynamicFormatter(template, config=file_config)
        result = file_formatter.format(**sample_data)
        print(f"   Result: {result}")


def example_dictionary_config():
    """Demonstrate configuration from dictionaries"""
    
    print("\n=== Dictionary Configuration Examples ===\n")
    
    template = "{{#green;✓ SUCCESS:}} {{Task: ;task}} {{Duration: ;duration}}ms"
    sample_data = {"task": "Data processing", "duration": 1250}
    
    # Example 1: Simple dictionary config
    print("1. Simple Dictionary Configuration:")
    config_dict = {
        "validation_mode": "graceful",
        "output_mode": "console", 
        "enable_colors": True,
        "enable_validation": False
    }
    
    formatter = DynamicFormatter.from_config(template, config_dict)
    result = formatter.format(**sample_data)
    print(f"   Result: {result}")
    print(f"   Config source: Dictionary")
    
    print()
    
    # Example 2: Comprehensive dictionary config
    print("2. Comprehensive Dictionary Configuration:")
    advanced_config = {
        "validation_mode": "auto_correct",
        "validation_level": "warning",
        "output_mode": "console",
        "enable_colors": True,
        "enable_validation": True,
        "enable_performance_monitoring": True,
        "max_template_sections": 200,
        "cache_parsed_templates": True
    }
    
    formatter = DynamicFormatter.from_config(template, advanced_config)
    result = formatter.format(**sample_data)
    print(f"   Result: {result}")
    print(f"   Validation mode: {formatter.config.validation_mode.value}")
    print(f"   Performance monitoring: {formatter.config.enable_performance_monitoring}")


def example_environment_config():
    """Demonstrate configuration from environment variables"""
    
    print("\n=== Environment Variable Configuration ===\n")
    
    template = "{{#blue;[INFO]:}} {{Service: ;service}} {{Status: ;status}}"
    sample_data = {"service": "API Gateway", "status": "Running"}
    
    # Set some example environment variables
    os.environ['FORMATTER_VALIDATION_MODE'] = 'graceful'
    os.environ['FORMATTER_OUTPUT_MODE'] = 'console'
    os.environ['FORMATTER_ENABLE_COLORS'] = 'true'
    os.environ['FORMATTER_ENABLE_VALIDATION'] = 'false'
    
    print("1. Environment Variable Configuration:")
    print("   Set environment variables:")
    print("   FORMATTER_VALIDATION_MODE=graceful")
    print("   FORMATTER_OUTPUT_MODE=console") 
    print("   FORMATTER_ENABLE_COLORS=true")
    print("   FORMATTER_ENABLE_VALIDATION=false")
    
    formatter = DynamicFormatter.from_environment(template)
    result = formatter.format(**sample_data)
    print(f"   Result: {result}")
    print(f"   Loaded from environment: {formatter.config.validation_mode.value}")
    
    # Clean up environment variables
    for key in ['FORMATTER_VALIDATION_MODE', 'FORMATTER_OUTPUT_MODE', 
                'FORMATTER_ENABLE_COLORS', 'FORMATTER_ENABLE_VALIDATION']:
        if key in os.environ:
            del os.environ[key]


def example_config_creation_and_saving():
    """Demonstrate creating and saving configuration files"""
    
    print("\n=== Configuration Creation and Saving ===\n")
    
    # Create custom configuration
    print("1. Creating Custom Configuration:")
    custom_config = FormatterConfig(
        validation_mode="graceful",
        output_mode="console",
        enable_colors=True,
        enable_validation=True,
        max_template_sections=150,
        auto_correct_suggestions=True
    )
    
    print(f"   Validation mode: {custom_config.validation_mode.value}")
    print(f"   Max template sections: {custom_config.max_template_sections}")
    
    # Save to file
    print("\n2. Saving Configuration to File:")
    try:
        # Create configs directory if it doesn't exist
        config_dir = Path("configs")
        config_dir.mkdir(exist_ok=True)
        
        custom_config.to_config_file("configs/custom.json")
        print("   Saved configuration to 'configs/custom.json'")
        
        # Load it back
        loaded_config = FormatterConfig.from_config_file("configs/custom.json")
        print(f"   Loaded back - validation mode: {loaded_config.validation_mode.value}")
        
    except Exception as e:
        print(f"   Error saving config: {e}")
    
    # Convert to dictionary
    print("\n3. Configuration as Dictionary:")
    config_dict = custom_config.to_dict()
    print("   Configuration dictionary:")
    for key, value in config_dict.items():
        print(f"     {key}: {value}")


def example_deployment_scenarios():
    """Demonstrate real-world deployment scenarios"""
    
    print("\n=== Real-World Deployment Scenarios ===\n")
    
    # Logging template for different environments
    log_template = "{{#timestamp_color;[;timestamp}}{{#timestamp_color;];}} {{#level_color;;level}} {{#cyan;;service}} {{Message: ;message}}"
    
    log_data = {
        "timestamp": "2024-01-15 14:30:25",
        "level": "ERROR", 
        "service": "payment-service",
        "message": "Payment processing failed"
    }
    
    print("1. Development Environment (strict validation, full feedback):")
    dev_config = FormatterConfig.development()
    dev_formatter = DynamicFormatter(log_template, config=dev_config)
    
    # Simulate missing field to show validation
    try:
        result = dev_formatter.format(
            timestamp="2024-01-15 14:30:25",
            level="ERROR",
            service="payment-service"
            # message intentionally missing to demonstrate validation
        )
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Validation caught issue: {type(e).__name__}")
        # Graceful fallback
        result = dev_formatter.format(**log_data)
        print(f"   With full data: {result}")
    
    print("\n2. Production Environment (graceful degradation, minimal validation):")
    prod_config = FormatterConfig.production()
    prod_formatter = DynamicFormatter(log_template, config=prod_config)
    
    # Missing fields handled gracefully
    result = prod_formatter.format(
        timestamp="2024-01-15 14:30:25",
        level="ERROR", 
        service="payment-service"
        # message missing but handled gracefully
    )
    print(f"   Result with missing field: {result}")
    
    print("\n3. File Logging (no colors, suitable for log files):")
    file_config = FormatterConfig(
        validation_mode="graceful",
        output_mode="file",
        enable_colors=False,
        enable_validation=False
    )
    file_formatter = DynamicFormatter(log_template, config=file_config)
    result = file_formatter.format(**log_data)
    print(f"   File output: {result}")
    
    print("\n4. Configuration Comparison:")
    print(f"   Development - validation: {dev_config.enable_validation}, colors: {dev_config.enable_colors}")
    print(f"   Production  - validation: {prod_config.enable_validation}, colors: {prod_config.enable_colors}")
    print(f"   File output - validation: {file_config.enable_validation}, colors: {file_config.enable_colors}")


def example_multi_environment_setup():
    """Demonstrate automatic environment-based configuration loading"""
    
    print("\n=== Multi-Environment Setup ===\n")
    
    template = "{{#level_color;[;level;]}} {{#bold;;service}} {{message}} {{Duration: ;duration;ms}}"
    
    def level_color(level):
        """Function that determines color based on log level"""
        return {"ERROR": "red", "WARNING": "yellow", "INFO": "green", "DEBUG": "blue"}.get(level, "white")
    
    # Simulate different environments
    environments = ["development", "production", "file_output"]
    
    sample_data = {
        "level": "ERROR",
        "service": "auth-service", 
        "message": "Authentication failed",
        "duration": 1250
    }
    
    for env in environments:
        print(f"{env.upper()} Environment:")
        
        try:
            # Load environment-specific config
            config_path = f"configs/{env}.json"
            
            # Add our custom function to the config
            config = FormatterConfig.from_config_file(config_path)
            config.functions["level_color"] = level_color
            
            formatter = DynamicFormatter(template, config=config)
            result = formatter.format(**sample_data)
            
            print(f"  Config: {config.validation_mode.value} mode, colors: {config.enable_colors}")
            print(f"  Result: {result}")
            
        except FileNotFoundError:
            print(f"  Config file not found: {config_path}")
            
        print()


def example_runtime_config_switching():
    """Demonstrate switching configurations at runtime"""
    
    print("\n=== Runtime Configuration Switching ===\n")
    
    template = "{{#status_color;Status: ;status}} {{Records: ;count}} {{Errors: ;errors}}"
    
    def status_color(status):
        return "green" if status == "SUCCESS" else "red"
    
    # Base data
    data = {"status": "SUCCESS", "count": 1500, "errors": 0}
    
    # Create different configurations
    configs = {
        "development": FormatterConfig.development(functions={"status_color": status_color}),
        "production": FormatterConfig.production(functions={"status_color": status_color}),
        "file_output": FormatterConfig(
            validation_mode="graceful",
            output_mode="file", 
            enable_colors=False,
            functions={"status_color": status_color}
        )
    }
    
    print("Same template, different configurations:")
    print(f"Template: {template}")
    print(f"Data: {data}")
    print()
    
    for config_name, config in configs.items():
        formatter = DynamicFormatter(template, config=config)
        result = formatter.format(**data)
        
        print(f"{config_name.upper()}: {result}")
        print(f"  - Mode: {config.validation_mode.value}")
        print(f"  - Output: {config.output_mode}")
        print(f"  - Colors: {config.enable_colors}")
        print()


def example_config_inheritance():
    """Demonstrate configuration inheritance and customization"""
    
    print("\n=== Configuration Inheritance ===\n")
    
    # Start with production base
    base_config = FormatterConfig.production()
    print("Base Production Config:")
    print(f"  Validation: {base_config.enable_validation}")
    print(f"  Performance monitoring: {base_config.enable_performance_monitoring}")
    print(f"  Max sections: {base_config.max_template_sections}")
    
    # Create customized version
    custom_config = base_config.copy(
        enable_performance_monitoring=True,  # Override: enable monitoring
        max_template_sections=200,           # Override: increase limit
        validation_level="warning"           # Override: change validation level
    )
    
    print("\nCustomized Config (based on production):")
    print(f"  Validation: {custom_config.enable_validation}")  # Inherited
    print(f"  Performance monitoring: {custom_config.enable_performance_monitoring}")  # Overridden
    print(f"  Max sections: {custom_config.max_template_sections}")  # Overridden
    print(f"  Validation level: {custom_config.validation_level.value}")  # Overridden
    print(f"  Validation mode: {custom_config.validation_mode.value}")  # Inherited
    
    # Show that original config is unchanged
    print("\nOriginal config unchanged:")
    print(f"  Performance monitoring: {base_config.enable_performance_monitoring}")
    print(f"  Max sections: {base_config.max_template_sections}")


def main():
    """Run all configuration examples"""
    
    print("Dynamic Formatting Package - Configuration Examples")
    print("=" * 60)
    
    try:
        example_config_file_usage()
        example_dictionary_config()
        example_environment_config()
        example_config_creation_and_saving()
        example_deployment_scenarios()
        example_multi_environment_setup()
        example_runtime_config_switching()
        example_config_inheritance()
        
        print("\n" + "=" * 60)
        print("Configuration examples completed successfully!")
        print("\nKey Benefits:")
        print("• Professional deployment patterns with JSON configs")
        print("• Environment-specific validation modes")
        print("• Flexible configuration sources (file, dict, env vars)")
        print("• Enterprise-ready configuration management")
        print("• Runtime configuration switching")
        print("• Configuration inheritance and customization")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()