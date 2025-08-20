"""
Data structures for formatted text spans and template sections.

These classes represent the parsed structure of templates and manage
the state needed for applying formatting across different token families.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class FormattedSpan:
    """
    Represents a span of text with associated formatting tokens
    
    Used for complex inline formatting where different parts of a section
    can have different formatting applied.
    """
    text: str
    tokens: Dict[str, List[str]]  # Maps token family to list of tokens
    
    def __post_init__(self):
        # Ensure tokens is a proper dict
        if not isinstance(self.tokens, dict):
            self.tokens = {}


@dataclass
class FormatSection:
    """
    Represents a complete template section like {{prefix;field;suffix}}
    
    Handles both simple sections (just text with field substitution) and
    complex sections (with multiple formatted spans).
    """
    field_name: str
    prefix: str = ""
    suffix: str = ""
    is_required: bool = False
    function_name: Optional[str] = None
    whole_section_formatting_tokens: Optional[Dict[str, List[str]]] = None
    spans: Optional[List[FormattedSpan]] = None
    
    def __post_init__(self):
        # Ensure default values are proper types
        if self.whole_section_formatting_tokens is None:
            self.whole_section_formatting_tokens = {}
        if self.spans is None:
            self.spans = []
    
    def is_simple_section(self) -> bool:
        """Check if this is a simple section (no complex spans)"""
        return not self.spans or len(self.spans) == 0
    
    def get_text_content(self, field_value: Any) -> str:
        """Get the basic text content without formatting"""
        return f"{self.prefix}{field_value}{self.suffix}"
    
    def has_conditional(self) -> bool:
        """Check if this section has a conditional function"""
        return self.function_name is not None
    
    def has_formatting(self) -> bool:
        """Check if this section has any formatting tokens"""
        return bool(self.whole_section_formatting_tokens)
