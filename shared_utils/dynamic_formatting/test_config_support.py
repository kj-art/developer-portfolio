"""
Test suite for configuration file support in dynamic formatting package.

Tests JSON config loading, environment variable configuration, and
various deployment scenario configurations.
"""

import os
import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config import FormatterConfig, ValidationMode, ValidationLevel
    from dynamic_formatting import DynamicFormatter
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the dynamic_formatting directory")
    sys.exit(1)


class TestFormatterConfigFileSupport:
    """Test configuration file loading and saving functionality"""
    
    def test_from_config_file_basic(self):
        """Test loading configuration from JSON file"""
        config_data = {
            "formatting": {
                "validation_mode": "graceful",
                "output_mode": "console",
                "enable_colors": True,
                "enable_validation": False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            config = FormatterConfig.from_config_file(config_path)
            
            assert config.validation_mode == ValidationMode.GRACEFUL
            assert config.output_mode == "console"
            assert config.enable_colors == True
            assert config.enable_validation == False
            
        finally:
            os.unlink(config_path)
    
    def test_from_config_file_flat_structure(self):
        """Test loading config without nested 'formatting' key"""
        config_data = {
            "validation_mode": "strict",
            "validation_level": "info",
            "max_template_sections": 200
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            config = FormatterConfig.from_config_file(config_path)
            
            assert config.validation_mode == ValidationMode.STRICT
            assert config.validation_level == ValidationLevel.INFO
            assert config.max_template_sections == 200
            
        finally:
            os.unlink(config_path)
    
    def test_from_config_file_not_found(self):
        """Test FileNotFoundError for missing config file"""
        try:
            FormatterConfig.from_config_file("nonexistent_config.json")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected
    
    def test_from_config_file_invalid_json(self):
        """Test JSONDecodeError for invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json syntax}')  # Invalid JSON
            config_path = f.name
        
        try:
            try:
                FormatterConfig.from_config_file(config_path)
                assert False, "Should have raised JSONDecodeError"
            except json.JSONDecodeError:
                pass  # Expected
        finally:
            os.unlink(config_path)
    
    def test_to_config_file_nested(self):
        """Test saving configuration to file with nested structure"""
        config = FormatterConfig(
            validation_mode=ValidationMode.GRACEFUL,
            output_mode="file",
            enable_colors=False,
            max_template_sections=150
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            config.to_config_file(config_path, nested=True)
            
            # Load and verify
            with open(config_path, 'r') as f:
                saved_data = json.load(f)
            
            assert 'formatting' in saved_data
            formatting_config = saved_data['formatting']
            assert formatting_config['validation_mode'] == 'graceful'
            assert formatting_config['output_mode'] == 'file'
            assert formatting_config['enable_colors'] == False
            assert formatting_config['max_template_sections'] == 150
            
        finally:
            os.unlink(config_path)
    
    def test_to_config_file_flat(self):
        """Test saving configuration to file with flat structure"""
        config = FormatterConfig(
            validation_mode=ValidationMode.AUTO_CORRECT,
            enable_validation=True
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            config.to_config_file(config_path, nested=False)
            
            # Load and verify
            with open(config_path, 'r') as f:
                saved_data = json.load(f)
            
            # Should be flat, not nested
            assert 'formatting' not in saved_data
            assert saved_data['validation_mode'] == 'auto_correct'
            assert saved_data['enable_validation'] == True
            
        finally:
            os.unlink(config_path)


class TestFormatterConfigEnvironment:
    """Test environment variable configuration loading"""
    
    def test_from_environment_basic(self):
        """Test loading configuration from environment variables"""
        env_vars = {
            'FORMATTER_VALIDATION_MODE': 'graceful',
            'FORMATTER_OUTPUT_MODE': 'file',
            'FORMATTER_ENABLE_COLORS': 'false',
            'FORMATTER_ENABLE_VALIDATION': 'true',
            'FORMATTER_MAX_TEMPLATE_SECTIONS': '300'
        }
        
        with patch.dict(os.environ, env_vars):
            config = FormatterConfig.from_environment()
            
            assert config.validation_mode == ValidationMode.GRACEFUL
            assert config.output_mode == 'file'
            assert config.enable_colors == False
            assert config.enable_validation == True
            assert config.max_template_sections == 300
    
    def test_from_environment_custom_prefix(self):
        """Test loading with custom environment variable prefix"""
        env_vars = {
            'MYAPP_VALIDATION_MODE': 'strict',
            'MYAPP_OUTPUT_MODE': 'console'
        }
        
        with patch.dict(os.environ, env_vars):
            config = FormatterConfig.from_environment(prefix='MYAPP_')
            
            assert config.validation_mode == ValidationMode.STRICT
            assert config.output_mode == 'console'
    
    def test_from_environment_empty(self):
        """Test environment loading with no relevant environment variables"""
        # Clear any existing formatter env vars
        env_to_clear = {k: None for k in os.environ.keys() if k.startswith('FORMATTER_')}
        
        with patch.dict(os.environ, env_to_clear, clear=False):
            config = FormatterConfig.from_environment()
            
            # Should return default configuration
            assert config.validation_mode == ValidationMode.GRACEFUL
            assert config.output_mode == 'console'


class TestDynamicFormatterConfigMethods:
    """Test DynamicFormatter configuration factory methods"""
    
    def test_from_config_file(self):
        """Test DynamicFormatter.from_config_file()"""
        config_data = {
            "formatting": {
                "validation_mode": "graceful",
                "output_mode": "console",
                "enable_validation": False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            template = "{{#red;Error: ;message}}"
            formatter = DynamicFormatter.from_config_file(template, config_path)
            
            assert formatter.format_string == template
            assert formatter.config.validation_mode == ValidationMode.GRACEFUL
            assert formatter.config.enable_validation == False
            
        finally:
            os.unlink(config_path)
    
    def test_from_config_dict(self):
        """Test DynamicFormatter.from_config() with dictionary"""
        template = "{{Status: ;status}}"
        config_dict = {
            "validation_mode": "auto_correct",
            "output_mode": "file",
            "enable_colors": False
        }
        
        formatter = DynamicFormatter.from_config(template, config_dict)
        
        assert formatter.format_string == template
        assert formatter.config.validation_mode == ValidationMode.AUTO_CORRECT
        assert formatter.config.output_mode == "file"
        assert formatter.config.enable_colors == False
    
    def test_from_config_formatter_config(self):
        """Test DynamicFormatter.from_config() with FormatterConfig instance"""
        template = "{{Message: ;msg}}"
        config = FormatterConfig.production()
        
        formatter = DynamicFormatter.from_config(template, config)
        
        assert formatter.format_string == template
        assert formatter.config.validation_mode == ValidationMode.GRACEFUL
        assert formatter.config.enable_validation == False  # Production default
    
    def test_from_config_file_path(self):
        """Test DynamicFormatter.from_config() with file path"""
        config_data = {"validation_mode": "strict"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            template = "{{Data: ;data}}"
            formatter = DynamicFormatter.from_config(template, config_path)
            
            assert formatter.config.validation_mode == ValidationMode.STRICT
            
        finally:
            os.unlink(config_path)
    
    def test_from_config_invalid_type(self):
        """Test DynamicFormatter.from_config() with invalid config type"""
        template = "{{Test: ;test}}"
        
        try:
            DynamicFormatter.from_config(template, 12345)  # Invalid type
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unsupported config type" in str(e)
    
    def test_from_environment(self):
        """Test DynamicFormatter.from_environment()"""
        env_vars = {
            'FORMATTER_VALIDATION_MODE': 'graceful',
            'FORMATTER_OUTPUT_MODE': 'console'
        }
        
        with patch.dict(os.environ, env_vars):
            template = "{{Level: ;level}}"
            formatter = DynamicFormatter.from_environment(template)
            
            assert formatter.config.validation_mode == ValidationMode.GRACEFUL
            assert formatter.config.output_mode == 'console'


class TestConfigurationIntegration:
    """Test end-to-end configuration functionality"""
    
    def test_deployment_scenario_development(self):
        """Test development deployment scenario"""
        config = FormatterConfig.development()
        template = "{{#red;Error: ;message}} {{Code: ;code}}"
        formatter = DynamicFormatter(template, config=config)
        
        # Should have strict validation and full monitoring
        assert config.validation_mode == ValidationMode.STRICT
        assert config.enable_validation == True
        assert config.enable_performance_monitoring == True
        assert config.auto_correct_suggestions == True
        
        # Test formatting works
        result = formatter.format(message="Test error", code=500)
        assert "Error: Test error" in result
        assert "Code: 500" in result
    
    def test_deployment_scenario_production(self):
        """Test production deployment scenario"""
        config = FormatterConfig.production()
        template = "{{#green;Success: ;message}} {{Time: ;timestamp}}"
        formatter = DynamicFormatter(template, config=config)
        
        # Should have graceful handling and minimal validation
        assert config.validation_mode == ValidationMode.GRACEFUL
        assert config.enable_validation == False
        assert config.enable_performance_monitoring == False
        
        # Test graceful handling of missing fields
        result = formatter.format(message="Operation completed")
        # Should handle missing timestamp gracefully
        assert "Success: Operation completed" in result
    
    def test_deployment_scenario_file_output(self):
        """Test file output deployment scenario"""
        config = FormatterConfig(
            validation_mode=ValidationMode.GRACEFUL,
            output_mode="file",
            enable_colors=False,
            enable_validation=False
        )
        template = "{{#red;Alert: ;message}}"
        formatter = DynamicFormatter(template, config=config)
        
        result = formatter.format(message="System warning")
        
        # Should not contain ANSI color codes in file mode
        assert '\033[' not in result  # No ANSI escape sequences
        assert "Alert: System warning" in result
    
    def test_configuration_roundtrip(self):
        """Test saving and loading configuration maintains all settings"""
        original_config = FormatterConfig(
            validation_mode=ValidationMode.AUTO_CORRECT,
            validation_level=ValidationLevel.WARNING,
            output_mode="console",
            enable_colors=True,
            enable_validation=True,
            max_template_sections=250,
            cache_parsed_templates=False
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            # Save configuration
            original_config.to_config_file(config_path)
            
            # Load configuration back
            loaded_config = FormatterConfig.from_config_file(config_path)
            
            # Verify all settings match
            assert loaded_config.validation_mode == original_config.validation_mode
            assert loaded_config.validation_level == original_config.validation_level
            assert loaded_config.output_mode == original_config.output_mode
            assert loaded_config.enable_colors == original_config.enable_colors
            assert loaded_config.enable_validation == original_config.enable_validation
            assert loaded_config.max_template_sections == original_config.max_template_sections
            assert loaded_config.cache_parsed_templates == original_config.cache_parsed_templates
            
        finally:
            os.unlink(config_path)


def test_configuration_examples():
    """Test that configuration examples run without errors"""
    # This would import and run the examples to ensure they work
    try:
        import examples_config
        # Test that examples can be imported and basic functionality works
        assert hasattr(examples_config, 'example_config_file_usage')
        assert hasattr(examples_config, 'example_dictionary_config')
        assert hasattr(examples_config, 'example_environment_config')
        
        print("Configuration examples import successfully")
        
    except ImportError:
        # Examples file may not exist yet in testing environment
        print("Configuration examples not available for testing")


def run_tests():
    """Simple test runner for development"""
    test_classes = [
        TestFormatterConfigFileSupport,
        TestFormatterConfigEnvironment, 
        TestDynamicFormatterConfigMethods,
        TestConfigurationIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\nRunning {test_class.__name__}:")
        instance = test_class()
        
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                total_tests += 1
                try:
                    method = getattr(instance, method_name)
                    method()
                    print(f"  ✓ {method_name}")
                    passed_tests += 1
                except Exception as e:
                    print(f"  ✗ {method_name}: {e}")
                    import traceback
                    traceback.print_exc()
    
    # Run individual test
    test_configuration_examples()
    
    print(f"\nTest Results: {passed_tests}/{total_tests} passed")
    
    if passed_tests == total_tests:
        print("All tests passed! ✓")
        return True
    else:
        print("Some tests failed! ✗")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)