"""
Unit tests for built-in extractors.

Tests all extractor functionality including edge cases and error handling.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from core.extractors import (
    split_extractor, regex_extractor, position_extractor, metadata_extractor,
    get_extractor, BUILTIN_EXTRACTORS
)
from core.processing_context import ProcessingContext


class TestSplitExtractor:
    """Test split_extractor functionality."""
    
    def test_basic_split(self, mock_metadata):
        """Test basic splitting functionality."""
        context = ProcessingContext(
            "HR_report_20240915.pdf",
            Path("HR_report_20240915.pdf"),
            mock_metadata
        )
        
        result = split_extractor(context, ['_', 'dept', 'type', 'date'])
        
        assert result['dept'] == 'HR'
        assert result['type'] == 'report'
        assert result['date'] == '20240915'
    
    def test_split_with_kwargs(self, mock_metadata):
        """Test splitting with keyword arguments."""
        context = ProcessingContext(
            "HR_report_20240915.pdf",
            Path("HR_report_20240915.pdf"),
            mock_metadata
        )
        
        result = split_extractor(context, [], split_on='_', fields='dept,type,date')
        
        assert result['dept'] == 'HR'
        assert result['type'] == 'report'
        assert result['date'] == '20240915'
    
    def test_split_insufficient_parts(self, mock_metadata):
        """Test splitting with insufficient parts."""
        context = ProcessingContext(
            "HR_report.pdf",  # Only 2 parts, need 4
            Path("HR_report.pdf"),
            mock_metadata
        )
        
        result = split_extractor(context, ['_', 'dept', 'type', 'date', 'extra'])
        
        assert result['dept'] == 'HR'
        assert result['type'] == 'report'
        assert result['date'] is None  # Missing parts should be None
        assert result['extra'] is None
    
    def test_split_skip_fields(self, mock_metadata):
        """Test splitting with underscore field names (skip)."""
        context = ProcessingContext(
            "HR_report_20240915_extra.pdf",
            Path("HR_report_20240915_extra.pdf"),
            mock_metadata
        )
        
        result = split_extractor(context, ['_', 'dept', '_', 'date'])  # Skip 'report'
        
        assert result['dept'] == 'HR'
        assert result['date'] == '20240915'
        assert '_' not in result  # Should not create field named '_'
    
    def test_split_no_delimiter_found(self, mock_metadata):
        """Test when delimiter is not found in filename."""
        context = ProcessingContext(
            "nodasheshere.pdf",
            Path("nodasheshere.pdf"),
            mock_metadata
        )
        
        result = split_extractor(context, ['_', 'dept', 'type'])
        
        # Should treat whole name as first field
        assert result['dept'] == 'nodasheshere'
        assert result['type'] is None
    
    def test_split_no_field_names(self, mock_metadata):
        """Test error when no field names provided."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        
        with pytest.raises(ValueError, match="requires field names"):
            split_extractor(context, ['_'])  # Only delimiter, no fields


class TestRegexExtractor:
    """Test regex_extractor functionality."""
    
    def test_basic_regex(self, mock_metadata):
        """Test basic regex extraction."""
        pattern = r'(?P<dept>\w+)_(?P<num>\d+)'
        context = ProcessingContext(
            "HR_123_document.pdf",
            Path("HR_123_document.pdf"),
            mock_metadata
        )
        
        result = regex_extractor(context, [pattern])
        
        assert result['dept'] == 'HR'
        assert result['num'] == '123'
    
    def test_regex_with_kwargs(self, mock_metadata):
        """Test regex with keyword arguments."""
        pattern = r'(?P<dept>\w+)_(?P<num>\d+)'
        context = ProcessingContext(
            "HR_123_document.pdf",
            Path("HR_123_document.pdf"),
            mock_metadata
        )
        
        result = regex_extractor(context, [], pattern=pattern)
        
        assert result['dept'] == 'HR'
        assert result['num'] == '123'
    
    def test_regex_no_match(self, mock_metadata):
        """Test regex with no matches."""
        pattern = r'(?P<dept>\w+)_(?P<num>\d+)'
        context = ProcessingContext(
            "nomatch.pdf",
            Path("nomatch.pdf"),
            mock_metadata
        )
        
        result = regex_extractor(context, [pattern])
        
        # Should return empty dict when no match
        assert result == {}
    
    def test_regex_complex_pattern(self, mock_metadata):
        """Test complex regex pattern."""
        pattern = r'(?P<client>[A-Z]+)_(?P<project>\w+)_v(?P<version>\d+\.\d+)_(?P<status>\w+)'
        context = ProcessingContext(
            "ACME_WebsiteRedesign_v2.1_final.pdf",
            Path("ACME_WebsiteRedesign_v2.1_final.pdf"),
            mock_metadata
        )
        
        result = regex_extractor(context, [pattern])
        
        assert result['client'] == 'ACME'
        assert result['project'] == 'WebsiteRedesign'
        assert result['version'] == '2.1'
        assert result['status'] == 'final'
    
    def test_regex_no_pattern(self, mock_metadata):
        """Test error when no pattern provided."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        
        with pytest.raises(ValueError, match="requires pattern"):
            regex_extractor(context, [])


class TestPositionExtractor:
    """Test position_extractor functionality."""
    
    def test_basic_position_extraction(self, mock_metadata):
        """Test basic position-based extraction."""
        positions = "0-2:dept,3-6:code,7-15:date"  # Fixed ranges for "HR_001_20240815"
        context = ProcessingContext(
            "HR_001_20240815.pdf",
            Path("HR_001_20240815.pdf"),
            mock_metadata
        )
        
        result = position_extractor(context, [positions])
        
        assert result['dept'] == 'HR'   # Characters 0-2 
        assert result['code'] == '001'  # Characters 3-6
        assert result['date'] == '20240815'  # Characters 7-15
    
    def test_position_with_kwargs(self, mock_metadata):
        """Test position extraction with keyword arguments."""
        positions = "0-2:dept,3-6:code"  # Fixed range for "HR_001_document"
        context = ProcessingContext(
            "HR_001_document.pdf",
            Path("HR_001_document.pdf"),
            mock_metadata
        )
        
        result = position_extractor(context, [], positions=positions)
        
        assert result['dept'] == 'HR'
        assert result['code'] == '001'
    
    def test_position_out_of_bounds(self, mock_metadata):
        """Test position extraction beyond filename length."""
        positions = "0-2:start,10-20:end"
        context = ProcessingContext(
            "short.pdf",  # Only 5 characters in stem
            Path("short.pdf"),
            mock_metadata
        )
        
        result = position_extractor(context, [positions])
        
        assert result['start'] == 'sh'  # Characters 0-2
        assert result['end'] is None  # Position 10-20 out of bounds
    
    def test_position_single_character(self, mock_metadata):
        """Test single character extraction."""
        positions = "0-1:first,4-5:fifth"
        context = ProcessingContext(
            "ABCDE.pdf",
            Path("ABCDE.pdf"),
            mock_metadata
        )
        
        result = position_extractor(context, [positions])
        
        assert result['first'] == 'A'
        assert result['fifth'] == 'E'


class TestMetadataExtractor:
    """Test metadata_extractor functionality."""
    
    def test_metadata_extraction_positional(self, mock_metadata):
        """Test basic metadata extraction with positional args."""
        # Add proper metadata values that the extractor expects
        metadata_with_timestamps = {
            'size': 1024,
            'created': 1692153600,  # Unix timestamp
            'modified': 1692240000,  # Unix timestamp  
            'type': 'file'
        }
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            metadata_with_timestamps
        )
        
        result = metadata_extractor(context, ['created', 'modified', 'size'])
        
        assert 'created' in result
        assert 'modified' in result  
        assert 'size' in result
        assert result['size'] == 1024
    
    def test_metadata_extraction_kwargs(self, mock_metadata):
        """Test metadata extraction with keyword arguments."""
        metadata_with_timestamps = {
            'size': 2048,
            'created': 1692153600,
            'modified': 1692240000,
            'type': 'file'
        }
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            metadata_with_timestamps
        )
        
        result = metadata_extractor(
            context, [], 
            created_date='created', 
            modified_date='modified',
            file_size='size'
        )
        
        assert 'created' in result
        assert 'modified' in result
        assert 'size' in result
        assert result['size'] == 2048


class TestExtractorFactory:
    """Test extractor factory function."""
    
    def test_get_extractor_split(self):
        """Test getting split extractor."""
        args = {
            'positional': ['_', 'dept', 'type', 'date'],
            'keyword': {}
        }
        extractor = get_extractor('split', args)
        
        assert callable(extractor)
    
    def test_get_extractor_regex(self):
        """Test getting regex extractor."""
        args = {
            'positional': [r'(?P<dept>\w+)_(?P<num>\d+)'],
            'keyword': {}
        }
        extractor = get_extractor('regex', args)
        
        assert callable(extractor)
    
    def test_get_extractor_position(self):
        """Test getting position extractor."""
        args = {
            'positional': ["0-2:dept,3-5:code"],
            'keyword': {}
        }
        extractor = get_extractor('position', args)
        
        assert callable(extractor)
    
    def test_get_extractor_metadata(self):
        """Test getting metadata extractor."""
        args = {
            'positional': ['created', 'modified'],
            'keyword': {}
        }
        extractor = get_extractor('metadata', args)
        
        assert callable(extractor)
    
    def test_get_extractor_custom_function(self, tmp_path):
        """Test getting custom extractor function."""
        function_file = tmp_path / "test_extractor.py"
        function_file.write_text("""
def custom_extractor(filename, file_path, metadata):
    return {'custom_field': 'custom_value'}
""")
        
        args = {
            'positional': ['custom_extractor'],
            'keyword': {}
        }
        extractor = get_extractor(str(function_file), args)
        
        assert callable(extractor)
    
    def test_get_extractor_invalid(self):
        """Test getting invalid extractor."""
        with pytest.raises(ValueError, match="Unknown extractor"):
            get_extractor('invalid_extractor', {})
    
    def test_builtin_extractors_registry(self):
        """Test that all expected extractors are in registry."""
        expected_extractors = ['split', 'regex', 'position', 'metadata']
        
        for extractor_name in expected_extractors:
            assert extractor_name in BUILTIN_EXTRACTORS
            assert callable(BUILTIN_EXTRACTORS[extractor_name])