"""
File operation utilities for data processors.

Provides shared functionality for file discovery, path processing, handler management,
and other file-related operations used by both in-memory and streaming processors.
"""

import os
from pathlib import Path
from typing import Iterator, Optional, Union, List
import pandas as pd
from shared_utils.logger import EnterpriseLogger
from .processing_config import ProcessingConfig
from .dataframe_utils import normalize_columns

from . import handlers
from .config import ALLOWED_EXTENSIONS, STREAMABLE_EXTENSIONS

def get_extension(file_path: str) -> str:
    print(f'file path|{file_path}|')
    return Path(file_path).suffix.lstrip('.')

def is_streamable_extension(extension: str) -> bool:
    return extension.lower() in STREAMABLE_EXTENSIONS

def get_files_iterator(
    input_folder: Union[str, Path], 
    recursive: bool = False, 
    filetype: Optional[Union[str, List[str]]] = None
) -> Iterator[Path]:
    """
    Memory-efficient iterator that yields valid files one at a time.
    
    Traverses the input folder and yields file paths that match the specified
    file type filter. Uses generator pattern to avoid loading all file paths
    into memory simultaneously for large directory structures.
    
    Args:
        input_folder: Path to folder containing files to process
        recursive: If True, search subdirectories recursively  
        filetype: File extensions to include (e.g. 'csv', ['csv', 'xlsx']).
                 If None, includes all supported file types.
                 
    Yields:
        Path: File paths that match the filter criteria
        
    Examples:
        >>> for file_path in get_files_iterator('data/', recursive=True, filetype='csv'):
        ...     print(f"Found: {file_path}")
        
        >>> files = list(get_files_iterator('data/', filetype=['csv', 'xlsx']))
        
    Raises:
        FileNotFoundError: If input_folder does not exist
        ValueError: If filetype contains unsupported extensions
    """
    path = Path(input_folder)
    files = path.rglob('*') if recursive else path.iterdir()
    valid_extensions = normalize_filetype(filetype)
    
    for file_path in files:
        if file_path.is_file():
            extension = file_path.suffix.lower()[1:]
            if extension in valid_extensions:
                yield file_path

def normalize_filetype(filetype: Optional[Union[str, List[str]]]) -> List[str]:
    """
    Normalize and validate filetype filter input.
    
    Converts various filetype input formats into a standardized list of
    lowercase extensions without dots. Validates that all extensions
    are supported by the system.
    
    Args:
        filetype: File type specification:
                 - None: Return all supported extensions
                 - str: Single extension (e.g., 'csv' or '.csv')
                 - List[str]: Multiple extensions
                 
    Returns:
        List[str]: Normalized list of lowercase extensions without dots
        
    Examples:
        >>> normalize_filetype('CSV')
        ['csv']
        >>> normalize_filetype(['.xlsx', 'json'])
        ['xlsx', 'json']
        >>> normalize_filetype(None)
        ['csv', 'xlsx', 'json']  # All supported types
        
    Raises:
        TypeError: If filetype is not str, list, or None
        ValueError: If any extension is not supported
    """
    if filetype is None:
        return ALLOWED_EXTENSIONS.copy()
    
    if isinstance(filetype, str):
        normalized = [filetype.lstrip('.').lower()]
    elif isinstance(filetype, list):
        normalized = [ext.lstrip('.').lower() for ext in filetype]
    else:
        raise TypeError(f"filetype must be str, list, or None. Got {type(filetype).__name__}: {filetype}")
    
    unsupported_filters = set(normalized) - set(ALLOWED_EXTENSIONS)

    if unsupported_filters:
        raise ValueError(f"Unsupported file types in filter: {unsupported_filters}. Supported: {ALLOWED_EXTENSIONS}")
    
    return normalized


def is_valid_file(file_path: Path, allowed_extensions: List[str]) -> bool:
    """
    Check if file has a valid extension for processing.
    
    Validates that the file extension matches one of the allowed extensions.
    Case-insensitive comparison with automatic dot removal.
    
    Args:
        file_path: File path to validate
        allowed_extensions: List of valid extensions (without dots)
        
    Returns:
        bool: True if file extension is in allowed list
        
    Examples:
        >>> is_valid_file(Path('data.csv'), ['csv', 'xlsx'])
        True
        >>> is_valid_file(Path('readme.txt'), ['csv', 'xlsx']) 
        False
    """
    pass


def get_source_file_path(file_path: Union[str, Path]) -> str:
    """
    Extract source file path relative to input folder.
    
    Converts absolute file path to relative path and removes the first
    directory component (input folder) to create a clean source file
    identifier for tracking data lineage.
    
    Args:
        file_path: Absolute or relative path to source file
        
    Returns:
        str: Cleaned relative path for source_file column
        
    Examples:
        >>> get_source_file_path('/home/user/data/subfolder/file.csv')
        'subfolder/file.csv'  # Removes 'data' input folder
        
        >>> get_source_file_path('/home/user/data/file.csv')
        'file.csv'  # Single file at root level
        
    Note:
        This function assumes the file_path includes the input folder
        as the first component in the relative path structure.
    """
    rel_path = os.path.relpath(str(file_path))
    path_parts = Path(rel_path).parts
    if len(path_parts) > 1:
        return str(Path(*path_parts[1:]))
    else:
        return path_parts[0]


def merge_kwargs(base_kwargs: dict, override_kwargs: dict) -> dict:
    """
    Safely merge kwargs dictionaries with override precedence.
    
    Combines two keyword argument dictionaries, with values from
    override_kwargs taking precedence over base_kwargs for duplicate keys.
    
    Args:
        base_kwargs: Base dictionary of keyword arguments
        override_kwargs: Override dictionary with higher precedence
        
    Returns:
        dict: Merged dictionary with override values taking precedence
        
    Examples:
        >>> base = {'encoding': 'utf-8', 'sep': ','}
        >>> override = {'sep': ';', 'header': 0}
        >>> merge_kwargs(base, override)
        {'encoding': 'utf-8', 'sep': ';', 'header': 0}
    """
    return {**base_kwargs, **override_kwargs}


def log_file_error(logger: EnterpriseLogger, operation: str, file_path: Union[str, Path], error: Exception) -> None:
    """
    Standardized file error logging with consistent format.
    
    Logs file processing errors using a consistent format that includes
    operation context, file information, and error details for debugging.
    
    Args:
        logger: Logger instance for error output
        operation: Description of operation that failed (e.g., 'reading', 'processing')
        file_path: Path to file that caused the error
        error: Exception that occurred
        
    Examples:
        >>> log_file_error(logger, 'reading', Path('data.csv'), FileNotFoundError('File not found'))
        # Logs: "Error reading file_name=data.csv error=File not found"
    """
    pass


def get_default_value_for_dtype(dtype_str: str):
    """
    Get appropriate default value for missing columns based on pandas data type.
    
    Returns sensible default values for different pandas data types when
    adding missing columns during column name normalization.
    
    Args:
        dtype_str: String representation of pandas dtype (e.g., 'int64', 'object')
        
    Returns:
        Default value appropriate for the data type:
        - object: None
        - int/float: None  
        - bool: False
        - datetime: None
        
    Examples:
        >>> get_default_value_for_dtype('int64')
        None
        >>> get_default_value_for_dtype('bool')
        False
    """
    pass