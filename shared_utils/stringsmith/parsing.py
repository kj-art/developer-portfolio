"""
Template parsing logic for StringSmith.
"""

import re
from typing import List, Optional, NamedTuple

# Handle both relative and absolute imports
try:
    from .exceptions import StringSmithError
except ImportError:
    from exceptions import StringSmithError


class InlineFormatting(NamedTuple):
    """Represents inline formatting within a part."""
    position: int  # Position in the text where this formatting starts
    type: str  # "color", "emphasis", or "condition"
    value: str  # The formatting value or function name


class TemplatePart(NamedTuple):
    """Represents a part of a section (prefix, field, or suffix)."""
    content: str  # The text content
    inline_formatting: List[InlineFormatting]  # Any inline formatting


class TemplateSection(NamedTuple):
    """Represents a complete template section."""
    is_mandatory: bool
    section_condition: Optional[str]  # Function name for section-level condition
    section_formatting: List[str]  # Section-level formatting (color_, emphasis_, or custom function)
    field_name: str  # Variable name (or synthetic name for positional)
    prefix: Optional[TemplatePart]
    field_part: TemplatePart  # The field itself (may have inline formatting)
    suffix: Optional[TemplatePart]


class TemplateParser:
    """Parses template strings into structured sections."""
    
    def __init__(self, delimiter: str = ";", escape_char: str = "\\"):
        self.delimiter = delimiter
        self.escape_char = escape_char
        
        # Regex to find template sections
        self.section_pattern = re.compile(r'\{\{(.*?)\}\}')
        
        # Regex to find inline formatting
        self.inline_pattern = re.compile(r'\{([#@?])([^}]*)\}')
    
    def parse_template(self, template: str) -> List[TemplateSection]:
        """
        Parse a template string into sections and regular text.
        
        Returns a list of TemplateSection objects and text segments.
        """
        sections = []
        last_end = 0
        
        for match in self.section_pattern.finditer(template):
            start, end = match.span()
            
            # Add any text before this section as a literal text section
            if start > last_end:
                text_content = self._unescape_text(template[last_end:start])
                if text_content:  # Only add non-empty text
                    sections.append(self._create_text_section(text_content))
            
            # Parse the section content
            section_content = match.group(1)
            section = self._parse_section(section_content)
            sections.append(section)
            
            last_end = end
        
        # Add any remaining text
        if last_end < len(template):
            text_content = self._unescape_text(template[last_end:])
            if text_content:
                sections.append(self._create_text_section(text_content))
        
        return sections
    
    def _create_text_section(self, text: str) -> TemplateSection:
        """Create a section for literal text (no variables)."""
        field_part = TemplatePart(content="", inline_formatting=[])
        prefix_part = TemplatePart(content=text, inline_formatting=[])
        
        return TemplateSection(
            is_mandatory=False,
            section_condition=None,
            section_formatting=[],
            field_name="",  # No field name for text sections
            prefix=prefix_part,
            field_part=field_part,
            suffix=None
        )
    
    def _parse_section(self, content: str) -> TemplateSection:
        """Parse the content of a single {{}} section."""
        is_mandatory = False
        section_condition = None
        section_formatting = []
        
        # Check for mandatory marker
        if content.startswith('!'):
            is_mandatory = True
            content = content[1:]
        
        # Parse section-level tokens (can be multiple consecutive tokens)
        remaining_content = content
        
        while remaining_content and remaining_content[0] in ('?', '#', '@'):
            token_type = remaining_content[0]
            remaining_content = remaining_content[1:]  # Remove the token character
            
            # Find where this token ends (either at next token or delimiter)
            token_end = 0
            while token_end < len(remaining_content):
                char = remaining_content[token_end]
                if char in ('?', '#', '@'):
                    # Next token starts here
                    break
                elif char == self.delimiter:
                    # Delimiter found - end of tokens
                    break
                token_end += 1
            
            token_part = remaining_content[:token_end]
            remaining_content = remaining_content[token_end:]
            
            # Process the token
            if token_type == '?':
                section_condition = token_part
            elif token_type in ('#', '@'):
                section_formatting.append(f"{token_type}_{token_part}")
        
        # If we have remaining content and it starts with delimiter, skip it
        if remaining_content.startswith(self.delimiter):
            remaining_content = remaining_content[1:]
        
        # Parse the remaining parts based on count
        if remaining_content:
            remaining_parts = self._split_unescaped(remaining_content)
        else:
            remaining_parts = []
        
        if not remaining_parts:
            # No parts - this shouldn't happen in normal usage
            raise StringSmithError(f"Invalid section format: {{{{{content}}}}}")
        
        if len(remaining_parts) == 1:
            # {{field}} or {{?func;field}} or {{#color;field}}
            prefix = None
            field_text = self._unescape_part(remaining_parts[0])
            # Parse field for inline formatting and extract clean field name
            field_part = self._parse_part(field_text)
            field_name = field_part.content
            suffix = None
        elif len(remaining_parts) == 2:
            # {{prefix;field}} or {{?func;prefix;field}} or {{#color;prefix;field}}
            prefix_text = self._unescape_part(remaining_parts[0])
            field_text = self._unescape_part(remaining_parts[1])
            # Parse field for inline formatting and extract clean field name
            field_part = self._parse_part(field_text)
            field_name = field_part.content
            suffix = None
            prefix = self._parse_part(prefix_text) if prefix_text else None
        elif len(remaining_parts) == 3:
            # {{prefix;field;suffix}} or {{?func;prefix;field;suffix}} etc.
            prefix_text = self._unescape_part(remaining_parts[0])
            field_text = self._unescape_part(remaining_parts[1])
            suffix_text = self._unescape_part(remaining_parts[2])
            # Parse field for inline formatting and extract clean field name
            field_part = self._parse_part(field_text)
            field_name = field_part.content
            prefix = self._parse_part(prefix_text) if prefix_text else None
            suffix = self._parse_part(suffix_text) if suffix_text else None
        else:
            raise StringSmithError(f"Too many parts in section: {{{{{content}}}}}")
        
        # field_part is now properly parsed
        
        return TemplateSection(
            is_mandatory=is_mandatory,
            section_condition=section_condition,
            section_formatting=section_formatting,
            field_name=field_name,
            prefix=prefix,
            field_part=field_part,
            suffix=suffix
        )
    
    def _parse_part(self, text: str) -> TemplatePart:
        """Parse a part (prefix or suffix) for inline formatting."""
        inline_formatting = []
        
        # Find all inline formatting tokens
        for match in self.inline_pattern.finditer(text):
            token_type = match.group(1)  # #, @, or ?
            token_value = match.group(2)
            position = match.start()
            
            if token_type == '#':
                inline_formatting.append(InlineFormatting(position, "color", token_value))
            elif token_type == '@':
                inline_formatting.append(InlineFormatting(position, "emphasis", token_value))
            elif token_type == '?':
                inline_formatting.append(InlineFormatting(position, "condition", token_value))
        
        # Remove the inline formatting tokens from the text but keep position tracking
        clean_text = text
        offset = 0
        
        # Sort inline formatting by position (reverse order for removal)
        sorted_formatting = sorted(inline_formatting, key=lambda x: x.position, reverse=True)
        
        for formatting in sorted_formatting:
            # Find the original token in the text
            start_pos = formatting.position
            # Find the end of the token (next '}')
            end_pos = text.find('}', start_pos) + 1
            if end_pos > start_pos:
                # Remove the token from clean_text and adjust positions
                clean_text = clean_text[:start_pos] + clean_text[end_pos:]
        
        # Adjust positions in inline_formatting after token removal
        adjusted_formatting = []
        for formatting in inline_formatting:
            # Calculate how many characters were removed before this position
            chars_removed = 0
            for other in inline_formatting:
                if other.position < formatting.position:
                    # Find token length
                    token_start = other.position
                    token_end = text.find('}', token_start) + 1
                    chars_removed += token_end - token_start
            
            new_position = formatting.position - chars_removed
            adjusted_formatting.append(InlineFormatting(
                new_position, formatting.type, formatting.value
            ))
        
        # Sort by position for processing
        adjusted_formatting.sort(key=lambda x: x.position)
        
        return TemplatePart(content=clean_text, inline_formatting=adjusted_formatting)
    
    def _find_unescaped_delimiter(self, text: str) -> int:
        """Find the first unescaped delimiter in the text."""
        i = 0
        while i < len(text):
            if text[i] == self.delimiter:
                # Check if it's escaped
                if i > 0 and text[i-1] == self.escape_char:
                    # Check if the escape char itself is escaped
                    escape_count = 0
                    j = i - 1
                    while j >= 0 and text[j] == self.escape_char:
                        escape_count += 1
                        j -= 1
                    # If even number of escape chars, the delimiter is not escaped
                    if escape_count % 2 == 0:
                        return i
                else:
                    return i
            i += 1
        return -1
    
    def _split_unescaped(self, text: str) -> List[str]:
        """Split text by unescaped delimiters."""
        parts = []
        current_part = ""
        i = 0
        
        while i < len(text):
            if text[i] == self.delimiter:
                # Check if it's escaped
                if i > 0 and text[i-1] == self.escape_char:
                    # Check if the escape char itself is escaped
                    escape_count = 0
                    j = i - 1
                    while j >= 0 and text[j] == self.escape_char:
                        escape_count += 1
                        j -= 1
                    # If odd number of escape chars, the delimiter is escaped
                    if escape_count % 2 == 1:
                        current_part += text[i]
                    else:
                        parts.append(current_part)
                        current_part = ""
                else:
                    parts.append(current_part)
                    current_part = ""
            else:
                current_part += text[i]
            i += 1
        
        parts.append(current_part)
        return parts
    
    def _unescape_part(self, text: str) -> str:
        """Remove escape characters from a part within a section."""
        # Unescape delimiters within the part
        text = text.replace(f'{self.escape_char}{self.delimiter}', self.delimiter)
        text = text.replace(f'{self.escape_char}{self.escape_char}', self.escape_char)  # Unescape escape char last
        return text
    
    def _unescape_text(self, text: str) -> str:
        """Remove escape characters from regular text."""
        # Unescape curly braces and delimiters
        text = text.replace(f'{self.escape_char}{{', '{')
        text = text.replace(f'{self.escape_char}}}', '}')
        text = text.replace(f'{self.escape_char}{self.delimiter}', self.delimiter)
        text = text.replace(f'{self.escape_char}{self.escape_char}', self.escape_char)  # Unescape escape char last
        return text