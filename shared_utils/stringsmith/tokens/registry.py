from typing import Dict, Callable, List
from .base import BaseTokenHandler
from collections import defaultdict

_TOKEN_REGISTRY = defaultdict(dict)
TOKEN_REGISTRY = {}
SORTED_TOKENS = []

def _build_sorted_registries(registry: dict):
    nested_sorted = {}
    flattened_items = []

    for pass_priority, token_map in registry.items():
        # --- Nested version ---
        sorted_inner = sorted(
            token_map.items(),
            key=lambda item: (-item[1][1][0], -item[1][1][1])  # length desc, sub_priority desc
        )
        nested_sorted[pass_priority] = {
            token_prefix: handler_class
            for token_prefix, (handler_class, _) in sorted_inner
        }

        # --- Collect for flattened ---
        for token_prefix, (handler_class, (tok_len, sub_priority)) in token_map.items():
            flattened_items.append(
                (token_prefix, handler_class, tok_len, int(pass_priority), sub_priority)
            )

    # --- Flattened version (SORTED_TOKENS should be a list) ---
    flattened_sorted = [
        token_prefix
        for token_prefix, handler_class, *_ in sorted(
            flattened_items,
            key=lambda x: (-x[2], -x[3], -x[4])  # length desc, pass_priority desc, sub_priority desc
        )
    ]

    return nested_sorted, flattened_sorted

def register_token_handler(token_prefix: str, reset_ansi: str = '', pass_priority: int = 0, sub_priority: int = 0):
    """Decorator that registers handlers when they're defined."""
    def decorator(handler_class):
        if not issubclass(handler_class, BaseTokenHandler):
            raise TypeError(f"Handler class must inherit from BaseTokenHandler")
        
        handler_class._REGISTERED_TOKEN = token_prefix
        handler_class._RESET_ANSI = reset_ansi

        _TOKEN_REGISTRY[str(pass_priority)][token_prefix] = (handler_class, (len(token_prefix), sub_priority))
        
        global TOKEN_REGISTRY, SORTED_TOKENS
        TOKEN_REGISTRY, SORTED_TOKENS = _build_sorted_registries(_TOKEN_REGISTRY)
        
        return handler_class
    return decorator

def create_token_handlers(functions: Dict[str, Callable] = None) -> List[List[BaseTokenHandler]]:
    """
    Create token handlers grouped by processing priority.
    
    Maintains the same structure as TOKEN_REGISTRY but instantiates handlers:
    - First dimension: Processing passes (sorted by priority, highest first)
    - Second dimension: Handlers within each pass (sorted by token length desc, then sub_priority desc)
    
    Args:
        functions: Custom functions for token handlers
        
    Returns:
        List[List[BaseTokenHandler]]: Handlers grouped by priority passes
        
    Example:
        TOKEN_REGISTRY structure:
        {
            '0': {'?': ConditionalHandler(sub_priority=1), '#': ColorHandler(sub_priority=0)},
            '-10': {'$': LiteralHandler}
        }
        
        Returns:
        [
            [ConditionalHandler(), ColorHandler()],    # Priority 0 (? first due to higher sub_priority)
            [LiteralHandler()]                         # Priority -10
        ]
    """
    functions = functions or {}
    grouped_handlers = []
    
    # Sort priority keys as integers (highest first)
    sorted_priority_keys = sorted(TOKEN_REGISTRY.keys(), key=int, reverse=True)
    for priority_key in sorted_priority_keys:
        priority_handlers = []
        token_dict = TOKEN_REGISTRY[priority_key]
        
        # Handlers are already sorted within each pass by _build_sorted_registries
        for token, handler_class in token_dict.items():
            handler = handler_class(functions)
            priority_handlers.append(handler)
        
        grouped_handlers.append(priority_handlers)
    
    return grouped_handlers