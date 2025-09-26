"""Conditional token handler for StringSmith."""

from typing import Any, Optional
from .base import BaseTokenHandler
from ..exceptions import StringSmithError
from ..core import SectionParts, TemplateSection
from .registry import register_token_handler

@register_token_handler('?', sub_priority=10)
class ConditionalTokenHandler(BaseTokenHandler):
    """
    Handles conditional tokens (?function_name) that show/hide sections.
    
    Conditional tokens call user-defined functions with field values and show
    the section only if the function returns a truthy value.
    
    Examples:
        >>> def is_error(level):
        ...     return level.lower() == 'error'
        >>> handler = ConditionalTokenHandler('?', {'is_error': is_error})
        >>> # Template: {{?is_error;[ERROR] ;level}}
        >>> # Shows "[ERROR] " prefix only when level is 'error'
    """

    def apply_section_formatting(self, section: TemplateSection, field_value: Any = None, kwargs: dict = None) -> bool:
        for fmt in section.section_formatting.get(self.token):
            if not self._call_function(fmt, field_value, kwargs):
                for k, v in section.parts.iter_fields():
                    section.parts[k] = ''
                    return False
        return True
    
    def get_static_formatting(self, token_value: str) -> Optional[str]:
        return None

    def apply_inline_formatting(
            self,
            split_part: list[str | tuple[str, str]],
            part_type: str,
            field_value: Any,
            kwargs: dict = None
            ) -> tuple[list[str | tuple[str, str]], bool]:
        groups = self._split_on_token(split_part)
        result = []
        show = True
        for group in groups:
            if isinstance(group, str): # is a matching splitter
                show = self._is_reset_token(group) or self._call_function(group, field_value, kwargs)
            elif show:
                result += group
        return (result, part_type != 'field' or show)
    
    def _split_on_token(
        self, 
        split_part: list[str | tuple[str, str]]
    ) -> list[list[str | tuple[str, str]] | str]:
        groups: list[list[str | tuple[str, str]] | str] = []
        current: list[str | tuple[str, str]] = []
        token = self.token

        for part in split_part:
            if isinstance(part, str) or part[0] != token:
                current.append(part)
            else:
                groups.append(current)
                groups.append(part[1])
                current = []

        if current:
            groups.append(current)

        return groups



    def get_replacement_text(self, token_value: str) -> str:
        return ''