"""
Formatting application logic for StringSmith.
"""

from typing import Dict, Callable, List, Any

# Handle both relative and absolute imports
try:
    from .exceptions import StringSmithError
except ImportError:
    from exceptions import StringSmithError

# Optional import for color support
try:
    from rich.color import Color
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class FormatApplier:
    """Applies formatting to text segments."""
    
    def __init__(self, functions: Dict[str, Callable]):
        self.functions = functions
        
        # ANSI escape codes for text emphasis
        self.emphasis_codes = {
            'bold': '\033[1m',
            'italic': '\033[3m',
            'underline': '\033[4m',
            'strikethrough': '\033[9m',
            'dim': '\033[2m',
        }
        
        self.reset_code = '\033[0m'
    
    def apply_formatting(self, text: str, formatting_list: List[str]) -> str:
        """
        Apply a list of formatting specifications to text.
        
        Args:
            text: The text to format
            formatting_list: List of formatting specs like "#_red", "@_bold"
        
        Returns:
            Formatted text with ANSI codes
        """
        if not formatting_list or not text:
            return text
        
        # Collect formatting codes
        codes = []
        
        for fmt in formatting_list:
            if fmt.startswith('#_'):
                color_name = fmt[2:]  # Remove '#_' prefix
                color_code = self._get_color_code(color_name)
                if color_code:
                    codes.append(color_code)
            elif fmt.startswith('@_'):
                emphasis_name = fmt[2:]  # Remove '@_' prefix
                if emphasis_name in self.emphasis_codes:
                    codes.append(self.emphasis_codes[emphasis_name])
                elif emphasis_name in self.functions:
                    # Custom formatting function
                    try:
                        text = self.functions[emphasis_name](text)
                    except Exception as e:
                        raise StringSmithError(f"Error applying custom formatting '{emphasis_name}': {e}")
            else:
                # Custom function (legacy format or direct function name)
                try:
                    if fmt in self.functions:
                        # Apply custom formatting function
                        text = self.functions[fmt](text)
                except Exception as e:
                    raise StringSmithError(f"Error applying custom formatting '{fmt}': {e}")
        
        # Apply ANSI codes if any
        if codes:
            return ''.join(codes) + text + self.reset_code
        
        return text
    
    def _get_color_code(self, color_name: str) -> str:
        """
        Get ANSI color code for a color name, hex code, or custom function.
        
        Args:
            color_name: Color name, hex code, or custom function name
        
        Returns:
            ANSI color code or empty string if not found/supported
        """
        # Handle custom function first
        if color_name in self.functions:
            try:
                color_value = self.functions[color_name]()
                if isinstance(color_value, str):
                    # Recursively process the returned value
                    return self._parse_color_value(color_value)
            except Exception:
                pass
        
        return self._parse_color_value(color_name)
    
    def _parse_color_value(self, color_value: str) -> str:
        """Parse a color value and return ANSI code using Rich."""
        if not isinstance(color_value, str):
            return ""
        
        color_value = color_value.strip()
        
        # If it's already an ANSI escape sequence, return as-is
        if color_value.startswith('\033['):
            return color_value
        
        # Use Rich for all color parsing and ANSI generation
        if HAS_RICH:
            try:
                color = Color.parse(color_value)
                # Get the ANSI escape sequence for foreground color
                ansi_codes = color.get_ansi_codes()
                if isinstance(ansi_codes, tuple) and len(ansi_codes) > 0:
                    # Return the foreground color code (first element) with proper ANSI formatting
                    fg_code = ansi_codes[0]
                    if fg_code and not fg_code.startswith('\033['):
                        return f'\033[{fg_code}m'
                    return fg_code if fg_code else ""
                elif isinstance(ansi_codes, str):
                    if ansi_codes and not ansi_codes.startswith('\033['):
                        return f'\033[{ansi_codes}m'
                    return ansi_codes
            except Exception:
                # Rich couldn't parse the color
                pass
        
        # If Rich isn't available or couldn't parse, return empty string
        return ""