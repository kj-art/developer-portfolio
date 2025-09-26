# data_pipeline/tests/test_processing_config.py

import pytest
from unittest.mock import Mock

from data_pipeline.core.processing_config import ProcessingConfig, IndexMode


class TestProcessingConfig:
    """Test ProcessingConfig validation and creation"""
    
    def test_minimal_config(self):
        """Test config with minimal required parameters"""
        config = ProcessingConfig(input_folder="/test/folder")
        
        assert config.input_folder == "/test/folder"
        assert config.output_file is None
        assert config.recursive is False
        assert config.to_lower is True
        assert config.spaces_to_underscores is True
        assert config.force_in_memory is False
        assert isinstance(config.read_options, dict)
        assert isinstance(config.write_options, dict)
    
    def test_full_config(self):
        """Test config with all parameters specified"""
        read_opts = {'encoding': 'utf-8', 'sep': ';'}
        write_opts = {'na_rep': 'NULL', 'index': False}
        
        config = ProcessingConfig(
            input_folder="/test/folder",
            output_file="/test/output.csv",
            recursive=True,
            file_type_filter=['csv', 'xlsx'],
            to_lower=False,
            spaces_to_underscores=False,
            index_mode=IndexMode.SEQUENTIAL,
            index_start=100,
            columns=['col1', 'col2'],
            force_in_memory=True,
            read_options=read_opts,
            write_options=write_opts
        )
        
        assert config.input_folder == "/test/folder"
        assert config.output_file == "/test/output.csv"
        assert config.recursive is True
        assert config.file_type_filter == ['csv', 'xlsx']
        assert config.to_lower is False
        assert config.spaces_to_underscores is False
        assert config.index_mode == IndexMode.SEQUENTIAL
        assert config.index_start == 100
        assert config.columns == ['col1', 'col2']
        assert config.force_in_memory is True
        assert config.read_options == read_opts
        assert config.write_options == write_opts
    
    def test_missing_input_folder(self):
        """Test validation with missing input folder"""
        with pytest.raises(ValueError, match="input_folder is required"):
            ProcessingConfig(input_folder="")
    
    def test_string_filetype_conversion(self):
        """Test automatic conversion of string filetype to list"""
        config = ProcessingConfig(
            input_folder="/test",
            file_type_filter="csv"
        )
        
        assert config.file_type_filter == ['csv']
    
    def test_comma_separated_columns_conversion(self):
        """Test automatic conversion of comma-separated columns"""
        config = ProcessingConfig(
            input_folder="/test",
            columns="col1, col2 , col3"
        )
        
        assert config.columns == ['col1', 'col2', 'col3']
    
    def test_invalid_read_options_type(self):
        """Test validation of read_options type"""
        with pytest.raises(TypeError, match="read_options must be a dictionary"):
            ProcessingConfig(
                input_folder="/test",
                read_options="invalid"
            )
    
    def test_invalid_write_options_type(self):
        """Test validation of write_options type"""
        with pytest.raises(TypeError, match="write_options must be a dictionary"):
            ProcessingConfig(
                input_folder="/test",
                write_options=["invalid"]
            )
    
    def test_with_schema_map_immutable_update(self):
        """Test immutable schema map update"""
        original_config = ProcessingConfig(input_folder="/test")
        schema_map = {"name": ["full_name", "customer_name"]}
        
        new_config = original_config.with_schema_map(schema_map)
        
        # Original should be unchanged
        assert original_config.schema_map is None
        
        # New config should have schema
        assert new_config.schema_map == schema_map
        assert new_config.input_folder == "/test"  # Other fields preserved


class TestIndexMode:
    """Test IndexMode enum functionality"""
    
    def test_index_mode_values(self):
        """Test IndexMode enum values"""
        assert IndexMode.NONE.value == 'none'
        assert IndexMode.LOCAL.value == 'local'
        assert IndexMode.SEQUENTIAL.value == 'sequential'
    
    def test_from_string_valid(self):
        """Test IndexMode creation from valid strings"""
        assert IndexMode.from_string('none') == IndexMode.NONE
        assert IndexMode.from_string('local') == IndexMode.LOCAL
        assert IndexMode.from_string('sequential') == IndexMode.SEQUENTIAL
        
        # Test case insensitive
        assert IndexMode.from_string('NONE') == IndexMode.NONE
        assert IndexMode.from_string('Local') == IndexMode.LOCAL
        assert IndexMode.from_string('SEQUENTIAL') == IndexMode.SEQUENTIAL
    
    def test_from_string_empty(self):
        """Test IndexMode with empty string"""
        assert IndexMode.from_string('') is None
        assert IndexMode.from_string(None) is None
    
    def test_from_string_invalid(self):
        """Test IndexMode with invalid string"""
        with pytest.raises(ValueError, match="Invalid index mode"):
            IndexMode.from_string('invalid')


class TestProcessingConfigCLIIntegration:
    """Test ProcessingConfig creation from CLI arguments"""
    
    def test_from_cli_args_minimal(self):
        """Test CLI args conversion with minimal arguments"""
        mock_args = Mock()
        mock_args.input_folder = "/test/folder"
        mock_args.output_file = None
        mock_args.recursive = False
        mock_args.filetype = None
        mock_args.to_lower = True
        mock_args.spaces_to_underscores = True
        mock_args.index_mode = None  # Set to None instead of letting it be a Mock
        mock_args.index_start = 0
        mock_args.columns = None
        mock_args.force_in_memory = False
        
        config = ProcessingConfig.from_cli_args(mock_args)
        
        assert config.input_folder == "/test/folder"
        assert config.index_mode is None
    
    def test_from_cli_args_full(self):
        """Test CLI args conversion with all arguments"""
        mock_args = Mock()
        mock_args.input_folder = "/test/folder"
        mock_args.output_file = "/test/output.csv"
        mock_args.recursive = True
        mock_args.filetype = ['csv', 'xlsx']
        mock_args.to_lower = False
        mock_args.spaces_to_underscores = True
        mock_args.index_mode = "sequential"
        mock_args.index_start = 100
        mock_args.columns = "col1,col2,col3"
        mock_args.force_in_memory = True
        
        read_kwargs = {'encoding': 'utf-8'}
        write_kwargs = {'na_rep': 'NULL'}
        
        config = ProcessingConfig.from_cli_args(mock_args, read_kwargs, write_kwargs)
        
        assert config.input_folder == "/test/folder"
        assert config.output_file == "/test/output.csv"
        assert config.recursive is True
        assert config.file_type_filter == ['csv', 'xlsx']
        assert config.to_lower is False
        assert config.spaces_to_underscores is True
        assert config.index_mode == IndexMode.SEQUENTIAL
        assert config.index_start == 100
        assert config.columns == ["col1", "col2", "col3"]
        assert config.force_in_memory is True
        assert config.read_options == read_kwargs
        assert config.write_options == write_kwargs
    
    def test_from_cli_args_index_mode_conversion(self):
        """Test proper IndexMode conversion from CLI string"""
        mock_args = Mock()
        mock_args.input_folder = "/test"
        mock_args.index_mode = "local"
        
        # Set other defaults
        for attr in ['output_file', 'recursive', 'filetype', 'to_lower', 
                     'spaces_to_underscores', 'index_start', 'columns', 'force_in_memory']:
            setattr(mock_args, attr, None)
        
        config = ProcessingConfig.from_cli_args(mock_args)
        
        assert config.index_mode == IndexMode.LOCAL