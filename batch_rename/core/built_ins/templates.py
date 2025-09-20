"""
Built-in templates for formatting extracted data into filenames.

Templates take a ProcessingContext (with extracted_data) and return formatted filename data.
Templates are applied AFTER all converters and are responsible for final filename formatting.
"""

from pathlib import Path
from typing import Dict, Any, Callable, List

from ..processing_context import ProcessingContext
from ..function_loader import load_custom_function


def template_formatter(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Apply Python format string template to generate formatted filename.
    
    Positional args: [template_string] 
    Keyword args: template=template_string
    
    Examples:
        template,"{dept}_{type}_{date}"
        template,template="{dept}_{type}_{date}"
    
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
    
    try:
        # Apply Python string formatting
        formatted_name = template_str.format(**context.extracted_data)
        return formatted_name
    except KeyError as e:
        raise ValueError(f"Template variable not found in extracted data: {e}")
    except Exception as e:
        raise ValueError(f"Template formatting failed: {e}")


def stringsmith_formatter(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Apply StringSmith template with graceful missing field handling.
    
    Positional args: [template_string]
    Keyword args: template=template_string
    
    Examples:
        stringsmith,"{{;dept;}}{{_;type;}}{{_;date;}}"
        stringsmith,template="{{;dept;}}{{_;type;}}{{_;date;}}"
    
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
        raise ValueError("stringsmith formatter requires template string")
    
    if not context.has_extracted_data():
        return context.base_name
    
    try:
        import sys
        from pathlib import Path
        
        stringsmith_path = Path.cwd()
        if stringsmith_path.exists():
            sys.path.insert(0, str(stringsmith_path))
        
        from shared_utils.stringsmith import TemplateFormatter
        
        # Create formatter and apply template
        formatter = TemplateFormatter(template_str, skip_empty=True)
        
        # Clean data - convert None to empty string for StringSmith
        clean_data = {}
        for key, value in context.extracted_data.items():
            if value is None:
                clean_data[key] = ""  # StringSmith will make section disappear
            else:
                clean_data[key] = str(value)
        
        formatted_name = formatter.format(**clean_data)
        return formatted_name
        
    except ImportError:
        raise ValueError("StringSmith not available. Install stringsmith or use 'template' formatter instead.")
    except Exception as e:
        raise ValueError(f"StringSmith formatting failed: {e}")


# Registry of built-in templates
BUILTIN_TEMPLATES = {
    'template': template_formatter,
    'stringsmith': stringsmith_formatter,
}


def get_template(template_name: str, template_args: Dict[str, Any]) -> Callable:
    """
    Get template function (built-in or custom).
    
    Args:
        template_name: Name of built-in template or path to custom function
        template_args: Dict with 'positional' and 'keyword' args
        
    Returns:
        Template function ready to call with ProcessingContext
    """
    if template_name in BUILTIN_TEMPLATES:
        # Built-in template
        template_func = BUILTIN_TEMPLATES[template_name]
        
        # Combine positional and keyword args
        pos_args = template_args.get('positional', [])
        kwargs = template_args.get('keyword', {})
        
        def configured_template(context: ProcessingContext) -> str:
            return template_func(context, pos_args, **kwargs)
        
        return configured_template
    
    elif Path(template_name).suffix == '.py':
        # Custom template function
        custom_func = load_custom_function(template_name, template_args.get('positional', [None])[0])
        
        # Get additional arguments (excluding function name)
        pos_args = template_args.get('positional', [])[1:]  # Skip function name
        kwargs = template_args.get('keyword', {})
        
        def configured_custom_template(context: ProcessingContext) -> str:
            return custom_func(context, *pos_args, **kwargs)
        
        return configured_custom_template
    
    else:
        raise ValueError(f"Unknown template: {template_name}")


def is_template_function(function_name: str) -> bool:
    """
    Check if a function name is a built-in template function.
    
    Args:
        function_name: Name to check
        
    Returns:
        True if it's a built-in template function
    """
    return function_name in BUILTIN_TEMPLATES