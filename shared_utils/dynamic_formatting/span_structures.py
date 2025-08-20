"""
Data structures for formatting spans and sections.

This module defines the core data structures used throughout the dynamic
formatting system for representing parsed template sections and formatting spans.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class FormattedSpan:
    """
    Represents a formatted text span with specific styling
    
    This allows for complex inline formatting where different parts
    of a section can have different colors, styles, etc.
    """
    text: str
    formatting_tokens: Dict[str, List[str]]  # prefix -> list of tokens
    
    def __str__(self) -> str:
        return self.text
    
    def is_empty(self) -> bool:
        """Check if this span contains any text"""
        return not self.text


@dataclass
class FormatSection:
    """
    Represents a complete format section with field, formatting, and structure
    
    This is the main unit of template processing, containing all information
    needed to render a section of the template.
    """
    field_name: str  # Name of the field to extract data from
    prefix: str  # Text before the field value
    suffix: str  # Text after the field value
    is_required: bool  # Whether this field is required (marked with !)
    function_name: Optional[str]  # Name of conditional or other function
    whole_section_formatting_tokens: Dict[str, List[str]]  # Formatting for entire section
    spans: List[FormattedSpan]  # For complex inline formatting
    
    def __str__(self) -> str:
        return f"FormatSection(field='{self.field_name}', prefix='{self.prefix}', suffix='{self.suffix}')"
    
    def is_simple_section(self) -> bool:
        """
        Check if this is a simple section (no complex spans)
        
        Simple sections can be rendered more efficiently as they don't
        require complex span processing.
        """
        return len(self.spans) == 0
    
    def has_formatting(self) -> bool:
        """Check if this section has any formatting tokens"""
        return bool(self.whole_section_formatting_tokens)
    
    def get_text_content(self, field_value: Any) -> str:
        """
        Get the complete text content for this section
        
        Args:
            field_value: The value of the field
            
        Returns:
            Complete text with prefix + field + suffix
        """
        # Convert field value to string
        if field_value is None:
            field_str = ""
        else:
            field_str = str(field_value)
        
        # Combine prefix, field, and suffix
        return f"{self.prefix}{field_str}{self.suffix}"
    
    def is_conditional(self) -> bool:
        """Check if this section has a conditional function"""
        return self.function_name is not None and self.function_name.startswith('?')
    
    def get_conditional_function_name(self) -> Optional[str]:
        """Get the name of the conditional function (without '?' prefix)"""
        if self.is_conditional():
            return self.function_name[1:]  # Remove '?' prefix
        return None