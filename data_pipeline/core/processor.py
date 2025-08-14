import os
from pathlib import Path
import pandas as pd
from . import readers
from .utils import merge_dataframes, normalize_columns
from .config import SCHEMA_MAP, ALLOWED_EXTENSIONS

class DataProcessor:
    def __init__(self, **file_options):
        """
        Initialize DataProcessor with default file reading options
        
        Args:
            **file_options: File type specific options (e.g. sep=';', 
                           engine='openpyxl', orient='records')
                           Options are passed to appropriate readers
        
        Example:
            processor = DataProcessor(sep=';', encoding='latin-1', 
                                    engine='openpyxl', orient='records')
        """
        self.file_options = file_options

    def process_folder(self, input_folder, recursive=False, **kwargs):
        """
        Process all files in a folder and return merged DataFrame
        
        Args:
            input_folder (str): Path to folder containing files to process
            recursive (bool, optional): If True, search subdirectories recursively. 
                                       Defaults to False.
        
        Returns:
            pandas.DataFrame: Merged DataFrame from all processed files
        """
        from pathlib import Path
        
        dataframes = []
        path = Path(input_folder)
        
        if recursive:
            files = path.rglob('*')  # Recursive: all files in subdirectories
        else:
            files = path.iterdir()   # Non-recursive: direct children only
        
        for file_path in files:
            if file_path.is_file():  # Skip directories
                data = self.read_file(str(file_path), **kwargs)
                if not data:
                    continue
                df = data.dataframe
                if not data.normalized:
                    df = normalize_columns(df, SCHEMA_MAP)
                dataframes.append(df)

        return merge_dataframes(dataframes)

    def read_file(self, file_path, **override_options):
        abs_path = os.path.abspath(file_path)
        print(f"Processing '{abs_path}'...")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{abs_path}' does not exist.")

        extension = Path(file_path).suffix.lower()[1:]
        if extension in ALLOWED_EXTENSIONS:
            try:
                # Dynamically instantiate reader class based on extension
                reader_class_name = f"{extension.capitalize()}Reader"
                reader_class = getattr(readers, reader_class_name)
                reader = reader_class()
                
                # Merge constructor options with override options
                final_options = {**self.file_options, **override_options}
                
                data = reader.read(file_path, **final_options)
                data.dataframe['source_file'] = abs_path
                print(f"Loaded: {data.dataframe.shape[0]} rows, {data.dataframe.shape[1]} columns")
                print(f"Columns: {list(data.dataframe.columns)}")
                return data
            except Exception as e:
                self._handle_read_error(e, abs_path)
        else:
            raise ValueError(f"Unsupported file type: '{extension}'. Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed.")

    def _handle_read_error(self, exception, file_path):
        """Handle errors from pandas read operations"""
        error_messages = {
            pd.errors.EmptyDataError: f"File '{file_path}' is empty",
            UnicodeDecodeError: f"Encoding issue with '{file_path}'",
            pd.errors.ParserError: f"File '{file_path}' has malformed data",
        }

        message = error_messages.get(type(exception), f"Failed to read {file_path}: {str(exception)}")
        raise ValueError(message) from exception