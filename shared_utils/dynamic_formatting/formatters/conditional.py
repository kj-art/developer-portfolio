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
    
    def parse_token(self, token_value: str, field_value: Optional[Any] = None) -> str:
        """
        Parse conditional token with configurable graceful degradation
        
        Unlike color/text formatters, conditionals don't have built-in tokens.
        Every conditional token must map to a function that returns a boolean.
        
        Args:
            token_value: Function name for conditional logic
            field_value: Field value to pass to function
            
        Returns:
            'show' if function returns truthy, 'hide' if falsy or function missing/failed
            
        Behavior by validation mode:
        - STRICT: Missing functions raise FormatterError
        - GRACEFUL: Missing functions return 'hide' (safe default)
        - AUTO_CORRECT: Same as graceful (no auto-correction for missing functions)
        """
        original_token = token_value
        
        # Check if function exists
        if not self.function_registry or original_token not in self.function_registry:
            # Behavior depends on validation mode
            if hasattr(self, '_config') and self._config.is_strict_mode():
                # Strict mode: raise error for missing functions
                available = list(self.function_registry.keys()) if self.function_registry else []
                suggestion = self._suggest_similar_function(original_token, available)
                
                error_msg = f"Conditional function '{original_token}' not found"
                if suggestion:
                    error_msg += f". Did you mean '{suggestion}'?"
                elif available:
                    error_msg += f". Available functions: {', '.join(available[:5])}"
                else:
                    error_msg += ". No conditional functions registered"
                
                self._raise_formatter_error(error_msg, original_token)
            else:
                # Graceful/auto-correct mode: missing function defaults to 'hide' (safer)
                return 'hide'
        
        try:
            func = self.function_registry[original_token]
            
            # Try calling with field_value first, then without arguments
            try:
                if field_value is not None:
                    result = func(field_value)
                else:
                    result = func()
            except TypeError:
                # Function might not accept field_value parameter
                try:
                    result = func()
                except Exception as e:
                    # Function signature issues
                    if hasattr(self, '_config') and self._config.is_strict_mode():
                        raise FunctionExecutionError(
                            f"Function signature mismatch - function may require parameters",
                            function_name=original_token,
                            original_error=e,
                            template=self.current_template,
                            position=self.current_position
                        )
                    else:
                        # Graceful: function signature issues default to hide
                        return 'hide'
            
            # For conditionals, we expect boolean-ish results, not strings
            # Convert the result to 'show' or 'hide' based on truthiness
            return 'show' if result else 'hide'
            
        except FunctionExecutionError:
            # Re-raise function execution errors in strict mode
            if hasattr(self, '_config') and self._config.is_strict_mode():
                raise
            else:
                # Graceful: function execution errors default to hide
                return 'hide'
        except Exception as e:
            # Any other function execution error
            if hasattr(self, '_config') and self._config.is_strict_mode():
                raise FunctionExecutionError(
                    f"Unexpected error during conditional function execution: {e}",
                    function_name=original_token,
                    original_error=e,
                    template=self.current_template,
                    position=self.current_position
                )
            else:
                # Graceful: any function error defaults to hide
                return 'hide'
    
    def apply_formatting(self, text: str, parsed_tokens: List[str], output_mode: str = 'console') -> str:
        """
        Apply conditional logic - show/hide text
        
        Note: This method shouldn't be called directly for conditionals.
        Conditional logic is handled during parsing by checking should_show_text().
        This is here for interface completeness.
        
        Args:
            text: Text to potentially show/hide
            parsed_tokens: List of conditional results ('show'/'hide')
            output_mode: Output mode (not used for conditionals)
            
        Returns:
            Original text (conditionals don't modify text, just control visibility)
        """
        return text
    
    def should_show_text(self, parsed_tokens: List[str]) -> bool:
        """
        Determine if text should be shown based on conditional tokens
        
        This is the main method used by the formatting system to determine
        if a conditional section or inline text should be visible.
        
        Args:
            parsed_tokens: List of conditional results from parse_token()
            
        Returns:
            False if any token says 'hide', True otherwise
        """
        # If any token says 'hide', hide the text
        # If all tokens say 'show' (or list is empty), show the text
        for token in parsed_tokens:
            if token == 'hide':
                return False
        return True
    
    def set_config(self, config) -> None:
        """Set configuration for validation mode handling"""
        self._config = config
    
    def _suggest_similar_function(self, func_name: str, available: List[str]) -> Optional[str]:
        """Suggest a similar function name"""
        if not available:
            return None
        
        func_lower = func_name.lower()
        
        # Look for substring matches first
        for func in available:
            if func_lower in func.lower() or func.lower() in func_lower:
                return func
        
        # Simple similarity
        best_match = None
        best_score = float('inf')
        
        for func in available:
            score = abs(len(func_name) - len(func))
            for i, char in enumerate(func_lower):
                if i < len(func) and char != func[i].lower():
                    score += 1
            
            if score < best_score and score <= 2:
                best_score = score
                best_match = func
        
        return best_match