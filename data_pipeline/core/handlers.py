import json
from abc import ABC, abstractmethod
from .utils import FileResult, merge_dataframes
import pandas as pd
import inspect

"""
File handlers for the data processing pipeline.

This module contains handler classes that handle different file formats. Each handler
is responsible for:
- Filtering kwargs to only those valid for its file type
- Reading the file using appropriate pandas/custom logic  
- Returning a consistent FileResult object

Handler classes follow a naming convention where the class name is the file extension
capitalized + "Handler" (e.g., 'csv' → CsvHandler, 'xlsx' → XlsxHandler). This allows
the DataProcessor to dynamically instantiate the correct handler based on file
extension without maintaining an explicit mapping.

Usage:
    handler = CsvHandler()
    result = handler.read('data.csv', sep=';', encoding='utf-8')

Adding New File Types:
    To support a new file format, create a new handler class following the naming
    convention (e.g., ParquetHandler for .parquet files) and implement the 
    FileHandler abstract base class methods.
"""

class FileHandler(ABC):
    """Abstract base class for file handlers"""

    def __init__(self):
        self._READ_KWARGS = self.get_read_kwargs()
        self._WRITE_KWARGS = self.get_write_kwargs()
    
    def get_function_name(self):
        """Override this if pandas function name differs from class name"""
        # Default: CsvHandler → read_csv, JsonHandler → read_json
        class_name = self.__class__.__name__.lower()
        return class_name.replace('handler', '')
    
    def get_read_function(self):
        return getattr(pd, f'read_{self.get_function_name()}')
    
    def get_write_function(self, dataframe):
        return getattr(dataframe, f'to_{self.get_function_name()}')
    
    def get_read_kwargs(self) -> set:
        sig = inspect.signature(self.get_read_function())
        return set(sig.parameters.keys())
    
    def get_write_kwargs(self) -> set:
        sig = inspect.signature(self.get_write_function(pd.DataFrame))
        return set(sig.parameters.keys()) - {'self'}  # Remove 'self' parameter

    @abstractmethod
    def read(self, file_path, **kwargs) -> FileResult:
        """Read file and return FileResult"""
        pass
    
    def write(self, dataframe, file_path, **kwargs) -> bool:
        """Default write implementation - works for most formats"""
        filtered_kwargs = self.filter_kwargs(kwargs, self._WRITE_KWARGS)
        self.get_write_function(dataframe)(file_path, **filtered_kwargs)

    def filter_kwargs(self, kwargs, valid_kwargs) -> dict:
        """Filter kwargs to only include valid ones for this handler"""
        return {k: v for k, v in kwargs.items() if k in valid_kwargs}
    
class CsvHandler(FileHandler):
    """Handler for CSV files"""
    
    def read(self, file_path, **kwargs) -> FileResult:
        """Read CSV file and return FileResult"""
        filtered_kwargs = self.filter_kwargs(kwargs, self._READ_KWARGS)
        df = pd.read_csv(file_path, **filtered_kwargs)
        return FileResult(dataframe=df, normalized=False)

class XlsxHandler(FileHandler):
    """Handler for Excel files"""

    def get_function_name(self):
        return 'excel'  # Override for pd.read_excel
    
    def read(self, file_path, **kwargs) -> FileResult:
        """Read Excel file and return FileResult with sheet_name handling"""
        filtered_kwargs = self.filter_kwargs(kwargs, self._READ_KWARGS)
        sheet_name = filtered_kwargs.pop('sheet_name', 0)
        
        if not isinstance(sheet_name, (int, str, list, type(None))):
            raise TypeError(
                f"sheet_name must be int (sheet index), str (sheet name), or None (all sheets). "
                f"Got {type(sheet_name).__name__}: {sheet_name}"
            )
        
        if sheet_name is None or isinstance(sheet_name, list):
            sheets_dict = pd.read_excel(file_path, sheet_name=sheet_name, **filtered_kwargs)
            merged_df = merge_dataframes(sheets_dict)
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
    
class JsonHandler(FileHandler):
    """Handler for JSON files"""

    def get_read_kwargs(self) -> set:
        return set(['encoding'])
    
    def read(self, file_path, **kwargs) -> FileResult:
        """Read JSON file and return FileResult, handling nested structures"""
        filtered_kwargs = self.filter_kwargs(kwargs, self._READ_KWARGS)
        
        with open(file_path, 'r', **filtered_kwargs) as f:
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
                merged_df = merge_dataframes(sheets_dict)
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