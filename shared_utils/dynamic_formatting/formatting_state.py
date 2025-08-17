"""
Formatting state management for dynamic formatting system.

This module handles the state tracking across formatting families,
ensuring proper isolation and stacking behavior.
"""

from typing import Dict, List, Any


class StackingError(Exception):
    """Raised when invalid stacking is attempted"""
    pass


class FormattingState:
    """Tracks formatting state across families"""
    
    def __init__(self):
        # Each family maintains its own list of active formatting tokens
        self.family_states = {}  # family_name -> list of parsed tokens
    
    def add_tokens(self, family_name: str, tokens: List[Any], allow_stacking: bool):
        """Add formatting tokens to a family"""
        if family_name not in self.family_states:
            self.family_states[family_name] = []
        
        family_tokens = self.family_states[family_name]
        
        for token in tokens:
            # Handle reset tokens
            if str(token) == 'reset':
                family_tokens.clear()
                continue
            
            # Check stacking rules
            if not allow_stacking and family_tokens:
                # Find non-reset tokens
                non_reset_tokens = [t for t in family_tokens if str(t) != 'reset']
                if non_reset_tokens:
                    raise StackingError(f"Formatter family '{family_name}' does not allow stacking. "
                                      f"Already has: {non_reset_tokens}, trying to add: {token}")
            
            family_tokens.append(token)
    
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
        """Check if state has any active (non-reset) formatting"""
        for family_name, tokens in self.family_states.items():
            active_tokens = [t for t in tokens if str(t) != 'reset']
            if active_tokens:
                return True
        return False
    
    def clear_family(self, family_name: str):
        """Clear all tokens for a specific family"""
        if family_name in self.family_states:
            self.family_states[family_name] = []