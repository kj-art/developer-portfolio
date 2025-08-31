"""
Abstract Syntax Tree structures for StringSmith template representation.

Defines the data structures that represent parsed templates as structured objects
for efficient conditional evaluation and formatting during runtime operations.
"""

from __future__ import annotations
from typing import List, Optional, Dict
from dataclasses import dataclass

from dataclasses import dataclass
from typing import Optional, Iterator

from dataclasses import dataclass
from typing import Optional, Iterator

from dataclasses import dataclass
from typing import Optional

@dataclass
class SectionParts:
    prefix: Optional[str] = None
    field: Optional[str] = None
    suffix: Optional[str] = None

    # support bracket access
    def __getitem__(self, key: str) -> str:
        if key not in ("prefix", "field", "suffix"):
            raise KeyError(f"{key} is not a valid field")
        return getattr(self, key) or ""

    # support bracket assignment
    def __setitem__(self, key: str, value: str):
        if key not in ("prefix", "field", "suffix"):
            raise KeyError(f"{key} is not a valid field")
        setattr(self, key, value)

    def copy(self) -> "SectionParts":
        return SectionParts(
            prefix=self.prefix,
            field=self.field,
            suffix=self.suffix
        )
    
    def iter_fields(self) -> Iterator[Tuple[str, str]]:
        for key in ("prefix", "field", "suffix"):
            yield key, self[key]

@dataclass
class TemplateSection:
    is_mandatory: bool
    section_formatting: Dict[str, List[str]]
    field_name: Optional[str]
    parts: SectionParts  # nested object
    live_tokens: List[str]

    def copy(self) -> TemplateSection:
        # shallow copy for parts
        return TemplateSection(
            is_mandatory=self.is_mandatory,
            section_formatting={k: v.copy() for k, v in self.section_formatting.items()},
            field_name=self.field_name,
            parts=self.parts.copy(),
            live_tokens=self.live_tokens.copy()
        )
