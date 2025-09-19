"""
Unit tests for built-in converters.

Tests all converter functionality including field preservation and error handling.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from core.converters import (
    pad_numbers_converter, date_format_converter, case_converter,
    get_converter, is_converter_function, BUILTIN_CONVERTERS
)
from core.processing_context import ProcessingContext


class TestPadNumbersConverter:
    """Test pad_numbers_converter functionality."""
    
    def test_pad_numbers_basic(self, mock_metadata):
        """Test basic number padding."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {
            'sequence': '5',
            'other_field': 'value'
        }
        
        result = pad_numbers_converter(context, ['sequence', '3'])
        
        assert result['sequence'] == '005'
        assert result['other_field'] == 'value'  # Other fields preserved
    
    def test_pad_numbers_with_kwargs(self, mock_metadata):
        """Test padding with keyword arguments."""
        context = ProcessingContext(
            "test.pdf", 
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'number': '12'}
        
        result = pad_numbers_converter(context, [], field='number', width=4)
        
        assert result['number'] == '0012'
    
    def test_pad_numbers_already_padded(self, mock_metadata):
        """Test padding numbers that are already correctly padded."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'number': '123'}  # Already 3 digits
        
        result = pad_numbers_converter(context, ['number', '3'])
        
        assert result['number'] == '123'  # Should remain unchanged
    
    def test_pad_numbers_with_text_prefix(self, mock_metadata):
        """Test padding numbers with text prefix like 'v2'."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'version': 'v2'}
        
        result = pad_numbers_converter(context, ['version', '3'])
        
        assert result['version'] == 'v002'
    
    def test_pad_numbers_missing_field(self, mock_metadata):
        """Test padding missing field."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'other_field': 'value'}
        
        with pytest.raises(ValueError, match="Field 'missing_field' not found"):
            pad_numbers_converter(context, ['missing_field', '3'])
    
    def test_pad_numbers_no_field_specified(self, mock_metadata):
        """Test error when no field is specified."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'number': '5'}
        
        with pytest.raises(ValueError, match="requires field name"):
            pad_numbers_converter(context, [])


class TestDateFormatConverter:
    """Test date_format_converter functionality."""
    
    def test_date_format_conversion(self, mock_metadata):
        """Test basic date format conversion."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {
            'date': '20240815',
            'other_field': 'value'
        }
        
        result = date_format_converter(context, ['date', '%Y%m%d', '%Y-%m-%d'])
        
        assert result['date'] == '2024-08-15'
        assert result['other_field'] == 'value'
    
    def test_date_format_with_kwargs(self, mock_metadata):
        """Test date conversion with keyword arguments."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'created': '08/15/2024'}
        
        result = date_format_converter(
            context, [], 
            field='created', 
            input_format='%m/%d/%Y',
            output_format='%Y-%m-%d'
        )
        
        assert result['created'] == '2024-08-15'
    
    def test_date_format_invalid_date(self, mock_metadata):
        """Test date conversion with invalid date."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'date': 'not_a_date'}
        
        with pytest.raises(ValueError, match="Date parsing failed"):
            date_format_converter(context, ['date', '%Y%m%d', '%Y-%m-%d'])
    
    def test_date_format_missing_field(self, mock_metadata):
        """Test date conversion with missing field."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'other_field': 'value'}
        
        with pytest.raises(ValueError, match="Field 'missing_date' not found"):
            date_format_converter(context, ['missing_date', '%Y%m%d'])


class TestCaseConverter:
    """Test case_converter functionality."""
    
    def test_case_upper(self, mock_metadata):
        """Test uppercase conversion."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {
            'text': 'hello world',
            'other_field': 'unchanged'
        }
        
        result = case_converter(context, ['text', 'upper'])
        
        assert result['text'] == 'HELLO WORLD'
        assert result['other_field'] == 'unchanged'
    
    def test_case_lower(self, mock_metadata):
        """Test lowercase conversion."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'text': 'HELLO WORLD'}
        
        result = case_converter(context, ['text', 'lower'])
        
        assert result['text'] == 'hello world'
    
    def test_case_title(self, mock_metadata):
        """Test title case conversion."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'text': 'hello world'}
        
        result = case_converter(context, ['text', 'title'])
        
        assert result['text'] == 'Hello World'
    
    def test_case_capitalize(self, mock_metadata):
        """Test capitalize conversion."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'text': 'hello world'}
        
        result = case_converter(context, ['text', 'capitalize'])
        
        assert result['text'] == 'Hello world'
    
    def test_case_with_kwargs(self, mock_metadata):
        """Test case conversion with keyword arguments."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'department': 'hr'}
        
        result = case_converter(context, [], field='department', case='upper')
        
        assert result['department'] == 'HR'
    
    def test_case_invalid_mode(self, mock_metadata):
        """Test invalid case mode."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'text': 'hello'}
        
        with pytest.raises(ValueError, match="Invalid case type"):
            case_converter(context, ['text', 'invalid_mode'])
    
    def test_case_missing_field(self, mock_metadata):
        """Test case conversion with missing field."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {'other_field': 'value'}
        
        with pytest.raises(ValueError, match="Field 'missing_field' not found"):
            case_converter(context, ['missing_field', 'upper'])


class TestConverterFactory:
    """Test converter factory function."""
    
    def test_get_converter_pad_numbers(self):
        """Test getting pad_numbers converter."""
        config = {
            'positional': ['sequence', '3'],
            'keyword': {}
        }
        converter = get_converter('pad_numbers', config)
        
        assert callable(converter)
    
    def test_get_converter_date_format(self):
        """Test getting date_format converter."""
        config = {
            'positional': ['date', '%Y%m%d', '%Y-%m-%d'],
            'keyword': {}
        }
        converter = get_converter('date_format', config)
        
        assert callable(converter)
    
    def test_get_converter_case(self):
        """Test getting case converter."""
        config = {
            'positional': ['text', 'upper'],
            'keyword': {}
        }
        converter = get_converter('case', config)
        
        assert callable(converter)
    
    def test_get_converter_with_kwargs(self):
        """Test getting converter with keyword arguments."""
        config = {
            'positional': ['number'],
            'keyword': {'width': 5}
        }
        converter = get_converter('pad_numbers', config)
        
        assert callable(converter)
    
    def test_get_converter_custom_function(self, tmp_path):
        """Test getting custom converter function."""
        function_file = tmp_path / "test_converter.py"
        function_file.write_text("""
def custom_converter(context):
    data = context.extracted_data.copy()
    data['custom_field'] = 'custom_value'
    return data
""")
        
        config = {
            'positional': ['custom_converter'],
            'keyword': {}
        }
        converter = get_converter(str(function_file), config)
        
        assert callable(converter)
    
    def test_get_converter_invalid(self):
        """Test getting invalid converter."""
        with pytest.raises(ValueError, match="Unknown converter"):
            get_converter('invalid_converter', {})


class TestBuiltinConverterRegistry:
    """Test built-in converter registry."""
    
    def test_builtin_converters_exist(self):
        """Test that expected built-in converters exist."""
        expected_converters = ['pad_numbers', 'date_format', 'case']
        
        for converter_name in expected_converters:
            assert converter_name in BUILTIN_CONVERTERS
            assert callable(BUILTIN_CONVERTERS[converter_name])
    
    def test_is_converter_function(self):
        """Test is_converter_function utility."""
        assert is_converter_function('pad_numbers') is True
        assert is_converter_function('date_format') is True
        assert is_converter_function('case') is True
        assert is_converter_function('invalid_function') is False


class TestConverterIntegration:
    """Test converter integration with ProcessingContext."""
    
    def test_converter_preserves_context(self, mock_metadata):
        """Test that converters preserve ProcessingContext structure."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {
            'department': 'hr',
            'sequence': '5'
        }
        
        # Apply multiple converters
        pad_config = {'positional': ['sequence', '3'], 'keyword': {}}
        case_config = {'positional': ['department', 'upper'], 'keyword': {}}
        
        pad_converter = get_converter('pad_numbers', pad_config)
        case_converter = get_converter('case', case_config)
        
        # Apply first converter
        result1 = pad_converter(context)
        context.extracted_data = result1
        
        # Apply second converter
        result2 = case_converter(context)
        
        # Both transformations should be preserved
        assert result2['sequence'] == '005'  # From pad_numbers
        assert result2['department'] == 'HR'  # From case converter
    
    def test_converter_error_handling(self, mock_metadata):
        """Test converter error handling."""
        context = ProcessingContext(
            "test.pdf",
            Path("test.pdf"),
            mock_metadata
        )
        context.extracted_data = {}  # Empty data
        
        config = {'positional': ['missing_field', '3'], 'keyword': {}}
        converter = get_converter('pad_numbers', config)
        
        with pytest.raises(ValueError):
            converter(context)