"""
Abstract Syntax Tree structures for StringSmith template representation.

Defines the data structures that represent parsed templates as structured objects
for efficient conditional evaluation and formatting during runtime operations.
"""

from __future__ import annotations
from typing import List, Optional, Dict
from dataclasses import dataclass
import copy

from .inline_formatting import InlineFormatting

@dataclass
class TemplatePart:
    """
    Represents a component part of a template section (prefix, field, or suffix).
    
    Args:
        content (str): Text content of this part.
        inline_formatting (List[InlineFormatting]): Inline formatting tokens with positions.
    
    Examples:
        >>> part = TemplatePart(content="Hello", inline_formatting=[])
        >>> fmt = InlineFormatting(position=0, type='#', value='red')
        >>> colored_part = TemplatePart(content="Error", inline_formatting=[fmt])
    """
    content: str  # The text content
    inline_formatting: List[InlineFormatting]  # Any inline formatting
    
    def copy(self) -> 'TemplatePart':
        """Create a deep copy for safe mutation during formatting."""
        return TemplatePart(
            content=self.content,
            inline_formatting=[copy.deepcopy(f) for f in self.inline_formatting]
        )

@dataclass
class TemplateSection:
    """
    Represents a complete template section with conditional evaluation logic.
    
    Template sections correspond to {{...}} constructs in templates and contain
    the logic for conditional rendering based on data availability.
    
    Args:
        is_mandatory (bool): Whether section requires field data (marked with '!').
        section_formatting (Dict[str, List[str]]): Section-level formatting tokens
                                                 by formatter type.
        field_name (Optional[str]): Field variable name, or None for literal text.
        prefix (Optional[TemplatePart]): Text before field value.
        field (TemplatePart): The field component itself.
        suffix (Optional[TemplatePart]): Text after field value.
    
    Examples:
        Simple field section:
        >>> field_part = TemplatePart(content="", inline_formatting=[])
        >>> section = TemplateSection(
        ...     is_mandatory=False,
        ...     section_formatting={},
        ...     field_name="username",
        ...     prefix=None,
        ...     field=field_part,
        ...     suffix=None
        ... )
        
        Section with formatting:
        >>> section = TemplateSection(
        ...     is_mandatory=True,
        ...     section_formatting={'#': ['red'], '@': ['bold']},
        ...     field_name="error",
        ...     prefix=TemplatePart(content="ERROR: ", inline_formatting=[]),
        ...     field=field_part,
        ...     suffix=None
        ... )
    """
    is_mandatory: bool
    section_formatting: Dict[str, List[str]]
    field_name: Optional[str]
    prefix: Optional[TemplatePart]
    field: TemplatePart
    suffix: Optional[TemplatePart]

    def copy(self) -> 'TemplateSection':
        """Create a deep copy for safe mutation during formatting."""
        def copy_part(part: Optional['TemplatePart']) -> Optional['TemplatePart']:
            return part.copy() if part else None

        # Deep copy section formatting dictionary
        new_section_formatting = {k: v.copy() for k, v in self.section_formatting.items()}

        return TemplateSection(
            is_mandatory=self.is_mandatory,
            section_formatting=new_section_formatting,
            field_name=self.field_name,
            prefix=copy_part(self.prefix),
            field=copy_part(self.field),
            suffix=copy_part(self.suffix)
        )