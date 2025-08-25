from __future__ import annotations
from typing import List, Optional, Dict
import copy
from dataclasses import dataclass
try:
    from .inline_formatting import InlineFormatting
except ImportError:
    from inline_formatting import InlineFormatting

@dataclass
class TemplatePart:
    """Represents a part of a section (prefix, field, or suffix)."""
    content: str  # The text content
    inline_formatting: List[InlineFormatting]  # Any inline formatting
    
    def copy(self) -> 'TemplatePart':
        """Return a deep copy of this TemplatePart."""
        return TemplatePart(
            content=self.content,
            inline_formatting=[copy.deepcopy(f) for f in self.inline_formatting]
        )

@dataclass
class TemplateSection:
    """Represents a complete template section."""
    is_mandatory: bool
    section_formatting: Dict[str, List[str]]  # Section-level formatting (color_, emphasis_, or custom function)
    field_name: Optional[str] # Keyword lookup name for this section. None if this is non-sectional, raw text
    prefix: Optional[TemplatePart]
    field: TemplatePart  # The field itself (may have inline formatting)
    suffix: Optional[TemplatePart]

    def copy(self) -> 'TemplateSection':
        """Return a deep copy of this TemplateSection."""
        def copy_part(part: Optional['TemplatePart']) -> Optional['TemplatePart']:
            return part.copy() if part else None

        # Deep copy the section_formatting dictionary
        new_section_formatting = {k: v.copy() for k, v in self.section_formatting.items()}

        return TemplateSection(
            is_mandatory=self.is_mandatory,
            section_formatting=new_section_formatting,
            field_name=self.field_name,
            prefix=copy_part(self.prefix),
            field=copy_part(self.field),
            suffix=copy_part(self.suffix)
        )