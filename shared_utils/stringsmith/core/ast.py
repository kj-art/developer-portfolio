"""
Abstract Syntax Tree structures for StringSmith template representation.

Defines the data structures that represent parsed templates as structured objects
for efficient conditional evaluation and formatting during runtime operations.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Iterator, Tuple
from dataclasses import dataclass

@dataclass
class SectionParts:
    """
    Container for the three parts of a template section: prefix, field, and suffix.
    
    Represents the parsed components of a template section after delimiter splitting.
    Provides convenient access methods for iteration and manipulation during
    formatting operations.
    
    Attributes:
        prefix: Text that appears before the field value
        field: The field name or formatting tokens for the field  
        suffix: Text that appears after the field value
        
    Examples:
        Basic section: "{{Hello ;name;}}" -> SectionParts("Hello ", "name", "")
        Full section: "{{User: ;username; logged in}}" -> SectionParts("User: ", "username", " logged in")
    """
    prefix: Optional[str] = None
    field: Optional[str] = None
    suffix: Optional[str] = None

    def __getitem__(self, key: str) -> str:
        """
        Get section part by name with automatic None-to-empty-string conversion.
        
        Args:
            key: Part name ('prefix', 'field', or 'suffix')
            
        Returns:
            str: Part content or empty string if None
            
        Raises:
            KeyError: If key is not a valid part name
        """
        if key not in ("prefix", "field", "suffix"):
            raise KeyError(f"{key} is not a valid field")
        return getattr(self, key) or ""

    def __setitem__(self, key: str, value: str):
        """
        Set section part by name.
        
        Args:
            key: Part name ('prefix', 'field', or 'suffix')
            value: New content for the part
            
        Raises:
            KeyError: If key is not a valid part name
        """
        if key not in ("prefix", "field", "suffix"):
            raise KeyError(f"{key} is not a valid field")
        setattr(self, key, value)

    def copy(self) -> SectionParts:
        """Create a shallow copy of this SectionParts instance."""
        return SectionParts(
            prefix=self.prefix,
            field=self.field,
            suffix=self.suffix
        )
    
    def iter_fields(self) -> Iterator[Tuple[str, str]]:
        """
        Iterate over all parts as (name, content) tuples.
        
        Yields:
            Tuple[str, str]: (part_name, part_content) for each part
            
        Example:
            >>> parts = SectionParts("Hello ", "name", "!")
            >>> list(parts.iter_fields())
            [('prefix', 'Hello '), ('field', 'name'), ('suffix', '!')]
        """
        for key in ("prefix", "field", "suffix"):
            yield key, self[key]

@dataclass
class TemplateSection:
    """
    Represents a parsed template section with formatting and field information.
    
    Contains all information needed to render a template section, including
    mandatory status, formatting tokens, field name, and section parts.
    This is the primary AST node for template processing.
    
    Attributes:
        is_mandatory: Whether this section is required (marked with '!')
        section_formatting: Formatting tokens organized by token type
        field_name: Name of the field this section represents (None for literal text)
        parts: The prefix, field, and suffix components
        
    Examples:
        Basic field: "{{name}}" -> TemplateSection(field_name="name", ...)
        Mandatory: "{{!email}}" -> TemplateSection(is_mandatory=True, field_name="email", ...)
        Formatted: "{{#red;Error: ;message;}}" -> TemplateSection with color formatting
        Literal: "Hello world" -> TemplateSection(field_name=None, ...)
    """
    is_mandatory: bool
    section_formatting: Dict[str, List[str]]
    field_name: Optional[str]
    parts: SectionParts  # nested object

    def copy(self) -> TemplateSection:
        # shallow copy for parts
        return TemplateSection(
            is_mandatory=self.is_mandatory,
            section_formatting={k: v.copy() for k, v in self.section_formatting.items()},
            field_name=self.field_name,
            parts=self.parts.copy()
        )
