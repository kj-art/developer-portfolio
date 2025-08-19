"""
Text style formatting implementation with configurable graceful degradation.

Handles text formatting tokens (@bold, @italic, etc.) with function fallback
support. Supports multiple text styles that can be combined naturally.

Enhanced with configurable graceful degradation modes for professional deployment.
"""

from typing import Any, List, Dict, Optional
from .base import FormatterBase, FormatterError


class TextFormatter(FormatterBase):
    """
    Handles text formatting tokens (@bold, @italic, etc.) with function fallback
    and configurable graceful degradation
    
    Supported styles:
    - bold: Makes text bold
    - italic: Makes text italic  
    - underline: Underlines text
    - reset/normal/default: Clears all text formatting
    
    Graceful Degradation Modes:
    - STRICT: Invalid tokens raise FormatterError
    - GRACEFUL: Invalid tokens return 'invalid' (no formatting applied)
    - AUTO_CORRECT: Invalid tokens auto-correct to suggested alternatives
    
    Text style behavior:
    - Multiple styles combine naturally (bold + italic = bold italic)
    - Reset tokens clear all text formatting
    - File output mode strips all formatting codes
    - Function fallback allows dynamic style selection
    """
    
    # Valid text formatting styles
    VALID_STYLES: Dict[str, str] = {
        'bold': '\033[1m',
        'italic': '\033[3m', 
        'underline': '\033[4m'
    }
    
    def get_family_name(self) -> str:
        return 'text'
    
    def _get_valid_tokens(self) -> List[str]:
        """Get list of valid text style tokens for error messages"""
        tokens = list(self.VALID_STYLES.keys())
        tokens.extend(['reset', 'normal', 'default'])
        if self.function_registry:
            tokens.append(f"functions: {', '.join(sorted(self.function_registry.keys()))}")
        return tokens
    
    def parse_token(self, token_value: str, field_value: Optional[Any] = None) -> str:
        """
        Parse text formatting token with function fallback and configurable graceful degradation
        
        Parsing order:
        1. Check for reset tokens (normal, default, reset)
        2. Try direct style lookup
        3. Try function fallback
        4. Handle invalid tokens based on validation mode
        
        Args:
            token_value: Text style token to parse
            field_value: Field value for function fallback
            
        Returns:
            Parsed style token (style name, 'reset', or 'invalid')
            
        Behavior by validation mode:
        - STRICT: Invalid tokens raise FormatterError
        - GRACEFUL: Invalid tokens return 'invalid' (no formatting applied)
        - AUTO_CORRECT: Invalid tokens auto-correct to suggested alternatives
        """
        original_token = token_value
        token_lower = token_value.lower()
        
        # Handle reset tokens
        if self.is_reset_token(token_lower):
            return 'reset'
        
        # Try direct style lookup
        if token_lower in self.VALID_STYLES:
            return token_lower
        
        # Function fallback - use original case for function names
        try:
            function_result = self._try_function_fallback(original_token, field_value)
            if function_result is not None:
                # Recursively parse the function result as a text style
                return self.parse_token(function_result, field_value)
        except Exception:
            # Function failed - handle based on validation mode
            pass
        
        # Handle invalid tokens based on validation mode
        return self._handle_invalid_token(original_token)
    
    def _handle_invalid_token(self, token_value: str) -> str:
        """Handle invalid tokens based on validation mode"""
        if hasattr(self, '_config'):
            if self._config.is_strict_mode():
                # Strict mode: raise error for invalid tokens
                suggestion = self._suggest_similar_token(token_value)
                error_msg = f"Invalid text style token: '{token_value}'"
                if suggestion:
                    error_msg += f". Did you mean '{suggestion}'?"
                self._raise_formatter_error(error_msg, token_value)
                
            elif self._config.is_auto_correct_mode():
                # Auto-correct mode: automatically use suggested alternative
                suggestion = self._suggest_similar_token(token_value)
                if suggestion:
                    # Recursively parse the suggested token
                    return self.parse_token(suggestion)
                else:
                    # No suggestion available, fall back to graceful
                    return 'invalid'
            else:
                # Graceful mode: return 'invalid' (no formatting applied)
                return 'invalid'
        else:
            # No config available, default to graceful behavior
            return 'invalid'
    
    def _suggest_similar_token(self, token_value: str) -> Optional[str]:
        """Suggest a similar valid token using fuzzy matching"""
        valid_tokens = set(self.VALID_STYLES.keys())
        valid_tokens.update(['reset', 'normal', 'default'])
        
        if not valid_tokens:
            return None
        
        # Simple similarity check
        token_lower = token_value.lower()
        
        # Exact substring matches
        for valid_token in valid_tokens:
            if token_lower in valid_token.lower() or valid_token.lower() in token_lower:
                return valid_token
        
        # Edit distance approximation (simple version)
        best_match = None
        best_score = float('inf')
        
        for valid_token in valid_tokens:
            # Simple score: length difference + character differences
            score = abs(len(token_value) - len(valid_token))
            for i, char in enumerate(token_lower):
                if i < len(valid_token) and char != valid_token[i].lower():
                    score += 1
            
            if score < best_score and score <= 3:  # Only suggest if reasonably close
                best_score = score
                best_match = valid_token
        
        return best_match
    
    def apply_formatting(self, text: str, parsed_tokens: List[str], output_mode: str = 'console') -> str:
        """
        Apply text formatting - multiple styles combine naturally
        
        Args:
            text: Text to format
            parsed_tokens: List of parsed style tokens
            output_mode: 'console' for ANSI codes, 'file' for plain text
            
        Returns:
            Formatted text with style codes (console) or plain text (file)
        """
        if output_mode != 'console' or not parsed_tokens:
            return text
        
        # Apply all style codes in sequence - they combine naturally
        style_codes: List[str] = []
        for token in parsed_tokens:
            if token == 'reset':
                style_codes = []  # Reset clears all previous styles
            elif token == 'invalid':
                # Skip invalid tokens - no formatting applied
                continue
            elif token in self.VALID_STYLES:
                style_codes.append(self.VALID_STYLES[token])
        
        if not style_codes:
            return text
        
        prefix = ''.join(style_codes)
        return f"{prefix}{text}"
    
    def set_config(self, config) -> None:
        """Set configuration for validation mode handling"""
        self._config = config