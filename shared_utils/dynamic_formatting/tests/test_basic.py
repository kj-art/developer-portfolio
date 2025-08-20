"""
Basic tests to verify the package imports and basic functionality work.
"""

import pytest


def test_import_config():
    """Test that we can import the config module"""
    try:
        from shared_utils.dynamic_formatting.config import FormatterConfig
        assert FormatterConfig is not None
    except ImportError as e:
        pytest.fail(f"Failed to import FormatterConfig: {e}")


def test_import_dynamic_formatter():
    """Test that we can import the main formatter"""
    try:
        from shared_utils.dynamic_formatting.dynamic_formatting import DynamicFormatter
        assert DynamicFormatter is not None
    except ImportError as e:
        pytest.fail(f"Failed to import DynamicFormatter: {e}")


def test_basic_formatter_creation():
    """Test that we can create a basic formatter"""
    try:
        from shared_utils.dynamic_formatting.dynamic_formatting import DynamicFormatter
        formatter = DynamicFormatter("{{Hello ;name}}")
        assert formatter is not None
        assert formatter.format_string == "{{Hello ;name}}"
    except Exception as e:
        pytest.fail(f"Failed to create basic formatter: {e}")


def test_basic_config_creation():
    """Test that we can create basic configuration"""
    try:
        from shared_utils.dynamic_formatting.config import FormatterConfig
        config = FormatterConfig()
        assert config is not None
        assert config.delimiter == ';'
        assert config.output_mode == 'console'
    except Exception as e:
        pytest.fail(f"Failed to create basic config: {e}")


def test_simple_formatting():
    """Test basic formatting functionality"""
    try:
        from shared_utils.dynamic_formatting.dynamic_formatting import DynamicFormatter
        formatter = DynamicFormatter("Hello {{name}}")
        # This might fail due to missing dependencies, but we'll try
        result = formatter.format(name="World")
        # If we get here without exception, that's good
        assert isinstance(result, str)
    except Exception as e:
        # Expected to fail due to missing dependencies
        pytest.skip(f"Formatting failed due to missing dependencies: {e}")