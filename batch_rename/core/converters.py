"""
Built-in converters for transforming extracted data.

Converters take extracted data and return formatted data for filename generation.
"""

from pathlib import Path
from typing import Dict, Any, Callable

from .function_loader import load_custom_function


def uppercase_converter(extracted_data: Dict[str, Any], filename: str, file_path: Path, metadata: Dict[str, Any], **args) -> Dict[str, Any]:
    """
    Convert specified fields to uppercase.
    
    Args:
        fields: Comma-separated list of fields to convert
        
    Example:
        extracted_data: {"dept": "hr", "type": "report"}
        fields: "dept"
        result: {"dept": "HR", "type": "report"}
    """
    fields_str = args.get('fields', '')
    if not fields_str:
        raise ValueError("uppercase converter requires 'fields' argument")
    
    field_names = [f.strip() for f in fields_str.split(',')]
    result = extracted_data.copy()
    
    for field_name in field_names:
        if field_name in result and result[field_name]:
            result[field_name] = str(result[field_name]).upper()
    
    return result


"""
Built-in converters for transforming extracted data.

Converters take extracted data and return formatted data for filename generation.
"""

from pathlib import Path
from typing import Dict, Any, Callable, List

from .function_loader import load_custom_function


def pad_numbers_converter(extracted_data: Dict[str, Any], filename: str, file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> Dict[str, Any]:
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
    
    result = extracted_data.copy()
    
    if field in result and result[field]:
        # Extract numeric part and pad
        value = str(result[field])
        # Handle cases like "v2" -> "v002"
        if value.isdigit():
            result[field] = value.zfill(width)
        else:
            # Try to find and pad just the numeric part
            import re
            match = re.search(r'(\d+)', value)
            if match:
                number = match.group(1)
                padded_number = number.zfill(width)
                result[field] = value.replace(number, padded_number)
    
    return result


def template_converter(extracted_data: Dict[str, Any], filename: str, file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Apply Python format string template.
    
    Positional args: [pattern]
    Keyword args: pattern=template_string
    
    Examples:
        template,"{dept}_{type}_{date}"
        template,pattern="{dept}_{sequence:03d}"
    """
    # Handle positional arguments
    if positional_args:
        pattern = positional_args[0]
    else:
        # Handle keyword arguments
        pattern = kwargs.get('pattern')
    
    if not pattern:
        raise ValueError("template converter requires pattern")
    
    try:
        # Convert string numbers to integers for formatting
        format_data = {}
        for key, value in extracted_data.items():
            if value and str(value).isdigit():
                format_data[key] = int(value)
            else:
                format_data[key] = value
        
        formatted_name = pattern.format(**format_data)
        return {'formatted_name': formatted_name}
    
    except (KeyError, ValueError) as e:
        raise ValueError(f"Template formatting failed: {e}")


def date_format_converter(extracted_data: Dict[str, Any], filename: str, file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Format date fields.
    
    Positional args: [field, input_format, output_format] or [field] (uses defaults)
    Keyword args: field=field_name, input_format=%Y%m%d, output_format=%Y-%m-%d
    
    Examples:
        date_format,date,"%Y%m%d","%Y-%m-%d"
        date_format,date  → uses default formats
        date_format,field=date,output_format="%Y-%m-%d"
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
    
    if not field:
        raise ValueError("date_format converter requires field name")
    
    result = extracted_data.copy()
    
    if field in result and result[field]:
        try:
            import datetime
            date_obj = datetime.datetime.strptime(str(result[field]), input_format)
            result[field] = date_obj.strftime(output_format)
        except ValueError as e:
            raise ValueError(f"Date formatting failed for field '{field}': {e}")
    
    return result


def stringsmith_converter(extracted_data: Dict[str, Any], filename: str, file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Apply StringSmith template for conditional formatting.
    
    Positional args: [template]
    Keyword args: template=stringsmith_template
    
    Examples:
        stringsmith,"{{;dept;}}{{_;type;}}{{_;date;}}"
        stringsmith,template="{{;dept;}}{{_;type;}}{{_;date;}}"
    """
    # Handle positional arguments
    if positional_args:
        template_str = positional_args[0]
    else:
        # Handle keyword arguments
        template_str = kwargs.get('template')
    
    if not template_str:
        raise ValueError("stringsmith converter requires template")
    
    try:
        # Import StringSmith from the correct location
        import sys
        from pathlib import Path
        
        # Add the shared_utils path (from debug we know it's in the project root)
        stringsmith_path = Path.cwd()
        if stringsmith_path.exists():
            sys.path.insert(0, str(stringsmith_path))
        
        from shared_utils.stringsmith import TemplateFormatter
        
        # Create formatter and apply template
        formatter = TemplateFormatter(template_str)
        
        # Clean data - convert None to empty string for StringSmith
        clean_data = {}
        for key, value in extracted_data.items():
            if value is None:
                clean_data[key] = ""  # StringSmith will make section disappear
            else:
                clean_data[key] = str(value)
        
        formatted_name = formatter.format(**clean_data)
        return {'formatted_name': formatted_name}
        
    except ImportError:
        raise ValueError("StringSmith not available. Install stringsmith or use 'template' converter instead.")
    except Exception as e:
        raise ValueError(f"StringSmith formatting failed: {e}")


# Registry of built-in converters
BUILTIN_CONVERTERS = {
    'pad_numbers': pad_numbers_converter,
    'template': template_converter,
    'date_format': date_format_converter,
    'stringsmith': stringsmith_converter,
}


def get_converter(converter_name: str, converter_args: Dict[str, Any]) -> Callable:
    """
    Get converter function (built-in or custom).
    
    Args:
        converter_name: Name of built-in converter or path to custom function
        converter_args: Dict with 'positional' and 'keyword' args
        
    Returns:
        Converter function ready to call
    """
    if converter_name in BUILTIN_CONVERTERS:
        # Built-in converter
        converter_func = BUILTIN_CONVERTERS[converter_name]
        
        # Combine positional and keyword args
        pos_args = converter_args.get('positional', [])
        kwargs = converter_args.get('keyword', {})
        
        def configured_converter(extracted_data: Dict[str, Any], filename: str, file_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
            return converter_func(extracted_data, filename, file_path, metadata, pos_args, **kwargs)
        
        return configured_converter
    
    elif Path(converter_name).suffix == '.py':
        # Custom converter function
        return load_custom_function(converter_name, 'convert_data')
    
    else:
        raise ValueError(f"Unknown converter: {converter_name}")