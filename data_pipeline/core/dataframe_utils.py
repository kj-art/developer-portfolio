from collections import namedtuple
import pandas as pd
from dataclasses import dataclass
from typing import Optional
from .processing_config import ProcessingConfig

FileResult = namedtuple('FileResult', ['dataframe', 'normalized'])

@dataclass
class ProcessingResult:
    files_processed: int
    total_rows: int
    total_columns: int
    processing_time: float
    output_file: Optional[str] = None 
    schema: Optional[dict] = None
    data: Optional[pd.DataFrame] = None      # Only for InMemory

def merge_dataframes(sheets, schema_map=None, to_lower=True, spaces_to_underscores=True):
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
            normalized_df = normalize_columns(df, schema_map, to_lower, spaces_to_underscores)
            normalized_df['sheet_name'] = sheet_name
            normalized_sheets.append(normalized_df)
    elif isinstance(sheets, list):
        for i, df in enumerate(sheets):
            normalized_df = normalize_columns(df, schema_map, to_lower, spaces_to_underscores)
            #normalized_df['sheet_name'] = f'sheet_{i}'
            normalized_sheets.append(normalized_df)
    else:
        raise TypeError(f"Expected dict or list, got {type(sheets)}")
    
    if not len(normalized_sheets):
        return pd.DataFrame()
    return pd.concat(normalized_sheets, ignore_index=True)

# core/utils.py
def normalize_columns(dataframe, schema_map=None, to_lower=True, spaces_to_underscores=True):
    """
    Normalize DataFrame column names and intelligently handle name columns
    
    Args:
        dataframe (pandas.DataFrame): DataFrame to normalize
        schema_map (dict, optional): Maps standard names to list of alternatives.
                                    If None, only basic normalization is performed.
        
    Returns:
        pandas.DataFrame: DataFrame with normalized column names and name handling
        
    Processing steps:
        1. Convert column names to lowercase with underscores
        2. Apply schema mapping to standardize column names (if provided)
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
    
    def normalize(string, force=False):
        if force or to_lower:
            string = string.lower()
        if force or spaces_to_underscores:
            string = string.replace(' ', '_')
        return string
        
    df_n = dataframe.copy()
    # For checking if columns exist, use fully normalized names
    normalized_cols = [normalize(col, True) for col in df_n.columns]
    df_n.columns = df_n.columns.map(normalize)

    # Apply schema mapping if provided
    if schema_map:
        # Create reverse mapping: {'full_name': 'name', 'location': 'city', 'loc': 'city'}
        rename_map = {}
        for standard_name, alternatives in schema_map.items():
            for alt_name in alternatives:
                rename_map[normalize(alt_name)] = standard_name
        
        df_n = df_n.rename(columns=rename_map)
    
    # Smart name handling with "fill in the gaps" logic
    normalized_cols = list(df_n.columns)
    name_index = normalized_cols.index('name') if 'name' in normalized_cols else -1
    first_index = normalized_cols.index('first_name') if 'first_name' in normalized_cols else -1
    last_index = normalized_cols.index('last_name') if 'last_name' in normalized_cols else -1
    
    if name_index != -1:
        # Get the actual current column name after normalization
        name_col = df_n.columns[name_index]
        
        # Split the full name
        name_parts = df_n[name_col].str.split(' ', n=1, expand=True)
        split_first = name_parts[0] if 0 in name_parts.columns else None
        split_last = name_parts[1] if 1 in name_parts.columns else None
        
        # Use existing columns if available, otherwise use split parts
        if first_index == -1 and split_first is not None:
            # Add first_name column
            df_n.insert(name_index + 1, normalize('first_name'), split_first)
        if last_index == -1 and split_last is not None:
            # Add last_name column  
            df_n.insert(name_index + 2, normalize('last_name'), split_last)
            
        # Drop the original name column
        df_n = df_n.drop([name_col], axis=1)
    
    return df_n

def normalize_chunk(chunk: pd.DataFrame, config: ProcessingConfig) -> pd.DataFrame:
    """Apply column normalization to a chunk."""
    schema_map = config.schema_map or {}  # Use config schema or empty dict
    return normalize_columns(
        chunk, 
        schema_map, 
        config.to_lower, 
        config.spaces_to_underscores
        )

def merge_dtypes(existing_dtype: Optional[str], new_dtype: str) -> str:
    """
    Merge two pandas dtypes, choosing the most permissive one.
    
    Combines data types from multiple files to create a unified column naming,
    selecting the most permissive type that can handle all data variations.
    Uses hierarchy: object > float64 > int64 > bool > datetime64[ns]
    
    Args:
        existing_dtype: Current dtype for the column (None if first occurrence)
        new_dtype: New dtype encountered for the same column
        
    Returns:
        str: Most permissive dtype that can handle both input types
        
    Examples:
        >>> merge_dtypes('int64', 'float64')
        'float64'  # float is more permissive than int
        
        >>> merge_dtypes('int64', 'object')
        'object'   # object is most permissive
        
        >>> merge_dtypes(None, 'int64')
        'int64'    # first occurrence
    """
    if existing_dtype is None:
        return new_dtype
    
    dtype_hierarchy = ['object', 'float64', 'int64', 'bool', 'datetime64[ns]']
    
    try:
        existing_pos = dtype_hierarchy.index(existing_dtype)
    except ValueError:
        existing_pos = 0
        
    try:
        new_pos = dtype_hierarchy.index(new_dtype)
    except ValueError:
        new_pos = 0
    
    return dtype_hierarchy[min(existing_pos, new_pos)]