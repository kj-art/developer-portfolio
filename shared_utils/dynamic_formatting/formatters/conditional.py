"""
Conditional formatting implementation with configurable graceful degradation.

Handles conditional formatting tokens (?function_name) that control
whether sections or inline content should be shown or hidden based
on function results. Now supports configurable error handling modes.
"""

from typing import Any, List, Optional
from .base import FormatterBase, FormatterError, FunctionExecutionError


class ConditionalFormatter(FormatterBase):
    """
    Handles conditional formatting tokens (?function_name) with configurable graceful degradation
    
    Conditionals work differently from color/text formatters:
    - They always require a function (no built-in conditionals)
    - Functions should return boolean-ish values
    - Results control visibility, not formatting
    - Used at both section level and inline level
    
    Graceful Degradation Modes:
    - STRICT: Missing functions raise FunctionNotFoundError
    - GRACEFUL: Missing functions default to 'hide' (safer default)
    - AUTO_CORRECT: Not applicable for conditionals (falls back to graceful)
    
    Usage patterns:
    - Section level: {{?has_items;Found ;count; items}}
    - Inline level: {{Message{?is_urgent} - URGENT: ;text}}
    """
    
    def get_family_name(self) -> str:
        return 'conditional'
    
    def _get_valid_tokens(self) -> List[str]:
        """Get list of valid conditional tokens for error messages"""
        if self.function_registry:
            return [f"functions: {', '.join(sorted(self.function_registry.keys()))}"]
        else:
            return ["No conditional functions registered"]
    
    def parse_token(self, token_value: str, field_value: Optional[Any] = None) -> bool:
        """
        Parse conditional token with configurable graceful degradation
        
        Unlike color/text formatters, conditionals don't have built-in tokens.
        Every conditional token must map to a function that returns a boolean.
        
        Args:
            token_value: Function name to execute
            field_value: Value to pass to the conditional function
            
        Returns:
            Boolean result of the conditional function
            
        Raises:
            FormatterError: If function not found and in strict mode
            FunctionExecutionError: If function execution fails and in strict mode
        """
        token_value = token_value.strip()
        
        # Conditionals always require functions - no built-in tokens
        if not self.function_registry or token_value not in self.function_registry:
            if self._is_graceful_mode():
                return False  # Hide section/content if function missing
            else:
                # Import here to avoid circular imports
                from ..dynamic_formatting import FunctionNotFoundError
                raise FunctionNotFoundError(
                    f"Conditional function not found: '{token_value}'",
                    function_name=token_value,
                    template=self.current_template,
                    position=self.current_position,
                    available_functions=list(self.function_registry.keys()) if self.function_registry else []
                )
        
        # Execute the conditional function
        func = self.function_registry[token_value]
        
        try:
            # Inspect function signature to determine how to call it
            import inspect
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            
            if len(params) == 0:
                # Function takes no parameters
                result = func()
            elif len(params) == 1:
                # Function takes one parameter (the field value)
                result = func(field_value)
            else:
                # Function takes multiple parameters - for conditionals, we might need
                # to pass additional context. For now, try to pass what we can.
                # This could be enhanced to pass more context like full data dict
                result = func(field_value)
            
            # Convert result to boolean
            return bool(result)
            
        except Exception as e:
            if self._is_graceful_mode():
                return False  # Hide section/content if function fails
            else:
                raise FunctionExecutionError(
                    f"Conditional function '{token_value}' execution failed",
                    function_name=token_value,
                    original_error=e,
                    template=self.current_template,
                    position=self.current_position
                )
    
    def apply_formatting(self, text: str, parsed_tokens: List[bool], output_mode: str = 'console') -> str:
        """
        Apply conditional logic to text (show/hide)
        
        Args:
            text: Text to conditionally show
            parsed_tokens: List of boolean results from conditional functions
            output_mode: Not used for conditionals
            
        Returns:
            Original text if any condition is True, empty string if all False
        """
        if not parsed_tokens:
            return text  # No conditions means show the text
        
        # If any condition is True, show the text
        if any(parsed_tokens):
            return text
        else:
            return ""  # Hide the text if all conditions are False
