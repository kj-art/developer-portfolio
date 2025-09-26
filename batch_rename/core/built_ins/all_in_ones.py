"""
Built-in all-in-one functions for batch rename operations.

These functions handle extraction, conversion, and formatting in a single step.
All functions take ProcessingContext and return formatted filename strings.
"""

from typing import Dict, Any, List
from ..processing_context import ProcessingContext


def replace_all_in_one(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Built-in find and replace all-in-one function.
    
    Performs multiple find/replace operations on the filename.
    
    Positional args: [find1, replace1, find2, replace2, ...]
    Keyword args: Not used currently
    
    Examples:
        replace,report,summary → replaces "report" with "summary"
        replace,HR,Human_Resources,2024,2025 → multiple replacements
    
    Returns:
        Modified filename string (without extension)
    """
    if len(positional_args) % 2 != 0:
        raise ValueError("replace function requires pairs of find/replace arguments")
    
    # Start with the original filename (without extension)
    new_name = context.base_name
    
    # Process find/replace pairs
    for i in range(0, len(positional_args), 2):
        find_text = positional_args[i]
        replace_text = positional_args[i + 1]
        new_name = new_name.replace(find_text, replace_text)
    
    return new_name


def lowercase_all_in_one(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Convert filename to lowercase.
    
    Simple all-in-one function that converts the entire filename to lowercase.
    
    Returns:
        Lowercase filename string
    """
    return context.base_name.lower()


def uppercase_all_in_one(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Convert filename to uppercase.
    
    Simple all-in-one function that converts the entire filename to uppercase.
    
    Returns:
        Uppercase filename string
    """
    return context.base_name.upper()


def clean_filename_all_in_one(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Clean filename by removing special characters and normalizing spaces.
    
    Positional args: [replacement_char] (default: "_")
    
    Examples:
        clean_filename → Replace spaces and special chars with "_"
        clean_filename,- → Replace with "-" instead
    
    Returns:
        Cleaned filename string
    """
    import re
    
    replacement_char = positional_args[0] if positional_args else "_"
    
    # Start with original filename
    clean_name = context.base_name
    
    # Replace spaces with replacement character
    clean_name = clean_name.replace(" ", replacement_char)
    
    # Remove special characters (keep alphanumeric, underscore, hyphen)
    clean_name = re.sub(r'[^\w\-]', replacement_char, clean_name)
    
    # Collapse multiple replacement characters into single ones
    clean_name = re.sub(f'{re.escape(replacement_char)}+', replacement_char, clean_name)
    
    # Remove leading/trailing replacement characters
    clean_name = clean_name.strip(replacement_char)
    
    return clean_name if clean_name else context.base_name


# Registry of built-in all-in-one functions
BUILTIN_ALL_IN_ONE = {
    'replace': replace_all_in_one,
    'lowercase': lowercase_all_in_one,
    'uppercase': uppercase_all_in_one,
    'clean_filename': clean_filename_all_in_one,
}