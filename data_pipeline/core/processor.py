import os
from pathlib import Path
import pandas as pd
from collections import namedtuple
import json

FileResult = namedtuple('FileResult', ['dataframe', 'normalized'])

class DataProcessor:
  _ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'json']
  _VALID_KWARGS = {
      'csv': ['sep', 'encoding', 'header', 'skiprows'],
      'xlsx': ['sheet_name', 'engine', 'header', 'skiprows'], 
      'json': ['orient', 'lines', 'encoding']
  }
  _SCHEMA_MAP = {
    'first_name': ['first', 'firstname'],
    'last_name': ['last', 'lastname'],
    'name': ['full_name', 'fullname'],
    'age': [],
    'city': ['location', 'loc'],
  }

  def __init__(self, **file_options):
    """
    Initialize DataProcessor with default file reading options
    
    Args:
        **file_options: File type specific options (e.g. csv_delimiter=';', 
                       excel_engine='openpyxl', json_orient='records')
                       Options are automatically filtered by file type
    
    Example:
        processor = DataProcessor(csv_delimiter=';', encoding='latin-1', 
                                excel_engine='openpyxl', json_orient='records')
    """
    self._csv_options = self._filter_options('csv', file_options)
    self._excel_options = self._filter_options('excel', file_options)
    self._json_options = self._filter_options('json', file_options)

  def _filter_options(self, extension, file_options):
    """
    Filter options dictionary to only include valid options for the given file type
    
    Args:
        options (dict): Dictionary of option key-value pairs
        extension (str): File extension ('csv', 'xlsx', 'json') 
        
    Returns:
        dict: Filtered options containing only valid keys for the file type
        
    Example:
        _filter_options({'sep': ';', 'sheet_name': 0}, 'csv') 
        # Returns: {'sep': ';'}
    """
    return {k: v for k, v in file_options.items() 
            if k in self._VALID_KWARGS.get(extension, [])}

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
    if not os.path.isfile(abs_path):
      print('not file')
      return
    if not os.path.exists(file_path):
      raise FileNotFoundError(f"The file '{abs_path}' does not exist.")

    extension = Path(file_path).suffix.lower()[1:]
    if extension in self._ALLOWED_EXTENSIONS:
      # Try to find a custom handler method for this file type (e.g., _read_xlsx)
      method_name = f'_read_{extension}'
      base_options = getattr(self, f'{extension}_options', {})
      filtered_kwargs = self._filter_options(extension, override_options)
      final_options = {**base_options, **filtered_kwargs}
      try:
        print(method_name)
        if hasattr(self, method_name):
            # Custom handler exists - use it (handles special cases like Excel multi-sheet)
            data = getattr(self, method_name)(file_path, **final_options)
        else:
          # No custom handler - try pandas directly (e.g., pd.read_csv)
          pd_name = method_name[1:] # Remove underscore: '_read_csv' -> 'read_csv'
          if hasattr(pd, pd_name):
            data = FileResult(
              dataframe=getattr(pd, pd_name)(file_path, **final_options), 
              normalized=False
          )
          else:
            raise ValueError(f"No method pandas.{pd_name} exists")
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
    
  def _read_xlsx(self, file_path, **kwargs):
    """
    Read Excel file and return DataFrame

    Args:
      file_path (str): Path to Excel file
      sheet_name (int|str|list|None, optional): Sheet(s) to read. Defaults to 0.
        Follows pandas.read_excel() behavior:
        - int: Sheet index (0-based, 0 = first sheet)
        - str: Sheet name (case-sensitive) 
        - list: List of sheet names/indices (mixed strings and ints allowed)
        - None: All sheets (custom behavior - merged into single DataFrame 
        with 'sheet_name' column, unlike pandas which returns dict)
      **kwargs: Additional arguments passed to pandas.read_excel()

    Returns:
      pandas.DataFrame: Data from specified sheet(s)

    Notes:
      When sheet_name=None, all sheets are combined into a single DataFrame
      with an added 'sheet_name' column. This differs from pandas behavior
      which returns a dictionary of DataFrames.
    """
    sheet_name = kwargs.pop('sheet_name', 0)

    if sheet_name is None or isinstance(sheet_name, list):
      sheets = pd.read_excel(file_path, sheet_name, **kwargs)
      print(f'sheets: {sheets}')
      print(f'df: {self.merge_dataframes(sheets)}')
      
      return FileResult(
          dataframe=self.merge_dataframes(sheets), 
          normalized=True
      )
    elif isinstance(sheet_name, (int, str)):
      excel_file = pd.ExcelFile(file_path)

      # Get the actual sheet name
      if isinstance(sheet_name, int):
        actual_sheet_name = excel_file.sheet_names[sheet_name]
      else:
        actual_sheet_name = sheet_name

      # Read from the already-opened file
      df = pd.read_excel(excel_file, sheet_name=sheet_name, **kwargs)
      df['sheet_name'] = actual_sheet_name

      excel_file.close()  # Clean up
      return FileResult(dataframe=df, normalized=False)
    else:
      raise TypeError(
        f"sheet_name must be int (sheet index), str (sheet name), or None (all sheets). "
        f"Got {type(sheet_name).__name__}: {sheet_name}"
      )
    
  def _read_json(self, file_path, **kwargs):
    """
    Read JSON file and return FileResult, handling both flat and nested structures
    
    Args:
        file_path (str): Path to JSON file
        **kwargs: Additional arguments passed to json.load() or pd.read_json()
        
    Returns:
        FileResult: Processed JSON data with normalized flag
        
    Supported JSON structures:
        - Flat array: [{"name": "John", "age": 25}, ...]
        - Nested object: {"employees": [{"name": "John", "details": {...}}]}
        
    Processing:
        - Flat arrays: Direct pandas DataFrame conversion
        - Nested objects: Top-level keys treated as sheet names, nested 
          dictionaries flattened one level, then merged with sheet_name column
          
    Note:
        Nested structures are flattened one level deep to ensure compatibility
        with other file formats during merging. Returns normalized=True for
        nested JSON since merging requires normalization.
    """   
    with open(file_path, 'r') as f:
      data = json.load(f)
    if isinstance(data, list):
      # Simple flat JSON array - direct pandas handling
      df = pd.DataFrame(data)
      return FileResult(dataframe=df, normalized=False)
    if isinstance(data, dict):
      sheets_dict = {}
      for key, value in data.items():
        if isinstance(value, list):
          # Flatten each record in the array
          flattened_records = []
          for record in value:
            flat_record = self._flatten_record(record)
            flattened_records.append(flat_record)
          
          sheets_dict[key] = pd.DataFrame(flattened_records)
      return FileResult(
        dataframe=self.merge_dataframes(sheets_dict), 
        normalized=True
    )
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