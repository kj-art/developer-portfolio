"""
Formatting state management for dynamic formatting system.

This module handles state tracking across formatting families,
maintaining lists of tokens for each family without restrictions.
"""

from typing import Dict, List, Any


class FormattingState:
    """Tracks formatting state across families"""
    
    def __init__(self):
        # Each family maintains its own list of formatting tokens
        self.family_states = {}  # family_name -> list of parsed tokens
    
    def add_tokens(self, family_name: str, tokens: List[Any]):
        """Add formatting tokens to a family"""
        if family_name not in self.family_states:
            self.family_states[family_name] = []
        
        self.family_states[family_name].extend(tokens)
    
    def get_family_tokens(self, family_name: str) -> List[Any]:
        """Get active tokens for a family"""
        return self.family_states.get(family_name, [])
    
    def copy(self):
        """Create a copy of the current state"""
        new_state = FormattingState()
        for family_name, tokens in self.family_states.items():
            new_state.family_states[family_name] = tokens.copy()
        return new_state
    
    def has_active_formatting(self) -> bool:
        """Check if state has any active formatting"""
        for family_name, tokens in self.family_states.items():
            if tokens:
                return True
        return False
    
    def clear_family(self, family_name: str):
        """Clear all tokens for a specific family"""
        if family_name in self.family_states:
            self.family_states[family_name] = []