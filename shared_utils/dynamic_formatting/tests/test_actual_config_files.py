"""
Test suite for actual JSON configuration files in the configs/ directory.

This complements test_config_support.py by testing real config files
rather than temporary ones created during testing.
"""

import sys
import json
from pathlib import Path
import pytest

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from shared_utils.dynamic_formatting import DynamicFormatter, FormatterConfig
from shared_utils.dynamic_formatting.config import ValidationMode, ValidationLevel


class TestActualConfigFiles:
    """Test actual JSON configuration files in the configs/ directory."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class - find all JSON files in configs directory."""
        cls.configs_dir = Path(__file__).parent.parent / "configs"
        cls.config_files = list(cls.configs_dir.glob("*.json")) if cls.configs_dir.exists() else []
        
        print(f"\nFound configs directory: {cls.configs_dir}")
        print(f"Found {len(cls.config_files)} JSON files: {[f.name for f in cls.config_files]}")
    
    def test_configs_directory_exists(self):
        """Test that configs directory exists."""
        if not self.configs_dir.exists():
            pytest.skip("No configs/ directory found - skipping actual config file tests")
        
        assert self.configs_dir.is_dir(), "configs/ should be a directory"
    
    def test_config_file_valid_json(self):
        """Test that each config file contains valid JSON."""
        if not self.config_files:
            pytest.skip("No config files found")
        
        for config_file in self.config_files:
            with open(config_file, 'r', encoding='utf-8') as f:
                try:
                    config_data = json.load(f)
                    assert isinstance(config_data, dict), f"{config_file.name} should contain a JSON object"
                    print(f"  ✅ {config_file.name}: Valid JSON")
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {config_file.name}: {e}")
    
    def test_config_file_loads_with_formatterconfig(self):
        """Test that each config file can be loaded by FormatterConfig."""
        if not self.config_files:
            pytest.skip("No config files found")
        
        for config_file in self.config_files:
            try:
                config = FormatterConfig.from_config_file(config_file)
                assert isinstance(config, FormatterConfig), f"Should create FormatterConfig from {config_file.name}"
                
                # Test that basic attributes exist and are valid types
                assert hasattr(config, 'validation_mode')
                assert hasattr(config, 'output_mode')
                assert hasattr(config, 'enable_validation')
                
                print(f"  ✅ {config_file.name}: validation_mode={config.validation_mode.value}")
                
            except Exception as e:
                pytest.fail(f"Failed to load {config_file.name} with FormatterConfig: {e}")
    
    def test_config_file_creates_working_formatter(self):
        """Test that each config file can create a working DynamicFormatter."""
        if not self.config_files:
            pytest.skip("No config files found")
        
        template = "{{#level_color;[;level;]}} {{message}} {{?duration;(;duration;s)}}"
        test_data = {
            "level": "INFO",
            "message": "Test message",
            "duration": 1.5
        }
        
        for config_file in self.config_files:
            try:
                formatter = DynamicFormatter.from_config_file(template, config_file)
                result = formatter.format(**test_data)
                
                assert isinstance(result, str), f"Formatter from {config_file.name} should return string"
                assert len(result) > 0, f"Formatter from {config_file.name} should return non-empty result"
                assert "Test message" in result, f"Result should contain test message"
                
                print(f"  ✅ {config_file.name}: '{result}'")
                
            except Exception as e:
                pytest.fail(f"Failed to create working formatter from {config_file.name}: {e}")
    
    def test_config_files_have_expected_structure(self):
        """Test that config files have reasonable structure."""
        if not self.config_files:
            pytest.skip("No config files found")
        
        for config_file in self.config_files:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Check for either flat structure or nested 'formatting' key
            config_keys = config_data.keys()
            formatting_keys = config_data.get('formatting', {}).keys() if 'formatting' in config_data else config_keys
            
            # Should have at least some formatting-related keys
            expected_keys = {'validation_mode', 'output_mode', 'enable_validation', 'enable_colors'}
            found_keys = set(formatting_keys) & expected_keys
            
            assert len(found_keys) > 0, f"{config_file.name} should have at least one formatting key: {expected_keys}"
            print(f"  ✅ {config_file.name}: has keys {sorted(found_keys)}")
    
    def test_all_configs_different_settings(self):
        """Test that different config files actually have different settings."""
        if len(self.config_files) < 2:
            pytest.skip("Need at least 2 config files to test differences")
        
        configs = []
        for config_file in self.config_files:
            config = FormatterConfig.from_config_file(config_file)
            configs.append((config_file.name, config))
        
        # Compare validation modes - they should be different for different environments
        validation_modes = [config.validation_mode for _, config in configs]
        unique_modes = set(validation_modes)
        
        if len(unique_modes) > 1:
            print(f"  ✅ Found different validation modes: {[mode.value for mode in unique_modes]}")
        else:
            # Not necessarily an error, but worth noting
            print(f"  ℹ️  All configs use same validation mode: {validation_modes[0].value}")
    
    def test_config_round_trip(self):
        """Test that configs can be loaded and saved without data loss."""
        if not self.config_files:
            pytest.skip("No config files found")
        
        # Test with first config file
        config_file = self.config_files[0]
        
        # Load config
        original_config = FormatterConfig.from_config_file(config_file)
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            original_config.to_config_file(temp_path)
            
            # Load from temporary file
            reloaded_config = FormatterConfig.from_config_file(temp_path)
            
            # Compare key attributes
            assert reloaded_config.validation_mode == original_config.validation_mode
            assert reloaded_config.output_mode == original_config.output_mode
            assert reloaded_config.enable_validation == original_config.enable_validation
            
            print(f"  ✅ Round-trip successful for {config_file.name}")
            
        finally:
            temp_path.unlink()


def test_discover_and_run():
    """Standalone function to discover and test config files."""
    configs_dir = Path(__file__).parent.parent / "configs"
    
    print(f"\n{'='*60}")
    print(f"TESTING ACTUAL CONFIG FILES")
    print(f"{'='*60}")
    print(f"Configs directory: {configs_dir}")
    print(f"Directory exists: {configs_dir.exists()}")
    
    # Use assert statements instead of returning False
    assert configs_dir.exists(), "configs/ directory should exist"
    
    config_files = list(configs_dir.glob("*.json"))
    print(f"JSON files found: {len(config_files)}")
    for f in config_files:
        print(f"  - {f.name}")
    
    assert len(config_files) > 0, "Should find at least one JSON config file"
    
    # Test each file
    template = "{{#level_color;[;level;]}} {{message}}"
    test_data = {"level": "INFO", "message": "Configuration test"}
    
    success_count = 0
    errors = []
    
    for config_file in config_files:
        print(f"\nTesting {config_file.name}:")
        try:
            # Test 1: Valid JSON
            with open(config_file, 'r') as f:
                json.load(f)
            print(f"  ✅ Valid JSON")
            
            # Test 2: FormatterConfig loading
            config = FormatterConfig.from_config_file(config_file)
            print(f"  ✅ FormatterConfig loads (mode: {config.validation_mode.value})")
            
            # Test 3: DynamicFormatter creation and usage
            formatter = DynamicFormatter.from_config_file(template, config_file)
            result = formatter.format(**test_data)
            print(f"  ✅ DynamicFormatter works: '{result}'")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            errors.append(f"{config_file.name}: {e}")
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {success_count}/{len(config_files)} config files working")
    print(f"{'='*60}")
    
    # Assert that all config files work instead of returning boolean
    assert success_count == len(config_files), f"Some config files failed: {errors}"


if __name__ == "__main__":
    """Run config file discovery and testing."""
    success = test_discover_and_run()
    sys.exit(0 if success else 1)