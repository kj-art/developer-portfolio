"""
Built-in all-in-one functions for batch rename operations.

These functions handle extraction, conversion, and formatting in a single step.
"""

from typing import Dict, Any, List
from ..processing_context import ProcessingContext


def replace_all_in_one(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Built-in find and replace all-in-one function.
    
    Performs multiple find/replace operations on the filename.
    
    Positional args: [find1, replace1, find2, replace2, ...]
    Keyword args: find_replace_pairs as dict
    
    Examples:
        replace,report,summary → replaces "report" with "summary"
        replace,HR,Human_Resources,2024,2025 → multiple replacements
    
    Args:
        context: ProcessingContext with filename info
        positional_args: List of alternating find/replace strings
        **kwargs: Optional keyword arguments (not used)
        
    Returns:
        Modified filename string
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


# Registry of built-in all-in-one functions
BUILTIN_ALL_IN_ONE = {
    'replace': replace_all_in_one,
}


def get_builtin_all_in_one(function_name: str, function_args: Dict[str, Any]):
    """
    Get built-in all-in-one function.
    
    Args:
        function_name: Name of the built-in function
        function_args: Arguments for the function
        
    Returns:
        Configured function ready to call with ProcessingContext
    """
    if function_name in BUILTIN_ALL_IN_ONE:
        func = BUILTIN_ALL_IN_ONE[function_name]
        pos_args = function_args.get('positional', [])
        kwargs = function_args.get('keyword', {})
        
        def configured_function(context: ProcessingContext) -> str:
            return func(context, pos_args, **kwargs)
        
        return configured_function
    else:
        raise ValueError(f"Unknown built-in all-in-one function: {function_name}")


def is_builtin_all_in_one(function_name: str) -> bool:
    """Check if a function name is a built-in all-in-one function."""
    return function_name in BUILTIN_ALL_IN_ONE