"""
Built-in filters for file selection.

Filters determine which files should be processed based on various criteria.
All filters take a ProcessingContext and return boolean values.
"""

import fnmatch
import datetime
from pathlib import Path
from typing import Dict, Any, List

from ..processing_context import ProcessingContext


def pattern_filter(context: ProcessingContext, positional_args: List[str], **kwargs) -> bool:
    """
    Filter files based on glob patterns.
    
    Positional args: [include_pattern, exclude_pattern] or [include_pattern]
    Keyword args: include=pattern, exclude=pattern
    
    Examples:
        pattern,*.pdf  → include="*.pdf"
        pattern,*.pdf,*_backup_*  → include="*.pdf", exclude="*_backup_*"
        pattern,include=*.pdf,exclude=*_backup_*
    
    Returns:
        True if file should be processed, False otherwise
    """
    filename = context.filename
    
    # Handle positional arguments
    if positional_args:
        include_pattern = positional_args[0] if len(positional_args) > 0 else None
        exclude_pattern = positional_args[1] if len(positional_args) > 1 else None
    else:
        include_pattern = kwargs.get('include')
        exclude_pattern = kwargs.get('exclude')
    
    # Check include pattern
    if include_pattern and not fnmatch.fnmatch(filename, include_pattern):
        return False
    
    # Check exclude pattern
    if exclude_pattern and fnmatch.fnmatch(filename, exclude_pattern):
        return False
    
    return True


def file_type_filter(context: ProcessingContext, positional_args: List[str], **kwargs) -> bool:
    """
    Filter files by extension.
    
    Positional args: [type1, type2, type3, ...] or [types_string]
    Keyword args: types=comma_separated_types
    
    Examples:
        file-type,pdf,jpg,docx  → types=["pdf", "jpg", "docx"]
        file-type,pdf  → types=["pdf"]
        file-type,types="pdf,jpg,docx"
    
    Returns:
        True if file extension matches any allowed type
    """
    # Handle positional arguments
    if positional_args:
        if len(positional_args) == 1 and ',' in positional_args[0]:
            # Single comma-separated string
            allowed_types = [ext.strip().lower().lstrip('.') for ext in positional_args[0].split(',')]
        else:
            # Multiple separate arguments
            allowed_types = [ext.strip().lower().lstrip('.') for ext in positional_args]
    else:
        # Handle keyword arguments
        types_str = kwargs.get('types', '')
        if not types_str:
            return True
        allowed_types = [ext.strip().lower().lstrip('.') for ext in types_str.split(',')]
    
    if not allowed_types:
        return True
        
    file_ext = context.extension.lower().lstrip('.')
    return file_ext in allowed_types


def file_size_filter(context: ProcessingContext, positional_args: List[str], **kwargs) -> bool:
    """
    Filter files by size.
    
    Positional args: [min_size_bytes, max_size_bytes]
    Keyword args: min_size=bytes, max_size=bytes
    
    Examples:
        file-size,1024,10485760  → Between 1KB and 10MB
        file-size,min_size=1024  → At least 1KB
        file-size,max_size=10485760  → At most 10MB
    
    Returns:
        True if file size is within specified range
    """
    file_size = context.file_size
    
    # Handle positional arguments
    if positional_args:
        min_size = int(positional_args[0]) if len(positional_args) > 0 and positional_args[0] else 0
        max_size = int(positional_args[1]) if len(positional_args) > 1 and positional_args[1] else float('inf')
    else:
        # Handle keyword arguments
        min_size = int(kwargs.get('min_size', 0))
        max_size = int(kwargs.get('max_size', float('inf')))
    
    return min_size <= file_size <= max_size


def name_length_filter(context: ProcessingContext, positional_args: List[str], **kwargs) -> bool:
    """
    Filter files by filename length.
    
    Positional args: [min_length, max_length]
    Keyword args: min_length=chars, max_length=chars
    
    Examples:
        name-length,5,50  → Between 5 and 50 characters
        name-length,min_length=10  → At least 10 characters
    
    Returns:
        True if filename length is within specified range
    """
    filename_length = len(context.base_name)
    
    # Handle positional arguments
    if positional_args:
        min_length = int(positional_args[0]) if len(positional_args) > 0 and positional_args[0] else 0
        max_length = int(positional_args[1]) if len(positional_args) > 1 and positional_args[1] else float('inf')
    else:
        # Handle keyword arguments
        min_length = int(kwargs.get('min_length', 0))
        max_length = int(kwargs.get('max_length', float('inf')))
    
    return min_length <= filename_length <= max_length


def date_modified_filter(context: ProcessingContext, positional_args: List[str], **kwargs) -> bool:
    """
    Filter files by modification date.
    
    Positional args: [operator, date_string]
    Keyword args: operator=op, date=date_string
    Operators: >, <, >=, <=, ==
    Date format: YYYY-MM-DD
    
    Examples:
        date-modified,>,2023-01-01  → Modified after Jan 1, 2023
        date-modified,==,2023-12-01  → Modified on Dec 1, 2023
    
    Returns:
        True if file modification date meets criteria
    """
    try:
        file_modified = context.modified_timestamp
        
        # Handle positional arguments
        if len(positional_args) >= 2:
            operator = positional_args[0]
            date_string = positional_args[1]
        else:
            # Handle keyword arguments
            operator = kwargs.get('operator', '>')
            date_string = kwargs.get('date')
        
        if not date_string:
            return True  # No date specified, don't filter
        
        # Parse threshold date
        try:
            threshold_date = datetime.datetime.strptime(date_string, '%Y-%m-%d')
            threshold_timestamp = threshold_date.timestamp()
        except ValueError:
            return True  # Invalid date format
        
        # Apply comparison
        if operator == '>':
            return file_modified > threshold_timestamp
        elif operator == '<':
            return file_modified < threshold_timestamp
        elif operator == '>=':
            return file_modified >= threshold_timestamp
        elif operator == '<=':
            return file_modified <= threshold_timestamp
        elif operator == '==':
            # Same day comparison
            file_date = datetime.datetime.fromtimestamp(file_modified).date()
            threshold_date = datetime.datetime.fromtimestamp(threshold_timestamp).date()
            return file_date == threshold_date
        else:
            return True
            
    except Exception:
        return True  # If parsing fails, don't filter


# Registry of built-in filters
BUILTIN_FILTERS = {
    'pattern': pattern_filter,
    'file-type': file_type_filter,
    'file-size': file_size_filter,
    'name-length': name_length_filter,
    'date-modified': date_modified_filter,
}