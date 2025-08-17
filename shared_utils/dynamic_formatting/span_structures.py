"""
Data structures for dynamic formatting system.

This module contains the core data structures used to represent
formatted spans and format sections.
"""

from typing import Dict, List, Optional, Union, Any


class FormattedSpan:
    """Represents a span of text with associated formatting tokens"""
    
    def __init__(self, text: str, formatting_tokens: Optional[Dict[str, List]] = None):
        self.text = text
        self.formatting_tokens = formatting_tokens or {}  # family_name -> list of parsed tokens
    
    def __repr__(self):
        return f"FormattedSpan(text='{self.text}', tokens={self.formatting_tokens})"


class FormatSection:
    """Represents a complete formatting section with field, prefix, suffix, and formatting"""
    
    def __init__(self, 
                 field_name: str, 
                 is_required: bool = False, 
                 prefix: Union[str, List[FormattedSpan]] = "", 
                 suffix: Union[str, List[FormattedSpan]] = "", 
                 field_formatting_tokens: Optional[Dict[str, List]] = None,
                 function_name: Optional[str] = None,
                 prefix_function: Optional[str] = None,
                 suffix_function: Optional[str] = None,
                 whole_section_formatting_tokens: Optional[Dict[str, List]] = None):
        
        self.field_name = field_name
        self.is_required = is_required
        self.prefix = prefix
        self.suffix = suffix
        self.field_formatting_tokens = field_formatting_tokens or {}
        self.function_name = function_name
        self.prefix_function = prefix_function
        self.suffix_function = suffix_function
        self.whole_section_formatting_tokens = whole_section_formatting_tokens or {}
    
    def __repr__(self):
        return (f"FormatSection(field='{self.field_name}', required={self.is_required}, "
                f"prefix={self.prefix}, suffix={self.suffix})")
    
    def has_inline_formatting(self) -> bool:
        """Check if this section has any inline formatting complexity"""
        return (not isinstance(self.prefix, str) or 
                not isinstance(self.suffix, str) or 
                bool(self.field_formatting_tokens))
    
    def is_simple_section(self) -> bool:
        """Check if this is a simple section (no inline formatting)"""
        return not self.has_inline_formatting()