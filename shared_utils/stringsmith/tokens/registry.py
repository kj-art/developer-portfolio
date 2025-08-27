"""Token registry for StringSmith handlers."""

from typing import Dict, Callable
from .base import BaseTokenHandler
from .color import ColorTokenHandler
from .emphasis import EmphasisTokenHandler
from .conditional import ConditionalTokenHandler
from .literal import LiteralTokenHandler

# Token registry mapping prefixes to handler classes
TOKEN_REGISTRY = {
    '?': ConditionalTokenHandler,
    '#': ColorTokenHandler,
    '@': EmphasisTokenHandler,
    '$': LiteralTokenHandler
}

RESET_ANSI = ''.join(
    handler_class.RESET_ANSI 
    for handler_class in TOKEN_REGISTRY.values()
)

# Tokens sorted by length (longest first) for parsing
SORTED_TOKENS = sorted(TOKEN_REGISTRY.keys(), key=len, reverse=True)

def create_token_handlers(functions: Dict[str, Callable] = None) -> Dict[str, BaseTokenHandler]:
    functions = functions or {}
    handlers = {}
    for token in TOKEN_REGISTRY:
        handler_class = TOKEN_REGISTRY[token]
        handler = handler_class(token, functions)
        handlers[token] = handler
    return handlers