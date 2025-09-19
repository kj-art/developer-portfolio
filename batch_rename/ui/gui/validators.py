"""
Validation functions for batch rename FunctionSelector widgets.
"""

import inspect
from .function_selector import ValidationResult


def batch_rename_validator(function) -> ValidationResult:
    """Validator for batch rename functions that expect ProcessingContext as first parameter."""
    try:
        sig = inspect.signature(function)
        params = list(sig.parameters.values())
        
        validation_points = []
        
        # Check: at least one parameter (should be ProcessingContext)
        if len(params) == 0:
            return ValidationResult(
                valid=False,
                message='Function must accept at least one parameter (ProcessingContext)',
                parameters=[]
            )
        
        # Check first parameter name/type hint for ProcessingContext
        first_param = params[0]
        context_hints = ['ProcessingContext', 'context']
        if (first_param.annotation != first_param.empty and 
            'ProcessingContext' in str(first_param.annotation)) or \
           any(hint in first_param.name.lower() for hint in context_hints):
            validation_points.append(f"✓ First parameter '{first_param.name}' appears to be ProcessingContext")
        else:
            validation_points.append(f"⚠ First parameter '{first_param.name}' should be ProcessingContext")
        
        # Get additional parameters for return value
        additional_params = params[1:]
        
        # Build multi-line message
        message = f"Valid signature: {function.__name__}()\n" + "\n".join(validation_points)
        
        return ValidationResult(
            valid=True,
            message=message,
            parameters=additional_params  # Skip first parameter (ProcessingContext)
        )
                
    except Exception as e:
        return ValidationResult(
            valid=False,
            message=f'Error inspecting function: {str(e)}',
            parameters=[]
        )