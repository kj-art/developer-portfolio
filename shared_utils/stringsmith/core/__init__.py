"""
Core StringSmith components - AST structures and parsing.

Architecture Note:
StringSmith uses a two-phase approach:
1. Template Structure Parsing (during __init__): Parse section boundaries, 
   validate syntax, prepare static formatting
2. Token Resolution (during format()): Resolve dynamic tokens and apply 
   formatting with runtime data

This design avoids complex position management while maintaining good performance
for the common case of template reuse.
"""

from .ast import TemplateSection, SectionParts
from .parser import TemplateParser
from .formatter import TemplateFormatter

__all__ = [
    'TemplateFormatter',
    'TemplateSection',
    'SectionParts',
    'TemplateParser'
]