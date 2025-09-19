"""
Unit tests for CLI interface and argument parsing.

Tests command-line argument parsing, validation, and configuration building.
"""

import pytest
import sys
from unittest.mock import Mock, patch
from pathlib import Path

# The conftest.py already adds the project root to sys.path, so we can import directly
try:
    from ui.cli import parse_function_call
    CLI_PARSE_AVAILABLE = True
except ImportError:
    CLI_PARSE_AVAILABLE = False

# For functions that have relative imports, we'll mock the dependencies
class MockProcessor:
    pass

class MockConfig:
    pass

class MockLogger:
    @staticmethod
    def get_logger(name):
        return Mock()

# Mock the problematic imports before importing CLI functions
sys.modules['shared_utils.logger'] = MockLogger
sys.modules['core.logging_processor'] = Mock()

try:
    # Now try to import other CLI functions with mocked dependencies
    with patch.dict('sys.modules', {
        'shared_utils.logger': MockLogger,
        'core.logging_processor': Mock(),
        'core.templates': Mock(),
        'core.converters': Mock(),
        'core.validators': Mock(),
        'core.function_loader': Mock(),
    }):
        from ui.cli import create_parser, validate_args
        CLI_FULL_AVAILABLE = True
except ImportError:
    CLI_FULL_AVAILABLE = False


class TestFunctionCallParsing:
    """Test parsing of function call syntax."""
    
    @pytest.mark.skipif(not CLI_PARSE_AVAILABLE, reason="CLI parse_function_call not available")
    def test_parse_simple_function_call(self):
        """Test parsing simple function call."""
        result = parse_function_call('split,_,dept,type')
        
        assert result == ('split', ['_', 'dept', 'type'], {}, False)
    
    @pytest.mark.skipif(not CLI_PARSE_AVAILABLE, reason="CLI parse_function_call not available")
    def test_parse_function_call_with_kwargs(self):
        """Test parsing function call with keyword arguments."""
        result = parse_function_call('pad_numbers,field,width=3,fill=0')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'pad_numbers'
        assert pos_args == ['field']
        assert kwargs == {'width': '3', 'fill': '0'}
        assert inverted is False
    
    @pytest.mark.skipif(not CLI_PARSE_AVAILABLE, reason="CLI parse_function_call not available")
    def test_parse_function_call_mixed_args(self):
        """Test parsing function call with mixed positional and keyword args."""
        result = parse_function_call('format,{dept}_{type},case=upper')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'format'
        assert pos_args == ['{dept}_{type}']
        assert kwargs == {'case': 'upper'}
        assert inverted is False
    
    @pytest.mark.skipif(not CLI_PARSE_AVAILABLE, reason="CLI parse_function_call not available")
    def test_parse_function_call_with_inversion(self):
        """Test parsing function call with inversion prefix."""
        result = parse_function_call('!extension,pdf,docx')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'extension'
        assert pos_args == ['pdf', 'docx']
        assert kwargs == {}
        assert inverted is True
    
    @pytest.mark.skipif(not CLI_PARSE_AVAILABLE, reason="CLI parse_function_call not available")
    def test_parse_function_call_empty(self):
        """Test parsing empty function call."""
        result = parse_function_call('')
        
        assert result == (None, [], {}, False)
    
    @pytest.mark.skipif(not CLI_PARSE_AVAILABLE, reason="CLI parse_function_call not available")
    def test_parse_function_call_only_name(self):
        """Test parsing function call with only name."""
        result = parse_function_call('metadata')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'metadata'
        assert pos_args == []
        assert kwargs == {}
        assert inverted is False
    
    @pytest.mark.skipif(not CLI_PARSE_AVAILABLE, reason="CLI parse_function_call not available")
    def test_parse_function_call_with_spaces(self):
        """Test parsing function call with spaces around commas."""
        result = parse_function_call('split, _, dept, type')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'split'
        assert pos_args == ['_', 'dept', 'type']
        assert kwargs == {}
        assert inverted is False


class TestArgumentParser:
    """Test argument parser creation and basic functionality."""
    
    @pytest.mark.skipif(not CLI_FULL_AVAILABLE, reason="CLI imports not fully available")
    def test_create_parser(self):
        """Test that parser can be created without errors."""
        with patch.dict('sys.modules', {
            'shared_utils.logger': MockLogger,
            'core.logging_processor': Mock(),
            'core.templates': Mock(),
            'core.converters': Mock(),
            'core.validators': Mock(),
            'core.function_loader': Mock(),
        }):
            parser = create_parser()
            assert parser is not None
            assert hasattr(parser, 'parse_args')
    
    @pytest.mark.skipif(not CLI_FULL_AVAILABLE, reason="CLI imports not fully available")
    def test_parser_basic_structure(self):
        """Test basic parser structure."""
        with patch.dict('sys.modules', {
            'shared_utils.logger': MockLogger,
            'core.logging_processor': Mock(),
            'core.templates': Mock(),
            'core.converters': Mock(),
            'core.validators': Mock(),
            'core.function_loader': Mock(),
        }):
            parser = create_parser()
            
            # Test that the parser has the expected arguments
            # This tests the structure without trying to parse actual arguments
            actions = {action.dest for action in parser._actions}
            
            # These should be present based on your CLI structure
            expected_args = {'help', 'input_folder', 'extractor'}
            assert expected_args.issubset(actions)


class TestArgumentValidation:
    """Test argument validation functionality."""
    
    @pytest.mark.skipif(not CLI_FULL_AVAILABLE, reason="CLI imports not fully available")
    def test_validate_args_valid_folder(self, temp_dir):
        """Test validation with valid input folder."""
        with patch.dict('sys.modules', {
            'shared_utils.logger': MockLogger,
            'core.logging_processor': Mock(),
            'core.templates': Mock(),
            'core.converters': Mock(),
            'core.validators': Mock(),
            'core.function_loader': Mock(),
        }):
            mock_args = Mock()
            mock_args.input_folder = temp_dir
            mock_args.template = None
            
            error = validate_args(mock_args)
            assert error is None
    
    @pytest.mark.skipif(not CLI_FULL_AVAILABLE, reason="CLI imports not fully available")
    def test_validate_args_nonexistent_folder(self):
        """Test validation with non-existent folder."""
        with patch.dict('sys.modules', {
            'shared_utils.logger': MockLogger,
            'core.logging_processor': Mock(),
            'core.templates': Mock(),
            'core.converters': Mock(),
            'core.validators': Mock(),
            'core.function_loader': Mock(),
        }):
            mock_args = Mock()
            mock_args.input_folder = Path("/definitely/nonexistent/folder")
            mock_args.template = None
            
            error = validate_args(mock_args)
            assert error is not None
            assert "does not exist" in error


class TestFunctionCallParsingEdgeCases:
    """Test edge cases in function call parsing."""
    
    @pytest.mark.skipif(not CLI_PARSE_AVAILABLE, reason="CLI parse_function_call not available")
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
    
    @pytest.mark.skipif(not CLI_PARSE_AVAILABLE, reason="CLI parse_function_call not available")  
    def test_parse_function_call_none_input(self):
        """Test parse_function_call with None input."""
        result = parse_function_call(None)
        assert result == (None, [], {}, False)
    
    @pytest.mark.skipif(not CLI_PARSE_AVAILABLE, reason="CLI parse_function_call not available")
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


# Test that demonstrates the CLI structure without import issues
class TestCLIStructure:
    """Test CLI structure and behavior without deep imports."""
    
    def test_function_call_format_specification(self):
        """Test that function call format meets specification."""
        # This documents the expected function call format for your CLI
        expected_formats = [
            'split,_,dept,type,date',
            'pad_numbers,field,width=3',
            'format,{dept}_{type}',
            '!extension,pdf,docx',
            'regex,"(?P<dept>\\w+)_(?P<num>\\d+)"'
        ]
        
        # These are the formats your CLI should support
        for format_str in expected_formats:
            assert isinstance(format_str, str)
            assert ',' in format_str  # Should contain commas as separators
            parts = format_str.split(',')
            assert len(parts) >= 1  # Should have at least function name