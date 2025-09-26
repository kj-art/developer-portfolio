"""
Unit tests for ProcessingContext class.
"""

import pytest
from pathlib import Path

from core.processing_context import ProcessingContext


class TestProcessingContextCreation:
    """Test ProcessingContext creation and basic properties."""
    
    def test_context_creation(self, temp_dir, mock_metadata):
        """Test basic context creation."""
        file_path = temp_dir / "HR_employee_data_2024.pdf"
        file_path.write_text("test content")
        
        context = ProcessingContext(
            filename=file_path.name,
            file_path=file_path,
            metadata=mock_metadata
        )
        
        assert context.filename == "HR_employee_data_2024.pdf"
        assert context.file_path == file_path
        assert context.metadata == mock_metadata
        assert context.base_name == "HR_employee_data_2024"
        assert context.extension == ".pdf"
        assert context.extracted_data is None
    
    def test_context_with_pathlib_path(self, temp_dir, mock_metadata):
        """Test context creation with pathlib Path object."""
        file_path = temp_dir / "test_file.txt"
        file_path.write_text("test content")
        
        context = ProcessingContext(
            filename=file_path.name,
            file_path=file_path,
            metadata=mock_metadata
        )
        
        assert context.filename == "test_file.txt"
        assert context.base_name == "test_file"
        assert context.extension == ".txt"
    
    def test_context_no_extension(self, temp_dir, mock_metadata):
        """Test context with file that has no extension."""
        file_path = temp_dir / "no_extension"
        file_path.write_text("test content")
        
        context = ProcessingContext(
            filename=file_path.name,
            file_path=file_path,
            metadata=mock_metadata
        )
        
        assert context.filename == "no_extension"
        assert context.base_name == "no_extension"
        assert context.extension == ""
    
    def test_context_multiple_dots(self, temp_dir, mock_metadata):
        """Test context with filename containing multiple dots."""
        file_path = temp_dir / "file.backup.tar.gz"
        file_path.write_text("test content")
        
        context = ProcessingContext(
            filename=file_path.name,
            file_path=file_path,
            metadata=mock_metadata
        )
        
        assert context.filename == "file.backup.tar.gz"
        assert context.base_name == "file.backup.tar"
        assert context.extension == ".gz"


class TestExtractedDataHandling:
    """Test extracted data storage and retrieval."""
    
    def test_set_extracted_data(self, sample_context):
        """Test setting extracted data."""
        test_data = {
            'dept': 'IT',
            'type': 'report',
            'year': '2024'
        }
        
        sample_context.extracted_data = test_data
        
        assert sample_context.extracted_data == test_data
        assert sample_context.has_extracted_data() is True
    
    def test_get_extracted_field_exists(self, extracted_context):
        """Test getting existing extracted field."""
        value = extracted_context.get_extracted_field('dept')
        assert value == 'HR'
    
    def test_get_extracted_field_missing(self, extracted_context):
        """Test getting missing extracted field."""
        value = extracted_context.get_extracted_field('missing_field')
        assert value is None
    
    def test_get_extracted_field_with_default(self, extracted_context):
        """Test getting missing field with default value."""
        value = extracted_context.get_extracted_field('missing_field', 'default_value')
        assert value == 'default_value'
    
    def test_has_extracted_data_true(self, extracted_context):
        """Test has_extracted_data when data exists."""
        assert extracted_context.has_extracted_data() is True
    
    def test_has_extracted_data_false(self, sample_context):
        """Test has_extracted_data when no data exists."""
        assert sample_context.has_extracted_data() is False
    
    def test_has_extracted_data_empty_dict(self, sample_context):
        """Test has_extracted_data with empty dictionary."""
        sample_context.extracted_data = {}
        assert sample_context.has_extracted_data() is False
    
    def test_update_extracted_data(self, extracted_context):
        """Test updating extracted data."""
        original_data = extracted_context.extracted_data.copy()
        
        extracted_context.extracted_data.update({
            'new_field': 'new_value',
            'dept': 'Finance'  # Override existing
        })
        
        assert extracted_context.get_extracted_field('new_field') == 'new_value'
        assert extracted_context.get_extracted_field('dept') == 'Finance'
        assert extracted_context.get_extracted_field('type') == 'employee'  # Preserved


class TestContextValidation:
    """Test context validation and error handling."""
    
    def test_nonexistent_file_path(self, mock_metadata):
        """Test context with nonexistent file path."""
        nonexistent_path = Path("/this/path/does/not/exist.txt")
        
        # Should not raise error during creation
        context = ProcessingContext(
            filename=nonexistent_path.name,
            file_path=nonexistent_path,
            metadata=mock_metadata
        )
        assert context.file_path == nonexistent_path
        assert context.filename == "exist.txt"


class TestContextProperties:
    """Test computed properties of ProcessingContext."""
    
    def test_unicode_filename_handling(self, temp_dir, mock_metadata):
        """Test context with unicode characters in filename."""
        file_path = temp_dir / "测试文件_ñáme.pdf"
        file_path.write_text("test content")
        
        context = ProcessingContext(
            filename=file_path.name,
            file_path=file_path,
            metadata=mock_metadata
        )
        
        assert context.filename == "测试文件_ñáme.pdf"
        assert context.base_name == "测试文件_ñáme"
        assert context.extension == ".pdf"
    
    def test_special_characters_filename(self, temp_dir, mock_metadata):
        """Test context with special characters in filename."""
        file_path = temp_dir / "file-name_with[special].chars.txt"
        file_path.write_text("test content")
        
        context = ProcessingContext(
            filename=file_path.name,
            file_path=file_path,
            metadata=mock_metadata
        )
        
        assert context.filename == "file-name_with[special].chars.txt"
        assert context.base_name == "file-name_with[special].chars"
        assert context.extension == ".txt"


class TestContextCopying:
    """Test copying and cloning of ProcessingContext."""
    
    def test_context_independence(self, temp_dir, mock_metadata):
        """Test that multiple contexts are independent."""
        file_path = temp_dir / "test.pdf"
        file_path.write_text("test content")
        
        context1 = ProcessingContext(
            filename=file_path.name,
            file_path=file_path,
            metadata=mock_metadata
        )
        context2 = ProcessingContext(
            filename=file_path.name,
            file_path=file_path,
            metadata=mock_metadata
        )
        
        # Set different extracted data
        context1.extracted_data = {'field1': 'value1'}
        context2.extracted_data = {'field2': 'value2'}
        
        assert context1.get_extracted_field('field1') == 'value1'
        assert context1.get_extracted_field('field2') is None
        assert context2.get_extracted_field('field1') is None
        assert context2.get_extracted_field('field2') == 'value2'
    
    def test_metadata_independence(self, temp_dir):
        """Test that metadata modifications don't affect other contexts."""
        file_path = temp_dir / "test.pdf"
        file_path.write_text("test content")
        
        metadata1 = {'size': 100}
        metadata2 = {'size': 200}
        
        context1 = ProcessingContext(
            filename=file_path.name,
            file_path=file_path,
            metadata=metadata1
        )
        context2 = ProcessingContext(
            filename=file_path.name,
            file_path=file_path,
            metadata=metadata2
        )
        
        # Modify one metadata dict
        metadata1['new_field'] = 'new_value'
        
        assert context1.metadata['new_field'] == 'new_value'
        assert 'new_field' not in context2.metadata


class TestContextStringRepresentation:
    """Test string representation of ProcessingContext."""
    
    def test_context_str(self, sample_context):
        """Test string representation of context."""
        str_repr = str(sample_context)
        
        assert sample_context.filename in str_repr
        assert "ProcessingContext" in str_repr
    
    def test_context_repr(self, sample_context):
        """Test repr representation of context."""
        repr_str = repr(sample_context)
        
        assert "ProcessingContext" in repr_str
        # Just check that it's a reasonable repr, don't be too strict about paths


class TestContextEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_very_long_filename(self, temp_dir, mock_metadata):
        """Test context with very long filename."""
        long_name = "a" * 200 + ".txt"
        file_path = temp_dir / long_name
        
        # Don't actually create the file to avoid filesystem limits
        context = ProcessingContext(
            filename=long_name,
            file_path=file_path,
            metadata=mock_metadata
        )
        
        assert context.filename == long_name
        assert context.base_name == "a" * 200
        assert context.extension == ".txt"
    
    def test_extracted_data_type_preservation(self, sample_context):
        """Test that extracted data preserves various data types."""
        test_data = {
            'string_field': 'text',
            'int_field': 123,
            'float_field': 45.67,
            'bool_field': True,
            'list_field': [1, 2, 3],
            'dict_field': {'nested': 'value'},
            'none_field': None
        }
        
        sample_context.extracted_data = test_data
        
        assert sample_context.get_extracted_field('string_field') == 'text'
        assert sample_context.get_extracted_field('int_field') == 123
        assert sample_context.get_extracted_field('float_field') == 45.67
        assert sample_context.get_extracted_field('bool_field') is True
        assert sample_context.get_extracted_field('list_field') == [1, 2, 3]
        assert sample_context.get_extracted_field('dict_field') == {'nested': 'value'}
        assert sample_context.get_extracted_field('none_field') is None