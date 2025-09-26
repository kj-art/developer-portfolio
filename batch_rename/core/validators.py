"""
Function signature validators for batch rename custom functions.

Provides type-specific validation for extractors, converters, templates, filters, and all-in-one functions.
"""

import inspect
from typing import Callable, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of function validation."""
    valid: bool
    message: str
    parameters: List[inspect.Parameter]


def _looks_like_context_param(param: inspect.Parameter) -> bool:
    """Check if parameter appears to be ProcessingContext."""
    # Check type annotation
    if param.annotation != param.empty:
        annotation_str = str(param.annotation)
        if 'ProcessingContext' in annotation_str:
            return True
    
    # Check parameter name
    context_names = ['context', 'ctx', 'processing_context']
    return param.name.lower() in context_names


def validate_extractor_function(function: Callable) -> ValidationResult:
    """
    Validate extractor function signature.
    
    Expected signature: def extract_data(context: ProcessingContext, *args, **kwargs) -> Dict[str, Any]
    Expected return: Dictionary with extracted field data
    """
    try:
        sig = inspect.signature(function)
        params = list(sig.parameters.values())
        
        validation_points = []
        
        # Check: at least one parameter (ProcessingContext)
        if len(params) == 0:
            return ValidationResult(
                valid=False,
                message='Extractor must accept at least one parameter (ProcessingContext)',
                parameters=[]
            )
        
        # Check first parameter for ProcessingContext
        first_param = params[0]
        if _looks_like_context_param(first_param):
            validation_points.append(f"✓ First parameter '{first_param.name}' appears to be ProcessingContext")
        else:
            validation_points.append(f"⚠ First parameter '{first_param.name}' should be ProcessingContext")
        
        # Check return annotation
        if sig.return_annotation != sig.empty:
            if 'dict' in str(sig.return_annotation).lower() or 'Dict' in str(sig.return_annotation):
                validation_points.append("✓ Return type annotation indicates Dict")
            else:
                validation_points.append("⚠ Return type should be Dict[str, Any] (extracted fields)")
        else:
            validation_points.append("ℹ No return type annotation (should return Dict[str, Any])")
        
        # Get additional parameters for GUI input
        additional_params = params[1:]
        
        # Build message
        message = f"Extractor: {function.__name__}()\n" + "\n".join(validation_points)
        message += "\n\nShould return: Dict with extracted field data"
        
        return ValidationResult(
            valid=True,
            message=message,
            parameters=additional_params
        )
                
    except Exception as e:
        return ValidationResult(
            valid=False,
            message=f'Error inspecting extractor function: {str(e)}',
            parameters=[]
        )


def validate_converter_function(function: Callable) -> ValidationResult:
    """
    Validate converter function signature.
    
    Expected signature: def convert_data(context: ProcessingContext, *args, **kwargs) -> Dict[str, Any]
    Expected return: Dictionary with converted/transformed field data
    """
    try:
        sig = inspect.signature(function)
        params = list(sig.parameters.values())
        
        validation_points = []
        
        if len(params) == 0:
            return ValidationResult(
                valid=False,
                message='Converter must accept at least one parameter (ProcessingContext)',
                parameters=[]
            )
        
        # Check first parameter for ProcessingContext
        first_param = params[0]
        if _looks_like_context_param(first_param):
            validation_points.append(f"✓ First parameter '{first_param.name}' appears to be ProcessingContext")
        else:
            validation_points.append(f"⚠ First parameter '{first_param.name}' should be ProcessingContext")
        
        # Check return annotation
        if sig.return_annotation != sig.empty:
            if 'dict' in str(sig.return_annotation).lower() or 'Dict' in str(sig.return_annotation):
                validation_points.append("✓ Return type annotation indicates Dict")
            else:
                validation_points.append("⚠ Return type should be Dict[str, Any] (transformed data)")
        else:
            validation_points.append("ℹ No return type annotation (should return Dict[str, Any])")
        
        additional_params = params[1:]
        
        message = f"Converter: {function.__name__}()\n" + "\n".join(validation_points)
        message += "\n\nShould return: Dict with converted/transformed data"
        
        return ValidationResult(
            valid=True,
            message=message,
            parameters=additional_params
        )
                
    except Exception as e:
        return ValidationResult(
            valid=False,
            message=f'Error inspecting converter function: {str(e)}',
            parameters=[]
        )


def validate_template_function(function: Callable) -> ValidationResult:
    """
    Validate template function signature.
    
    Expected signature: def format_filename(context: ProcessingContext, *args, **kwargs) -> str
    Expected return: Formatted filename string (without extension)
    """
    try:
        sig = inspect.signature(function)
        params = list(sig.parameters.values())
        
        validation_points = []
        
        if len(params) == 0:
            return ValidationResult(
                valid=False,
                message='Template must accept at least one parameter (ProcessingContext)',
                parameters=[]
            )
        
        # Check first parameter for ProcessingContext
        first_param = params[0]
        if _looks_like_context_param(first_param):
            validation_points.append(f"✓ First parameter '{first_param.name}' appears to be ProcessingContext")
        else:
            validation_points.append(f"⚠ First parameter '{first_param.name}' should be ProcessingContext")
        
        # Check return annotation
        if sig.return_annotation != sig.empty:
            if 'str' in str(sig.return_annotation).lower():
                validation_points.append("✓ Return type annotation indicates str")
            else:
                validation_points.append("⚠ Return type should be str (formatted filename)")
        else:
            validation_points.append("ℹ No return type annotation (should return str)")
        
        additional_params = params[1:]
        
        message = f"Template: {function.__name__}()\n" + "\n".join(validation_points)
        message += "\n\nShould return: str (formatted filename without extension)"
        
        return ValidationResult(
            valid=True,
            message=message,
            parameters=additional_params
        )
                
    except Exception as e:
        return ValidationResult(
            valid=False,
            message=f'Error inspecting template function: {str(e)}',
            parameters=[]
        )


def validate_filter_function(function: Callable) -> ValidationResult:
    """
    Validate filter function signature.
    
    Expected signature: def filter_file(context: ProcessingContext, *args, **kwargs) -> bool
    Expected return: True if file should be processed, False to skip
    """
    try:
        sig = inspect.signature(function)
        params = list(sig.parameters.values())
        
        validation_points = []
        
        if len(params) == 0:
            return ValidationResult(
                valid=False,
                message='Filter must accept at least one parameter (ProcessingContext)',
                parameters=[]
            )
        
        # Check first parameter for ProcessingContext
        first_param = params[0]
        if _looks_like_context_param(first_param):
            validation_points.append(f"✓ First parameter '{first_param.name}' appears to be ProcessingContext")
        else:
            validation_points.append(f"⚠ First parameter '{first_param.name}' should be ProcessingContext")
        
        # Check return annotation
        if sig.return_annotation != sig.empty:
            if 'bool' in str(sig.return_annotation).lower():
                validation_points.append("✓ Return type annotation indicates bool")
            else:
                validation_points.append("⚠ Return type should be bool (True = process, False = skip)")
        else:
            validation_points.append("ℹ No return type annotation (should return bool)")
        
        additional_params = params[1:]
        
        message = f"Filter: {function.__name__}()\n" + "\n".join(validation_points)
        message += "\n\nShould return: bool (True = process file, False = skip file)"
        
        return ValidationResult(
            valid=True,
            message=message,
            parameters=additional_params
        )
                
    except Exception as e:
        return ValidationResult(
            valid=False,
            message=f'Error inspecting filter function: {str(e)}',
            parameters=[]
        )


def validate_allinone_function(function: Callable) -> ValidationResult:
    """
    Validate all-in-one function signature.
    
    Expected signature: def process_file(context: ProcessingContext, *args, **kwargs) -> str
    Expected return: Formatted filename string (handles extraction + conversion + formatting)
    """
    try:
        sig = inspect.signature(function)
        params = list(sig.parameters.values())
        
        validation_points = []
        
        if len(params) == 0:
            return ValidationResult(
                valid=False,
                message='All-in-one function must accept at least one parameter (ProcessingContext)',
                parameters=[]
            )
        
        # Check first parameter for ProcessingContext
        first_param = params[0]
        if _looks_like_context_param(first_param):
            validation_points.append(f"✓ First parameter '{first_param.name}' appears to be ProcessingContext")
        else:
            validation_points.append(f"⚠ First parameter '{first_param.name}' should be ProcessingContext")
        
        # Check return annotation
        if sig.return_annotation != sig.empty:
            if 'str' in str(sig.return_annotation).lower():
                validation_points.append("✓ Return type annotation indicates str")
            else:
                validation_points.append("⚠ Return type should be str (formatted filename)")
        else:
            validation_points.append("ℹ No return type annotation (should return str)")
        
        additional_params = params[1:]
        
        message = f"All-in-One: {function.__name__}()\n" + "\n".join(validation_points)
        message += "\n\nShould return: str (complete formatted filename without extension)"
        
        return ValidationResult(
            valid=True,
            message=message,
            parameters=additional_params
        )
                
    except Exception as e:
        return ValidationResult(
            valid=False,
            message=f'Error inspecting all-in-one function: {str(e)}',
            parameters=[]
        )


# Function type mappings for easy access
FUNCTION_VALIDATORS = {
    'extractor': validate_extractor_function,
    'converter': validate_converter_function, 
    'template': validate_template_function,
    'filter': validate_filter_function,
    'allinone': validate_allinone_function
}


def get_validator(function_type: str) -> Callable:
    """
    Get appropriate validator for function type.
    
    Args:
        function_type: Type of function ('extractor', 'converter', 'template', 'filter', 'allinone')
        
    Returns:
        Validator function
        
    Raises:
        ValueError: If function_type is not recognized
    """
    if function_type not in FUNCTION_VALIDATORS:
        raise ValueError(f"Unknown function type: {function_type}")
    
    return FUNCTION_VALIDATORS[function_type]