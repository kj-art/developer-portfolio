"""
Unit tests for CLI interface and argument parsing.

Tests command-line argument parsing, validation, and configuration building.
"""

import pytest
import sys
from unittest.mock import Mock, patch
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the CLI module directly
from ui.cli import parse_function_call, create_parser, validate_args


class TestFunctionCallParsing:
    """Test parsing of function call syntax."""
    
    def test_parse_simple_function_call(self):
        """Test parsing simple function call."""
        result = parse_function_call('split,_,dept,type')
        
        assert result == ('split', ['_', 'dept', 'type'], {}, False)
    
    def test_parse_function_call_with_kwargs(self):
        """Test parsing function call with keyword arguments."""
        result = parse_function_call('pad_numbers,field,width=3,fill=0')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'pad_numbers'
        assert pos_args == ['field']
        assert kwargs == {'width': '3', 'fill': '0'}
        assert inverted is False
    
    def test_parse_function_call_mixed_args(self):
        """Test parsing function call with mixed positional and keyword args."""
        result = parse_function_call('format,{dept}_{type},case=upper')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'format'
        assert pos_args == ['{dept}_{type}']
        assert kwargs == {'case': 'upper'}
        assert inverted is False
    
    def test_parse_function_call_with_inversion(self):
        """Test parsing function call with inversion prefix."""
        result = parse_function_call('!extension,pdf,docx')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'extension'
        assert pos_args == ['pdf', 'docx']
        assert kwargs == {}
        assert inverted is True
    
    def test_parse_function_call_empty(self):
        """Test parsing empty function call."""
        result = parse_function_call('')
        
        assert result == (None, [], {}, False)
    
    def test_parse_function_call_none(self):
        """Test parsing None input."""
        result = parse_function_call(None)
        
        assert result == (None, [], {}, False)
    
    def test_parse_function_call_only_name(self):
        """Test parsing function call with only name."""
        result = parse_function_call('metadata')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'metadata'
        assert pos_args == []
        assert kwargs == {}
        assert inverted is False
    
    def test_parse_function_call_with_spaces(self):
        """Test parsing function call with spaces around commas."""
        result = parse_function_call('split, _, dept, type')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'split'
        assert pos_args == ['_', 'dept', 'type']
        assert kwargs == {}
        assert inverted is False


class TestFunctionCallParsingEdgeCases:
    """Test edge cases in function call parsing."""
    
    def test_function_call_parsing_edge_cases(self):
        """Test edge cases in function call parsing."""
        # Test with equals in value
        result = parse_function_call('format,template={name}={value}')
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'format'
        assert pos_args == []
        assert kwargs == {'template': '{name}={value}'}
        
        # Test with quotes (should be handled as regular text)
        result = parse_function_call('regex,"pattern"')
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'regex'
        assert pos_args == ['"pattern"']
        
        # Test with special characters
        result = parse_function_call('split,_@#$%,field1,field2')
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'split'
        assert pos_args == ['_@#$%', 'field1', 'field2']


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""
    
    def test_parse_function_call_malformed_kwargs(self):
        """Test parse_function_call with malformed keyword arguments."""
        # Multiple equals signs - should take first split
        result = parse_function_call('func,key=value=extra')
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'func'
        assert kwargs == {'key': 'value=extra'}  # Should preserve everything after first =
        
        # Empty key or value
        result = parse_function_call('func,=value')
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'func'
        assert kwargs == {'': 'value'}
        
        result = parse_function_call('func,key=')
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'func'
        assert kwargs == {'key': ''}


class TestArgumentParser:
    """Test argument parser creation and basic functionality."""
    
    def test_create_parser(self):
        """Test that parser can be created without errors."""
        parser = create_parser()
        assert parser is not None
        assert hasattr(parser, 'parse_args')
    
    def test_parser_basic_structure(self):
        """Test basic parser structure."""
        parser = create_parser()
        
        # Test that the parser has the expected arguments
        actions = {action.dest for action in parser._actions}
        
        # These should be present based on the CLI structure
        expected_args = {'help', 'input_folder', 'extractor', 'extract_and_convert'}
        assert expected_args.issubset(actions)


class TestArgumentValidation:
    """Test argument validation functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        yield temp_path
        shutil.rmtree(temp_dir)
    
    def test_validate_args_valid_folder(self, temp_dir):
        """Test validation with valid input folder."""
        mock_args = Mock()
        mock_args.input_folder = temp_dir
        mock_args.template = None
        mock_args.extractor = "split"
        mock_args.converter = ["case"]
        mock_args.extract_and_convert = None
        
        error = validate_args(mock_args)
        assert error is None
    
    def test_validate_args_nonexistent_folder(self):
        """Test validation with non-existent folder."""
        mock_args = Mock()
        mock_args.input_folder = Path("/definitely/nonexistent/folder")
        mock_args.template = None
        
        error = validate_args(mock_args)
        assert error is not None
        assert "does not exist" in error
    
    def test_validate_args_extractor_without_converter(self):
        """Test validation fails when extractor has no converter or template."""
        mock_args = Mock()
        mock_args.input_folder = Path.cwd()  # Use current directory as it exists
        mock_args.template = None
        mock_args.extractor = "split"
        mock_args.converter = None
        mock_args.extract_and_convert = None
        
        error = validate_args(mock_args)
        assert error is not None
        assert "must provide at least one" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])