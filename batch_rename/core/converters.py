"""
Built-in converters for transforming extracted data.

Converters take a ProcessingContext (with extracted_data) and return transformed data.
Converters should ONLY modify field values, never add/remove fields or do final formatting.
Final formatting is the job of templates.
"""

from pathlib import Path
from typing import Dict, Any, Callable, List
import re
import datetime

from .processing_context import ProcessingContext
from .function_loader import load_custom_function


def pad_numbers_converter(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Zero-pad numbers in specified fields.
    
    Positional args: [field, width] or [field] (width defaults to 3)
    Keyword args: field=field_name, width=3
    
    Examples:
        pad_numbers,sequence,3  → field="sequence", width=3
        pad_numbers,sequence    → field="sequence", width=3 (default)
        pad_numbers,field=sequence,width=4
    """
    # Handle positional arguments
    if positional_args:
        field = positional_args[0]
        width = int(positional_args[1]) if len(positional_args) > 1 else 3
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
        # Handle cases like "v2" -> "v002"
        if value.isdigit():
            result[field] = value.zfill(width)
        else:
            # Try to find and pad just the numeric part
            match = re.search(r'(\d+)', value)
            if match:
                number = match.group(1)
                padded_number = number.zfill(width)
                result[field] = value.replace(number, padded_number)
    elif field not in result:
        available_fields = list(result.keys())
        raise ValueError(f"Field '{field}' not found. Available fields: {available_fields}")
    
    return result


def date_format_converter(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Convert date formats in extracted data.
    
    Positional args: [field, input_format, output_format] or [field, input_format] (output defaults to %Y-%m-%d)
    Keyword args: field=field_name, input_format=fmt, output_format=fmt
    
    Examples:
        date_format,date,%Y%m%d,%Y-%m-%d
        date_format,field=created,input_format=%m/%d/%Y,output_format=%Y-%m-%d
    """
    # Handle positional arguments
    if positional_args:
        field = positional_args[0]
        input_format = positional_args[1] if len(positional_args) > 1 else '%Y%m%d'
        output_format = positional_args[2] if len(positional_args) > 2 else '%Y-%m-%d'
    else:
        # Handle keyword arguments
        field = kwargs.get('field')
        input_format = kwargs.get('input_format', '%Y%m%d')
        output_format = kwargs.get('output_format', '%Y-%m-%d')
    
    if not field or not input_format:
        raise ValueError("date_format converter requires field and input_format")
    
    if not context.has_extracted_data():
        return context.extracted_data or {}
    
    result = context.extracted_data.copy()
    
    if field in result and result[field]:
        try:
            # Parse the date using input format
            date_obj = datetime.datetime.strptime(str(result[field]), input_format)
            # Format using output format
            result[field] = date_obj.strftime(output_format)
        except ValueError as e:
            raise ValueError(f"Date parsing failed for field '{field}' with value '{result[field]}': {e}")
    elif field not in result:
        available_fields = list(result.keys())
        raise ValueError(f"Field '{field}' not found. Available fields: {available_fields}")
    
    return result


def case_converter(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Convert field values to specified case.
    
    Positional args: [field, case_type] where case_type is 'upper', 'lower', 'title', 'capitalize'
    Keyword args: field=field_name, case=case_type
    
    Examples:
        case,dept,upper     → Convert 'dept' field to uppercase
        case,field=name,case=title  → Convert 'name' field to title case
    """
    # Handle positional arguments
    if positional_args:
        field = positional_args[0]
        case_type = positional_args[1] if len(positional_args) > 1 else 'lower'
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


# Registry of built-in converters (templates removed)
BUILTIN_CONVERTERS = {
    'pad_numbers': pad_numbers_converter,
    'date_format': date_format_converter,
    'case': case_converter,
}


def get_converter(converter_name: str, converter_args: Dict[str, Any]) -> Callable:
    """
    Get converter function (built-in or custom).
    
    Args:
        converter_name: Name of built-in converter or path to custom function
        converter_args: Dict with 'positional' and 'keyword' args
        
    Returns:
        Converter function ready to call with ProcessingContext
    """
    if converter_name in BUILTIN_CONVERTERS:
        # Built-in converter
        converter_func = BUILTIN_CONVERTERS[converter_name]
        
        # Combine positional and keyword args
        pos_args = converter_args.get('positional', [])
        kwargs = converter_args.get('keyword', {})
        
        def configured_converter(context: ProcessingContext) -> Dict[str, Any]:
            return converter_func(context, pos_args, **kwargs)
        
        return configured_converter
    
    elif Path(converter_name).suffix == '.py':
        # Custom converter function
        custom_func = load_custom_function(converter_name, converter_args.get('positional', [None])[0])
        
        # Get additional arguments (excluding function name)
        pos_args = converter_args.get('positional', [])[1:]  # Skip function name
        kwargs = converter_args.get('keyword', {})
        
        def configured_custom_converter(context: ProcessingContext) -> Dict[str, Any]:
            return custom_func(context, *pos_args, **kwargs)
        
        return configured_custom_converter
    
    else:
        raise ValueError(f"Unknown converter: {converter_name}")


def is_converter_function(function_name: str) -> bool:
    """
    Check if a function name is a built-in converter function.
    
    Args:
        function_name: Name to check
        
    Returns:
        True if it's a built-in converter function
    """
    return function_name in BUILTIN_CONVERTERS