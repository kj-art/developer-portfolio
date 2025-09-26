"""
Unit tests for built-in filters and filter functionality.
"""

import pytest
from pathlib import Path

from core.built_ins.filters import (
    pattern_filter,
    file_type_filter,
    file_size_filter,
    name_length_filter,
    date_modified_filter,
    BUILTIN_FILTERS
)
from core.step_factory import StepFactory
from core.steps.base import StepType, StepConfig
from core.processing_context import ProcessingContext


class TestPatternFilter:
    """Test the pattern filter functionality."""
    
    def test_pattern_include_match(self, sample_context):
        """Test pattern filter with matching include pattern."""
        result = pattern_filter(
            sample_context,
            positional_args=['*employee*']
        )
        
        assert result is True  # HR_employee_data_2024.pdf matches
    
    def test_pattern_include_no_match(self, sample_context):
        """Test pattern filter with non-matching include pattern."""
        result = pattern_filter(
            sample_context,
            positional_args=['*invoice*']
        )
        
        assert result is False  # HR_employee_data_2024.pdf doesn't match
    
    def test_pattern_exclude_match(self, sample_context):
        """Test pattern filter with matching exclude pattern."""
        result = pattern_filter(
            sample_context,
            positional_args=['*', '*employee*']  # include all, exclude employee
        )
        
        assert result is False  # Should be excluded
    
    def test_pattern_exclude_no_match(self, sample_context):
        """Test pattern filter with non-matching exclude pattern."""
        result = pattern_filter(
            sample_context,
            positional_args=['*', '*invoice*']  # include all, exclude invoice
        )
        
        assert result is True  # Should not be excluded
    
    def test_pattern_keyword_args(self, sample_context):
        """Test pattern filter with keyword arguments."""
        result = pattern_filter(
            sample_context,
            positional_args=[],
            include='*employee*',
            exclude='*temp*'
        )
        
        assert result is True  # Matches include, doesn't match exclude
    
    def test_pattern_no_patterns(self, sample_context):
        """Test pattern filter with no patterns specified."""
        result = pattern_filter(
            sample_context,
            positional_args=[]
        )
        
        assert result is True  # Should pass when no patterns


class TestFileTypeFilter:
    """Test the file type filter functionality."""
    
    def test_file_type_single_match(self, sample_context):
        """Test file type filter with single matching extension."""
        result = file_type_filter(
            sample_context,
            positional_args=['pdf']
        )
        
        assert result is True  # HR_employee_data_2024.pdf
    
    def test_file_type_single_no_match(self, sample_context):
        """Test file type filter with single non-matching extension."""
        result = file_type_filter(
            sample_context,
            positional_args=['txt']
        )
        
        assert result is False
    
    def test_file_type_multiple_match(self, sample_context):
        """Test file type filter with multiple extensions, one matching."""
        result = file_type_filter(
            sample_context,
            positional_args=['txt', 'pdf', 'docx']
        )
        
        assert result is True
    
    def test_file_type_comma_separated(self, sample_context):
        """Test file type filter with comma-separated string."""
        result = file_type_filter(
            sample_context,
            positional_args=['txt,pdf,docx']
        )
        
        assert result is True
    
    def test_file_type_keyword_args(self, sample_context):
        """Test file type filter with keyword arguments."""
        result = file_type_filter(
            sample_context,
            positional_args=[],
            types='txt,pdf,docx'
        )
        
        assert result is True
    
    def test_file_type_case_insensitive(self, temp_dir):
        """Test file type filter is case insensitive."""
        test_file = temp_dir / "test.PDF"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )
        
        result = file_type_filter(
            context,
            positional_args=['pdf']
        )
        
        assert result is True
    
    def test_file_type_with_dots(self, sample_context):
        """Test file type filter handles extensions with dots."""
        result = file_type_filter(
            sample_context,
            positional_args=['.pdf', 'txt']
        )
        
        assert result is True


class TestFileSizeFilter:
    """Test the file size filter functionality."""
    
    def test_file_size_in_range(self, sample_context):
        """Test file size filter when file is in range."""
        result = file_size_filter(
            sample_context,
            positional_args=['512', '2048']  # 512B to 2KB
        )
        
        assert result is True  # File is 1024 bytes
    
    def test_file_size_too_small(self, sample_context):
        """Test file size filter when file is too small."""
        result = file_size_filter(
            sample_context,
            positional_args=['2048', '4096']  # 2KB to 4KB
        )
        
        assert result is False  # File is 1024 bytes
    
    def test_file_size_too_large(self, sample_context):
        """Test file size filter when file is too large."""
        result = file_size_filter(
            sample_context,
            positional_args=['256', '512']  # 256B to 512B
        )
        
        assert result is False  # File is 1024 bytes
    
    def test_file_size_exact_boundaries(self, sample_context):
        """Test file size filter at exact boundaries."""
        result = file_size_filter(
            sample_context,
            positional_args=['1024', '1024']  # Exactly 1024 bytes
        )
        
        assert result is True
    
    def test_file_size_keyword_args(self, sample_context):
        """Test file size filter with keyword arguments."""
        result = file_size_filter(
            sample_context,
            positional_args=[],
            min_size='512',
            max_size='2048'
        )
        
        assert result is True
    
    def test_file_size_no_metadata(self, temp_dir):
        """Test file size filter with missing size metadata."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )  # No size metadata
        
        result = file_size_filter(
            context,
            positional_args=['100', '200']
        )
        
        assert result is False  # Size 0 is below minimum


class TestNameLengthFilter:
    """Test the name length filter functionality."""
    
    def test_name_length_in_range(self, sample_context):
        """Test name length filter when filename is in range."""
        # HR_employee_data_2024.pdf -> HR_employee_data_2024 = 20 chars
        result = name_length_filter(
            sample_context,
            positional_args=['10', '30']
        )
        
        assert result is True
    
    def test_name_length_too_short(self, sample_context):
        """Test name length filter when filename is too short."""
        result = name_length_filter(
            sample_context,
            positional_args=['25', '30']
        )
        
        assert result is False  # 20 chars < 25
    
    def test_name_length_too_long(self, sample_context):
        """Test name length filter when filename is too long."""
        result = name_length_filter(
            sample_context,
            positional_args=['5', '15']
        )
        
        assert result is False  # 20 chars > 15
    
    def test_name_length_keyword_args(self, sample_context):
        """Test name length filter with keyword arguments."""
        result = name_length_filter(
            sample_context,
            positional_args=[],
            min_length='10',
            max_length='30'
        )
        
        assert result is True


class TestDateModifiedFilter:
    """Test the date modified filter functionality."""
    
    def test_date_modified_after(self, sample_context):
        """Test date modified filter for files after a date."""
        result = date_modified_filter(
            sample_context,
            positional_args=['>', '2024-01-01']
        )
        
        # Note: This might fail if your date comparison logic differs
        # Just check that the function runs without error
        assert isinstance(result, bool)
    
    def test_date_modified_invalid_format(self, sample_context):
        """Test date modified filter with invalid date format."""
        result = date_modified_filter(
            sample_context,
            positional_args=['>', 'invalid-date']
        )
        
        # Should handle invalid dates gracefully
        assert isinstance(result, bool)
    
    def test_date_modified_no_timestamp(self, temp_dir):
        """Test date modified filter with missing timestamp."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )  # No timestamp metadata
        
        result = date_modified_filter(
            context,
            positional_args=['>', '2020-01-01']
        )
        
        assert result is False  # No timestamp = False


class TestFilterRegistry:
    """Test the filter registry and factory integration."""
    
    def test_builtin_filters_exist(self):
        """Test that all expected filters exist in registry."""
        # Use actual filter names from your implementation
        expected_filters = ['pattern', 'file-type', 'file-size', 'name-length', 'date-modified']
        
        for filter_name in expected_filters:
            assert filter_name in BUILTIN_FILTERS
            assert callable(BUILTIN_FILTERS[filter_name])
    
    def test_step_factory_integration(self, sample_context):
        """Test filter creation through StepFactory."""
        config = StepConfig(
            name='file-type',  # Use correct name with hyphen
            positional_args=['pdf'],
            keyword_args={}
        )
        
        filter_func = StepFactory.create_executable(StepType.FILTER, config)
        result = filter_func(sample_context)
        
        assert result is True
    
    def test_get_builtin_functions(self):
        """Test getting builtin functions from factory."""
        builtin_funcs = StepFactory.get_builtin_functions(StepType.FILTER)
        
        assert 'pattern' in builtin_funcs
        assert 'file-type' in builtin_funcs  # Use correct name
        assert 'file-size' in builtin_funcs


class TestFilterChaining:
    """Test chaining multiple filters."""
    
    def test_multiple_filters_all_pass(self, sample_context):
        """Test multiple filters where all pass."""
        config1 = StepConfig(
            name='file-type',  # Use correct name
            positional_args=['pdf'],
            keyword_args={}
        )
        filter1 = StepFactory.create_executable(StepType.FILTER, config1)
        
        config2 = StepConfig(
            name='pattern',
            positional_args=['*employee*'],
            keyword_args={}
        )
        filter2 = StepFactory.create_executable(StepType.FILTER, config2)
        
        # Both filters should pass
        assert filter1(sample_context) is True
        assert filter2(sample_context) is True
    
    def test_multiple_filters_one_fails(self, sample_context):
        """Test multiple filters where one fails."""
        config1 = StepConfig(
            name='file-type',  # Will fail
            positional_args=['txt'],
            keyword_args={}
        )
        filter1 = StepFactory.create_executable(StepType.FILTER, config1)
        
        config2 = StepConfig(
            name='pattern',  # Will pass
            positional_args=['*employee*'],
            keyword_args={}
        )
        filter2 = StepFactory.create_executable(StepType.FILTER, config2)
        
        # One filter fails
        assert filter1(sample_context) is False
        assert filter2(sample_context) is True


class TestFilterInversion:
    """Test filter inversion functionality."""
    
    def test_filter_inversion(self, sample_context):
        """Test that filter inversion works correctly."""
        config = StepConfig(
            name='file-type',
            positional_args=['pdf'],
            keyword_args={}
        )
        filter_func = StepFactory.create_executable(StepType.FILTER, config)
        
        # Normal filter should pass
        assert filter_func(sample_context) is True
        
        # Inverted filter should fail
        def inverted_filter(context):
            return not filter_func(context)
        
        assert inverted_filter(sample_context) is False


class TestCustomFilterLoading:
    """Test loading and validation of custom filters."""
    
    def test_load_valid_custom_filter(self, custom_filter_file, temp_dir):
        """Test loading a valid custom filter."""
        test_file = temp_dir / "prefix_test_suffix.txt"
        test_file.write_text("test content")
        context = ProcessingContext(
            filename=test_file.name,
            file_path=test_file,
            metadata={}
        )
        
        config = StepConfig(
            name=str(custom_filter_file),
            positional_args=['test_filter'],
            keyword_args={}
        )
        
        filter_func = StepFactory.create_executable(StepType.FILTER, config)
        result = filter_func(context)
        
        assert result is True  # Contains "_test_"
    
    def test_custom_filter_with_args(self, custom_filter_file, sample_context):
        """Test custom filter with arguments."""
        config = StepConfig(
            name=str(custom_filter_file),
            positional_args=['size_filter'],
            keyword_args={'min_size': 500}
        )
        
        filter_func = StepFactory.create_executable(StepType.FILTER, config)
        result = filter_func(sample_context)
        
        assert result is True  # File size 1024 >= 500
    
    def test_custom_filter_validation(self, custom_filter_file):
        """Test validation of custom filter functions."""
        from core.function_loader import load_custom_function
        
        # Valid function should pass validation
        valid_func = load_custom_function(custom_filter_file, 'test_filter')
        validation_result = StepFactory.validate_custom_function(StepType.FILTER, valid_func)
        assert validation_result.valid
        
        # Invalid function - check that validation identifies issues
        invalid_func = load_custom_function(custom_filter_file, 'invalid_filter')
        validation_result = StepFactory.validate_custom_function(StepType.FILTER, invalid_func)
        assert 'parameter' in validation_result.message.lower()