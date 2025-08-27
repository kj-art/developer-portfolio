"""
Template parsing engine for StringSmith conditional formatting.

This module handles the core parsing logic that converts template strings into
structured AST objects for efficient runtime evaluation. The parser recognizes
template sections ({{...}}), inline formatting tokens, escape sequences, and
custom delimiters.
"""

import re
from typing import List, Optional, Dict, Tuple


from ..exceptions import StringSmithError
from ..tokens import TOKEN_REGISTRY, SORTED_TOKENS
from . import TemplatePart, TemplateSection, InlineFormatting

class TemplateParser:
    """
    Parses template strings into structured AST representations for efficient evaluation.
    
    TemplateParser converts StringSmith template strings into TemplateSection objects
    that can be efficiently evaluated with runtime data. The parser handles the full
    complexity of StringSmith template syntax including formatting tokens, escape
    sequences, and custom delimiters.
    
    Args:
        delimiter (str, optional): Character(s) separating components within template
                                 sections. Defaults to ';'.
        escape_char (str, optional): Character(s) for escape sequences. Defaults to '\\'.
        
    Examples:
        >>> parser = TemplateParser()
        >>> sections = parser.parse_template("{{Hello ;name;}}")
        
        >>> parser = TemplateParser(delimiter='|')
        >>> sections = parser.parse_template("{{Hello|name|!}}")
    """
    
    def __init__(self, delimiter: str = ";", escape_char: str = "\\"):
        """Initialize parser with configurable syntax options."""
        self.delimiter = delimiter
        self.escape_char = escape_char
        
        # Pre-compile regex patterns for efficient parsing
        self.section_pattern = re.compile(r'\{\{(.*?)\}\}')
        
        # Inline formatting pattern with escape handling
        escaped_tokens = [re.escape(token) for token in SORTED_TOKENS]
        token_pattern = '|'.join(escaped_tokens)
        esc = re.escape(escape_char)  # "\\" becomes "\\\\"
        self.inline_pattern = re.compile(f'(?<!{esc})(?:{esc}{esc})*\\{{({token_pattern})([^}}]*)\\}}')

    def parse_template(self, template: str) -> List[TemplateSection]:
        """
        Parse a complete template string into structured sections.
        
        Args:
            template (str): Template string to parse.
        
        Returns:
            List[TemplateSection]: Ordered list of template sections.
        
        Raises:
            StringSmithError: If template contains invalid syntax.
        """
        sections = []
        last_end = 0
        
        # Process each {{...}} section
        for match in self.section_pattern.finditer(template):
            start, end = match.span()
            
            # Add literal text before this section
            if start > last_end:
                text_content = self._unescape_text(template[last_end:start])
                if text_content:  # Only add non-empty text
                    sections.append(self._create_text_section(text_content))
            
            # Parse the section content
            section_content = match.group(1)
            section = self._parse_section(section_content)
            sections.append(section)
            
            last_end = end
        
        # Add remaining literal text
        if last_end < len(template):
            text_content = self._unescape_text(template[last_end:])
            if text_content:
                sections.append(self._create_text_section(text_content))
        
        return sections
    
    def _create_text_section(self, text: str) -> TemplateSection:
        """Create a TemplateSection for literal text (no variables)."""
        field_part = TemplatePart(content="", inline_formatting=[])
        prefix_part = TemplatePart(content=text, inline_formatting=[])
        
        return TemplateSection(
            is_mandatory=False,
            section_formatting=[],
            field_name=None,  # None indicates literal text
            prefix=prefix_part,
            field=field_part,
            suffix=None
        )
    
    def _split_unescaped(self, content: str) -> List[str]:
        """Split content on delimiter characters that are not escaped."""
        # Match: (even number of escape chars)(delimiter)
        # (?<!\\) ensures we're not in the middle of escape sequence
        # (\\\\)* matches zero or more pairs of escapes (even count)
        esc = re.escape(self.escape_char)
        delim = re.escape(self.delimiter)
        pattern = f"(?<!{esc})(?:{esc}{esc})*{delim}"
        
        return re.split(pattern, content)

    def split_by_substrings(self, text: str, substrings: List[str]) -> Dict[str, List[str]]:
        """Split text by multiple substrings, tracking which delimiter was used."""
        # Sort by length (longest first) to avoid partial matches
        sorted_subs = sorted(substrings, key=len, reverse=True)
        
        # Create regex pattern with capturing groups
        escaped_subs = [re.escape(sub) for sub in sorted_subs]
        pattern = f"({'|'.join(escaped_subs)})"
        
        # Split while keeping delimiters
        parts = re.split(pattern, text)
        
        # Organize into dictionary
        result = {sub: [] for sub in substrings}
        current_key = None
        
        for part in parts:
            if part in substrings:
                current_key = part
            elif current_key is not None and part:  # Skip empty parts
                result[current_key].append(part)
        
        return result
    
    def _extract_starting_token(self, text: str) -> Tuple[Optional[str], str]:
        """Extract starting token and return (token, remaining_text)."""
        if text:
            # Sort by length descending to match longest tokens first
            for token in SORTED_TOKENS:
                if text.startswith(token):
                    remaining = text[len(token):]
                    return token, remaining
        
        return None, text
    
    def _parse_section(self, content: str) -> TemplateSection:
        """Parse the content of a single {{}} section."""
        is_mandatory, content = self._extract_mandatory_marker(content)
        section_tokens, parts = self._extract_formatting_tokens(content)
        prefix, field, suffix = self._split_into_parts(parts)

        field_part = self._parse_field_part(field)
        return TemplateSection(
                is_mandatory=is_mandatory,
                section_formatting=section_tokens,
                field_name=field_part.content,
                prefix=self._parse_text_part(prefix),
                field=field_part,
                suffix=self._parse_text_part(suffix)
            )
    
    def _extract_mandatory_marker(self, content: str) -> tuple[bool, str]:
        """Extract mandatory marker and return cleaned content."""
        if content.startswith('!'):
            return True, content[1:]
        return False, content
    
    def _extract_formatting_tokens(self, content: str) -> tuple[Dict[str, List[str]], List[str]]:
        """Extract formatting tokens from the beginning of section content."""
        parts = self._split_unescaped(content)
        
        if not parts:
            return {}, []
        
        first_token, _ = self._extract_starting_token(parts[0])
        if first_token:
            format_part = parts.pop(0)
            section_tokens = self.split_by_substrings(format_part, TOKEN_REGISTRY.keys())
            return section_tokens, parts
        
        return {}, parts
    
    def _split_into_parts(self, parts: List[str]) -> tuple[str, str, str]:
        """Split remaining parts into prefix, field, and suffix."""
        prefix = ''
        field = ''
        suffix = ''

        match len(parts):
            case 0: 
                pass
            case 1: 
                field = parts[0]
            case 2: 
                prefix, field = parts
            case 3: 
                prefix, field, suffix = parts
            case _: 
                section_repr = f"{{{{{self.delimiter.join(parts)}}}}}"
                raise StringSmithError(f"Too many parts in section: {section_repr}")

        return prefix, field, suffix
    
    def _parse_field_part(self, text: str) -> TemplatePart:
        """Parse field component with validation for field-specific formatting rules."""
        formatting = self._parse_text_part(text)

        # Validate that all formatting tokens are at the beginning
        for fmt in formatting.inline_formatting:
            if fmt.position != 0:
                raise StringSmithError(
                    f"Field formatting tokens must be at the beginning of the field part. "
                    f"Found {fmt.type}{fmt.value} token at position {fmt.position} in '{text}'"
                )
            
        return formatting

    def _parse_text_part(self, text: str) -> TemplatePart:
        """Parse text part extracting inline formatting tokens and calculating positions."""  
        inline_formatting = []
        clean_position = 0
        result = ""
        last_end = 0
        
        # Process each inline formatting token
        for match in re.finditer(self.inline_pattern, text):
            # Add text before this token
            text_before = text[last_end:match.start()]
            unescaped_before = self._unescape_part(text_before)
            result += unescaped_before
            clean_position += len(unescaped_before)  # Use unescaped length for position
            
            # Validate and process token
            token_type = match.group(1)
            token_value = match.group(2)
            if '{' in token_value or '}' in token_value:
                raise StringSmithError(f"Nested braces not allowed in token: '{{{token_type}{token_value}}}'")
            
            # Record token at current position
            inline_formatting.append(InlineFormatting(clean_position, token_type, token_value))
            
            last_end = match.end()
        
        # Add remaining text
        remaining_text = text[last_end:]
        result += self._unescape_part(remaining_text)
        
        return TemplatePart(content=result, inline_formatting=inline_formatting)
    
    def _unescape_part(self, part: str) -> str:
        """Remove escape sequences from text part."""
        if not part:
            return part
        
        result = ""
        i = 0
        while i < len(part):
            char = part[i]
            if char == self.escape_char and i + 1 < len(part):
                # Escaped character - add next character literally
                result += part[i + 1]
                i += 2
            else:
                # Regular character
                result += char
                i += 1
        
        return result
    
    def _unescape_text(self, text: str) -> str:
        """Remove escape sequences from literal text."""
        return self._unescape_part(text)