"""
Template parsing engine for StringSmith conditional formatting.

This module handles the core parsing logic that converts template strings into
structured AST-like objects for efficient runtime evaluation. The parser recognizes
template sections ({{...}}), inline formatting tokens (#color, @emphasis, ?conditional),
escape sequences, and custom delimiters.

Key Components:
    TemplateParser: Main parsing class that processes templates into TemplateSection objects
    Section parsing: Converts {{field}} syntax into structured conditional sections
    Inline formatting: Processes {#color} and {@emphasis} tokens within template text
    Escape handling: Manages backslash escapes for literal braces and delimiters

Architecture:
    Templates are parsed once during TemplateFormatter initialization and cached as
    structured objects. This front-loads parsing overhead for optimal runtime performance
    during repeated format() operations.

Thread Safety:
    TemplateParser instances are stateless after construction and safe for concurrent
    use across multiple threads.
"""

import re
from typing import List, Optional, Dict, Tuple

# Handle both relative and absolute imports
try:
    from .exceptions import StringSmithError
    from .token_handlers import TOKEN_REGISTRY, SORTED_TOKENS, TemplatePart, TemplateSection
    from .inline_formatting import InlineFormatting
except ImportError:
    from exceptions import StringSmithError
    from token_handlers import TOKEN_REGISTRY, SORTED_TOKENS, TemplatePart, TemplateSection
    from inline_formatting import InlineFormatting

class TemplateParser:
    """Parses template strings into structured sections."""
    
    def __init__(self, delimiter: str = ";", escape_char: str = "\\"):
        self.delimiter = delimiter
        self.escape_char = escape_char
        
        # Regex to find template sections
        self.section_pattern = re.compile(r'\{\{(.*?)\}\}')
        
        # Regex to find inline formatting
        #self.inline_pattern = re.compile(r'\{([#@?])([^}]*)\}')
        escaped_tokens = [re.escape(token) for token in SORTED_TOKENS]
        token_pattern = '|'.join(escaped_tokens)
        #self.inline_pattern = re.compile(f'\\{{({token_pattern})([^}}]*)\\}}')
        esc = re.escape(escape_char)  # "\\" becomes "\\\\"
        self.inline_pattern = re.compile(f'(?<!{esc})(?:{esc}{esc})*\\{{({token_pattern})([^}}]*)\\}}')

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
            section_formatting=[],
            field_name=None,
            prefix=prefix_part,
            field=field_part,
            suffix=None
        )
    
    def _split_unescaped(self, content: str) -> List[str]:
        """Split on delimiter preceded by even number (including 0) of escape chars."""
        # Match: (even number of escape chars)(delimiter)
        # (?<!\\) ensures we're not in the middle of escape sequence
        # (\\\\)* matches zero or more pairs of escapes (even count)
        esc = re.escape(self.escape_char)
        delim = re.escape(self.delimiter)
        pattern = f"(?<!{esc})(?:{esc}{esc})*{delim}"
        
        return re.split(pattern, content)

    def split_by_substrings(self, text: str, substrings: List[str]) -> Dict[str, List[str]]:
        """Split text by multiple substrings, keeping track of which delimiter was used."""
        
        # Sort by length (longest first) to avoid partial matches
        sorted_subs = sorted(substrings, key=len, reverse=True)
        
        # Create regex pattern with capturing groups
        escaped_subs = [re.escape(sub) for sub in sorted_subs]
        pattern = f"({'|'.join(escaped_subs)})"
        
        # Split while keeping delimiters
        parts = re.split(pattern, text)
        
        # Organize into dict
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
        is_mandatory = False
        
        # Check for mandatory marker
        if content.startswith('!'):
            is_mandatory = True
            content = content[1:]
        
        parts = self._split_unescaped(content)
        if self._extract_starting_token(parts[0])[0]:
            format_part = parts.pop(0)
            section_tokens = self.split_by_substrings(format_part, TOKEN_REGISTRY.keys())
        else:
            section_tokens = {}

        prefix = ''
        field = ''
        suffix = ''

        match len(parts):
            case 0: pass
            case 1: field = parts[0]
            case 2: prefix, field = parts
            case 3: prefix, field, suffix = parts
            case _: raise StringSmithError(f"Too many parts in section: {{{{{content}}}}}")

        field_part = self._parse_field_part(field)
        return TemplateSection(
                is_mandatory=is_mandatory,
                section_formatting=section_tokens,
                field_name=field_part.content,
                prefix=self._parse_text_part(prefix),
                field=field_part,
                suffix=self._parse_text_part(suffix)
            )
    
    def _parse_field_part(self, text: str) -> TemplatePart:
        formatting = self._parse_text_part(text)
        if any(fmt.position != 0 for fmt in formatting.inline_formatting):
            raise StringSmithError("Field formatting tokens must be at the beginning of the field part")
        return formatting

    def _parse_text_part(self, text: str) -> TemplatePart:
        """Extract inline formatting tokens and return clean positions + clean text."""
        
        inline_formatting = []
        clean_position = 0
        result = ""
        last_end = 0
        
        for match in re.finditer(self.inline_pattern, text):
            # Add text before this match (unescaped)
            text_before = text[last_end:match.start()]
            unescaped_before = self._unescape_part(text_before)
            result += unescaped_before
            clean_position += len(unescaped_before)  # Use unescaped length for position
            
            # Validate and process token
            token_type = match.group(1)
            token_value = match.group(2)
            if '{' in token_value or '}' in token_value:
                raise StringSmithError(f"Nested braces not allowed in token: '{{{token_type}{token_value}}}'")
            
            # Record token at current clean position
            inline_formatting.append(InlineFormatting(clean_position, token_type, token_value))
            
            last_end = match.end()
        
        # Add remaining text after processing escape sequences
        remaining_text = text[last_end:]
        result += self._unescape_part(remaining_text)
        
        return TemplatePart(content=result, inline_formatting=inline_formatting)
    
    def _unescape_part(self, part: str) -> str:
        """Remove escape sequences from a part."""
        if not part:
            return part
        
        result = ""
        i = 0
        while i < len(part):
            char = part[i]
            if char == self.escape_char and i + 1 < len(part):
                # Escaped character - add the next character literally
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