import os
from pathlib import Path
import pandas as pd
from collections import namedtuple

FileResult = namedtuple('FileResult', ['dataframe', 'normalized'])

class DataProcessor:
  _ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'json']
  _SCHEMA_MAP = {
    'name': ['full_name'],
    'age': [],
    'city': ['location'],
  }

  def __init__(self, csv_delimiter=',', encoding='utf-8', excel_sheet=0):
    self._csv_delimiter = csv_delimiter
    self._encoding = encoding
    self._excel_sheet = excel_sheet

  def process_folder(self, input_folder):
    """Process all files in a folder and return merged DataFrame"""
    dataframes = []
    for file in input_folder:
      data = self.read_file(file)
      #data is FileResult. Check if it has been normalized already before normalizing
      #dataframes.append(df)

    return self.merge_dataframes(dataframes)
  
  def normalize_columns(self):
    pass
    '''schema_map = {
    "combine": {
        "name": ["first_name", "last_name"]  # Combine these into 'name'
    },
    "rename": {
        "customer_name": "name",
        "AGE": "age"
    }
}'''

  def merge_dataframes(self, dataframes):
    pass

  def read_file(self, file_path, **kwargs):
    abs_path = os.path.abspath(file_path)
    print(f"Processing '{abs_path}'...")
    if not os.path.exists(file_path):
      raise FileNotFoundError(f"The file '{abs_path}' does not exist.")

    extension = Path(file_path).suffix.lower()[1:]
    if extension in self._ALLOWED_EXTENSIONS:
      method_name = f'_read_{extension}'
      if hasattr(self, method_name):
        try:
          data = getattr(self, method_name)(file_path, **kwargs)
          print(f"Loaded: {data.dataframe.shape[0]} rows, {data.dataframe.shape[1]} columns")
          print(f"Columns: {list(data.dataframe.columns)}")
          return data
        except Exception as e:
          self._handle_read_error(e, abs_path)
      else:
        raise ValueError(f"No '{method_name}' handler defined for extension: {extension}")
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

  def _read_csv(self, file_path, **kwargs):
    """Read CSV file and return DataFrame"""
    # Use class configuration options
    return FileResult(
          dataframe=pd.read_csv(
              file_path,
              sep=self._csv_delimiter,
              encoding=self._encoding
          ), 
          normalized=False
      )
    
  def _read_xlsx(self, file_path, sheet_name=0, **kwargs):
   """
   Read Excel file and return DataFrame
   
   Args:
       file_path (str): Path to Excel file
       sheet_name (int|str|None, optional): Sheet(s) to read. Defaults to 0.
           - int: Sheet index (0-based, 0 = first sheet)
           - str: Sheet name (case-sensitive)
           - None: All sheets combined with 'sheet_name' column added
   
   Returns:
       pandas.DataFrame: Data from specified sheet(s)
       
   Notes:
       When sheet_name=None, all sheets are normalized individually before 
       combining to handle different column structures across sheets.
   """
  
  def _read_json(self, file_path, **kwargs):
    """Read JSON file and return DataFrame"""
    # Use class configuration options
    return pd.read_csv(
        file_path,
        sep=self._csv_delimiter,
        encoding=self._encoding
    )