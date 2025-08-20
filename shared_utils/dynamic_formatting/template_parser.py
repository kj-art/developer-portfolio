"""
Template parsing logic for dynamic formatting system.

This module handles parsing of format strings into structured format sections and spans.
The parser supports:
- Template sections with {{...}} syntax
- Inline formatting tokens (#color, @style, ?conditional)
- Comprehensive escape sequence handling (\\{, \\}, \\;)
- Function fallback integration
- Family-based formatting state management
- Positional arguments via field position tracking
"""

from typing import Dict, List, Union, Optional, Any, Tuple
from .span_structures import FormattedSpan, FormatSection


class DynamicFormattingError(Exception):
    """Base exception for dynamic formatting errors"""
    pass


class ParseError(DynamicFormattingError):
    """Raised when template parsing fails"""
    pass


class TemplateParser:
    """Handles parsing of format template strings with full type safety"""
    
    def __init__(self, delimiter: str = ';', token_formatters: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize template parser
        
        Args:
            delimiter: Character used to separate template parts
            token_formatters: Dictionary mapping token prefixes to formatter instances
        """
        self.delimiter = delimiter
        self.token_formatters = token_formatters or {}
        self.positional_counter = 0  # Track positional sections for arguments
    
    def parse_format_string(self, format_string: str) -> List[Union[str, FormatSection]]:
        """
        Parse a format string into sections, handling escape sequences
        
        Args:
            format_string: Template string to parse
            
        Returns:
            List of string literals and FormatSection objects
            
        Raises:
            ParseError: If template syntax is invalid
        """
        sections: List[Union[str, FormatSection]] = []
        i = 0
        current_literal = ""
        
        while i < len(format_string):
            char = format_string[i]
            
            # Check for escaped characters (backslash followed by delimiter, brace, etc.)
            if char == '\\' and i + 1 < len(format_string):
                next_char = format_string[i + 1]
                escapable_chars = f'{{}};{self.delimiter}'
                if next_char in escapable_chars:
                    current_literal += next_char  # Add the escaped character literally
                    i += 2  # Skip both backslash and escaped character
                    continue
                else:
                    # Not an escape sequence, keep the backslash
                    current_literal += char
                    i += 1
                    continue
            
            if char == '{' and i + 1 < len(format_string) and format_string[i + 1] == '{':
                if current_literal:
                    sections.append(current_literal)
                    current_literal = ""
                
                i += 2  # Skip {{
                template_content = ""
                while i < len(format_string):
                    if (i + 1 < len(format_string) and 
                        format_string[i] == '}' and format_string[i + 1] == '}'):
                        break
                    template_content += format_string[i]
                    i += 1
                
                if i + 1 < len(format_string):
                    i += 2  # Skip }}
                else:
                    raise ParseError("Unclosed template section: missing }}")
                
                try:
                    section = self._parse_template_content(template_content)
                    sections.append(section)
                except Exception as e:
                    raise ParseError(f"Error parsing template '{template_content}': {e}")
            else:
                current_literal += char
                i += 1
        
        if current_literal:
            sections.append(current_literal)
        
        return sections
    
    def _parse_template_content(self, content: str) -> FormatSection:
        """
        Parse the content of a template section {{...}}
        
        Args:
            content: Content inside the template braces
            
        Returns:
            Parsed FormatSection object
            
        Raises:
            ParseError: If template content is malformed
        """
        # Handle required field marker
        is_required = False
        if content.startswith('!'):
            is_required = True
            content = content[1:]
        
        # Extract leading tokens (functions and formatting that apply to whole section)
        function_name: Optional[str] = None
        whole_section_tokens: Dict[str, List[str]] = {}
        
        # Process tokens in sequence
        while True:
            found_token = False
            
            # Look for conditional function (?function_name)
            if content.startswith('?'):
                end_pos = self._find_token_end(content, 1)
                function_name = content[1:end_pos]
                content = content[end_pos:]
                found_token = True
            
            # Look for formatting tokens (#color, @style)
            elif content and content[0] in self.token_formatters:
                prefix = content[0]
                end_pos = self._find_token_end(content, 1)
                token_value = content[1:end_pos]
                
                if prefix not in whole_section_tokens:
                    whole_section_tokens[prefix] = []
                whole_section_tokens[prefix].append(token_value)
                content = content[end_pos:]
                found_token = True
            
            if not found_token:
                break
        
        # Split remaining content by delimiter to get prefix, field, suffix
        parts = content.split(self.delimiter)
        
        # Handle positional arguments (empty field name)
        if len(parts) == 1 and not parts[0]:
            # Empty template like {{}} - this is a positional argument
            field_name = f"__pos_{self.positional_counter}__"
            prefix = ""
            suffix = ""
            self.positional_counter += 1
        elif len(parts) == 1:
            # Just field name: {{field}}
            field_name = parts[0] if parts[0] else f"__pos_{self.positional_counter}__"
            if not parts[0]:
                self.positional_counter += 1
            prefix = ""
            suffix = ""
        elif len(parts) == 2:
            # Two parts - could be prefix;field or field;suffix
            if parts[0] and not parts[1]:
                # Pattern: {{prefix;}} - treat as prefix and positional field
                prefix = parts[0]
                field_name = f"__pos_{self.positional_counter}__"
                suffix = ""
                self.positional_counter += 1
            elif not parts[0] and parts[1]:
                # Pattern: {{;suffix}} - treat as positional field and suffix
                prefix = ""
                field_name = f"__pos_{self.positional_counter}__"
                suffix = parts[1]
                self.positional_counter += 1
            else:
                # Pattern: {{prefix;field}} - prefix and named field
                prefix = parts[0]
                field_name = parts[1] if parts[1] else f"__pos_{self.positional_counter}__"
                if not parts[1]:
                    self.positional_counter += 1
                suffix = ""
        elif len(parts) == 3:
            # Three parts: {{prefix;field;suffix}}
            prefix = parts[0]
            field_name = parts[1] if parts[1] else f"__pos_{self.positional_counter}__"
            if not parts[1]:
                self.positional_counter += 1
            suffix = parts[2]
        else:
            # More than 3 parts - join extra parts as suffix
            prefix = parts[0]
            field_name = parts[1] if parts[1] else f"__pos_{self.positional_counter}__"
            if not parts[1]:
                self.positional_counter += 1
            suffix = self.delimiter.join(parts[2:])
        
        return FormatSection(
            field_name=field_name,
            prefix=prefix,
            suffix=suffix,
            is_required=is_required,
            function_name=function_name,
            whole_section_formatting_tokens=whole_section_tokens,
            spans=[]  # Complex spans not implemented in this fix
        )
    
    def _find_token_end(self, content: str, start_pos: int) -> int:
        """Find the end position of a token"""
        i = start_pos
        while i < len(content):
            char = content[i]
            # Stop at delimiter, another token, or end
            if char == self.delimiter or char in self.token_formatters:
                break
            i += 1
        return i