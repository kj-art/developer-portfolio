"""
Data structures for dynamic formatting system.

This module contains the core data structures used to represent
formatted spans and format sections with comprehensive type annotations.
"""

from typing import Dict, List, Optional, Union, Any


class FormattedSpan:
    """
    Represents a span of text with associated formatting tokens
    
    Used for inline formatting within template sections, where different
    parts of the text can have different formatting applied.
    """
    
    def __init__(self, text: str, formatting_tokens: Optional[Dict[str, List[Any]]] = None) -> None:
        """
        Initialize a formatted span
        
        Args:
            text: The text content of this span
            formatting_tokens: Dictionary mapping family names to lists of raw tokens
        """
        self.text = text
        self.formatting_tokens = formatting_tokens or {}  # family_name -> list of parsed tokens
    
    def __repr__(self) -> str:
        return f"FormattedSpan(text='{self.text}', tokens={self.formatting_tokens})"
    
    def has_formatting(self) -> bool:
        """Check if this span has any formatting tokens"""
        return bool(self.formatting_tokens)
    
    def get_families(self) -> List[str]:
        """Get list of formatting families used in this span"""
        return list(self.formatting_tokens.keys())


class FormatSection:
    """
    Represents a complete formatting section with field, prefix, suffix, and formatting
    
    This is the main structural unit of a template - each {{...}} block becomes
    a FormatSection that knows how to render itself.
    """
    
    def __init__(self, 
                 field_name: str, 
                 is_required: bool = False, 
                 prefix: Union[str, List[FormattedSpan]] = "", 
                 suffix: Union[str, List[FormattedSpan]] = "", 
                 field_formatting_tokens: Optional[Dict[str, List[Any]]] = None,
                 function_name: Optional[str] = None,
                 prefix_function: Optional[str] = None,
                 suffix_function: Optional[str] = None,
                 whole_section_formatting_tokens: Optional[Dict[str, List[Any]]] = None) -> None:
        """
        Initialize a format section
        
        Args:
            field_name: Name of the field to format
            is_required: Whether this field is required (marked with !)
            prefix: Prefix text or formatted spans
            suffix: Suffix text or formatted spans  
            field_formatting_tokens: Formatting tokens for the field value
            function_name: Conditional function name for section visibility
            prefix_function: Function to generate prefix text
            suffix_function: Function to generate suffix text
            whole_section_formatting_tokens: Formatting tokens for entire section
        """
        self.field_name = field_name
        self.is_required = is_required
        self.prefix = prefix
        self.suffix = suffix
        self.field_formatting_tokens = field_formatting_tokens or {}
        self.function_name = function_name
        self.prefix_function = prefix_function
        self.suffix_function = suffix_function
        self.whole_section_formatting_tokens = whole_section_formatting_tokens or {}
    
    def __repr__(self) -> str:
        return (f"FormatSection(field='{self.field_name}', required={self.is_required}, "
                f"prefix={self.prefix}, suffix={self.suffix})")
    
    def has_inline_formatting(self) -> bool:
        """
        Check if this section has any inline formatting complexity
        
        Returns:
            True if section has complex formatting that requires span rendering
        """
        return (not isinstance(self.prefix, str) or 
                not isinstance(self.suffix, str) or 
                bool(self.field_formatting_tokens))
    
    def is_simple_section(self) -> bool:
        """
        Check if this is a simple section (no inline formatting)
        
        Simple sections can be rendered more efficiently using string concatenation
        instead of the more complex span-based rendering system.
        
        Returns:
            True if section can use simple string concatenation
        """
        return not self.has_inline_formatting()
    
    def has_functions(self) -> bool:
        """Check if this section uses any function calls"""
        return bool(self.function_name or self.prefix_function or self.suffix_function)
    
    def get_all_formatting_families(self) -> List[str]:
        """
        Get all formatting families used in this section
        
        Returns:
            List of family names used in any part of this section
        """
        families = set()
        
        # Add families from whole section tokens
        families.update(self.whole_section_formatting_tokens.keys())
        
        # Add families from field tokens
        families.update(self.field_formatting_tokens.keys())
        
        # Add families from prefix spans
        if isinstance(self.prefix, list):
            for span in self.prefix:
                families.update(span.formatting_tokens.keys())
        
        # Add families from suffix spans
        if isinstance(self.suffix, list):
            for span in self.suffix:
                families.update(span.formatting_tokens.keys())
        
        return list(families)
    
    def is_positional(self) -> bool:
        """
        Check if this section represents a positional argument
        
        Positional sections have synthetic field names starting with __pos_
        
        Returns:
            True if this is a positional argument section
        """
        return self.field_name.startswith('__pos_')
    
    def get_positional_index(self) -> Optional[int]:
        """
        Get the positional index if this is a positional section
        
        Returns:
            Index number for positional arguments, None if not positional
        """
        if self.is_positional():
            try:
                # Extract number from __pos_N__
                import re
                match = re.match(r'__pos_(\d+)__', self.field_name)
                if match:
                    return int(match.group(1))
            except (ValueError, AttributeError):
                pass
        return None