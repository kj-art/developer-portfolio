# data_pipeline/tests/test_handlers.py

import pytest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import json

from data_pipeline.core.handlers import CsvHandler, XlsxHandler, JsonHandler, get_handler_for_extension


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_csv_file(temp_dir):
    """Create sample CSV file"""
    csv_content = "Name,Age,City\nJohn Doe,25,New York\nJane Smith,30,Chicago\n"
    csv_file = temp_dir / "test.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def sample_excel_file(temp_dir):
    """Create sample Excel file"""
    df = pd.DataFrame({
        'Name': ['Alice Brown', 'Bob Wilson'],
        'Age': [28, 35],
        'City': ['Seattle', 'Boston']
    })
    excel_file = temp_dir / "test.xlsx"
    df.to_excel(excel_file, index=False)
    return excel_file


@pytest.fixture
def sample_json_file(temp_dir):
    """Create sample JSON file"""
    json_data = [
        {"name": "Charlie Davis", "age": 32, "city": "Denver"},
        {"name": "Diana Prince", "age": 29, "city": "Miami"}
    ]
    json_file = temp_dir / "test.json"
    json_file.write_text(json.dumps(json_data))
    return json_file


class TestCsvHandler:
    """Test CSV file handler"""
    
    def test_handler_properties(self):
        """Test basic handler properties"""
        handler = CsvHandler()
        
        assert handler.extension == "csv"
        assert handler.streamable is True
        assert handler.schema_sample_rows == 2
    
    def test_read_basic_csv(self, sample_csv_file):
        """Test reading basic CSV file"""
        handler = CsvHandler()
        chunks = list(handler.read(str(sample_csv_file)))
        
        assert len(chunks) == 1  # Small file should be one chunk
        df = chunks[0]
        
        assert len(df) == 2
        assert list(df.columns) == ['Name', 'Age', 'City']
        assert df.iloc[0]['Name'] == 'John Doe'
        assert df.iloc[1]['Age'] == 30
    
    def test_read_with_custom_separator(self, temp_dir):
        """Test reading CSV with custom separator"""
        csv_content = "Name;Age;City\nJohn;25;NYC\nJane;30;CHI\n"
        csv_file = temp_dir / "semicolon.csv"
        csv_file.write_text(csv_content)
        
        handler = CsvHandler()
        chunks = list(handler.read(str(csv_file), sep=';'))
        df = chunks[0]
        
        assert len(df) == 2
        assert df.iloc[0]['Name'] == 'John'
        assert df.iloc[0]['City'] == 'NYC'
    
    def test_read_with_custom_encoding(self, temp_dir):
        """Test reading CSV with custom encoding"""
        # Create file with special characters
        csv_content = "Name,City\nJosé,São Paulo\nBjörk,Reykjavík\n"
        csv_file = temp_dir / "encoded.csv"
        csv_file.write_bytes(csv_content.encode('utf-8'))
        
        handler = CsvHandler()
        chunks = list(handler.read(str(csv_file), encoding='utf-8'))
        df = chunks[0]
        
        assert len(df) == 2
        assert df.iloc[0]['Name'] == 'José'
        assert df.iloc[1]['City'] == 'Reykjavík'
    
    def test_read_chunked(self, temp_dir):
        """Test chunked reading of large CSV"""
        # Create larger CSV
        rows = []
        for i in range(10):
            rows.append(f"Person{i},{20+i},City{i}")
        
        csv_content = "Name,Age,City\n" + "\n".join(rows)
        csv_file = temp_dir / "large.csv"
        csv_file.write_text(csv_content)
        
        handler = CsvHandler()
        chunks = list(handler.read(str(csv_file), chunk_size=3))
        
        # Should have multiple chunks
        assert len(chunks) > 1
        
        # Verify total rows
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == 10
    
    def test_filter_kwargs(self):
        """Test kwargs filtering for CSV handler"""
        handler = CsvHandler()
        
        # Test read kwargs filtering
        kwargs = {'sep': ',', 'encoding': 'utf-8', 'invalid_param': 'test'}
        filtered = handler.filter_kwargs(kwargs, mode='read')
        
        assert 'sep' in filtered
        assert 'encoding' in filtered
        assert 'invalid_param' not in filtered
        
        # Test write kwargs filtering
        write_kwargs = {'sep': ';', 'na_rep': 'NULL', 'invalid_param': 'test'}
        filtered_write = handler.filter_kwargs(write_kwargs, mode='write')
        
        assert 'sep' in filtered_write
        assert 'na_rep' in filtered_write
        assert 'invalid_param' not in filtered_write
    
    def test_write_csv(self, temp_dir):
        """Test writing CSV file"""
        df = pd.DataFrame({
            'Name': ['Test User'],
            'Age': [25],
            'City': ['Test City']
        })
        
        output_file = temp_dir / "output.csv"
        handler = CsvHandler()
        handler.write(df, str(output_file), index=False)  # Explicitly disable index
        
        assert output_file.exists()
        
        # Verify content
        written_df = pd.read_csv(output_file)
        pd.testing.assert_frame_equal(df, written_df)


class TestXlsxHandler:
    """Test Excel file handler"""
    
    def test_handler_properties(self):
        """Test basic handler properties"""
        handler = XlsxHandler()
        
        assert handler.extension == "xlsx"
        assert handler.streamable is False
        assert handler.schema_sample_rows == 5
    
    def test_read_basic_excel(self, sample_excel_file):
        """Test reading basic Excel file"""
        handler = XlsxHandler()
        chunks = list(handler.read(str(sample_excel_file)))
        
        assert len(chunks) == 1
        df = chunks[0]
        
        assert len(df) == 2
        # Excel handler adds sheet_name column
        expected_cols = ['Name', 'Age', 'City', 'sheet_name']
        assert list(df.columns) == expected_cols
        assert df.iloc[0]['Name'] == 'Alice Brown'
        assert df.iloc[0]['sheet_name'] == 'Sheet1'  # Default sheet name
    
    def test_read_specific_sheet_by_index(self, temp_dir):
        """Test reading specific sheet by index"""
        # Create multi-sheet Excel file
        with pd.ExcelWriter(temp_dir / "multi_sheet.xlsx") as writer:
            pd.DataFrame({'col1': [1, 2]}).to_excel(writer, sheet_name='Sheet1', index=False)
            pd.DataFrame({'col2': [3, 4]}).to_excel(writer, sheet_name='Sheet2', index=False)
        
        handler = XlsxHandler()
        chunks = list(handler.read(str(temp_dir / "multi_sheet.xlsx"), sheet_name=1))
        df = chunks[0]
        
        assert 'col2' in df.columns
        assert df.iloc[0]['col2'] == 3
        assert df.iloc[0]['sheet_name'] == 'Sheet2'
    
    def test_read_specific_sheet_by_name(self, temp_dir):
        """Test reading specific sheet by name"""
        with pd.ExcelWriter(temp_dir / "named_sheet.xlsx") as writer:
            pd.DataFrame({'data': [1, 2]}).to_excel(writer, sheet_name='DataSheet', index=False)
        
        handler = XlsxHandler()
        chunks = list(handler.read(str(temp_dir / "named_sheet.xlsx"), sheet_name='DataSheet'))
        df = chunks[0]
        
        assert 'data' in df.columns
        assert df.iloc[0]['sheet_name'] == 'DataSheet'
    
    def test_read_all_sheets(self, temp_dir):
        """Test reading all sheets (sheet_name=None)"""
        with pd.ExcelWriter(temp_dir / "all_sheets.xlsx") as writer:
            pd.DataFrame({'col1': [1, 2]}).to_excel(writer, sheet_name='First', index=False)
            pd.DataFrame({'col2': [3, 4]}).to_excel(writer, sheet_name='Second', index=False)
        
        handler = XlsxHandler()
        chunks = list(handler.read(str(temp_dir / "all_sheets.xlsx"), sheet_name=None))
        df = chunks[0]
        
        # Should merge sheets and add sheet_name column
        assert len(df) == 4  # 2 rows from each sheet
        assert 'sheet_name' in df.columns
        sheet_names = df['sheet_name'].unique()
        assert 'First' in sheet_names
        assert 'Second' in sheet_names
    
    def test_invalid_sheet_name_type(self, sample_excel_file):
        """Test error handling for invalid sheet_name type"""
        handler = XlsxHandler()
        
        with pytest.raises(TypeError, match="sheet_name must be int"):
            list(handler.read(str(sample_excel_file), sheet_name={'invalid': 'type'}))
    
    def test_write_excel(self, temp_dir):
        """Test writing Excel file"""
        df = pd.DataFrame({
            'Name': ['Test User'],
            'Value': [42]
        })
        
        output_file = temp_dir / "output.xlsx"
        handler = XlsxHandler()
        handler.write(df, str(output_file), index=False)  # Explicitly disable index
        
        assert output_file.exists()
        
        # Verify content
        written_df = pd.read_excel(output_file)
        pd.testing.assert_frame_equal(df, written_df)


class TestJsonHandler:
    """Test JSON file handler"""
    
    def test_handler_properties(self):
        """Test basic handler properties"""
        handler = JsonHandler()
        
        assert handler.extension == "json"
        assert handler.streamable is False
        assert handler.schema_sample_rows is None  # JSON doesn't use sampling
    
    def test_read_simple_json_array(self, sample_json_file):
        """Test reading simple JSON array"""
        handler = JsonHandler()
        chunks = list(handler.read(str(sample_json_file)))
        
        assert len(chunks) == 1
        df = chunks[0]
        
        assert len(df) == 2
        assert list(df.columns) == ['name', 'age', 'city']
        assert df.iloc[0]['name'] == 'Charlie Davis'
    
    def test_read_nested_json(self, temp_dir):
        """Test reading nested JSON structure"""
        nested_data = {
            "employees": [
                {
                    "name": "John",
                    "details": {"age": 30, "city": "NYC"}
                },
                {
                    "name": "Jane", 
                    "details": {"age": 25, "city": "LA"}
                }
            ]
        }
        
        json_file = temp_dir / "nested.json"
        json_file.write_text(json.dumps(nested_data))
        
        handler = JsonHandler()
        chunks = list(handler.read(str(json_file)))
        df = chunks[0]
        
        # Should flatten nested structure and column normalization occurs
        assert 'first_name' in df.columns  # name gets split
        assert 'age' in df.columns         # Flattened from details
        assert 'city' in df.columns        # Flattened from details
        assert 'sheet_name' in df.columns  # Should add sheet name (key)
        assert len(df) == 2
    
    def test_read_multiple_arrays(self, temp_dir):
        """Test reading JSON with multiple arrays"""
        multi_data = {
            "customers": [
                {"name": "Customer1", "type": "individual"}
            ],
            "companies": [
                {"name": "Company1", "type": "business"}
            ]
        }
        
        json_file = temp_dir / "multi.json"
        json_file.write_text(json.dumps(multi_data))
        
        handler = JsonHandler()
        chunks = list(handler.read(str(json_file)))
        df = chunks[0]
        
        # Should merge arrays with sheet_name indicating source
        assert len(df) == 2
        assert 'sheet_name' in df.columns
        sheet_names = df['sheet_name'].unique()
        assert 'customers' in sheet_names
        assert 'companies' in sheet_names
    
    def test_read_invalid_json_structure(self, temp_dir):
        """Test error handling for invalid JSON structure"""
        # JSON that's not a list or dict with arrays
        invalid_data = "just a string"
        
        json_file = temp_dir / "invalid.json"
        json_file.write_text(json.dumps(invalid_data))
        
        handler = JsonHandler()
        
        with pytest.raises(ValueError, match="Unsupported JSON root type"):
            list(handler.read(str(json_file)))
    
    def test_read_dict_without_arrays(self, temp_dir):
        """Test error handling for dict without array values"""
        data = {
            "config": {"setting1": "value1"},
            "metadata": "some string"
        }
        
        json_file = temp_dir / "no_arrays.json"
        json_file.write_text(json.dumps(data))
        
        handler = JsonHandler()
        
        with pytest.raises(ValueError, match="No array data found"):
            list(handler.read(str(json_file)))
    
    def test_flatten_record(self):
        """Test record flattening functionality"""
        handler = JsonHandler()
        
        record = {
            "name": "John",
            "address": {
                "street": "123 Main St",
                "city": "Anytown"
            },
            "age": 30
        }
        
        flattened = handler._flatten_record(record)
        
        assert flattened['name'] == 'John'
        assert flattened['age'] == 30
        assert flattened['street'] == '123 Main St'  # From nested dict
        assert flattened['city'] == 'Anytown'       # From nested dict
        assert 'address' not in flattened           # Nested dict should be gone
    
    def test_read_with_encoding(self, temp_dir):
        """Test reading JSON with specific encoding"""
        data = [{"name": "José", "city": "São Paulo"}]
        
        json_file = temp_dir / "encoded.json"
        json_file.write_bytes(json.dumps(data).encode('utf-8'))
        
        handler = JsonHandler()
        chunks = list(handler.read(str(json_file), encoding='utf-8'))
        df = chunks[0]
        
        assert df.iloc[0]['name'] == 'José'
        assert df.iloc[0]['city'] == 'São Paulo'


class TestHandlerFactory:
    """Test handler factory function"""
    
    def test_get_handler_for_csv(self):
        """Test getting CSV handler"""
        handler = get_handler_for_extension('csv')
        assert isinstance(handler, CsvHandler)
    
    def test_get_handler_for_xlsx(self):
        """Test getting Excel handler"""
        handler = get_handler_for_extension('xlsx')
        assert isinstance(handler, XlsxHandler)
    
    def test_get_handler_for_json(self):
        """Test getting JSON handler"""
        handler = get_handler_for_extension('json')
        assert isinstance(handler, JsonHandler)
    
    def test_get_handler_case_insensitive(self):
        """Test case insensitive handler lookup"""
        handler_upper = get_handler_for_extension('CSV')
        handler_mixed = get_handler_for_extension('XlSx')
        
        assert isinstance(handler_upper, CsvHandler)
        assert isinstance(handler_mixed, XlsxHandler)
    
    def test_get_handler_unsupported_extension(self):
        """Test error for unsupported extension"""
        with pytest.raises(ValueError, match="Unsupported file format: .pdf"):
            get_handler_for_extension('pdf')
    
    def test_get_handler_empty_extension(self):
        """Test error for empty extension"""
        with pytest.raises(ValueError, match="Unsupported file format"):
            get_handler_for_extension('')


class TestHandlerIntegration:
    """Test handler integration scenarios"""
    
    def test_round_trip_csv(self, temp_dir):
        """Test writing and reading back CSV"""
        original_df = pd.DataFrame({
            'name': ['Alice', 'Bob'],
            'value': [1.5, 2.7],
            'active': [True, False]
        })
        
        csv_file = temp_dir / "round_trip.csv"
        
        # Write
        handler = CsvHandler()
        handler.write(original_df, str(csv_file), index=False)
        
        # Read back
        chunks = list(handler.read(str(csv_file)))
        read_df = chunks[0]
        
        # Should preserve data (though types might change)
        assert len(read_df) == len(original_df)
        assert list(read_df.columns) == list(original_df.columns)
        assert read_df.iloc[0]['name'] == 'Alice'
    
    def test_round_trip_excel(self, temp_dir):
        """Test writing and reading back Excel"""
        original_df = pd.DataFrame({
            'text': ['Hello', 'World'],
            'number': [42, 84],
            'decimal': [3.14, 2.71]
        })
        
        excel_file = temp_dir / "round_trip.xlsx"
        
        # Write
        handler = XlsxHandler()
        handler.write(original_df, str(excel_file), index=False)
        
        # Read back
        chunks = list(handler.read(str(excel_file)))
        read_df = chunks[0]
        
        # Remove added sheet_name column for comparison
        read_df = read_df.drop('sheet_name', axis=1)
        
        # Should preserve data types better than CSV
        pd.testing.assert_frame_equal(original_df, read_df, check_dtype=False)
    
    def test_handler_kwargs_isolation(self):
        """Test that handlers don't interfere with each other's kwargs"""
        csv_handler = CsvHandler()
        xlsx_handler = XlsxHandler()
        
        # CSV should accept 'sep' but not 'sheet_name'
        csv_kwargs = csv_handler.filter_kwargs({'sep': ';', 'sheet_name': 'test'}, 'read')
        assert 'sep' in csv_kwargs
        assert 'sheet_name' not in csv_kwargs
        
        # Excel should accept 'sheet_name' but not 'sep'
        xlsx_kwargs = xlsx_handler.filter_kwargs({'sep': ';', 'sheet_name': 'test'}, 'read')
        assert 'sheet_name' in xlsx_kwargs
        assert 'sep' not in xlsx_kwargs