"""
Formatting application logic for StringSmith.
"""

from typing import Dict, Callable, List, Any

# Handle both relative and absolute imports
try:
    from .exceptions import StringSmithError
    from .token_handlers import create_token_handlers, ColorTokenHandler, EmphasisTokenHandler
except ImportError:
    from exceptions import StringSmithError
    from token_handlers import create_token_handlers, ColorTokenHandler, EmphasisTokenHandler


class FormatApplier:
    """Applies formatting to text segments using token handlers."""
    
    def __init__(self, functions: Dict[str, Callable]):
        self.functions = functions
        self.token_handlers = create_token_handlers(functions)
        self.reset_code = '\033[0m'
    
    def apply_formatting(self, text: str, formatting_list: List[str]) -> str:
        """
        Apply a list of formatting specifications to text using token handlers.
        
        Args:
            text: The text to format
            formatting_list: List of formatting specs like "#_red", "@_bold"
        
        Returns:
            Formatted text with ANSI codes
        """
        if not formatting_list or not text:
            return text
        
        # Collect formatting codes by type
        color_codes = []
        emphasis_codes = []
        
        # Get handlers
        color_handler = self.token_handlers['color']
        emphasis_handler = self.token_handlers['emphasis']
        
        for fmt in formatting_list:
            if fmt.startswith('#_'):
                color_value = fmt[2:]  # Remove '#_' prefix
                if isinstance(color_handler, ColorTokenHandler):
                    color_code = color_handler.get_ansi_code(color_value)
                    if color_code:
                        color_codes.append(color_code)
            elif fmt.startswith('@_'):
                emphasis_value = fmt[2:]  # Remove '@_' prefix
                if isinstance(emphasis_handler, EmphasisTokenHandler):
                    # Check if this is a custom function
                    if emphasis_value in self.functions:
                        try:
                            # Apply custom formatting function
                            text = self.functions[emphasis_value](text)
                        except Exception as e:
                            raise StringSmithError(f"Error applying custom formatting '{emphasis_value}': {e}")
                    else:
                        # Apply standard emphasis
                        emphasis_code = emphasis_handler.get_ansi_code(emphasis_value)
                        if emphasis_code:
                            emphasis_codes.append(emphasis_code)
        
        # Apply ANSI codes if any
        all_codes = color_codes + emphasis_codes
        if all_codes:
            return ''.join(all_codes) + text + self.reset_code
        
        return text