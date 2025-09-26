# data_pipeline/tests/test_schema_detector.py

import pytest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import json

from data_pipeline.core.services.schema_detector import SchemaDetector
from data_pipeline.core.processing_config import ProcessingConfig


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def schema_detector():
    """Create SchemaDetector instance"""
    return SchemaDetector()


@pytest.fixture
def mixed_schema_files(temp_dir):
    """Create files with different but compatible schemas"""
    # File 1: Basic customer data
    df1 = pd.DataFrame({
        'Customer Name': ['John Doe', 'Jane Smith'],
        'Age': [25, 30],
        'City': ['New York', 'Chicago'],
        'Email': ['john@email.com', 'jane@email.com']
    })
    file1 = temp_dir / "customers1.csv"
    df1.to_csv(file1, index=False)
    
    # File 2: Similar data with different column names
    df2 = pd.DataFrame({
        'Full Name': ['Bob Wilson', 'Alice Brown'],
        'Years': [35, 28],
        'Location': ['Boston', 'Seattle'],
        'Email Address': ['bob@email.com', 'alice@email.com']
    })
    file2 = temp_dir / "customers2.xlsx"
    df2.to_excel(file2, index=False)
    
    # File 3: JSON with nested structure
    json_data = [
        {
            "name": "Charlie Davis",
            "personal_info": {"age": 32, "city": "Denver"},
            "contact": {"email": "charlie@email.com"}
        }
    ]
    file3 = temp_dir / "customers3.json"
    file3.write_text(json.dumps(json_data))
    
    return {
        'file1': file1,
        'file2': file2,
        'file3': file3,
        'expected_columns': ['customer_name', 'age', 'city', 'email']
    }


@pytest.fixture
def conflicting_types_files(temp_dir):
    """Create files with conflicting data types"""
    # File 1: ID as integer
    df1 = pd.DataFrame({
        'ID': [1, 2, 3],
        'Value': [10.5, 20.1, 30.7]
    })
    file1 = temp_dir / "data1.csv"
    df1.to_csv(file1, index=False)
    
    # File 2: ID as string
    df2 = pd.DataFrame({
        'ID': ['A001', 'B002', 'C003'],
        'Value': [15, 25, 35]  # Integer values
    })
    file2 = temp_dir / "data2.csv"
    df2.to_csv(file2, index=False)
    
    return {'file1': file1, 'file2': file2}


class TestSchemaDetector:
    """Test SchemaDetector functionality"""
    
    def test_detect_schema_from_predefined_columns(self, schema_detector, temp_dir):
        """Test schema building from predefined columns"""
        config = ProcessingConfig(
            input_folder=str(temp_dir),
            columns=['id', 'name', 'email', 'created_date']
        )
        
        schema = schema_detector.detect_schema(config)
        
        assert isinstance(schema, dict)
        assert 'id' in schema
        assert 'name' in schema
        assert 'email' in schema
        assert 'created_date' in schema
        assert 'source_file' in schema  # Always added
        
        # Should default to object type
        assert schema['name'] == 'object'
    
    def test_detect_schema_from_files(self, schema_detector, mixed_schema_files, temp_dir):
        """Test schema detection from actual files"""
        config = ProcessingConfig(
            input_folder=str(temp_dir),
            to_lower=True,
            spaces_to_underscores=True
        )
        
        schema = schema_detector.detect_schema(config)
        
        assert isinstance(schema, dict)
        assert len(schema) > 0
        assert 'source_file' in schema
        
        # Should have normalized column names
        column_names = list(schema.keys())
        assert all('_' in name or name == 'source_file' or name.islower() for name in column_names)
    
    def test_schema_type_merging(self, schema_detector, conflicting_types_files, temp_dir):
        """Test type merging with conflicting data types"""
        config = ProcessingConfig(
            input_folder=str(temp_dir),
            file_type_filter=['csv']
        )
        
        schema = schema_detector.detect_schema(config)
        
        # ID column should be promoted to object (most permissive)
        assert schema['id'] == 'object'
        
        # Value column should be float64 (more permissive than int64)
        assert schema['value'] == 'float64'
    
    def test_empty_folder_handling(self, schema_detector, temp_dir):
        """Test behavior with empty folder"""
        config = ProcessingConfig(input_folder=str(temp_dir))
        
        with pytest.raises(ValueError, match="No valid files found"):
            schema_detector.detect_schema(config)
    
    def test_file_type_filtering(self, schema_detector, mixed_schema_files, temp_dir):
        """Test schema detection with file type filtering"""
        config = ProcessingConfig(
            input_folder=str(temp_dir),
            file_type_filter=['csv']  # Only CSV files
        )
        
        schema = schema_detector.detect_schema(config)
        
        # Should only detect schema from CSV files
        assert isinstance(schema, dict)
        assert len(schema) > 0
    
    def test_custom_schema_map_integration(self, schema_detector, temp_dir):
        """Test integration with custom schema mapping"""
        # Create a simple test file
        df = pd.DataFrame({
            'Customer Name': ['John', 'Jane'],
            'Email Address': ['john@test.com', 'jane@test.com']
        })
        test_file = temp_dir / "test.csv"
        df.to_csv(test_file, index=False)
        
        schema_map = {
            'name': ['Customer Name', 'Full Name'],
            'email': ['Email Address', 'Email', 'Contact Email']
        }
        
        config = ProcessingConfig(
            input_folder=str(temp_dir),
            schema_map=schema_map
        )
        
        schema = schema_detector.detect_schema(config)
        
        # Should have mapped column names (name gets split into first_name/last_name)
        assert 'first_name' in schema
        assert 'email' in schema
    
    def test_sampling_rows_parameter(self, schema_detector, temp_dir):
        """Test custom sampling row count"""
        # Create file with many rows
        large_df = pd.DataFrame({
            'col1': range(1000),
            'col2': [f'value_{i}' for i in range(1000)]
        })
        test_file = temp_dir / "large.csv"
        large_df.to_csv(test_file, index=False)
        
        config = ProcessingConfig(input_folder=str(temp_dir))
        
        # Should work with small sample size
        schema = schema_detector.detect_schema(config, sample_rows=50)
        
        assert 'col1' in schema
        assert 'col2' in schema
    
    def test_malformed_file_handling(self, schema_detector, temp_dir):
        """Test handling of malformed files during schema detection"""
        # Create a malformed CSV
        malformed_file = temp_dir / "bad.csv"
        malformed_file.write_text("This is not a valid CSV\nwith proper structure")
        
        # Create a good file
        good_df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        good_file = temp_dir / "good.csv"
        good_df.to_csv(good_file, index=False)
        
        config = ProcessingConfig(input_folder=str(temp_dir))
        
        # Should detect schema from good file and skip bad one
        schema = schema_detector.detect_schema(config)
        
        assert 'col1' in schema
        assert 'col2' in schema


class TestSchemaDetectorInternals:
    """Test internal methods of SchemaDetector"""
    
    def test_build_schema_from_columns(self, schema_detector):
        """Test _build_schema_from_columns method"""
        columns = ['id', 'name', 'email']
        schema_map = {'name': 'string', 'id': 'int64'}
        
        schema = schema_detector._build_schema_from_columns(columns, schema_map)
        
        assert schema['id'] == 'int64'  # From schema map
        assert schema['name'] == 'string'  # From schema map
        assert schema['email'] == 'object'  # Default
        assert 'source_file' in schema
    
    def test_merge_schema_type_promotion(self, schema_detector):
        """Test _merge_schema method with type promotion"""
        main_schema = {'col1': 'int64', 'col2': 'object'}
        file_schema = {'col1': 'float64', 'col3': 'bool'}
        
        schema_detector._merge_schema(main_schema, file_schema)
        
        # Type should be promoted to float64
        assert main_schema['col1'] == 'float64'
        
        # New column should be added
        assert main_schema['col3'] == 'bool'
        
        # Existing column unchanged
        assert main_schema['col2'] == 'object'