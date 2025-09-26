"""
Built-in templates for formatting final filenames.

Templates take a ProcessingContext and return str (formatted filename without extension).
"""

import re
from typing import Dict, Any, List

from ..processing_context import ProcessingContext


def template_formatter(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Simple Python-style string template formatter.
    
    Positional args: [template_string]
    Keyword args: template=template_string
    
    Uses {field} syntax for field substitution.
    
    Examples:
        template,"{dept}_{type}_{date}"  → "HR_employee_2024"
        template,"{dept}-{type}.v{year}"  → "HR-employee.v2024"
    
    Returns:
        Formatted filename string (without extension)
    """
    # Handle positional arguments
    if positional_args:
        template_str = positional_args[0]
    else:
        # Handle keyword arguments
        template_str = kwargs.get('template')
    
    if not template_str:
        raise ValueError("template formatter requires template string")
    
    if not context.has_extracted_data():
        return context.base_name
    
    # Simple string formatting with extracted data
    try:
        return template_str.format(**context.extracted_data)
    except KeyError as e:
        # Handle missing fields by returning template with available substitutions
        available_data = {k: v for k, v in context.extracted_data.items() if v}
        try:
            # Try partial formatting by creating a safe formatter
            class SafeFormatter(str):
                def __mod__(self, values):
                    return self
                def format_map(self, mapping):
                    import string
                    formatter = string.Formatter()
                    args = []
                    kwargs = {}
                    for literal_text, field_name, format_spec, conversion in formatter.parse(self):
                        if field_name is not None and field_name in mapping:
                            kwargs[field_name] = mapping[field_name]
                    
                    # Build result with available fields only
                    result = self
                    for field, value in kwargs.items():
                        result = result.replace(f'{{{field}}}', str(value))
                    return result
            
            safe_template = SafeFormatter(template_str)
            return safe_template.format_map(available_data)
        except:
            return template_str  # Fallback to template string


def stringsmith_formatter(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Apply StringSmith template with graceful missing field handling.
    
    Positional args: [template_string]
    Keyword args: template=template_string
    
    StringSmith features:
    - {{field}} - Basic field substitution with graceful missing data handling
    - {{prefix;field;suffix}} - Conditional sections that disappear when field missing
    - {{#color@emphasis;prefix;field;suffix}} - Rich formatting with colors and text emphasis
    - {{!field}} - Mandatory fields (throws error if missing)
    
    Examples:
        stringsmith,"{{dept|upper}}_{{sequence:03d}}_{{date}}"
        stringsmith,"{{Department: ;dept;}} {{(ID: ;id;)}}"
    
    Returns:
        Formatted filename string (without extension)
    """
    # Handle positional arguments
    if positional_args:
        template_str = positional_args[0]
    else:
        # Handle keyword arguments
        template_str = kwargs.get('template')
    
    # Allow empty template string - return empty result
    if template_str is None:
        raise ValueError("stringsmith formatter requires template string")
    
    if template_str == '':
        return ''
    
    if not context.has_extracted_data():
        return context.base_name
    
    try:
        # Import StringSmith formatter from shared_utils
        from shared_utils.stringsmith import TemplateFormatter
        
        # Create formatter with the template
        formatter = TemplateFormatter(template_str)
        
        # Format using extracted data
        result = formatter.format(**context.extracted_data)
        
        return result
        
    except Exception as e:
        raise ValueError(f"StringSmith formatting failed: {e}")


def join_formatter(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Join specified fields with a separator.
    
    Positional args: [field1, field2, field3, ...] (field names to join)
    Keyword args: separator=sep (default: "_")
    
    Only includes fields that are specified and have non-empty values.
    
    Examples:
        join,dept,type,category,separator=_  → "HR_employee_data"
        join,dept,type,separator=-  → "HR-employee"
        join,dept,missing,type  → "HR_employee" (skips missing field)
    
    Returns:
        Specified fields joined with separator
    """
    if not context.has_extracted_data():
        return context.base_name
    
    # Get separator from kwargs
    separator = kwargs.get('separator', '_')
    
    # If no specific fields requested, use all fields
    if not positional_args:
        # Get all field values in the order they appear in the dict
        # Note: Python 3.7+ preserves dict insertion order
        values = []
        for field_name, value in context.extracted_data.items():
            if value:  # Only include non-empty values
                values.append(str(value))
        
        if values:
            return separator.join(values)
        else:
            return context.base_name  # Fallback to original name
    
    # Join only specified fields
    values = []
    for field_name in positional_args:
        if field_name in context.extracted_data:
            value = context.extracted_data[field_name]
            if value:  # Only include non-empty values
                values.append(str(value))
    
    if values:
        return separator.join(values)
    else:
        return context.base_name  # Fallback to original name


# Registry of built-in templates
BUILTIN_TEMPLATES = {
    'template': template_formatter,
    'stringsmith': stringsmith_formatter,
    'join': join_formatter,
}