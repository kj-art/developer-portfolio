"""
Built-in converters for transforming extracted data fields.

Converters take a ProcessingContext (with extracted_data) and return Dict[str, Any] with transformed data.
All converters preserve field structure - same keys in and out.
"""

from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from ..processing_context import ProcessingContext


def pad_numbers_converter(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Pad numeric fields with leading zeros.
    
    Positional args: [field_name, width]
    Keyword args: field=field_name, width=width
    
    Examples:
        pad_numbers,sequence,3  → "5" becomes "005"
        pad_numbers,field=id,width=4  → "42" becomes "0042"
    
    Returns:
        Dict with the specified field zero-padded
    """
    # Handle positional arguments
    if len(positional_args) >= 2:
        field = positional_args[0]
        width = int(positional_args[1])
    else:
        # Handle keyword arguments
        field = kwargs.get('field')
        width = int(kwargs.get('width', 3))
    
    if not field:
        raise ValueError("pad_numbers converter requires field name")
    
    if not context.has_extracted_data():
        return context.extracted_data or {}
    
    result = context.extracted_data.copy()
    
    if field in result and result[field]:
        # Extract numeric part and pad
        value = str(result[field])
        # Try to extract just the numbers
        numeric_part = ''.join(filter(str.isdigit, value))
        if numeric_part:
            padded = numeric_part.zfill(width)
            # Replace the numeric part in the original value
            result[field] = value.replace(numeric_part, padded, 1)
    elif field not in result:
        available_fields = list(result.keys())
        raise ValueError(f"Field '{field}' not found. Available fields: {available_fields}")
    
    return result


def date_format_converter(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Convert date field from one format to another.
    
    Positional args: [field_name, input_format, output_format]
    Keyword args: field=field_name, input_format=format, output_format=format
    
    Examples:
        date_format,date,%Y%m%d,%Y-%m-%d  → "20231201" becomes "2023-12-01"
        date_format,created,%Y-%m-%d,%B %d, %Y  → "2023-12-01" becomes "December 01, 2023"
    
    Returns:
        Dict with the date field reformatted
    """
    # Handle positional arguments
    if len(positional_args) >= 3:
        field = positional_args[0]
        input_fmt = positional_args[1]
        output_fmt = positional_args[2]
    else:
        # Handle keyword arguments
        field = kwargs.get('field')
        input_fmt = kwargs.get('input_format', '%Y%m%d')
        output_fmt = kwargs.get('output_format', '%Y-%m-%d')
    
    if not field:
        raise ValueError("date_format converter requires field name")
    
    if not context.has_extracted_data():
        return context.extracted_data or {}
    
    result = context.extracted_data.copy()
    
    if field in result and result[field]:
        try:
            # Parse the date with input format
            date_obj = datetime.strptime(str(result[field]), input_fmt)
            # Format with output format
            result[field] = date_obj.strftime(output_fmt)
        except ValueError as e:
            # If date parsing fails, keep original value
            pass
    elif field not in result:
        available_fields = list(result.keys())
        raise ValueError(f"Field '{field}' not found. Available fields: {available_fields}")
    
    return result


def case_converter(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Convert field text case.
    
    Positional args: [field_name, case_type]
    Keyword args: field=field_name, case=case_type
    Case types: upper, lower, title, capitalize
    
    Examples:
        case,dept,upper  → "hr" becomes "HR"
        case,name,title  → "john doe" becomes "John Doe"
    
    Returns:
        Dict with the specified field case-converted
    """
    # Handle positional arguments
    if len(positional_args) >= 2:
        field = positional_args[0]
        case_type = positional_args[1]
    else:
        # Handle keyword arguments
        field = kwargs.get('field')
        case_type = kwargs.get('case', 'lower')
    
    if not field:
        raise ValueError("case converter requires field name")
    
    if case_type not in ['upper', 'lower', 'title', 'capitalize']:
        raise ValueError(f"Invalid case type '{case_type}'. Must be: upper, lower, title, capitalize")
    
    if not context.has_extracted_data():
        return context.extracted_data or {}
    
    result = context.extracted_data.copy()
    
    if field in result and result[field]:
        value = str(result[field])
        if case_type == 'upper':
            result[field] = value.upper()
        elif case_type == 'lower':
            result[field] = value.lower()
        elif case_type == 'title':
            result[field] = value.title()
        elif case_type == 'capitalize':
            result[field] = value.capitalize()
    elif field not in result:
        available_fields = list(result.keys())
        raise ValueError(f"Field '{field}' not found. Available fields: {available_fields}")
    
    return result


# Registry of built-in converters
BUILTIN_CONVERTERS = {
    'pad_numbers': pad_numbers_converter,
    'date_format': date_format_converter,
    'case': case_converter,
}