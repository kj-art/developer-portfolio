from typing import Dict, Callable, List
from .base import BaseTokenHandler
from collections import defaultdict

TOKEN_REGISTRY = defaultdict(dict)
SORTED_TOKENS = []

def register_token_handler(token_prefix: str, reset_ansi: str = '', pass_priority: int = 0):
    """Decorator that registers handlers when they're defined."""
    def decorator(handler_class):
        if not issubclass(handler_class, BaseTokenHandler):
            raise TypeError(f"Handler class must inherit from BaseTokenHandler")
        
        handler_class._REGISTERED_TOKEN = token_prefix
        handler_class._RESET_ANSI = reset_ansi
        
        # Register immediately when decorator runs
        TOKEN_REGISTRY[str(pass_priority)][token_prefix] = handler_class
        
        # Update sorted list
        global SORTED_TOKENS
        SORTED_TOKENS = sorted(SORTED_TOKENS + [token_prefix], key=len, reverse=True)
        
        return handler_class
    return decorator

def create_token_handlers(functions: Dict[str, Callable] = None) -> List[List[BaseTokenHandler]]:
    """
    Create token handlers grouped by processing priority.
    
    Maintains the same structure as TOKEN_REGISTRY but instantiates handlers:
    - First dimension: Processing passes (sorted by priority, lowest first)
    - Second dimension: Handlers within each pass
    
    Args:
        escape_char: Character used for escape sequences
        functions: Custom functions for token handlers
        
    Returns:
        List[List[BaseTokenHandler]]: Handlers grouped by priority passes
        
    Example:
        TOKEN_REGISTRY structure:
        {
            '-10': {'?': ConditionalHandler},
            '0': {'#': ColorHandler, '@': EmphasisHandler}, 
            '10': {'$': LiteralHandler}
        }
        
        Returns:
        [
            [ConditionalHandler()],                    # Priority -10
            [ColorHandler(), EmphasisHandler()],       # Priority 0  
            [LiteralHandler()]                         # Priority 10
        ]
    """
    functions = functions or {}
    grouped_handlers = []
    
    # Sort priority keys as integers (lowest first)
    sorted_priority_keys = sorted(TOKEN_REGISTRY.keys(), key=int)
    
    for priority_key in sorted_priority_keys:
        priority_handlers = []
        token_dict = TOKEN_REGISTRY[priority_key]
        
        # Instantiate all handlers in this priority group
        for token, handler_class in token_dict.items():
            handler = handler_class(functions)
            priority_handlers.append(handler)
        
        grouped_handlers.append(priority_handlers)
    
    return grouped_handlers