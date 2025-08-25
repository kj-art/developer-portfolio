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