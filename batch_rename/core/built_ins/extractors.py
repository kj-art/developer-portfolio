"""
Built-in extractors for parsing data from filenames and metadata.

Extractors take a ProcessingContext and return Dict[str, Any] with extracted field data.
"""

import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from ..processing_context import ProcessingContext


def split_extractor(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Split filename by delimiter and assign field names.
    
    The most commonly used extractor for structured filenames. Splits the base
    filename (without extension) on the specified delimiter and maps parts to
    named fields. Handles missing parts gracefully by assigning empty strings.
    
    Args:
        context: Processing context with filename and metadata
        positional_args: [delimiter, field1, field2, ...] where delimiter is 
                        the character to split on, followed by field names
        **kwargs: Not used by this extractor
    
    Returns:
        Dictionary mapping field names to extracted values
        
    Examples:
        Filename: "HR_employee_data_2024.pdf"
        Args: ['_', 'dept', 'type', 'category', 'year']
        Result: {'dept': 'HR', 'type': 'employee', 'category': 'data', 'year': '2024'}
        
        Filename: "CompanyReport_Q1.pdf" (fewer parts than fields)
        Args: ['_', 'company', 'quarter', 'year']  
        Result: {'company': 'CompanyReport', 'quarter': 'Q1', 'year': ''}
        
    Note:
        - Extension is automatically stripped before processing
        - Extra filename parts beyond field names are ignored
        - Missing parts result in empty string values
    """
    if not positional_args:
        raise ValueError("split extractor requires delimiter and field names")
    
    delimiter = positional_args[0]
    field_names = positional_args[1:]
    
    if not field_names:
        raise ValueError("split extractor requires at least one field name")
    
    # Split the base filename (without extension)
    filename_parts = context.base_name.split(delimiter)
    
    # Create result dict with field mappings
    result = {}
    for i, field_name in enumerate(field_names):
        if i < len(filename_parts):
            result[field_name] = filename_parts[i]
        else:
            result[field_name] = ""  # Empty string for missing parts
    
    return result


def regex_extractor(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Extract data using regex named groups or numbered groups with field mapping.
    
    Positional args: [regex_pattern]
    Keyword args: pattern=regex_pattern, field1=name1, field2=name2, etc.
    
    Examples:
        regex,"(?P<dept>\\w+)_(?P<num>\\d+)"  → "HR_12345.pdf" becomes {"dept": "HR", "num": "12345"}
        regex,"([A-Z]+)_(\\d+)",field1=dept,field2=num  → "HR_12345.pdf" becomes {"dept": "HR", "num": "12345"}
    
    Returns:
        Dict with named group matches or mapped numbered groups
    """
    # Get pattern from positional or keyword args
    if positional_args:
        pattern = positional_args[0]
    else:
        pattern = kwargs.get('pattern')
    
    if not pattern:
        raise ValueError("regex extractor requires pattern")
    
    try:
        match = re.search(pattern, context.base_name)
        if not match:
            return {}  # No matches found
            
        # Check if pattern uses named groups
        if match.groupdict():
            return match.groupdict()
        
        # Handle numbered groups with field mapping
        result = {}
        groups = match.groups()
        
        # Map numbered groups to field names using fieldN=name kwargs
        for i, group_value in enumerate(groups, 1):
            field_key = f'field{i}'
            if field_key in kwargs:
                field_name = kwargs[field_key]
                result[field_name] = group_value
        
        return result
        
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")


def position_extractor(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Extract data from specific character positions.
    
    Positional args: [position_spec1, position_spec2, ...]
    Position spec format: "start-end:fieldname" or "start:fieldname" (single char)
    
    Examples:
        position,"0-2:dept,3-5:code"  → "HRX123report.pdf" becomes {"dept": "HRX", "code": "123"}
        position,"0:first,1-3:next"   → "A123report.pdf" becomes {"first": "A", "next": "123"}
    
    Returns:
        Dict with field data extracted from character positions
    """
    if not positional_args:
        raise ValueError("position extractor requires position specifications")
    
    result = {}
    filename = context.base_name
    
    # Handle comma-separated specs in single argument or multiple arguments
    if len(positional_args) == 1 and ',' in positional_args[0]:
        specs = [spec.strip() for spec in positional_args[0].split(',')]
    else:
        specs = positional_args
    
    for spec in specs:
        if ':' not in spec:
            raise ValueError(f"Invalid position spec '{spec}'. Format: 'start-end:fieldname' or 'start:fieldname'")
        
        pos_part, field_name = spec.split(':', 1)
        
        try:
            if '-' in pos_part:
                # Range: "0-2" (inclusive end)
                start, end = map(int, pos_part.split('-', 1))
                if start < len(filename):
                    result[field_name] = filename[start:end+1]
                else:
                    result[field_name] = ""
            else:
                # Single position: "0"
                pos = int(pos_part)
                if pos < len(filename):
                    result[field_name] = filename[pos]
                else:
                    result[field_name] = ""
        except ValueError as e:
            raise ValueError(f"Invalid position specification '{pos_part}': {e}")
    
    return result


def metadata_extractor(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Extract file metadata as fields.
    
    Positional args: [field1, field2, field3, ...] (available: created, modified, size)
    
    Examples:
        metadata,created,modified,size  → Extract creation date, modification date, and file size
        metadata,size                   → Extract only file size
    
    Returns:
        Dict with requested metadata fields
    """
    available_fields = ['created', 'modified', 'size']
    
    if not positional_args:
        # Default to all fields
        requested_fields = available_fields
    else:
        requested_fields = positional_args
    
    result = {}
    
    for field in requested_fields:
        if field not in available_fields:
            raise ValueError(f"Unknown metadata field '{field}'. Available: {', '.join(available_fields)}")
        
        # Handle timestamp fields - check for both 'created'/'modified' and 'created_timestamp'/'modified_timestamp'
        if field in ['created', 'modified']:
            timestamp_key = f'{field}_timestamp'
            if timestamp_key in context.metadata:
                timestamp = context.metadata[timestamp_key]
                if isinstance(timestamp, (int, float)):
                    # Convert Unix timestamp to datetime
                    dt = datetime.fromtimestamp(timestamp)
                    result[field] = dt.strftime('%Y-%m-%d')
                else:
                    result[field] = str(timestamp)
            elif field in context.metadata:
                timestamp = context.metadata[field]
                if isinstance(timestamp, datetime):
                    result[field] = timestamp.strftime('%Y-%m-%d')
                else:
                    result[field] = str(timestamp)
            else:
                result[field] = ''
        elif field in context.metadata:
            # Handle other fields like 'size'
            if field == 'size':
                # Format size as KB
                size_bytes = context.metadata[field]
                result[field] = str(size_bytes // 1024) if size_bytes >= 1024 else '0'
            else:
                result[field] = str(context.metadata[field])
        else:
            # Default empty value when metadata not available
            result[field] = ''
    
    return result


# Registry of built-in extractor functions
BUILTIN_EXTRACTORS = {
    'split': split_extractor,
    'regex': regex_extractor,
    'position': position_extractor,
    'metadata': metadata_extractor,
}