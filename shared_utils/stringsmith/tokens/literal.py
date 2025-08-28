"""Literal token handler for text transformation via custom functions."""

from typing import Any, Optional, List
from .base import BaseTokenHandler
from ..exceptions import StringSmithError
from ..core import TemplateSection, TemplatePart, InlineFormatting

class LiteralTokenHandler(BaseTokenHandler):
    """Handles literal tokens that inject custom function results directly into text."""
    RESET_ANSI = ''  # Literal tokens don't produce ANSI escape codes

    def _apply_sectional_formatting(self, token_value: str, field_value: Any, text: tuple[str, str, str]) -> Optional[tuple]:
        """Sectional literal tokens are not supported."""
        raise StringSmithError(f"Sectional tokens can not be literal.")
    
    def apply_inline_formatting(self, text_segment: str, position: int, token_value: str, field_value: Any = None) -> tuple[str, bool]:
        """Insert marker for literal function processing during finalization."""
        is_bake = field_value is None  # Baking phase
        if is_bake:
            return text_segment, False
        if token_value not in self.functions:
            raise StringSmithError(f"Error applying function '{token_value}'")

        # Insert marker for finalization processing
        return f"{text_segment[:position]}\uE001{text_segment[position:]}", False 
    
    def finalize(self, section: TemplateSection, field_value: Any) -> bool:
        """Process literal token markers and inject function results.
        
        Returns:
            bool: True if original field value should be appended, False if replaced by literals
        """
        for part in [section.prefix, section.suffix]:
            inline_literals = part.get_inline_formatting_of_type(self._token)
            part.content = self._finalize(part, inline_literals, field_value)

        part = section.field
        inline_literals = part.get_inline_formatting_of_type(self._token)
        
        if len(inline_literals):
            part.content = self._finalize(part, inline_literals, field_value)
            return False
        return True
    
    def _finalize(self, part: TemplatePart, inline_literals: List[InlineFormatting], field_value: Any):
        """Replace literal token markers with function results."""
        segments = part.content.split('\uE001')
        content = segments.pop()
        if len(segments) != len(inline_literals):
            raise StringSmithError(f"Error finalizing text_segment '{part.content}': Mismatch between formatting length and number of literal ANSI markers")
        for inline in inline_literals:
            content = segments.pop() + str(self._call_function(inline.value, field_value)) + content
        return content

    def get_ansi_code(self, token_value: str) -> str:
        """Literal tokens don't generate ANSI codes."""
        return ''