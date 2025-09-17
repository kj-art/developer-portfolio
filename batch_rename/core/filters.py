"""
Built-in filters for file selection.

Filters determine which files should be processed based on various criteria.
"""

import fnmatch
import re
from pathlib import Path
from typing import Dict, Any, List


def pattern_filter(file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> bool:
    """
    Filter files based on glob patterns.
    
    Positional args: [include_pattern, exclude_pattern] or [include_pattern]
    Keyword args: include=pattern, exclude=pattern
    
    Examples:
        pattern,*.pdf  → include="*.pdf"
        pattern,*.pdf,*_backup_*  → include="*.pdf", exclude="*_backup_*"
        pattern,include=*.pdf,exclude=*_backup_*
    """
    filename = file_path.name
    
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


def file_type_filter(file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> bool:
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
        
    file_ext = file_path.suffix.lower().lstrip('.')
    return file_ext in allowed_types
"""
Built-in filters for file selection.

Filters determine which files should be processed based on various criteria.
"""

import fnmatch
import re
from pathlib import Path
from typing import Dict, Any, List


def file_size_filter(file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> bool:
    """
    Filter files by size.
    
    Positional args: [min_size, max_size] or [min_size] or [max_size]
    Keyword args: min=size, max=size
    
    Examples:
        file-size,1MB,100MB  → min="1MB", max="100MB"
        file-size,1MB        → min="1MB"
        file-size,min=1MB,max=100MB
    """
    def parse_size(size_str: str) -> int:
        """Parse size string like '1MB' to bytes."""
        if not size_str:
            return 0
        
        size_str = size_str.upper().strip()
        units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
        
        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                number = size_str[:-len(unit)]
                return int(float(number) * multiplier)
        
        # No unit, assume bytes
        return int(size_str)
    
    file_size = metadata['size']
    
    # Handle positional arguments
    if positional_args:
        min_size = positional_args[0] if len(positional_args) > 0 else None
        max_size = positional_args[1] if len(positional_args) > 1 else None
    else:
        min_size = kwargs.get('min')
        max_size = kwargs.get('max')
    
    if min_size and file_size < parse_size(min_size):
        return False
    
    if max_size and file_size > parse_size(max_size):
        return False
    
    return True


def name_length_filter(file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> bool:
    """
    Filter files by name length.
    
    Positional args: [min_length, max_length] or [min_length]
    Keyword args: min=length, max=length
    
    Examples:
        name-length,5,50  → min=5, max=50
        name-length,5     → min=5
        name-length,min=5,max=50
    """
    name_length = len(file_path.stem)  # Length without extension
    
    # Handle positional arguments
    if positional_args:
        min_length = int(positional_args[0]) if len(positional_args) > 0 else None
        max_length = int(positional_args[1]) if len(positional_args) > 1 else None
    else:
        min_length = int(kwargs.get('min')) if kwargs.get('min') else None
        max_length = int(kwargs.get('max')) if kwargs.get('max') else None
    
    if min_length and name_length < min_length:
        return False
    
    if max_length and name_length > max_length:
        return False
    
    return True


def date_modified_filter(file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> bool:
    """
    Filter files by modification date.
    
    Positional args: [after_date, before_date] or [after_date]
    Keyword args: after=date, before=date
    
    Examples:
        date-modified,2024-01-01,2024-12-31
        date-modified,after=2024-01-01
        date-modified,"1 week ago"
    """
    import datetime
    
    file_mtime = datetime.datetime.fromtimestamp(metadata['modified'])
    
    # Handle positional arguments
    if positional_args:
        after_str = positional_args[0] if len(positional_args) > 0 else None
        before_str = positional_args[1] if len(positional_args) > 1 else None
    else:
        after_str = kwargs.get('after')
        before_str = kwargs.get('before')
    
    if after_str:
        if after_str.lower().endswith('ago'):
            # Handle relative dates like "1 week ago"
            import re
            match = re.match(r'(\d+)\s*(day|week|month)s?\s*ago', after_str.lower())
            if match:
                amount, unit = match.groups()
                amount = int(amount)
                
                if unit == 'day':
                    after_date = datetime.datetime.now() - datetime.timedelta(days=amount)
                elif unit == 'week':
                    after_date = datetime.datetime.now() - datetime.timedelta(weeks=amount)
                elif unit == 'month':
                    after_date = datetime.datetime.now() - datetime.timedelta(days=amount*30)
            else:
                after_date = datetime.datetime.strptime(after_str, '%Y-%m-%d')
        else:
            after_date = datetime.datetime.strptime(after_str, '%Y-%m-%d')
        
        if file_mtime < after_date:
            return False
    
    if before_str:
        before_date = datetime.datetime.strptime(before_str, '%Y-%m-%d')
        if file_mtime > before_date:
            return False
    
    return True


# Registry of built-in filters
BUILTIN_FILTERS = {
    'pattern': pattern_filter,
    'file-type': file_type_filter,
    'file-size': file_size_filter,
    'name-length': name_length_filter,
    'date-modified': date_modified_filter,
}


def apply_filters(file_path: Path, filter_configs: List[Dict[str, Any]]) -> bool:
    """
    Apply all filters to a file (AND logic).
    
    Args:
        file_path: Path to file being filtered
        filter_configs: List of filter configurations with new function call structure
        
    Returns:
        True if file passes all filters
    """
    if not filter_configs:
        return True
    
    # Gather file metadata
    try:
        stat = file_path.stat()
        metadata = {
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
        }
    except OSError:
        return False
    
    # Apply each filter
    for filter_config in filter_configs:
        filter_name = filter_config['name']
        positional_args = filter_config.get('positional', [])
        kwargs = filter_config.get('keyword', {})
        inverted = filter_config.get('inverted', False)
        
        if filter_name in BUILTIN_FILTERS:
            filter_func = BUILTIN_FILTERS[filter_name]
            result = filter_func(file_path, metadata, positional_args, **kwargs)
            
            # Apply inversion if needed
            if inverted:
                result = not result
            
            # Short-circuit on first failure (AND logic)
            if not result:
                return False
        else:
            # TODO: Handle custom filter functions
            print(f"Warning: Unknown filter '{filter_name}', skipping")
    
    return True