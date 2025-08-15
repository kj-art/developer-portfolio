import os
from pathlib import Path
import pandas as pd
from . import handlers
from .utils import merge_dataframes, normalize_columns
from .config import SCHEMA_MAP, ALLOWED_EXTENSIONS

class DataProcessor:
    def __init__(self, **file_options):
        """
        Initialize DataProcessor with default file reading options
        
        Args:
            **file_options: File type specific options (e.g. sep=';', 
                           engine='openpyxl', orient='records')
                           Options are passed to appropriate handlers
        
        Example:
            processor = DataProcessor(sep=';', encoding='latin-1', 
                                    engine='openpyxl', orient='records')
        """
        self.file_options = file_options

    def process_folder(self, input_folder, recursive=False, filetype=None, schema_map=None, to_lower=True, spaces_to_underscores=True, **kwargs):
        """
        Process all files in a folder and return merged DataFrame
        
        Args:
            input_folder (str): Path to folder containing files to process
            recursive (bool, optional): If True, search subdirectories recursively. 
                                      Defaults to False.
            filetype (str|list, optional): File extensions to process. 
                                                Can be single string or list of strings.
                                                Defaults to all supported types.
            schema_map (dict, optional): Column name mapping for normalization.
                                      Maps standard names to list of alternatives.
                                      If None, uses default SCHEMA_MAP from config.
            **kwargs: Additional options passed to file handlers
        
        Returns:
            pandas.DataFrame: Merged DataFrame from all processed files
        """
        
        schema_map = schema_map or SCHEMA_MAP
        dataframes = []
        path = Path(input_folder)
        
        if recursive:
            files = path.rglob('*')  # Recursive: all files in subdirectories
        else:
            files = path.iterdir()   # Non-recursive: direct children only
        
        for file_path in files:
            if file_path.is_file():  # Skip directories
                data = self.read_file(str(file_path), filetype, **kwargs)
                if not data:
                    continue
                df = data.dataframe
                if not data.normalized:
                    df = normalize_columns(df, schema_map, to_lower, spaces_to_underscores)
                dataframes.append(df)

        return merge_dataframes(dataframes, schema_map, to_lower, spaces_to_underscores)

    def _normalize_filetype(self, filetype=None):
        """
        Normalize and validate filetype filter input
        
        Args:
            filetype (str|list|None, optional): File extensions to allow.
                                                      Can be:
                                                      - None: defaults to all supported types
                                                      - str: single extension (e.g., 'csv')
                                                      - list: multiple extensions (e.g., ['csv', 'xlsx'])
        
        Returns:
            list: Validated list of file extensions
            
        Raises:
            TypeError: If filetype is not str, list, or None
            ValueError: If any extension in filetype is not supported
            
        Examples:
            >>> self._normalize_filetype(None)
            ['csv', 'xlsx', 'json']

            >>> self._normalize_filetype(123)  # Wrong type
            TypeError: filetype must be str, list, or None. Got int: 123
            
            >>> self._normalize_filetype('.csv')
            ['csv']
            
            >>> self._normalize_filetype(['csv', '.xlsx'])
            ['csv', 'xlsx']
            
            >>> self._normalize_filetype(['txt'])  # Unsupported
            ValueError: Unsupported file types in filter: {'txt'}. Supported: ['csv', 'xlsx', 'json']
        """
        if filetype is None:
            filetype = ALLOWED_EXTENSIONS
        else:
            if isinstance(filetype, list):
                # Strip leading dots from extensions in list
                filetype = [ext.lstrip('.').lower() for ext in filetype]
            elif isinstance(filetype, str):
                filetype = [filetype.lstrip('.').lower()]
            else:
                raise TypeError(f"filetype must be str, list, or None. Got {type(filetype).__name__}: {filetype}")
            unsupported_filters = set(filetype) - set(ALLOWED_EXTENSIONS)
            if unsupported_filters:
                raise ValueError(f"Unsupported file types in filter: {unsupported_filters}. Supported: {ALLOWED_EXTENSIONS}")
        return filetype
    
    def _get_handler_for_extension(self, extension):
        """Get handler class for a given extension"""
        handler_class_name = f"{extension.capitalize()}Handler"
        try:
            handler_class = getattr(handlers, handler_class_name)
        except AttributeError:
            from .config import ALLOWED_EXTENSIONS
            raise ValueError(f"Unsupported file format: .{extension}. Supported: {[f'.{ext}' for ext in ALLOWED_EXTENSIONS]}")
        
        return handler_class()

    def read_file(self, file_path, filetype=None, **override_options):
        """
        Read a single file if it matches the filetype filter
        
        Args:
            file_path (str): Path to file to read
            filetype (str|list, optional): File extensions to allow. 
                                                Defaults to all supported types.
            **override_options: Options passed to file handlers
        
        Returns:
            FileResult|None: FileResult if file matches filter, None if filtered out
        """
        abs_path = os.path.abspath(file_path)
        print(f"Processing '{abs_path}'...")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{abs_path}' does not exist.")

        extension = Path(file_path).suffix.lower()[1:]

        if extension not in self._normalize_filetype(filetype):
            return None
        
        handler = self._get_handler_for_extension(extension)
        
        # Merge constructor options with override options
        final_options = {**self.file_options, **override_options}
        
        data = handler.read(file_path, **final_options)
        data.dataframe['source_file'] = os.path.relpath(abs_path)
        print(f"Loaded: {data.dataframe.shape[0]} rows, {data.dataframe.shape[1]} columns")
        print(f"Columns: {list(data.dataframe.columns)}")
        return data
    
    def write_file(self, dataframe, output_path, **override_options):
        """
        Save DataFrame to file, determining format from file extension
        
        Args:
            dataframe (pandas.DataFrame): DataFrame to save
            output_path (str): Path to output file
            **override_options: Options passed to file handlers
        """
        
        abs_path = os.path.abspath(output_path)
        extension = Path(output_path).suffix.lower()[1:]  # Remove the dot
        
        if not extension:
            raise ValueError(f"Output file must have an extension to determine format: {output_path}")
        
        handler = self._get_handler_for_extension(extension)
        
        # Merge constructor options with override options
        final_options = {**self.file_options, **override_options}
        
        # Write the file
        handler.write(dataframe, output_path, **final_options)
        print(f"Data saved to '{abs_path}' ({len(dataframe)} rows, {len(dataframe.columns)} columns)")