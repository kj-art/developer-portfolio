"""
Built-in filters for file selection.

Filters determine which files should be processed based on various criteria.
All filters take a ProcessingContext and return boolean values.
"""

import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Callable

from ..processing_context import ProcessingContext
from ..function_loader import load_custom_function


def pattern_filter(context: ProcessingContext, positional_args: List[str], **kwargs) -> bool:
    """
    Filter files based on glob patterns.
    
    Positional args: [include_pattern, exclude_pattern] or [include_pattern]
    Keyword args: include=pattern, exclude=pattern
    
    Examples:
        pattern,*.pdf  → include="*.pdf"
        pattern,*.pdf,*_backup_*  → include="*.pdf", exclude="*_backup_*"
        pattern,include=*.pdf,exclude=*_backup_*
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
    
    Positional args: [min_size, max_size] or [min_size] or [size_range]
    Keyword args: min_size=size, max_size=size
    
    Examples:
        file-size,1MB,100MB  → min=1MB, max=100MB
        file-size,min_size=1MB,max_size=100MB
        file-size,1MB,100MB  → size range
    """
    file_size = context.file_size
    
    # Parse size strings to bytes
    def parse_size(size_str):
        if not size_str:
            return None
        
        size_str = size_str.strip().upper()
        
        # Extract number and unit
        import re
        match = re.match(r'(\d+(?:\.\d+)?)\s*([KMGT]?B)?', size_str)
        if not match:
            return None
        
        number = float(match.group(1))
        unit = match.group(2) or 'B'
        
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024**2,
            'GB': 1024**3,
            'TB': 1024**4
        }
        
        return int(number * multipliers.get(unit, 1))
    
    # Handle positional arguments
    if positional_args:
        if len(positional_args) >= 2:
            min_size = parse_size(positional_args[0])
            max_size = parse_size(positional_args[1])
        elif len(positional_args) == 1:
            # Check if it's a range or just min size
            if ',' in positional_args[0]:
                parts = positional_args[0].split(',')
                min_size = parse_size(parts[0]) if parts[0].strip() else None
                max_size = parse_size(parts[1]) if len(parts) > 1 and parts[1].strip() else None
            else:
                min_size = parse_size(positional_args[0])
                max_size = None
        else:
            min_size = max_size = None
    else:
        # Handle keyword arguments
        min_size = parse_size(kwargs.get('min_size', ''))
        max_size = parse_size(kwargs.get('max_size', ''))
    
    # Apply filters
    if min_size is not None and file_size < min_size:
        return False
    
    if max_size is not None and file_size > max_size:
        return False
    
    return True


def name_length_filter(context: ProcessingContext, positional_args: List[str], **kwargs) -> bool:
    """
    Filter files by filename length.
    
    Positional args: [min_length, max_length] or [length_range]
    Keyword args: min_length=num, max_length=num
    
    Examples:
        name-length,5,50  → min=5, max=50
        name-length,5,50  → length range
        name-length,min_length=5,max_length=50
    """
    filename_length = len(context.base_name)
    
    # Handle positional arguments
    if positional_args:
        if len(positional_args) >= 2:
            min_length = int(positional_args[0]) if positional_args[0] else None
            max_length = int(positional_args[1]) if positional_args[1] else None
        elif len(positional_args) == 1:
            # Check if it's a range string
            if ',' in positional_args[0]:
                parts = positional_args[0].split(',')
                min_length = int(parts[0]) if parts[0].strip() else None
                max_length = int(parts[1]) if len(parts) > 1 and parts[1].strip() else None
            else:
                min_length = int(positional_args[0])
                max_length = None
        else:
            min_length = max_length = None
    else:
        # Handle keyword arguments
        min_length = kwargs.get('min_length')
        max_length = kwargs.get('max_length')
        
        if min_length is not None:
            min_length = int(min_length)
        if max_length is not None:
            max_length = int(max_length)
    
    # Apply filters
    if min_length is not None and filename_length < min_length:
        return False
    
    if max_length is not None and filename_length > max_length:
        return False
    
    return True


def date_modified_filter(context: ProcessingContext, positional_args: List[str], **kwargs) -> bool:
    """
    Filter files by modification date.
    
    Positional args: [date_threshold] or [operator, date_threshold]
    Keyword args: date=date_threshold, operator=comparison
    
    Examples:
        date-modified,2024-01-01  → files modified after 2024-01-01
        date-modified,>,2024-01-01  → files modified after 2024-01-01
        date-modified,<,2024-01-01  → files modified before 2024-01-01
    """
    file_modified = context.modified_timestamp
    
    # Handle positional arguments
    if positional_args:
        if len(positional_args) >= 2 and positional_args[0] in ['>', '<', '>=', '<=', '==']:
            operator = positional_args[0]
            date_threshold = positional_args[1]
        else:
            operator = '>='  # Default: files newer than threshold
            date_threshold = positional_args[0]
    else:
        # Handle keyword arguments
        operator = kwargs.get('operator', '>=')
        date_threshold = kwargs.get('date')
    
    if not date_threshold:
        return True
    
    # Parse date threshold
    try:
        # Handle relative dates like "1 week ago", "2 days ago"
        if 'ago' in date_threshold.lower():
            import re
            match = re.search(r'(\d+)\s+(day|week|month|year)s?\s+ago', date_threshold.lower())
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
                
                from datetime import datetime, timedelta
                now = datetime.now()
                
                if unit == 'day':
                    threshold_date = now - timedelta(days=amount)
                elif unit == 'week':
                    threshold_date = now - timedelta(weeks=amount)
                elif unit == 'month':
                    threshold_date = now - timedelta(days=amount * 30)  # Approximate
                elif unit == 'year':
                    threshold_date = now - timedelta(days=amount * 365)  # Approximate
                
                threshold_timestamp = threshold_date.timestamp()
            else:
                return True  # Invalid relative date format
        else:
            # Handle absolute dates
            try:
                threshold_date = datetime.datetime.strptime(date_threshold, '%Y-%m-%d')
                threshold_timestamp = threshold_date.timestamp()
            except ValueError:
                try:
                    threshold_date = datetime.datetime.strptime(date_threshold, '%Y-%m-%d %H:%M:%S')
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


def get_filter(filter_name: str, filter_args: Dict[str, Any]) -> Callable:
    """
    Get filter function (built-in or custom).
    
    Args:
        filter_name: Name of built-in filter or path to custom function
        filter_args: Dict with 'positional', 'keyword', and 'inverted' keys
        
    Returns:
        Filter function ready to call with ProcessingContext
    """
    if filter_name in BUILTIN_FILTERS:
        # Built-in filter
        filter_func = BUILTIN_FILTERS[filter_name]
        
        # Combine positional and keyword args
        pos_args = filter_args.get('positional', [])
        kwargs = filter_args.get('keyword', {})
        inverted = filter_args.get('inverted', False)
        
        def configured_filter(context: ProcessingContext) -> bool:
            result = filter_func(context, pos_args, **kwargs)
            return not result if inverted else result
        
        return configured_filter
    
    elif Path(filter_name).suffix == '.py':
        # Custom filter function
        custom_func = load_custom_function(filter_name, filter_args.get('positional', [None])[0])
        
        # Get additional arguments (excluding function name)
        pos_args = filter_args.get('positional', [])[1:]  # Skip function name
        kwargs = filter_args.get('keyword', {})
        inverted = filter_args.get('inverted', False)
        
        def configured_custom_filter(context: ProcessingContext) -> bool:
            result = custom_func(context, *pos_args, **kwargs)
            return not result if inverted else result
        
        return configured_custom_filter
    
    else:
        raise ValueError(f"Unknown filter: {filter_name}")