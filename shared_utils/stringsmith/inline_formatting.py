"""
Inline formatting data structures and position management for StringSmith.

This module defines the data structures used to track formatting tokens discovered
within template sections, managing their positions and values for efficient
application during the formatting process.

Key Classes:
    InlineFormatting: Represents a single formatting token with position and metadata
    Position tracking: Handles text position adjustments as formatting is applied
    Token coordination: Manages multiple overlapping format tokens within text sections

Usage Pattern:
    InlineFormatting objects are created during template parsing to capture the
    location and type of formatting tokens. During format() operations, these
    objects guide the application of ANSI codes and conditional logic.

Thread Safety:
    InlineFormatting objects are immutable after creation and safe for concurrent
    access across multiple formatting operations.
"""

from dataclasses import dataclass

@dataclass
class InlineFormatting:
    position: int
    type: str  
    value: str
    
    def adjust_position(self, offset: int):
        """Adjust position by offset amount."""
        self.position += offset
    
    def set_position(self, new_position: int):
        """Set position to new value."""
        self.position = new_position