"""
Unit tests for built-in filters.

Tests all filter functionality including inversion and edge cases.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from core.filters import (
    pattern_filter, file_type_filter, file_size_filter, name_length_filter, date_modified_filter,
    get_filter, BUILTIN_FILTERS
)
from core.processing_context import ProcessingContext


class TestPatternFilter:
    """Test pattern_filter functionality."""
    
    def test_pattern_include_match(self, mock_metadata):
        """Test pattern filter with matching include pattern."""
        context = ProcessingContext(
            "document.pdf",
            Path("document.pdf"),
            mock_metadata
        )
        
        result = pattern_filter(context, ['*.pdf'])
        
        assert result is True
    
    def test_pattern_include_no_match(self, mock_metadata):
        """Test pattern filter with non-matching include pattern."""
        context = ProcessingContext(
            "image.jpg",
            Path("image.jpg"),
            mock_metadata
        )
        
        result = pattern_filter(context, ['*.pdf'])
        
        assert result is False
    
    def test_pattern_exclude_match(self, mock_metadata):
        """Test pattern filter with matching exclude pattern."""
        context = ProcessingContext(
            "temp_file.pdf",
            Path("temp_file.pdf"),
            mock_metadata
        )
        
        result = pattern_filter(context, ['*.pdf', '*temp*'])
        
        assert result is False  # Excluded because matches temp pattern
    
    def test_pattern_with_kwargs(self, mock_metadata):
        """Test pattern filter with keyword arguments."""
        context = ProcessingContext(
            "document.pdf",
            Path("document.pdf"),
            mock_metadata
        )
        
        result = pattern_filter(context, [], include='*.pdf', exclude='*temp*')
        
        assert result is True
    
    def test_pattern_exclude_only(self, mock_metadata):
        """Test pattern filter with exclude pattern only."""
        context = ProcessingContext(
            "temp_file.pdf",
            Path("temp_file.pdf"),
            mock_metadata
        )
        
        result = pattern_filter(context, [], exclude='*temp*')
        
        assert result is False


class TestFileTypeFilter:
    """Test file_type_filter functionality."""
    
    def test_file_type_single_match(self, mock_metadata):
        """Test file type filter with single matching type."""
        context = ProcessingContext(
            "document.pdf",
            Path("document.pdf"),
            mock_metadata
        )
        
        result = file_type_filter(context, ['pdf'])
        
        assert result is True
    
    def test_file_type_multiple_match(self, mock_metadata):
        """Test file type filter with multiple types."""
        context = ProcessingContext(
            "document.pdf",
            Path("document.pdf"),
            mock_metadata
        )
        
        result = file_type_filter(context, ['pdf', 'docx', 'jpg'])
        
        assert result is True
    
    def test_file_type_no_match(self, mock_metadata):
        """Test file type filter with non-matching type."""
        context = ProcessingContext(
            "document.pdf",
            Path("document.pdf"),
            mock_metadata
        )
        
        result = file_type_filter(context, ['jpg', 'docx'])
        
        assert result is False
    
    def test_file_type_comma_separated(self, mock_metadata):
        """Test file type filter with comma-separated string."""
        context = ProcessingContext(
            "document.pdf",
            Path("document.pdf"),
            mock_metadata
        )
        
        result = file_type_filter(context, ['pdf,docx,jpg'])
        
        assert result is True
    
    def test_file_type_with_kwargs(self, mock_metadata):
        """Test file type filter with keyword arguments."""
        context = ProcessingContext(
            "document.pdf",
            Path("document.pdf"),
            mock_metadata
        )
        
        result = file_type_filter(context, [], types='pdf,docx,jpg')
        
        assert result is True
    
    def test_file_type_case_insensitive(self, mock_metadata):
        """Test file type filter is case insensitive."""
        context = ProcessingContext(
            "document.PDF",
            Path("document.PDF"),
            mock_metadata
        )
        
        result = file_type_filter(context, ['pdf'])
        
        assert result is True


class TestFileSizeFilter:
    """Test file_size_filter functionality."""
    
    def test_file_size_min_only(self):
        """Test file size filter with minimum size only."""
        metadata = {'size': 2048}  # 2KB - this is accessed via property
        context = ProcessingContext(
            "large_file.pdf",
            Path("large_file.pdf"),
            metadata
        )
        
        result = file_size_filter(context, ['1KB'])
        
        assert result is True
    
    def test_file_size_below_minimum(self):
        """Test file size filter below minimum."""
        metadata = {'size': 512}  # 512B - accessed via context.file_size property
        context = ProcessingContext(
            "small_file.pdf",
            Path("small_file.pdf"),
            metadata
        )
        
        result = file_size_filter(context, ['1KB'])
        
        assert result is False
    
    def test_file_size_range(self):
        """Test file size filter with min and max range."""
        metadata = {'size': 3072}  # 3KB
        context = ProcessingContext(
            "medium_file.pdf",
            Path("medium_file.pdf"),
            metadata
        )
        
        result = file_size_filter(context, ['1KB', '5KB'])
        
        assert result is True
    
    def test_file_size_above_maximum(self):
        """Test file size filter above maximum."""
        metadata = {'size': 6 * 1024}  # 6KB
        context = ProcessingContext(
            "large_file.pdf",
            Path("large_file.pdf"),
            metadata
        )
        
        result = file_size_filter(context, ['1KB', '5KB'])
        
        assert result is False
    
    def test_file_size_with_kwargs(self):
        """Test file size filter with keyword arguments."""
        metadata = {'size': 2048}
        context = ProcessingContext(
            "file.pdf",
            Path("file.pdf"),
            metadata
        )
        
        result = file_size_filter(context, [], min_size='1KB', max_size='5KB')
        
        assert result is True
    
    def test_file_size_units(self):
        """Test file size filter with different units."""
        metadata = {'size': 1024 * 1024}  # 1MB
        context = ProcessingContext(
            "file.pdf",
            Path("file.pdf"),
            metadata
        )
        
        result = file_size_filter(context, ['500KB', '2MB'])
        
        assert result is True


class TestNameLengthFilter:
    """Test name_length_filter functionality."""
    
    def test_name_length_min_only(self, mock_metadata):
        """Test name length filter with minimum length."""
        context = ProcessingContext(
            "short_name.pdf",
            Path("short_name.pdf"),
            mock_metadata
        )
        
        result = name_length_filter(context, ['5'])
        
        assert result is True  # "short_name" is 10 characters
    
    def test_name_length_below_minimum(self, mock_metadata):
        """Test name length filter below minimum."""
        context = ProcessingContext(
            "a.pdf",
            Path("a.pdf"),
            mock_metadata
        )
        
        result = name_length_filter(context, ['5'])
        
        assert result is False  # "a" is 1 character
    
    def test_name_length_range(self, mock_metadata):
        """Test name length filter with range."""
        context = ProcessingContext(
            "medium_name.pdf",
            Path("medium_name.pdf"),
            mock_metadata
        )
        
        result = name_length_filter(context, ['5', '15'])
        
        assert result is True  # "medium_name" is 11 characters
    
    def test_name_length_with_kwargs(self, mock_metadata):
        """Test name length filter with keyword arguments."""
        context = ProcessingContext(
            "test_file.pdf",
            Path("test_file.pdf"),
            mock_metadata
        )
        
        result = name_length_filter(context, [], min_length='5', max_length='15')
        
        assert result is True


class TestFilterFactory:
    """Test filter factory function."""
    
    def test_get_filter_pattern(self):
        """Test getting pattern filter."""
        config = {
            'positional': ['*.pdf'],
            'keyword': {},
            'inverted': False
        }
        filter_func = get_filter('pattern', config)
        
        assert callable(filter_func)
    
    def test_get_filter_file_type(self):
        """Test getting file-type filter."""
        config = {
            'positional': ['pdf', 'docx'],
            'keyword': {},
            'inverted': False
        }
        filter_func = get_filter('file-type', config)
        
        assert callable(filter_func)
    
    def test_get_filter_file_size(self):
        """Test getting file-size filter."""
        config = {
            'positional': ['1KB', '5KB'],
            'keyword': {},
            'inverted': False
        }
        filter_func = get_filter('file-size', config)
        
        assert callable(filter_func)
    
    def test_get_filter_with_inversion(self):
        """Test getting filter with inversion."""
        config = {
            'positional': ['*.pdf'],
            'keyword': {},
            'inverted': True
        }
        filter_func = get_filter('pattern', config)
        
        assert callable(filter_func)
    
    def test_get_filter_custom_function(self, tmp_path):
        """Test getting custom filter function."""
        function_file = tmp_path / "test_filter.py"
        function_file.write_text("""
def custom_filter(context):
    return True
""")
        
        config = {
            'positional': ['custom_filter'],
            'keyword': {},
            'inverted': False
        }
        filter_func = get_filter(str(function_file), config)
        
        assert callable(filter_func)
    
    def test_get_filter_invalid(self):
        """Test getting invalid filter."""
        with pytest.raises(ValueError, match="Unknown filter"):
            get_filter('invalid_filter', {})


class TestFilterIntegration:
    """Test filter integration and inversion."""
    
    def test_filter_inversion(self, mock_metadata):
        """Test that filter inversion works properly."""
        context = ProcessingContext(
            "document.pdf",
            Path("document.pdf"),
            mock_metadata
        )
        
        # Normal filter should match PDF
        config_normal = {
            'positional': ['pdf'],
            'keyword': {},
            'inverted': False
        }
        filter_normal = get_filter('file-type', config_normal)
        assert filter_normal(context) is True
        
        # Inverted filter should exclude PDF
        config_inverted = {
            'positional': ['pdf'],
            'keyword': {},
            'inverted': True
        }
        filter_inverted = get_filter('file-type', config_inverted)
        assert filter_inverted(context) is False
    
    def test_builtin_filters_registry(self):
        """Test that all expected filters are in registry."""
        expected_filters = ['pattern', 'file-type', 'file-size', 'name-length', 'date-modified']
        
        for filter_name in expected_filters:
            assert filter_name in BUILTIN_FILTERS
            assert callable(BUILTIN_FILTERS[filter_name])