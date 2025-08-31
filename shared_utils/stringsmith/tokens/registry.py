from typing import Dict, Callable
from .base import BaseTokenHandler

TOKEN_REGISTRY = {}
SORTED_TOKENS = []
RESET_ANSI = ''

def register_token_handler(token_prefix):
    """Decorator that registers handlers when they're defined."""
    def decorator(handler_class):
        if not issubclass(handler_class, BaseTokenHandler):
            raise TypeError(f"Handler class must inherit from BaseTokenHandler")
        
        # Store token on class
        handler_class._REGISTERED_TOKEN = token_prefix
        
        # Register immediately when decorator runs
        TOKEN_REGISTRY[token_prefix] = handler_class
        
        # Update sorted list
        global SORTED_TOKENS
        SORTED_TOKENS = sorted(TOKEN_REGISTRY.keys(), key=len, reverse=True)

        global RESET_ANSI
        RESET_ANSI += handler_class.RESET_ANSI
        
        return handler_class
    return decorator

def create_token_handlers(escape_char: str, functions: Dict[str, Callable] = None) -> Dict[str, BaseTokenHandler]:
    functions = functions or {}
    handlers = {}
    for token, handler_class in TOKEN_REGISTRY.items():
        # No need to pass token - decorator already set it on the class
        handler = handler_class(escape_char, functions)
        handlers[token] = handler
    return handlers