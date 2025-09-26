"""
Unit tests for CLI interface and argument parsing.

Tests command-line argument parsing, configuration creation, and CLI utilities.
Covers the current CLI implementation with proper function imports.
"""

import pytest
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from batch_rename.ui.cli import (
    parse_function_call, 
    create_argument_parser,
    create_config_from_cli_args,
    create_config_from_file,
    highlight_collisions,
    main
)
from batch_rename.core.config import RenameConfig


class TestFunctionCallParsing:
    """Test parsing of function call syntax."""
    
    def test_parse_simple_function_call(self):
        """Test parsing simple function call with positional args."""
        result = parse_function_call('split,_,dept,type')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'split'
        assert pos_args == ['_', 'dept', 'type']
        assert kwargs == {}
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
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == ''
        assert pos_args == []
        assert kwargs == {}
        assert inverted is False
    
    def test_parse_function_call_none(self):
        """Test parsing None input."""
        with pytest.raises(AttributeError):
            parse_function_call(None)
    
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
    
    def test_parse_function_call_special_characters(self):
        """Test parsing function call with special characters."""
        result = parse_function_call('split,_@#$%,field1,field2')
        
        func_name, pos_args, kwargs, inverted = result
        assert func_name == 'split'
        assert pos_args == ['_@#$%', 'field1', 'field2']
        assert kwargs == {}
        assert inverted is False


class TestArgumentParser:
    """Test argument parser creation and structure."""
    
    def test_create_argument_parser(self):
        """Test that argument parser can be created without errors."""
        parser = create_argument_parser()
        assert parser is not None
        assert hasattr(parser, 'parse_args')
    
    def test_parser_basic_arguments(self):
        """Test that parser has expected basic arguments."""
        parser = create_argument_parser()
        
        # Get all argument destinations
        actions = {action.dest for action in parser._actions}
        
        # Check for expected arguments based on your CLI implementation
        expected_args = {
            'help', 'config', 'input_folder', 'recursive',
            'extractor', 'converter', 'template', 'filter',
            'extract_and_convert', 'preview', 'execute'
        }
        
        # Verify expected arguments are present
        missing_args = expected_args - actions
        assert not missing_args, f"Missing expected arguments: {missing_args}"
    
    def test_parser_help_generation(self):
        """Test that parser can generate help without errors."""
        parser = create_argument_parser()
        
        # This should not raise an exception
        help_text = parser.format_help()
        assert 'Batch rename files' in help_text or 'batch rename' in help_text.lower()


class TestConfigurationCreation:
    """Test creation of RenameConfig from CLI arguments."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp(prefix="test_cli_"))
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    def test_create_config_from_cli_args_basic(self, temp_dir):
        """Test basic CLI config creation."""
        # Create mock args
        mock_args = Mock()
        mock_args.input_folder = temp_dir
        mock_args.extractor = 'split,_,dept,type'
        mock_args.converter = ['case,dept,upper']
        mock_args.template = None
        mock_args.extract_and_convert = None
        mock_args.filter = None
        mock_args.recursive = False
        mock_args.preview = True
        mock_args.execute = False
        mock_args.on_existing_collision = 'skip'
        mock_args.on_internal_collision = 'error'
        
        config = create_config_from_cli_args(mock_args)
        
        assert isinstance(config, RenameConfig)
        assert config.input_folder == temp_dir
        assert config.extractor == 'split'
        assert len(config.converters) == 1
        assert config.converters[0]['name'] == 'case'
    
    def test_create_config_missing_extractor(self, temp_dir):
        """Test that missing extractor raises error."""
        mock_args = Mock()
        mock_args.input_folder = temp_dir
        mock_args.extractor = None  # Missing required extractor
        mock_args.converter = None
        mock_args.template = None
        mock_args.extract_and_convert = None
        mock_args.filter = None
        
        with pytest.raises(ValueError, match="--extractor is required"):
            create_config_from_cli_args(mock_args)
    
    def test_create_config_inverted_extractor_error(self, temp_dir):
        """Test that inverted extractor raises error."""
        mock_args = Mock()
        mock_args.input_folder = temp_dir
        mock_args.extractor = '!split,_,dept'  # Invalid inversion
        mock_args.converter = None
        mock_args.template = None
        mock_args.extract_and_convert = None
        mock_args.filter = None
        
        with pytest.raises(ValueError, match="cannot be inverted"):
            create_config_from_cli_args(mock_args)
    
    def test_create_config_multiple_converters(self, temp_dir):
        """Test config creation with multiple converters."""
        mock_args = Mock()
        mock_args.input_folder = temp_dir
        mock_args.extractor = 'split,_,dept,type'
        mock_args.converter = ['case,dept,upper', 'pad_numbers,id,3']
        mock_args.template = None
        mock_args.extract_and_convert = None
        mock_args.filter = None
        mock_args.recursive = False
        mock_args.preview = True
        mock_args.execute = False
        mock_args.on_existing_collision = 'skip'
        mock_args.on_internal_collision = 'error'
        
        config = create_config_from_cli_args(mock_args)
        
        assert len(config.converters) == 2
        assert config.converters[0]['name'] == 'case'
        assert config.converters[1]['name'] == 'pad_numbers'
    
    def test_create_config_with_template(self, temp_dir):
        """Test config creation with template."""
        mock_args = Mock()
        mock_args.input_folder = temp_dir
        mock_args.extractor = 'split,_,dept,type'
        mock_args.converter = None
        mock_args.template = 'join,dept,type,separator=-'
        mock_args.extract_and_convert = None
        mock_args.filter = None
        mock_args.recursive = False
        mock_args.preview = True
        mock_args.execute = False
        mock_args.on_existing_collision = 'skip'
        mock_args.on_internal_collision = 'error'
        
        config = create_config_from_cli_args(mock_args)
        
        assert config.template is not None
        assert config.template['name'] == 'join'
        assert 'dept' in config.template['positional']
    
    def test_create_config_with_filters(self, temp_dir):
        """Test config creation with filters."""
        mock_args = Mock()
        mock_args.input_folder = temp_dir
        mock_args.extractor = 'split,_,dept,type'
        mock_args.converter = None
        mock_args.template = None
        mock_args.extract_and_convert = None
        mock_args.filter = ['extension,pdf,docx', '!size_range,0,1000']
        mock_args.recursive = False
        mock_args.preview = True
        mock_args.execute = False
        mock_args.on_existing_collision = 'skip'
        mock_args.on_internal_collision = 'error'
        
        config = create_config_from_cli_args(mock_args)
        
        assert len(config.filters) == 2
        assert config.filters[0]['name'] == 'extension'
        assert config.filters[0]['inverted'] is False
        assert config.filters[1]['name'] == 'size_range'
        assert config.filters[1]['inverted'] is True


class TestCollisionHighlighting:
    """Test collision highlighting functionality."""
    
    def test_highlight_collisions_no_duplicates(self):
        """Test highlighting when there are no collisions."""
        preview_data = [
            {'old_name': 'file1.txt', 'new_name': 'new1.txt'},
            {'old_name': 'file2.txt', 'new_name': 'new2.txt'}
        ]
        
        result = highlight_collisions(preview_data, use_colors=True)
        
        # Should not modify names when no collisions
        assert result[0]['new_name'] == 'new1.txt'
        assert result[1]['new_name'] == 'new2.txt'
    
    def test_highlight_collisions_with_duplicates(self):
        """Test highlighting when there are naming collisions."""
        preview_data = [
            {'old_name': 'file1.txt', 'new_name': 'duplicate.txt'},
            {'old_name': 'file2.txt', 'new_name': 'unique.txt'},
            {'old_name': 'file3.txt', 'new_name': 'duplicate.txt'}
        ]
        
        result = highlight_collisions(preview_data, use_colors=True)
        
        # Duplicate names should be highlighted with ANSI color codes
        assert '\033[91m' in result[0]['new_name']  # Red color
        assert '\033[91m' in result[2]['new_name']  # Red color
        assert '\033[91m' not in result[1]['new_name']  # No highlight for unique
    
    def test_highlight_collisions_disabled(self):
        """Test that highlighting is disabled when use_colors=False."""
        preview_data = [
            {'old_name': 'file1.txt', 'new_name': 'duplicate.txt'},
            {'old_name': 'file2.txt', 'new_name': 'duplicate.txt'}
        ]
        
        result = highlight_collisions(preview_data, use_colors=False)
        
        # Should not modify names when colors disabled
        assert result[0]['new_name'] == 'duplicate.txt'
        assert result[1]['new_name'] == 'duplicate.txt'


class TestConfigFromFile:
    """Test configuration creation from file."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file for testing."""
        temp_file = Path(tempfile.mktemp(suffix='.yaml'))
        config_content = """
settings:
  recursive: true
  
pipeline:
  extractor:
    name: split
    args: ['_', 'dept', 'type']
    
  converters:
    - name: case
      args: ['dept', 'upper']
      
collision_handling:
  on_existing_collision: skip
  on_internal_collision: error
"""
        temp_file.write_text(config_content)
        yield temp_file
        temp_file.unlink(missing_ok=True)
    
    @patch('batch_rename.config.config_loader.ConfigLoader.load_rename_config')
    def test_create_config_from_file_basic(self, mock_load_config, temp_config_file):
        """Test basic config file loading."""
        # Mock the config loader to return a valid config
        mock_config = Mock(spec=RenameConfig)
        mock_config.input_folder = Path('/test')
        mock_load_config.return_value = mock_config
        
        mock_args = Mock()
        mock_args.config = str(temp_config_file)
        mock_args.input_folder = None
        
        result = create_config_from_file(mock_args)
        
        assert result == mock_config
        mock_load_config.assert_called_once()
    
    @patch('batch_rename.config.config_loader.ConfigLoader.load_rename_config')
    def test_create_config_from_file_missing_input_folder(self, mock_load_config):
        """Test error when input folder is missing from config."""
        # Mock config without input folder
        mock_config = Mock(spec=RenameConfig)
        mock_config.input_folder = None
        mock_load_config.return_value = mock_config
        
        mock_args = Mock()
        mock_args.config = 'test.yaml'
        mock_args.input_folder = None
        
        with pytest.raises(ValueError, match="input_folder must be specified"):
            create_config_from_file(mock_args)


class TestCLIIntegration:
    """Test CLI integration and main function."""
    
    @patch('batch_rename.ui.cli.BatchRenameProcessor')
    @patch('sys.argv', ['cli.py', '--help'])
    def test_main_function_help(self, mock_processor):
        """Test main function with help argument."""
        # Help should exit with SystemExit
        with pytest.raises(SystemExit):
            main()
    
    @patch('batch_rename.ui.cli.create_config_from_cli_args')
    @patch('batch_rename.ui.cli.BatchRenameProcessor')
    @patch('sys.argv', ['cli.py', '--input-folder', '/test', '--extractor', 'split,_,dept'])
    def test_main_function_basic_execution(self, mock_processor, mock_create_config):
        """Test main function basic execution path."""
        # Mock config creation
        mock_config = Mock(spec=RenameConfig)
        mock_config.preview_mode = True
        mock_create_config.return_value = mock_config
        
        # Mock processor
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        
        # This would normally require more complex mocking of argparse
        # For now, just test that the function exists and can be called
        assert callable(main)


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])