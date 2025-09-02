"""
Token handler registration system for StringSmith.

Manages the registration and organization of token handlers by priority,
enabling ordered processing of formatting tokens during template rendering.
The registry system supports multi-pass processing where different token
types can be processed in different phases.
"""

from typing import Dict, Callable, List
from .base import BaseTokenHandler
from collections import defaultdict

# Internal registry structures
_TOKEN_REGISTRY = defaultdict(dict)
TOKEN_REGISTRY = {}
SORTED_TOKENS = []

def _build_sorted_registries(registry: dict):
    """
    Build sorted registry structures from raw registration data.
    
    Processes the raw token registration data to create optimized lookup
    structures with proper priority ordering. Tokens are sorted by length
    (longest first) within each priority level to prevent partial matches.
    
    Args:
        registry: Raw registration data organized by priority levels
        
    Returns:
        tuple: (nested_sorted_dict, flattened_sorted_list)
            - nested_sorted_dict: Registry organized by priority with sorted tokens
            - flattened_sorted_list: Flat list of all tokens in processing order
            
    Processing Order:
        1. Pass priority (highest first): -10, 0, 10
        2. Token length (longest first): '##', '#'  
        3. Sub-priority (highest first): 10, 5, 0
    """
    nested_sorted = {}
    flattened_items = []

    # Process each priority level
    for pass_priority, token_map in registry.items():
        # Sort tokens within this priority level
        sorted_inner = sorted(
            token_map.items(),
            key=lambda item: (-item[1][1][0], -item[1][1][1])  # length desc, sub_priority desc
        )

        # Build nested structure for this priority
        nested_sorted[pass_priority] = {
            token_prefix: handler_class
            for token_prefix, (handler_class, _) in sorted_inner
        }

        # Collect items for flattened structure
        for token_prefix, (handler_class, (tok_len, sub_priority)) in token_map.items():
            flattened_items.append(
                (token_prefix, handler_class, tok_len, int(pass_priority), sub_priority)
            )

    # Build flattened sorted list (global processing order)
    flattened_sorted = [
        token_prefix
        for token_prefix, handler_class, *_ in sorted(
            flattened_items,
            key=lambda x: (-x[2], -x[3], -x[4])  # length desc, pass_priority desc, sub_priority desc
        )
    ]

    return nested_sorted, flattened_sorted

def register_token_handler(token_prefix: str, reset_ansi: str = '', pass_priority: int = 0, sub_priority: int = 0):
    """
    Decorator for registering token handlers with priority-based processing.
    
    Registers token handlers in the global registry with specified processing
    priorities. Handlers are organized into processing passes that execute
    in priority order, enabling complex formatting interactions.
    
    Args:
        token_prefix: Character(s) that identify this token type (e.g., '#', '@', '?')
        reset_ansi: ANSI sequence to reset this token type's formatting
        pass_priority: Processing pass priority (higher values processed first)
        sub_priority: Priority within the same pass (higher values processed first)
        
    Returns:
        Decorator function that registers the handler class
        
    Examples:
        # Basic color handler (default priority)
        @register_token_handler('#', '\\033[39m')
        class ColorTokenHandler(BaseTokenHandler):
            pass
            
        # High-priority conditional handler
        @register_token_handler('?', '', pass_priority=0, sub_priority=10)
        class ConditionalTokenHandler(BaseTokenHandler):
            pass
            
        # Low-priority literal handler
        @register_token_handler('$', '', pass_priority=-10)
        class LiteralTokenHandler(BaseTokenHandler):
            pass
            
    Processing Order:
        Handlers are processed in this order:
        1. Pass priority (highest first)
        2. Token length (longest prefixes first within each pass)
        3. Sub-priority (highest first for same-length tokens)
        
    Thread Safety:
        Registration should only occur during module import time.
        The registry structures are rebuilt on each registration.
    """
    def decorator(handler_class):
        # Validate handler class inheritance
        if not issubclass(handler_class, BaseTokenHandler):
            raise TypeError(f"Handler class must inherit from BaseTokenHandler")
        
        # Set class-level registration attributes
        handler_class._REGISTERED_TOKEN = token_prefix
        handler_class._RESET_ANSI = reset_ansi

        # Register in internal structure
        _TOKEN_REGISTRY[str(pass_priority)][token_prefix] = (handler_class, (len(token_prefix), sub_priority))
        
        # Rebuild sorted registry structures
        global TOKEN_REGISTRY, SORTED_TOKENS
        TOKEN_REGISTRY, SORTED_TOKENS = _build_sorted_registries(_TOKEN_REGISTRY)
        
        return handler_class
    return decorator

def create_token_handlers(functions: Dict[str, Callable] = None) -> List[List[BaseTokenHandler]]:
    """
    Create token handler instances organized by processing priority.
    
    Instantiates all registered token handlers with the provided function
    registry and organizes them into priority-ordered processing passes.
    This structure enables multi-pass token processing with proper precedence.
    
    Args:
        functions: Custom functions to provide to token handlers
        
    Returns:
        List[List[BaseTokenHandler]]: Handlers grouped by processing passes
            - Outer list: Processing passes (sorted by priority, highest first)
            - Inner list: Handlers within each pass (sorted by token length, sub-priority)
        
    Example Registry Structure:
        TOKEN_REGISTRY = {
            '0': {'?': ConditionalHandler, '#': ColorHandler},
            '-10': {'$': LiteralHandler}
        }
        
        Returns:
        [
            [ConditionalHandler(functions), ColorHandler(functions)],  # Priority 0
            [LiteralHandler(functions)]                                # Priority -10
        ]
        
    Processing Flow:
        1. Template text is processed by each pass in sequence
        2. Within each pass, handlers process tokens in parallel
        3. Later passes see the results of earlier passes
        4. This enables complex token interactions and precedence
    """
    functions = functions or {}
    grouped_handlers = []
    
    # Process passes in priority order (highest first)
    sorted_priority_keys = sorted(TOKEN_REGISTRY.keys(), key=int, reverse=True)
    for priority_key in sorted_priority_keys:
        priority_handlers = []
        token_dict = TOKEN_REGISTRY[priority_key]
        
        # Handlers within each pass are already sorted by _build_sorted_registries
        for token, handler_class in token_dict.items():
            handler = handler_class(functions)
            priority_handlers.append(handler)
        
        grouped_handlers.append(priority_handlers)
    
    return grouped_handlers