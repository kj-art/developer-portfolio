import json
from abc import ABC, abstractmethod
from .types import FileResult
import pandas as pd
import inspect

"""
File readers for the data processing pipeline.

This module contains reader classes that handle different file formats. Each reader
is responsible for:
- Filtering kwargs to only those valid for its file type
- Reading the file using appropriate pandas/custom logic  
- Returning a consistent FileResult object

Reader classes follow a naming convention where the class name is the file extension
capitalized + "Reader" (e.g., 'csv' → CsvReader, 'xlsx' → XlsxReader). This allows
the DataProcessor to dynamically instantiate the correct reader based on file
extension without maintaining an explicit mapping.

Usage:
    reader = CsvReader()
    result = reader.read('data.csv', sep=';', encoding='utf-8')

Adding New File Types:
    To support a new file format, create a new reader class following the naming
    convention (e.g., ParquetReader for .parquet files) and implement the 
    FileReader abstract base class methods.
"""

class FileReader(ABC):
    """Abstract base class for file readers"""

    def __init__(self):
        self._VALID_KWARGS = self.get_valid_kwargs()
    
    def get_pandas_function_name(self):
        """Override this if pandas function name differs from class name"""
        # Default: CsvReader → read_csv, JsonReader → read_json
        class_name = self.__class__.__name__.lower()
        return class_name.replace('reader', '')
    
    def get_valid_kwargs(self) -> set:
        func_name = self.get_pandas_function_name()
        pandas_func = getattr(pd, f'read_{func_name}')
        sig = inspect.signature(pandas_func)
        return set(sig.parameters.keys())

    @abstractmethod
    def read(self, file_path, **kwargs) -> FileResult:
        """Read file and return FileResult"""
        pass
    
    def filter_kwargs(self, kwargs) -> dict:
        """Filter kwargs to only include valid ones for this reader"""
        return {k: v for k, v in kwargs.items() if k in self._VALID_KWARGS}
    
    def _merge_sheets(self, sheets_dict):
        """Merge dictionary of DataFrames into single DataFrame"""
        normalized_sheets = []
        for sheet_name, df in sheets_dict.items():
            df['sheet_name'] = sheet_name
            normalized_sheets.append(df)
        
        if not normalized_sheets:
            return pd.DataFrame()
        return pd.concat(normalized_sheets, ignore_index=True)

class CsvReader(FileReader):
    """Reader for CSV files"""
    
    def get_valid_kwargs(self) -> list:
        return ['sep', 'encoding', 'header', 'skiprows']
    
    def read(self, file_path, **kwargs) -> FileResult:
        """Read CSV file and return FileResult"""
        filtered_kwargs = self.filter_kwargs(kwargs)
        df = pd.read_csv(file_path, **filtered_kwargs)
        return FileResult(dataframe=df, normalized=False)

class XlsxReader(FileReader):
    """Reader for Excel files"""

    def get_pandas_function_name(self):
        return 'excel'  # Override for pd.read_excel
    
    def read(self, file_path, **kwargs) -> FileResult:
        """Read Excel file and return FileResult with sheet_name handling"""
        filtered_kwargs = self.filter_kwargs(kwargs)
        sheet_name = filtered_kwargs.pop('sheet_name', 0)
        
        if not isinstance(sheet_name, (int, str, list, type(None))):
            raise TypeError(
                f"sheet_name must be int (sheet index), str (sheet name), or None (all sheets). "
                f"Got {type(sheet_name).__name__}: {sheet_name}"
            )
        
        if sheet_name is None or isinstance(sheet_name, list):
            sheets_dict = pd.read_excel(file_path, sheet_name=sheet_name, **filtered_kwargs)
            merged_df = self._merge_sheets(sheets_dict)
            return FileResult(dataframe=merged_df, normalized=True)
        elif isinstance(sheet_name, int):
            excel_file = pd.ExcelFile(file_path)
            actual_sheet_name = excel_file.sheet_names[sheet_name]
            df = pd.read_excel(excel_file, sheet_name=sheet_name, **filtered_kwargs)
            excel_file.close()
            df['sheet_name'] = actual_sheet_name
            return FileResult(dataframe=df, normalized=False)
        else:  # str
            df = pd.read_excel(file_path, sheet_name=sheet_name, **filtered_kwargs)
            df['sheet_name'] = sheet_name
            return FileResult(dataframe=df, normalized=False)
    
class JsonReader(FileReader):
    """Reader for JSON files"""
    
    def read(self, file_path, **kwargs) -> FileResult:
        """Read JSON file and return FileResult, handling nested structures"""
        filtered_kwargs = self.filter_kwargs(kwargs)
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            # Simple flat JSON array - direct pandas handling
            df = pd.DataFrame(data)
            return FileResult(dataframe=df, normalized=False)
        elif isinstance(data, dict):
            # Nested JSON - treat keys as sheet names
            sheets_dict = {}
            for key, value in data.items():
                if isinstance(value, list):
                    # Flatten each record in the array
                    flattened_records = []
                    for record in value:
                        flat_record = self._flatten_record(record)
                        flattened_records.append(flat_record)
                    
                    sheets_dict[key] = pd.DataFrame(flattened_records)
            
            if sheets_dict:
                merged_df = self._merge_sheets(sheets_dict)
                return FileResult(dataframe=merged_df, normalized=True)
            else:
                raise ValueError(f"No array data found in nested JSON: {file_path}")
        else:
            raise ValueError(f"Unsupported JSON root type: {type(data).__name__}. Expected dict or list.")
    
    def _flatten_record(self, record):
        """Flatten nested dictionaries one level deep"""
        flattened = {}
        for key, value in record.items():
            if isinstance(value, dict):
                # Spread the nested dict into the parent
                flattened.update(value)
            else:
                flattened[key] = value
        return flattened