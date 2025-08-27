
"""
Inline formatting data structures for StringSmith.

Represents formatting tokens within template text with position information
for efficient application during the formatting process.
"""

from dataclasses import dataclass

@dataclass
class InlineFormatting:
    """
    Represents a single inline formatting token with position and metadata.
    
    Args:
        position (int): Character position where formatting should be applied.
        type (str): Type of formatting token ('#' for color, '@' for emphasis, etc.).
        value (str): The formatting specification ('red', 'bold', function name, etc.).
    
    Examples:
        >>> fmt = InlineFormatting(position=5, type='#', value='red')
        >>> # Applies red color starting at character position 5
    """
    position: int
    type: str  
    value: str
    
    def adjust_position(self, offset: int):
        """Adjust position by the specified offset."""
        self.position += offset
    
    def set_position(self, new_position: int):
        """Set position to a specific value."""
        self.position = new_position