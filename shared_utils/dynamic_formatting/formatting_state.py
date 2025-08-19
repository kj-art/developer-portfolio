"""
Formatting state management for dynamic formatting system.

This module handles state tracking across formatting families,
maintaining lists of tokens for each family without restrictions.
"""

from typing import Dict, List, Any, Union


class FormattingState:
    """
    Tracks formatting state across families
    
    Each family (color, text, conditional) maintains its own list of formatting tokens.
    This allows families to operate independently while maintaining proper state
    isolation and reset behavior.
    """
    
    def __init__(self) -> None:
        # Each family maintains its own list of formatting tokens
        self.family_states: Dict[str, List[Union[str, int, bool]]] = {}
    
    def add_tokens(self, family_name: str, tokens: List[Union[str, int, bool]]) -> None:
        """
        Add formatting tokens to a family
        
        Args:
            family_name: Name of the formatting family (e.g., 'color', 'text')
            tokens: List of parsed formatting tokens to add
        """
        if family_name not in self.family_states:
            self.family_states[family_name] = []
        
        self.family_states[family_name].extend(tokens)
    
    def get_family_tokens(self, family_name: str) -> List[Union[str, int, bool]]:
        """
        Get active tokens for a family
        
        Args:
            family_name: Name of the formatting family
            
        Returns:
            List of active tokens for the family, empty list if family not found
        """
        return self.family_states.get(family_name, [])
    
    def copy(self) -> 'FormattingState':
        """
        Create a copy of the current state
        
        Returns:
            New FormattingState instance with copied family states
        """
        new_state = FormattingState()
        for family_name, tokens in self.family_states.items():
            new_state.family_states[family_name] = tokens.copy()
        return new_state
    
    def has_active_formatting(self) -> bool:
        """
        Check if state has any active formatting
        
        Returns:
            True if any family has active tokens, False otherwise
        """
        for family_name, tokens in self.family_states.items():
            if tokens:
                return True
        return False
    
    def clear_family(self, family_name: str) -> None:
        """
        Clear all tokens for a specific family
        
        Args:
            family_name: Name of the formatting family to clear
        """
        if family_name in self.family_states:
            self.family_states[family_name] = []
    
    def clear_all(self) -> None:
        """Clear all formatting state for all families"""
        self.family_states.clear()
    
    def get_all_families(self) -> List[str]:
        """
        Get list of all active family names
        
        Returns:
            List of family names that have been used in this state
        """
        return list(self.family_states.keys())
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        active_families = [f for f, tokens in self.family_states.items() if tokens]
        return f"FormattingState(active_families={active_families})"