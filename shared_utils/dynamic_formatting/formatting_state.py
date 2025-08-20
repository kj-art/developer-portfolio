"""
Formatting state management for dynamic formatting system.

Manages the state of formatting tokens across different families (color, text, etc.)
to ensure consistent application and proper interaction between different formatters.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class FormattingState:
    """
    Tracks the current formatting state across different token families
    
    Used to manage how different formatting tokens interact with each other
    and ensure consistent application across complex formatting scenarios.
    """
    
    # Current active tokens by family
    color_tokens: List[str] = field(default_factory=list)
    text_tokens: List[str] = field(default_factory=list)
    conditional_results: List[bool] = field(default_factory=list)
    
    # Reset flags
    color_reset: bool = False
    text_reset: bool = False
    
    def add_color_token(self, token: str) -> None:
        """Add a color token to the current state"""
        if token == 'reset':
            self.color_reset = True
            self.color_tokens.clear()
        else:
            self.color_tokens.append(token)
    
    def add_text_token(self, token: str) -> None:
        """Add a text style token to the current state"""
        if token == 'reset':
            self.text_reset = True
            self.text_tokens.clear()
        else:
            self.text_tokens.append(token)
    
    def add_conditional_result(self, result: bool) -> None:
        """Add a conditional function result"""
        self.conditional_results.append(result)
    
    def should_show_content(self) -> bool:
        """Check if content should be shown based on conditional results"""
        if not self.conditional_results:
            return True  # No conditions means show content
        return any(self.conditional_results)  # Show if any condition is True
    
    def get_active_color_tokens(self) -> List[str]:
        """Get the currently active color tokens"""
        return self.color_tokens.copy()
    
    def get_active_text_tokens(self) -> List[str]:
        """Get the currently active text style tokens"""
        return self.text_tokens.copy()
    
    def clear(self) -> None:
        """Clear all formatting state"""
        self.color_tokens.clear()
        self.text_tokens.clear()
        self.conditional_results.clear()
        self.color_reset = False
        self.text_reset = False
    
    def copy(self) -> 'FormattingState':
        """Create a copy of this formatting state"""
        return FormattingState(
            color_tokens=self.color_tokens.copy(),
            text_tokens=self.text_tokens.copy(),
            conditional_results=self.conditional_results.copy(),
            color_reset=self.color_reset,
            text_reset=self.text_reset
        )
