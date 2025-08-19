"""
Color formatting implementation with configurable graceful degradation.

Handles color formatting tokens (#red, #FF0000, etc.) with function fallback
support. Supports ANSI colors, hex colors, named colors, and dynamic color
selection through function calls.

Enhanced with configurable graceful degradation modes for professional deployment.
"""

from typing import Any, List, Dict, Optional
from .base import FormatterBase, FormatterError

try:
    import matplotlib.colors as mcolors
    NAMED_COLORS: Dict[str, str] = mcolors.CSS4_COLORS
except ImportError:
    # Fallback basic colors if matplotlib not available
    NAMED_COLORS = {
        'red': '#FF0000', 'green': '#00FF00', 'blue': '#0000FF',
        'yellow': '#FFFF00', 'cyan': '#00FFFF', 'magenta': '#FF00FF',
        'black': '#000000', 'white': '#FFFFFF', 'gray': '#808080'
    }


class ColorFormatter(FormatterBase):
    """
    Handles color formatting tokens (#red, #FF0000, etc.) with function fallback
    and configurable graceful degradation
    
    Supports multiple color formats:
    - ANSI color names: red, blue, green, etc.
    - Hex colors: FF0000, 0000FF, etc. (with or without #)
    - Named colors: Any color name from matplotlib's CSS4_COLORS
    - Function fallback: Any function that returns a valid color
    
    Graceful Degradation Modes:
    - STRICT: Invalid tokens raise FormatterError
    - GRACEFUL: Invalid tokens return 'invalid' (no formatting applied)
    - AUTO_CORRECT: Invalid tokens auto-correct to suggested alternatives
    
    Color behavior:
    - Later colors override earlier colors naturally via ANSI codes
    - Reset tokens clear all color formatting
    - File output mode strips all color codes
    """
    
    # ANSI color code mappings
    ANSI_COLORS: Dict[str, int] = {
        'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
        'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37,
        'bright_black': 90, 'bright_red': 91, 'bright_green': 92,
        'bright_yellow': 93, 'bright_blue': 94, 'bright_magenta': 95,
        'bright_cyan': 96, 'bright_white': 97
    }
    
    def get_family_name(self) -> str:
        return 'color'
    
    def _get_valid_tokens(self) -> List[str]:
        """Get list of valid color tokens for error messages"""
        tokens = list(self.ANSI_COLORS.keys())
        tokens.extend(['reset', 'normal', 'default'])
        tokens.extend(['hex colors (6 digits)', 'matplotlib color names'])
        if self.function_registry:
            tokens.append(f"functions: {', '.join(sorted(self.function_registry.keys()))}")
        return tokens
    
    def parse_token(self, token_value: str, field_value: Optional[Any] = None) -> str:
        """
        Parse color token with function fallback and configurable graceful degradation
        
        Parsing order:
        1. Check for reset tokens (normal, default, reset)
        2. Try direct ANSI color lookup
        3. Try hex color parsing
        4. Try named colors from matplotlib
        5. Try function fallback
        6. Handle invalid tokens based on validation mode
        
        Args:
            token_value: Color token to parse
            field_value: Field value for function fallback
            
        Returns:
            Parsed color token (ANSI name, hex, 'reset', or 'invalid')
            
        Behavior by validation mode:
        - STRICT: Invalid tokens raise FormatterError
        - GRACEFUL: Invalid tokens return 'invalid' (no formatting applied)
        - AUTO_CORRECT: Invalid tokens auto-correct to suggested alternatives
        """
        original_token = token_value
        token_value = token_value.lower()
        
        # Handle reset tokens
        if self.is_reset_token(token_value):
            return 'reset'
        
        # Try direct ANSI color lookup
        if token_value in self.ANSI_COLORS:
            return token_value
        
        # Try hex color
        if len(token_value) == 6 and all(c in '0123456789abcdef' for c in token_value):
            return f"#{token_value}"
        
        # Try named colors from matplotlib
        if token_value in NAMED_COLORS:
            return self._map_named_color_to_ansi(token_value)
        
        # Function fallback - use original case for function names
        try:
            function_result = self._try_function_fallback(original_token, field_value)
            if function_result is not None:
                # Recursively parse the function result as a color
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
                error_msg = f"Invalid color token: '{token_value}'"
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
        valid_tokens = set(self.ANSI_COLORS.keys())
        valid_tokens.update(['reset', 'normal', 'default'])
        valid_tokens.update(NAMED_COLORS.keys())
        
        if not valid_tokens:
            return None
        
        # Simple similarity check - could be enhanced with proper fuzzy matching
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
        Apply color formatting - later colors override earlier ones
        
        Args:
            text: Text to format
            parsed_tokens: List of parsed color tokens
            output_mode: 'console' for ANSI codes, 'file' for plain text
            
        Returns:
            Formatted text with color codes (console) or plain text (file)
        """
        if output_mode != 'console' or not parsed_tokens:
            return text
        
        # Apply all color codes in sequence - terminal will use the last one
        color_codes: List[str] = []
        for token in parsed_tokens:
            if token == 'reset':
                color_codes = []  # Reset clears all previous colors
            elif token == 'invalid':
                # Skip invalid tokens - no formatting applied
                continue
            else:
                ansi_code = self._get_ansi_code(token)
                color_codes.append(f"\033[{ansi_code}m")
        
        if not color_codes:
            return text
        
        prefix = ''.join(color_codes)
        return f"{prefix}{text}"
    
    def set_config(self, config) -> None:
        """Set configuration for validation mode handling"""
        self._config = config
    
    def _map_named_color_to_ansi(self, color_name: str) -> str:
        """Map matplotlib color name to closest ANSI color"""
        # Direct mapping for common colors
        color_mapping: Dict[str, str] = {
            'red': 'red', 'green': 'green', 'blue': 'blue', 
            'yellow': 'yellow', 'cyan': 'cyan', 'magenta': 'magenta',
            'black': 'black', 'white': 'white', 'gray': 'bright_black',
            'grey': 'bright_black'
        }
        
        if color_name in color_mapping:
            return color_mapping[color_name]
        
        # For other colors, convert through hex
        hex_color = NAMED_COLORS[color_name].lower()
        return self._hex_to_ansi_name(hex_color)
    
    def _get_ansi_code(self, color: str) -> int:
        """Convert color to ANSI code"""
        color_lower = color.lower().lstrip('#')
        
        # Direct ANSI color name mapping
        if color_lower in self.ANSI_COLORS:
            return self.ANSI_COLORS[color_lower]
        
        # Hex color mapping to closest ANSI
        return self._hex_to_ansi_code(color_lower)
    
    def _hex_to_ansi_name(self, hex_color: str) -> str:
        """Convert hex color to closest ANSI color name"""
        hex_color = hex_color.lstrip('#').lower()
        
        # Simple mapping of common hex values to ANSI names
        hex_to_ansi_name: Dict[str, str] = {
            '000000': 'black', 'ff0000': 'red', '00ff00': 'green', 'ffff00': 'yellow',
            '0000ff': 'blue', 'ff00ff': 'magenta', '00ffff': 'cyan', 'ffffff': 'white',
            '008000': 'green',  # CSS 'green' 
            '800080': 'magenta', # CSS 'purple' -> magenta
            '808080': 'bright_black'  # CSS 'gray'
        }
        
        if hex_color in hex_to_ansi_name:
            return hex_to_ansi_name[hex_color]
        
        # Fallback to closest basic color (could be enhanced with color distance calculation)
        return 'white'
    
    def _hex_to_ansi_code(self, hex_color: str) -> int:
        """Convert hex color to ANSI code"""
        ansi_name = self._hex_to_ansi_name(hex_color)
        return self.ANSI_COLORS.get(ansi_name, 37)