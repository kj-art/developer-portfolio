"""Literal token handler for text transformation via custom functions."""

from typing import Any, Optional, Dict, Callable
from .base import BaseTokenHandler
from ..exceptions import StringSmithError
from ..core import SectionParts

class LiteralTokenHandler(BaseTokenHandler):
    """Handles literal tokens that inject custom function results directly into text."""
    RESET_ANSI = ''  # Literal tokens don't produce ANSI escape codes
    _all_tokens = None

    def __init__(self, token: str, escape_char: str, functions: Dict[str, Callable] = None):
        super().__init__(token, escape_char, functions)
        if LiteralTokenHandler._all_tokens is None:
            from .registry import TOKEN_REGISTRY
            LiteralTokenHandler._all_tokens = list(TOKEN_REGISTRY.keys())

    def _apply_sectional_formatting(self, token_value: str, field_value: Any, parts: SectionParts) -> bool:
        """Sectional literal tokens are not supported."""
        raise StringSmithError(f"Sectional tokens can not be literal.")
    
    def apply_inline_formatting(self, parts: SectionParts, field_value: Any = None) -> bool:
        """Insert marker for literal function processing during finalization."""
        if field_value is None: # Baking phase
            return False

        def apply_inline_formatting_to_part(p:str) -> bool:
            nonlocal parts
            dynamic = set()
            for start, end, token_value in self.find_token(parts[p]):
                if token_value in self.functions:    
                    dynamic.add(token_value)
                    continue

                raise StringSmithError(f"Error applying function '{token_value}'")
                    
            parts[p] = self._replace_dynamic_tokens(parts[p], dynamic, field_value)
            return len(dynamic) == 0

        for p in ['prefix', 'suffix']:
            apply_inline_formatting_to_part(p)
        return apply_inline_formatting_to_part('field')

    def get_replacement_text(self, token_value: str, field_value: str = None) -> str:
        # prevent an infinite loop if the user tries to pass back a token that will then be found by find_token again
        for token in LiteralTokenHandler._all_tokens:
            for _ in self.find_token(token_value, token):
                raise StringSmithError(f"Invalid literal token value '{token_value}'. Literal values cannot contain tokens.")
        return token_value