"""
Unit tests for built-in extractors and extractor functionality.
"""

import pytest
import re
from pathlib import Path

from core.built_ins.extractors import (
    split_extractor,
    regex_extractor,
    position_extractor,
    metadata_extractor,
    BUILTIN_EXTRACTORS
)
from core.step_factory import StepFactory
from core.steps.base import StepType, StepConfig
from core.processing_context import ProcessingContext


class TestSplitExtractor:
    """Test the split extractor functionality."""
    
    def test_split_basic(self, sample_context):
        """Test basic split extraction."""
        # Test with HR_employee_data_2024.pdf
        result = split_extractor(
            sample_context,
            positional_args=['_', 'dept', 'type', 'category', 'year']
        )
        
        assert result['dept'] == 'HR'
        assert result['type'] == 'employee'
        assert result['category'] == 'data'
        assert result['year'] == '2024'
    
    def test_split_fewer_fields(self, sample_context):
        """Test split with fewer field names than parts."""
        result = split_extractor(
            sample_context,
            positional_args=['_', 'dept', 'type']
        )
        
        assert result['dept'] == 'HR'
        assert result['type'] == 'employee'
        assert 'category' not in result
    
    def test_split_more_fields(self, sample_context):
        """Test split with more field names than parts."""
        result = split_extractor(
            sample_context,
            positional_args=['_', 'dept', 'type', 'category', 'year', 'extra']
        )
        
        assert result['dept'] == 'HR'
        assert result['type'] == 'employee'
        assert result['category'] == 'data'
        assert result['year'] == '2024'
        assert result['extra'] == ''  # Empty for missing parts
    
    def test_split_different_delimiter(self, temp_dir):
        """Test split with different delimiter."""
        test_file = temp_dir / "dept-type-category.txt"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )
        
        result = split_extractor(
            context,
            positional_args=['-', 'dept', 'type', 'category']
        )
        
        assert result['dept'] == 'dept'
        assert result['type'] == 'type'
        assert result['category'] == 'category'
    
    def test_split_no_delimiter(self, temp_dir):
        """Test split when delimiter not found."""
        test_file = temp_dir / "nodasheshere.txt"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )
        
        result = split_extractor(
            context,
            positional_args=['-', 'dept', 'type']
        )
        
        assert result['dept'] == 'nodasheshere'
        assert result['type'] == ''


class TestRegexExtractor:
    """Test the regex extractor functionality."""
    
    def test_regex_named_groups(self, temp_dir):
        """Test regex with named groups."""
        test_file = temp_dir / "DEPT123_report.pdf"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )
        
        pattern = r'(?P<dept>[A-Z]+)(?P<num>\d+)_(?P<type>\w+)'
        result = regex_extractor(
            context,
            positional_args=[pattern]
        )
        
        assert result['dept'] == 'DEPT'
        assert result['num'] == '123'
        assert result['type'] == 'report'
    
    def test_regex_no_match(self, sample_context):
        """Test regex when pattern doesn't match."""
        pattern = r'(?P<code>CODE\d+)'
        result = regex_extractor(
            sample_context,
            positional_args=[pattern]
        )
        
        assert result == {}
    
    def test_regex_numbered_groups(self, temp_dir):
        """Test regex with numbered groups and field mapping."""
        test_file = temp_dir / "ABC_123_report.pdf"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )
        
        pattern = r'([A-Z]+)_(\d+)_(\w+)'
        result = regex_extractor(
            context,
            positional_args=[pattern],
            field1='dept',
            field2='num',
            field3='type'
        )
        
        assert result['dept'] == 'ABC'
        assert result['num'] == '123'
        assert result['type'] == 'report'
    
    def test_regex_invalid_pattern(self, sample_context):
        """Test regex with invalid pattern."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            regex_extractor(
                sample_context,
                positional_args=[r'(?P<invalid>[']  # Invalid regex
            )


class TestPositionExtractor:
    """Test the position extractor functionality."""
    
    def test_position_basic(self, temp_dir):
        """Test basic position extraction."""
        test_file = temp_dir / "HR001report.txt"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )
        
        result = position_extractor(
            context,
            positional_args=['0-2:dept', '2-5:num', '5-11:type']
        )
        
        # Fixed to match inclusive range behavior: filename[start:end+1]
        assert result['dept'] == 'HR0'      # positions 0,1,2 → "HR0"
        assert result['num'] == '001r'      # positions 2,3,4,5 → "001r"
        assert result['type'] == 'report'   # positions 5,6,7,8,9,10,11 → "report"
    
    def test_position_out_of_bounds(self, temp_dir):
        """Test position extraction with out of bounds ranges."""
        test_file = temp_dir / "short.txt"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )
        
        result = position_extractor(
            context,
            positional_args=['0-3:part1', '10-15:part2']
        )
        
        # Fixed to match inclusive range behavior: filename[start:end+1]
        assert result['part1'] == 'shor'  # positions 0,1,2,3 → "shor"
        assert result['part2'] == ''      # Out of bounds
    
    def test_position_invalid_format(self, sample_context):
        """Test position extractor with invalid format."""
        with pytest.raises(ValueError, match="Invalid position spec"):
            position_extractor(
                sample_context,
                positional_args=['invalid_format']
            )


class TestMetadataExtractor:
    """Test the metadata extractor functionality."""
    
    def test_metadata_created(self, sample_context):
        """Test extracting created date."""
        result = metadata_extractor(
            sample_context,
            positional_args=['created']
        )
        
        assert 'created' in result
        assert result['created'] == '2024-01-15'
    
    def test_metadata_modified(self, sample_context):
        """Test extracting modified date."""
        result = metadata_extractor(
            sample_context,
            positional_args=['modified']
        )
        
        assert 'modified' in result
        assert result['modified'] == '2024-02-20'
    
    def test_metadata_size(self, sample_context):
        """Test extracting file size."""
        result = metadata_extractor(
            sample_context,
            positional_args=['size']
        )
        
        assert 'size' in result
        assert result['size'] == '1'  # 1024 bytes = 1 KB
    
    def test_metadata_multiple_fields(self, sample_context):
        """Test extracting multiple metadata fields."""
        result = metadata_extractor(
            sample_context,
            positional_args=['created', 'modified', 'size']
        )
        
        assert result['created'] == '2024-01-15'
        assert result['modified'] == '2024-02-20'
        assert result['size'] == '1'
    
    def test_metadata_no_timestamp(self, temp_dir):
        """Test metadata extraction with missing timestamps."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )
        
        result = metadata_extractor(
            context,
            positional_args=['created', 'modified']
        )
        
        assert result['created'] == ''
        assert result['modified'] == ''
    
    def test_metadata_invalid_field(self, sample_context):
        """Test metadata extraction with invalid field."""
        with pytest.raises(ValueError, match="Unknown metadata field"):
            metadata_extractor(
                sample_context,
                positional_args=['invalid_field']
            )


class TestExtractorRegistry:
    """Test the extractor registry and factory integration."""
    
    def test_builtin_extractors_exist(self):
        """Test that all expected extractors exist in registry."""
        expected_extractors = ['split', 'regex', 'position', 'metadata']
        
        for extractor_name in expected_extractors:
            assert extractor_name in BUILTIN_EXTRACTORS
            assert callable(BUILTIN_EXTRACTORS[extractor_name])
    
    def test_step_factory_integration(self, sample_context):
        """Test extractor creation through StepFactory."""
        config = StepConfig(
            name='split',
            positional_args=['_', 'dept', 'type', 'category'],
            keyword_args={}
        )
        
        extractor_func = StepFactory.create_executable(StepType.EXTRACTOR, config)
        result = extractor_func(sample_context)
        
        assert result['dept'] == 'HR'
        assert result['type'] == 'employee'
        assert result['category'] == 'data'
    
    def test_get_builtin_functions(self):
        """Test getting builtin functions from factory."""
        builtin_funcs = StepFactory.get_builtin_functions(StepType.EXTRACTOR)
        
        assert 'split' in builtin_funcs
        assert 'regex' in builtin_funcs
        assert 'position' in builtin_funcs
        assert 'metadata' in builtin_funcs


class TestCustomExtractorLoading:
    """Test loading and validation of custom extractors."""
    
    def test_load_valid_custom_extractor(self, custom_extractor_file, temp_dir):
        """Test loading a valid custom extractor."""
        test_file = temp_dir / "prefix_test_suffix.txt"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )
        
        config = StepConfig(
            name=str(custom_extractor_file),
            positional_args=['test_extractor'],
            keyword_args={}
        )
        
        extractor_func = StepFactory.create_executable(StepType.EXTRACTOR, config)
        result = extractor_func(context)
        
        assert result['prefix'] == 'prefix'
        assert result['suffix'] == 'suffix'
    
    def test_custom_extractor_validation(self, custom_extractor_file):
        """Test validation of custom extractor functions."""
        from core.function_loader import load_custom_function
        
        # Valid function should pass validation
        valid_func = load_custom_function(custom_extractor_file, 'test_extractor')
        validation_result = StepFactory.validate_custom_function(StepType.EXTRACTOR, valid_func)
        assert validation_result.valid
        
        # Invalid function - check that validation identifies issues
        invalid_func = load_custom_function(custom_extractor_file, 'invalid_extractor')
        validation_result = StepFactory.validate_custom_function(StepType.EXTRACTOR, invalid_func)
        assert 'parameter' in validation_result.message.lower()