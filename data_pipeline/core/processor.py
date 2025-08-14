import os
from pathlib import Path
import pandas as pd
from . import readers
    
class DataProcessor:
    _ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'json']
    _SCHEMA_MAP = {
        'name': ['full_name'],
        'age': [],
        'city': ['location', 'loc'],
    }

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
                    df = self.normalize_columns(df)
                dataframes.append(df)

        return self.merge_dataframes(dataframes)
    
    def normalize_columns(self, dataframe):
        """
        Normalize DataFrame column names and intelligently handle name columns
        
        Args:
            dataframe (pandas.DataFrame): DataFrame to normalize
            
        Returns:
            pandas.DataFrame: DataFrame with normalized column names and name handling
            
        Processing steps:
            1. Convert column names to lowercase with underscores
            2. Apply schema mapping to standardize column names
            3. Intelligently combine name data:
               - If full name exists, split it into first/last components
               - Use existing first_name/last_name columns when available
               - Fill missing name columns from split full name when needed
               - Prioritizes separate columns over split data
               
        Example:
            Input: ['Full Name', 'First Name', 'AGE', 'Location']
            Output: ['first_name', 'last_name', 'age', 'city']
            
        Note:
            When both full name and separate name columns exist, separate 
            columns take precedence with full name used to fill any gaps.
        """
        df_n = dataframe.copy()
        df_n.columns = (df_n.columns
                        .str.lower()
                        .str.replace(' ', '_'))
        
        # Create reverse mapping: {'full_name': 'name', 'location': 'city', 'loc': 'city'}
        rename_map = {}
        for standard_name, alternatives in self._SCHEMA_MAP.items():
            for alt_name in alternatives:
                rename_map[alt_name.lower().replace(' ', '_')] = standard_name
        
        df_n = df_n.rename(columns=rename_map)
        
        # Smart name handling with "fill in the gaps" logic
        has_name = 'name' in df_n.columns
        has_first = 'first_name' in df_n.columns
        has_last = 'last_name' in df_n.columns
        
        if has_name:
            # Split the full name
            name_parts = df_n['name'].str.split(' ', n=1, expand=True)
            split_first = name_parts[0] if 0 in name_parts.columns else None
            split_last = name_parts[1] if 1 in name_parts.columns else None
            
            # Use existing columns if available, otherwise use split parts
            if not has_first and split_first is not None:
                df_n['first_name'] = split_first
            if not has_last and split_last is not None:
                df_n['last_name'] = split_last
                
            # Drop the original name column
            df_n = df_n.drop(['name'], axis=1)
        
        return df_n

    def merge_dataframes(self, sheets):
        """
        Merge multiple DataFrames into single DataFrame with normalized columns
        
        Args:
            sheets (dict|list): Either:
                - dict: Dictionary where keys are sheet names, values are DataFrames 
                  (typical output from pandas.read_excel with sheet_name=None)
                - list: List of DataFrames to merge
            
        Returns:
            pandas.DataFrame: Combined DataFrame with normalized columns and 
                             'sheet_name' column indicating source sheet
            
        Processing:
            1. Normalizes columns in each DataFrame individually
            2. Adds 'sheet_name' column to track data source
            3. Concatenates all DataFrames with continuous index
            
        Note:
            Each DataFrame is normalized before merging to ensure consistent 
            column names and avoid duplicate columns from different naming 
            conventions across sheets.
        """
        normalized_sheets = []
        if isinstance(sheets, dict):
            for sheet_name, df in sheets.items():
                normalized_df = self.normalize_columns(df)
                normalized_df['sheet_name'] = sheet_name
                normalized_sheets.append(normalized_df)
        elif isinstance(sheets, list):
            for i, df in enumerate(sheets):
                normalized_df = self.normalize_columns(df)
                #normalized_df['sheet_name'] = f'sheet_{i}'
                normalized_sheets.append(normalized_df)
        else:
            raise TypeError(f"Expected dict or list, got {type(sheets)}")
        
        if not len(normalized_sheets):
            return pd.DataFrame()
        return pd.concat(normalized_sheets, ignore_index=True)

    def read_file(self, file_path, **override_options):
        abs_path = os.path.abspath(file_path)
        print(f"Processing '{abs_path}'...")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{abs_path}' does not exist.")

        extension = Path(file_path).suffix.lower()[1:]
        if extension in self._ALLOWED_EXTENSIONS:
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
            raise ValueError(f"Unsupported file type: '{extension}'. Only {', '.join(self._ALLOWED_EXTENSIONS)} files are allowed.")

    def _handle_read_error(self, exception, file_path):
        """Handle errors from pandas read operations"""
        error_messages = {
            pd.errors.EmptyDataError: f"File '{file_path}' is empty",
            UnicodeDecodeError: f"Encoding issue with '{file_path}'",
            pd.errors.ParserError: f"File '{file_path}' has malformed data",
        }

        message = error_messages.get(type(exception), f"Failed to read {file_path}: {str(exception)}")
        raise ValueError(message) from exception