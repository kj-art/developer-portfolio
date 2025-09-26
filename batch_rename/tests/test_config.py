"""
Unit tests for configuration classes and validation.
"""

import pytest
from pathlib import Path

from core.config import RenameConfig, RenameResult


class TestRenameConfigCreation:
    """Test RenameConfig creation and validation."""
    
    def test_minimal_valid_config(self, temp_dir):
        """Test creation with minimal valid configuration."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'field'], 'keyword': {}}
        )
        
        assert config.input_folder == temp_dir
        assert config.extractor == "split"
        assert config.extractor_args == {'positional': ['_', 'field'], 'keyword': {}}
        assert config.converters == []
        assert config.filters == []
        assert config.template is None
    
    def test_config_with_string_path(self, temp_dir):
        """Test configuration with string path."""
        config = RenameConfig(
            input_folder=str(temp_dir),
            extractor="split",
            extractor_args={'positional': ['_', 'field'], 'keyword': {}}
        )
        
        assert config.input_folder == Path(str(temp_dir))
        assert isinstance(config.input_folder, Path)
    
    def test_full_config(self, temp_dir):
        """Test creation with full configuration."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'dept', 'type'], 'keyword': {}},
            converters=[
                {
                    'name': 'case',
                    'positional': ['dept', 'upper'],
                    'keyword': {}
                }
            ],
            filters=[
                {
                    'name': 'file_type',
                    'positional': ['pdf'],
                    'keyword': {},
                    'inverted': False
                }
            ],
            template={
                'name': 'stringsmith',
                'positional': ['{dept}_{type}'],
                'keyword': {}
            }
        )
        
        assert len(config.converters) == 1
        assert len(config.filters) == 1
        assert config.template is not None
        assert config.template['name'] == 'stringsmith'


class TestRenameConfigValidation:
    """Test RenameConfig validation logic."""
    
    def test_missing_input_folder(self):
        """Test validation fails when input_folder is missing."""
        with pytest.raises(ValueError, match="input_folder is required"):
            RenameConfig(
                input_folder=None,
                extractor="split"
            )
    
    def test_missing_extractor_and_extract_and_convert(self, temp_dir):
        """Test validation fails when both extractor and extract_and_convert are missing."""
        with pytest.raises(ValueError, match="Must specify either extractor or extract_and_convert"):
            RenameConfig(
                input_folder=temp_dir
            )
    
    def test_both_extractor_and_extract_and_convert(self, temp_dir):
        """Test validation fails when both are specified."""
        with pytest.raises(ValueError, match="Cannot specify both extractor and extract_and_convert"):
            RenameConfig(
                input_folder=temp_dir,
                extractor="split",
                extract_and_convert="some_function"
            )
    
    def test_extractor_without_converter_or_template(self, temp_dir):
        """Test validation for extractor without converter or template."""
        # Non-split extractor should require converter or template
        with pytest.raises(ValueError, match="must provide at least one converter or template"):
            RenameConfig(
                input_folder=temp_dir,
                extractor="regex",
                extractor_args={'positional': [r'(?P<field>\w+)'], 'keyword': {}}
            )
    
    def test_split_extractor_exception(self, temp_dir):
        """Test that split extractor doesn't require converter or template."""
        # Split extractor should work without converter/template
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'field'], 'keyword': {}}
        )
        
        assert config.extractor == "split"
    
    def test_invalid_template_name(self, temp_dir):
        """Test validation of invalid template name."""
        with pytest.raises(ValueError, match="Invalid template"):
            RenameConfig(
                input_folder=temp_dir,
                extractor="split",
                extractor_args={'positional': ['_', 'field'], 'keyword': {}},
                template={
                    'name': 'invalid_template_name',
                    'positional': [],
                    'keyword': {}
                }
            )
    
    def test_valid_builtin_template(self, temp_dir):
        """Test validation accepts valid built-in templates."""
        valid_templates = ['stringsmith', 'join', 'template']
        
        for template_name in valid_templates:
            config = RenameConfig(
                input_folder=temp_dir,
                extractor="split",
                extractor_args={'positional': ['_', 'field'], 'keyword': {}},
                template={
                    'name': template_name,
                    'positional': [],
                    'keyword': {}
                }
            )
            assert config.template['name'] == template_name
    
    def test_custom_template_file(self, temp_dir):
        """Test validation accepts custom .py template files."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'field'], 'keyword': {}},
            template={
                'name': 'custom_template.py',
                'positional': ['function_name'],
                'keyword': {}
            }
        )
        
        assert config.template['name'] == 'custom_template.py'


class TestRenameConfigDefaults:
    """Test default value handling in RenameConfig."""
    
    def test_default_extractor_args(self, temp_dir):
        """Test default extractor_args."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split"
        )
        
        assert config.extractor_args == {}
    
    def test_default_converters(self, temp_dir):
        """Test default converters list."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'field'], 'keyword': {}}
        )
        
        assert config.converters == []
        assert isinstance(config.converters, list)
    
    def test_default_filters(self, temp_dir):
        """Test default filters list."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'field'], 'keyword': {}}
        )
        
        assert config.filters == []
        assert isinstance(config.filters, list)
    
    def test_none_values_converted_to_defaults(self, temp_dir):
        """Test that None values are converted to appropriate defaults."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args=None,
            converters=None,
            filters=None
        )
        
        assert config.extractor_args == {}
        assert config.converters == []
        assert config.filters == []


class TestRenameResultCreation:
    """Test RenameResult creation and properties."""
    
    def test_default_result(self):
        """Test RenameResult with default values."""
        result = RenameResult()
        
        assert result.files_analyzed == 0
        assert result.files_to_rename == 0
        assert result.files_filtered_out == 0
        assert result.files_renamed == 0
        assert result.errors == 0
        assert result.collisions == 0
        assert result.existing_file_collisions == []
        assert result.internal_collisions == []
        assert result.processing_time == 0.0
        assert result.preview_data == []
        assert result.error_details == []
    
    def test_result_with_values(self):
        """Test RenameResult with specific values."""
        preview_data = [
            {'original_name': 'file1.pdf', 'new_name': 'new1.pdf'},
            {'original_name': 'file2.pdf', 'new_name': 'new2.pdf'}
        ]
        
        error_details = [
            {'file': 'error_file.pdf', 'error': 'Permission denied'}
        ]
        
        result = RenameResult(
            files_analyzed=10,
            files_to_rename=8,
            files_filtered_out=2,
            files_renamed=7,
            errors=1,
            collisions=1,
            processing_time=1.5,
            preview_data=preview_data,
            error_details=error_details
        )
        
        assert result.files_analyzed == 10
        assert result.files_to_rename == 8
        assert result.files_filtered_out == 2
        assert result.files_renamed == 7
        assert result.errors == 1
        assert result.collisions == 1
        assert result.processing_time == 1.5
        assert len(result.preview_data) == 2
        assert len(result.error_details) == 1
    
    def test_collision_data_structure(self):
        """Test collision data structure."""
        existing_collisions = [
            {'file': 'source.pdf', 'target': 'existing.pdf', 'type': 'existing'}
        ]
        
        internal_collisions = [
            {'files': ['file1.pdf', 'file2.pdf'], 'target': 'same_name.pdf', 'type': 'internal'}
        ]
        
        result = RenameResult(
            existing_file_collisions=existing_collisions,
            internal_collisions=internal_collisions
        )
        
        assert len(result.existing_file_collisions) == 1
        assert len(result.internal_collisions) == 1
        assert result.existing_file_collisions[0]['type'] == 'existing'
        assert result.internal_collisions[0]['type'] == 'internal'


class TestConfigDataStructures:
    """Test data structure validation and consistency."""
    
    def test_converter_structure(self, temp_dir):
        """Test converter configuration structure."""
        converters = [
            {
                'name': 'case',
                'positional': ['field', 'upper'],
                'keyword': {}
            },
            {
                'name': 'pad_numbers',
                'positional': ['number_field'],
                'keyword': {'width': 3}
            }
        ]
        
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'field'], 'keyword': {}},
            converters=converters
        )
        
        assert len(config.converters) == 2
        assert config.converters[0]['name'] == 'case'
        assert config.converters[1]['keyword']['width'] == 3
    
    def test_filter_structure(self, temp_dir):
        """Test filter configuration structure."""
        filters = [
            {
                'name': 'file_type',
                'positional': ['pdf', 'txt'],
                'keyword': {},
                'inverted': False
            },
            {
                'name': 'pattern',
                'positional': [],
                'keyword': {'include': '*.doc*'},
                'inverted': True
            }
        ]
        
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'field'], 'keyword': {}},
            filters=filters
        )
        
        assert len(config.filters) == 2
        assert config.filters[0]['inverted'] is False
        assert config.filters[1]['inverted'] is True
        assert config.filters[1]['keyword']['include'] == '*.doc*'
    
    def test_template_structure(self, temp_dir):
        """Test template configuration structure."""
        template = {
            'name': 'stringsmith',
            'positional': ['{field1}_{field2}'],
            'keyword': {'fallback': 'default_name'}
        }
        
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'field1', 'field2'], 'keyword': {}},
            template=template
        )
        
        assert config.template['name'] == 'stringsmith'
        assert config.template['positional'][0] == '{field1}_{field2}'
        assert config.template['keyword']['fallback'] == 'default_name'


class TestConfigEdgeCases:
    """Test edge cases in configuration."""
    
    def test_empty_positional_args(self, temp_dir):
        """Test configuration with empty positional args."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="metadata",
            extractor_args={'positional': [], 'keyword': {}},
            template={  # Add required template for metadata extractor
                'name': 'stringsmith',
                'positional': ['{{size}}_{{created}}'],
                'keyword': {}
            }
        )
        
        assert config.extractor_args['positional'] == []
    
    def test_empty_keyword_args(self, temp_dir):
        """Test configuration with empty keyword args."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'field'], 'keyword': {}}
        )
        
        assert config.extractor_args['keyword'] == {}
    
    def test_config_immutability_attempt(self, temp_dir):
        """Test that modifying config after creation doesn't break validation."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'field'], 'keyword': {}}
        )
        
        # Modifying the config after creation should be possible but not affect validation
        original_extractor = config.extractor
        config.extractor = "regex"
        
        assert config.extractor == "regex"
        # Original validation was for split extractor, so this change could be invalid
        # but we don't re-validate after creation
    
    def test_nonexistent_input_folder(self):
        """Test configuration with nonexistent input folder."""
        nonexistent_path = Path("/this/path/does/not/exist")
        
        # Should not raise error during config creation
        config = RenameConfig(
            input_folder=nonexistent_path,
            extractor="split",
            extractor_args={'positional': ['_', 'field'], 'keyword': {}}
        )
        
        assert config.input_folder == nonexistent_path


class TestResultCalculations:
    """Test calculated fields and result logic."""
    
    def test_success_rate_calculation(self):
        """Test success rate calculation logic."""
        result = RenameResult(
            files_analyzed=10,
            files_renamed=8,
            errors=2
        )
        
        # Should be able to calculate success rate
        if result.files_analyzed > 0:
            success_rate = result.files_renamed / result.files_analyzed
            assert success_rate == 0.8
    
    def test_filtering_efficiency(self):
        """Test filtering efficiency metrics."""
        result = RenameResult(
            files_analyzed=20,
            files_filtered_out=15,
            files_to_rename=5
        )
        
        # Total files processed = analyzed + filtered out
        total_files = result.files_analyzed + result.files_filtered_out
        assert total_files == 35
        
        # Filtering ratio
        if total_files > 0:
            filter_ratio = result.files_filtered_out / total_files
            assert filter_ratio == 15/35
    
    def test_collision_impact(self):
        """Test collision impact on results."""
        result = RenameResult(
            files_analyzed=10,
            files_to_rename=10,
            collisions=3,
            files_renamed=7  # 3 blocked by collisions
        )
        
        # Files blocked by collisions
        blocked_files = result.files_to_rename - result.files_renamed
        assert blocked_files == 3
        assert blocked_files == result.collisions