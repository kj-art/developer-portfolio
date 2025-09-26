"""Literal token handler for text transformation via custom functions."""

from typing import Optional, Dict, Callable, Any
from .base import BaseTokenHandler
from ..exceptions import StringSmithError
from .registry import register_token_handler, SORTED_TOKENS

@register_token_handler('$')
class LiteralTokenHandler(BaseTokenHandler):
    """Handles literal tokens that inject custom function results directly into text."""
    def __init__(self, functions: Dict[str, Callable] = None):
        super().__init__(functions)
        from ..core import TemplateParser
        self._parser = TemplateParser()
        self._token_regex = self._parser.create_token_regex(*SORTED_TOKENS)

    def apply_inline_formatting(
            self,
            split_part: list[str | tuple[str, str]],
            part_type: str,
            field_value: Any,
            kwargs: Dict = None
            ) -> tuple[list[str | tuple[str, str]], bool]:
        token = self.token
        formatting_found = False
        for i, value in enumerate(split_part):
            if isinstance(value, str):
                continue
            part_token, token_value = value
            if token != part_token:
                continue
            formatting_found = True
            token_value = self.get_replacement_text(self._call_function(token_value, field_value, kwargs))
            split_part[i] = token_value
        return split_part, part_type != 'field' or not formatting_found
    
    def get_static_formatting(self, token_value: str) -> Optional[str]:
        return None

    def get_replacement_text(self, token_value: str) -> str:
        # prevent an infinite loop if the user tries to pass back a token that will then be found by find_token again
        split_tokens = self._parser.split_tokens(token_value, self._token_regex)
        if any(isinstance(x, tuple) for x in split_tokens):
            raise StringSmithError(f"Invalid literal token value '{token_value}'. Literal values cannot contain token syntax. Please consider using escape characters.")
        return token_value