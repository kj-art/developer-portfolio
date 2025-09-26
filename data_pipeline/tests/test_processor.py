# data_pipeline/tests/test_processor.py

import pytest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import json
from unittest.mock import Mock, patch

from data_pipeline.core.processor import DataProcessor
from data_pipeline.core.processing_config import ProcessingConfig, IndexMode
from data_pipeline.core.dataframe_utils import ProcessingResult


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing"""
    return [
        "Name,Age,City\n",
        "John Doe,25,New York\n",
        "Jane Smith,30,Chicago\n",
        "Bob Johnson,35,Boston\n"
    ]


@pytest.fixture
def sample_excel_data():
    """Sample Excel data as DataFrame"""
    return pd.DataFrame({
        'Full Name': ['Alice Brown', 'Charlie Wilson'],
        'Years': [28, 45],
        'Location': ['Seattle', 'Denver']
    })


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing"""
    return [
        {"employee_name": "David Lee", "age": 32, "department": "Engineering"},
        {"employee_name": "Sarah Connor", "age": 29, "department": "Marketing"}
    ]


@pytest.fixture
def create_test_files(temp_dir, sample_csv_data, sample_excel_data, sample_json_data):
    """Create test files in temporary directory"""
    # Create CSV file
    csv_file = temp_dir / "test1.csv"
    csv_file.write_text(''.join(sample_csv_data))
    
    # Create Excel file
    excel_file = temp_dir / "test2.xlsx"
    sample_excel_data.to_excel(excel_file, index=False)
    
    # Create JSON file
    json_file = temp_dir / "test3.json"
    json_file.write_text(json.dumps(sample_json_data))
    
    # Create subdirectory with another file
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    csv_file2 = subdir / "test4.csv"
    csv_file2.write_text("ID,Value\n1,A\n2,B\n")
    
    return {
        'csv_file': csv_file,
        'excel_file': excel_file,
        'json_file': json_file,
        'csv_file2': csv_file2,
        'subdir': subdir
    }


class TestDataProcessor:
    """Test the main DataProcessor class"""
    
    def test_processor_initialization(self):
        """Test processor creates with default options"""
        processor = DataProcessor()
        assert processor is not None
        assert isinstance(processor._read_options, dict)
        assert isinstance(processor._write_options, dict)
    
    def test_processor_with_custom_options(self):
        """Test processor with custom read/write options"""
        read_opts = {'encoding': 'utf-8', 'sep': ';'}
        write_opts = {'na_rep': 'NULL'}
        
        processor = DataProcessor(read_kwargs=read_opts, write_kwargs=write_opts)
        assert processor._read_options == read_opts
        assert processor._write_options == write_opts
    
    def test_basic_processing_csv_output(self, create_test_files, temp_dir):
        """Test basic processing with CSV output (streaming)"""
        output_file = temp_dir / "output.csv"
        
        config = ProcessingConfig(
            input_folder=str(temp_dir),
            output_file=str(output_file),
            recursive=False
        )
        
        processor = DataProcessor()
        result = processor.run(config)
        
        # Check result
        assert isinstance(result, ProcessingResult)
        assert result.files_processed > 0
        assert result.total_rows > 0
        assert result.processing_time > 0
        assert output_file.exists()
        
        # Check output content
        output_df = pd.read_csv(output_file)
        assert len(output_df) > 0
        assert 'source_file' in output_df.columns
    
    def test_basic_processing_excel_output(self, create_test_files, temp_dir):
        """Test basic processing with Excel output (in-memory)"""
        output_file = temp_dir / "output.xlsx"
        
        config = ProcessingConfig(
            input_folder=str(temp_dir),
            output_file=str(output_file),
            recursive=False
        )
        
        processor = DataProcessor()
        result = processor.run(config)
        
        # Check result
        assert result.files_processed > 0
        assert output_file.exists()
        assert result.data is not None  # In-memory should return data
        
        # Check output content
        output_df = pd.read_excel(output_file)
        assert len(output_df) > 0
    
    def test_recursive_processing(self, create_test_files, temp_dir):
        """Test recursive file discovery"""
        output_file = temp_dir / "output.csv"
        
        config = ProcessingConfig(
            input_folder=str(temp_dir),
            output_file=str(output_file),
            recursive=True
        )
        
        processor = DataProcessor()
        result = processor.run(config)
        
        # Should find files in subdirectories
        assert result.files_processed >= 2  # At least main dir + subdir files
        
        # Check subdirectory file is included
        output_df = pd.read_csv(output_file)
        source_files = output_df['source_file'].unique()
        assert any('subdir' in str(f) for f in source_files)
    
    def test_file_type_filtering(self, create_test_files, temp_dir):
        """Test file type filtering"""
        output_file = temp_dir / "output.csv"
        
        config = ProcessingConfig(
            input_folder=str(temp_dir),
            output_file=str(output_file),
            file_type_filter=['csv'],  # Only CSV files
            recursive=True
        )
        
        processor = DataProcessor()
        result = processor.run(config)
        
        # Should only process CSV files
        output_df = pd.read_csv(output_file)
        source_files = output_df['source_file'].unique()
        assert all(str(f).endswith('.csv') for f in source_files)
    
    def test_force_in_memory_processing(self, create_test_files, temp_dir):
        """Test forcing in-memory processing for CSV output"""
        output_file = temp_dir / "output.csv"
        
        config = ProcessingConfig(
            input_folder=str(temp_dir),
            output_file=str(output_file),
            force_in_memory=True
        )
        
        processor = DataProcessor()
        result = processor.run(config)
        
        # Should have data available (in-memory characteristic)
        assert result.data is not None
        assert len(result.data) > 0
    
    def test_console_output(self, create_test_files, temp_dir, capsys):
        """Test console output mode"""
        config = ProcessingConfig(
            input_folder=str(temp_dir),
            output_file=None,  # Console output
            recursive=False
        )
        
        processor = DataProcessor()
        result = processor.run(config)
        
        # Should have processed files but no output file
        assert result.files_processed > 0
        assert result.output_file is None
        
        # Should have printed to console
        captured = capsys.readouterr()
        assert len(captured.out) > 0
    
    def test_invalid_input_folder(self):
        """Test handling of invalid input folder"""
        config = ProcessingConfig(
            input_folder="./definitely_nonexistent_test_folder_12345",
            output_file="output.csv"
        )
        
        processor = DataProcessor()
        
        # The processor should raise FileNotFoundError for invalid paths
        # This is correct behavior - fail fast for invalid input
        with pytest.raises(FileNotFoundError):
            result = processor.run(config)
    
    def test_get_available_strategies(self):
        """Test strategy enumeration"""
        processor = DataProcessor()
        strategies = processor.get_available_strategies()
        
        assert isinstance(strategies, list)
        assert "streaming" in strategies
        assert "in_memory" in strategies
    
    def test_get_service_status(self):
        """Test service status reporting"""
        processor = DataProcessor()
        status = processor.get_service_status()
        
        assert isinstance(status, dict)
        assert "schema_detector" in status
        assert "file_processor" in status
        assert "output_writer" in status