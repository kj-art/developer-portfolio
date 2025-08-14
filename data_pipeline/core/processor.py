import os
from pathlib import Path
import pandas as pd
from collections import namedtuple

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

  def process_folder(self, input_folder):
    """Process all files in a folder and return merged DataFrame"""
    dataframes = []
    for file in input_folder:
      data = self.read_file(file)
      #data is FileResult. Check if it has been normalized already before normalizing
      #dataframes.append(df)

    return self.merge_dataframes(dataframes)
  
  def normalize_columns(self, dataframe):
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

  def merge_dataframes(self, sheets_dict):
    """
    Merge dictionary of DataFrames into single DataFrame
    
    Args:
        sheets_dict (dict): Dictionary where keys are sheet names, values are DataFrames
        
    Returns:
        pandas.DataFrame: Combined DataFrame with 'sheet_name' column added
    """
    pass

  def read_file(self, file_path, **override_options):
    abs_path = os.path.abspath(file_path)
    print(f"Processing '{abs_path}'...")
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
      return FileResult(
          dataframe=self.merge_dataframes(sheets), 
          normalized=True
      )
    elif isinstance(sheet_name, (int, str)):
      return FileResult(
        pd.read_excel(file_path, sheet_name, **kwargs),
        normalized=False
      )
    else:
      raise TypeError(
        f"sheet_name must be int (sheet index), str (sheet name), or None (all sheets). "
        f"Got {type(sheet_name).__name__}: {sheet_name}"
      )