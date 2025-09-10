from .dataframe_utils import FileResult, merge_dataframes
from .config import ALLOWED_EXTENSIONS, STREAMABLE_EXTENSIONS
from typing import Iterator
from abc import ABC, abstractmethod
import pandas as pd
import inspect
import json
import sys

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
    _SCHEMA_SAMPLE_ROWS:int = None

    @classmethod
    def get_schema_sample_rows(cls) -> int:
        return cls._SCHEMA_SAMPLE_ROWS
    
    @classmethod
    def get_extension(cls) -> str:
        return cls.__name__[:-len("Handler")].lower()

    @classmethod
    def is_streamable(cls) -> bool:
        return cls.get_extension() in STREAMABLE_EXTENSIONS

    def __init__(self):
        self._READ_KWARGS = self.get_read_kwargs()
        self._WRITE_KWARGS = self.get_write_kwargs()

    @property
    def schema_sample_rows(self) -> int:
        return type(self).get_schema_sample_rows()

    @property
    def extension(self) -> str:
        return type(self).get_extension()

    @property
    def streamable(self) -> bool:
        return type(self).is_streamable()

    def get_function_name(self):
        """Override this if pandas function name differs from class name"""
        # Default: CsvHandler → read_csv, JsonHandler → read_json
        class_name = self.__class__.__name__.lower()
        return class_name.replace('handler', '')
    
    def get_read_function(self):
        return getattr(pd, f'read_{self.get_function_name()}')
    
    def get_write_function(self, dataframe:pd.DataFrame):
        return getattr(dataframe, f'to_{self.get_function_name()}')
    
    def get_read_kwargs(self) -> set:
        sig = inspect.signature(self.get_read_function())
        return set(sig.parameters.keys())
    
    def get_write_kwargs(self) -> set:
        sig = inspect.signature(self.get_write_function(pd.DataFrame))
        return set(sig.parameters.keys()) - {'self'}  # Remove 'self' parameter

    def filter_kwargs(self, kwargs, mode='read'):
        """
        Filter kwargs to only include valid parameters for this handler
        
        Args:
            kwargs (dict): Keyword arguments to filter
            mode (str): Either 'read' or 'write' to specify which valid kwargs to use
            
        Returns:
            dict: Filtered kwargs containing only valid parameters
            
        Raises:
            ValueError: If mode is not 'read' or 'write', or if handler doesn't support the mode
        """
        kwarg_attr_name = f"_{mode.upper()}_KWARGS"
        
        if hasattr(self, kwarg_attr_name):
            valid_kwargs = getattr(self, kwarg_attr_name)
        else:
            raise ValueError(f"Handler {self.__class__.__name__} does not support mode '{mode}'. "
                           f"Expected attribute '{kwarg_attr_name}' not found.")
        
        return {k: v for k, v in kwargs.items() if k in valid_kwargs}

    @abstractmethod
    def read(self, file_path: str, **kwargs) -> FileResult:
        """Read file and return FileResult"""
        pass
    
    def write(self, dataframe: pd.DataFrame, file_path: str, **kwargs) -> bool:
        """Default write implementation - works for most formats"""
        filtered_kwargs = self.filter_kwargs(kwargs, mode='write')
        self.get_write_function(dataframe)(file_path, **filtered_kwargs)
    
class CsvHandler(FileHandler):
    """Handler for CSV files"""
    _SCHEMA_SAMPLE_ROWS:int = 2
    
    def read(self, file_path: str, chunk_size: int = 10000, **kwargs) -> Iterator[pd.DataFrame]:
        """Read CSV file and return FileResult"""
        filtered_kwargs = self.filter_kwargs(kwargs, mode='read')
        for chunk in pd.read_csv(file_path, chunksize=chunk_size, **filtered_kwargs):
            yield chunk

        #df = pd.read_csv(file_path, chunksize=chunk_size, **filtered_kwargs)
        #return FileResult(dataframe=df, normalized=False)

class XlsxHandler(FileHandler):
    """Handler for Excel files"""
    _SCHEMA_SAMPLE_ROWS:int = 5

    def get_function_name(self):
        return 'excel'  # Override for pd.read_excel
    
    def read(self, file_path: str, **kwargs) -> Iterator[pd.DataFrame]:
        """Read Excel file and return FileResult with sheet_name handling"""
        filtered_kwargs = self.filter_kwargs(kwargs, mode='read')
        sheet_name = filtered_kwargs.pop('sheet_name', 0)
        
        if not isinstance(sheet_name, (int, str, list, type(None))):
            raise TypeError(
                f"sheet_name must be int (sheet index), str (sheet name), or None (all sheets). "
                f"Got {type(sheet_name).__name__}: {sheet_name}"
            )
        
        if sheet_name is None or isinstance(sheet_name, list):
            sheets_dict = pd.read_excel(file_path, sheet_name=sheet_name, **filtered_kwargs)
            df = merge_dataframes(sheets_dict)
            #merged_df = merge_dataframes(sheets_dict)
            #return FileResult(dataframe=merged_df, normalized=True)
        elif isinstance(sheet_name, int):
            excel_file = pd.ExcelFile(file_path)
            actual_sheet_name = excel_file.sheet_names[sheet_name]
            df = pd.read_excel(excel_file, sheet_name=sheet_name, **filtered_kwargs)
            excel_file.close()
            df['sheet_name'] = actual_sheet_name
            #return FileResult(dataframe=df, normalized=False)
        else:  # str
            df = pd.read_excel(file_path, sheet_name=sheet_name, **filtered_kwargs)
            df['sheet_name'] = sheet_name
            #return FileResult(dataframe=df, normalized=False)
        yield df
class JsonHandler(FileHandler):
    """Handler for JSON files"""

    def get_read_kwargs(self) -> set:
        return set(['encoding'])
    
    def read(self, file_path: str, **kwargs) -> Iterator[pd.DataFrame]:
        """Read JSON file and return FileResult, handling nested structures"""
        filtered_kwargs = self.filter_kwargs(kwargs, mode='read')
        
        with open(file_path, 'r', **filtered_kwargs) as f:
            data = json.load(f)
        
        if isinstance(data, list):
            # Simple flat JSON array - direct pandas handling
            yield pd.DataFrame(data) 
            #df = pd.DataFrame(data)
            #return FileResult(dataframe=df, normalized=False)
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
                yield merge_dataframes(sheets_dict)
                #merged_df = merge_dataframes(sheets_dict)
                #return FileResult(dataframe=merged_df, normalized=True)
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
    
def get_handler_for_extension(extension: str) -> FileHandler:
    """
    Get file handler instance for the specified extension.
    
    Dynamically instantiates the appropriate handler class based on file
    extension using naming convention (e.g., 'csv' -> CsvHandler).
    
    Args:
        extension: File extension without dot (e.g., 'csv', 'xlsx', 'json')
        
    Returns:
        FileHandler: Handler instance for the file type
        
    Raises:
        ValueError: If extension is not supported or handler not found
        
    Examples:
        >>> handler = get_handler_for_extension('csv')
        >>> isinstance(handler, CsvHandler)
        True
        
    Note:
        Handler classes must follow naming convention: {Extension}Handler
        where Extension is the capitalized file extension.
    """
    handler_class_name = f"{extension.capitalize()}Handler"
    try:
        handler_class = getattr(sys.modules[__name__], handler_class_name)
    except AttributeError:
        print(f"Unsupported file format: .{extension}. Supported: {[f'.{ext}' for ext in ALLOWED_EXTENSIONS]}")
        raise ValueError(f"Unsupported file format: .{extension}. Supported: {[f'.{ext}' for ext in ALLOWED_EXTENSIONS]}")
    
    return handler_class()