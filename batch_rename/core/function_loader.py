"""
Custom function loader for user-provided Python files.

Handles loading and validation of custom extractor, converter, and filter functions.
"""

import importlib.util
from pathlib import Path
from typing import Callable


def load_custom_function(file_path: str, function_name: str) -> Callable:
    """
    Load a custom function from a Python file.
    
    Args:
        file_path: Path to Python file containing the function
        function_name: Name of function to load
        
    Returns:
        The loaded function
        
    Raises:
        ValueError: If file doesn't exist or function not found
        ImportError: If file can't be imported
    """
    path = Path(file_path)
    
    if not path.exists():
        raise ValueError(f"Function file not found: {file_path}")
    
    if not path.suffix == '.py':
        raise ValueError(f"Function file must be a .py file: {file_path}")
    
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("custom_module", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the function
        if not hasattr(module, function_name):
            raise ValueError(f"Function '{function_name}' not found in {file_path}")
        
        func = getattr(module, function_name)
        
        if not callable(func):
            raise ValueError(f"'{function_name}' in {file_path} is not a function")
        
        return func
        
    except Exception as e:
        if isinstance(e, (ValueError, ImportError)):
            raise
        else:
            raise ImportError(f"Error loading function from {file_path}: {e}")


def validate_extractor_function(func: Callable) -> bool:
    """
    Validate that a function has the correct signature for an extractor.
    
    Expected signature:
    def extract_data(context: ProcessingContext, *args, **kwargs) -> dict
    """
    try:
        import inspect
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        
        # Check that function has at least one parameter (ProcessingContext)
        if len(params) >= 1:
            # Check if first parameter name suggests ProcessingContext
            first_param = params[0]
            # Accept common parameter names for ProcessingContext
            valid_names = ['context', 'ctx', 'processing_context', 'filename', 'file_path']
            return any(name in first_param.lower() for name in valid_names) or len(params) >= 3
        else:
            return False
    except Exception:
        # If we can't inspect, assume it's valid
        return True


def validate_converter_function(func: Callable) -> bool:
    """
    Validate that a function has the correct signature for a converter.
    
    Expected signature:
    def convert_data(context: ProcessingContext, *args, **kwargs) -> dict
    """
    try:
        import inspect
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        
        # Check that function has at least one parameter (ProcessingContext)
        if len(params) >= 1:
            return True
        else:
            return False
    except Exception:
        return True


def validate_combined_function(func: Callable) -> bool:
    """
    Validate that a function has the correct signature for extract_and_convert.
    
    Expected signature:
    def extract_and_convert(context: ProcessingContext, *args, **kwargs) -> dict
    """
    try:
        import inspect
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        
        # Check that function has at least one parameter (ProcessingContext)
        if len(params) >= 1:
            return True
        else:
            return False
    except Exception:
        return True