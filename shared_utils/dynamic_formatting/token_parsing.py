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

PARSING ARCHITECTURE:
    1. Top-level parsing splits format strings into literal text and template sections
    2. Template content parsing extracts functions, formatting tokens, and field references  
    3. Formatted text parsing handles inline formatting within text spans
    4. Escape sequence processing converts \\{ → { throughout all levels
    5. All field sections are tracked for positional argument support

POSITIONAL ARGUMENT PARSING RULES:
    {{}} - valid positional field (empty field name)
    {{#red}} - valid positional field with formatting token  
    {{my_field;}} - valid for both, field name ignored for positional (prefix;field pattern)
    {{my_field}} - valid for both, field name ignored for positional (single field)
    {{#red;my_field}} - valid for both, token;field pattern
    {{prefix;my_field}} - valid for both, prefix;field pattern
    {{prefix;my_field;suffix}} - valid for both, prefix;field;suffix pattern
    {{#red@bold;prefix;my_field}} - valid for both, token;prefix;field pattern
    {{#red@bold;prefix;my_field;suffix}} - valid for both, token;prefix;field;suffix pattern

PERFORMANCE:
    - Single-pass parsing with O(n) time complexity
    - Efficient escape sequence handling
    - Minimal object creation for simple cases
"""

from typing import Dict, List, Union, Callable, Optional
from .span_structures import FormattedSpan, FormatSection


class DynamicFormattingError(Exception):
    """Base exception for dynamic formatting errors"""
    pass


class ParseError(DynamicFormattingError):
    """Raised when template parsing fails"""
    pass


class TemplateParser:
    """Handles parsing of format template strings"""
    
    def __init__(self, delimiter: str = ';', token_formatters: Dict = None):
        self.delimiter = delimiter
        self.token_formatters = token_formatters or {}
        self.positional_field_count = 0  # Track number of field sections for positional support
    
    def parse_format_string(self, format_string: str) -> List[Union[str, FormatSection]]:
        """Parse a format string into sections, handling escape sequences"""
        sections = []
        i = 0
        current_literal = ""
        
        while i < len(format_string):
            char = format_string[i]
            
            # Check for escaped braces
            if char == '\\' and i + 1 < len(format_string) and format_string[i + 1] in '{}':
                current_literal += format_string[i + 1]  # Add the literal brace
                i += 2  # Skip both backslash and brace
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
        """Parse the content of a template section {{...}}"""
        if not content:
            # Empty content like {{}} - this is a valid positional field
            self.positional_field_count += 1
            return FormatSection(
                field_name=f"__pos_{self.positional_field_count - 1}__",
                is_required=False,
                prefix=None,
                suffix=None,
                field_formatting_tokens={},
                function_name=None,
                whole_section_formatting_tokens={}
            )
        
        # Handle required field marker
        is_required = False
        if content.startswith('!'):
            is_required = True
            content = content[1:]
        
        # Extract leading tokens (functions and formatting that apply to whole section)
        function_name = None
        whole_section_tokens = {}
        
        while True:
            found_token = False
            
            # Look for conditional function (?function_name)
            if content.startswith('?') and self.delimiter in content:
                end_pos = content.find(self.delimiter)
                function_name = content[1:end_pos]
                content = content[end_pos + 1:]
                found_token = True
                continue
            
            # Look for formatting tokens
            for token_char, formatter in self.token_formatters.items():
                if content.startswith(token_char):
                    i = 1  # Start after the token character
                    token_value = ""
                    
                    # Find the end of this token value
                    while i < len(content):
                        char = content[i]
                        if char == self.delimiter:
                            # Semicolon ends this token and moves to next part
                            break
                        elif char in self.token_formatters:
                            # Another token character starts a new token
                            break
                        else:
                            token_value += char
                            i += 1
                    
                    if not token_value:
                        # No value found, skip this
                        break
                    
                    family_name = formatter.get_family_name()
                    if family_name not in whole_section_tokens:
                        whole_section_tokens[family_name] = []
                    
                    # Store the raw token value for now - will be parsed with field_value later
                    whole_section_tokens[family_name].append(token_value)
                    
                    # Move past this token
                    content = content[i:]
                    if content.startswith(self.delimiter):
                        content = content[1:]
                    
                    found_token = True
                    break
            
            if not found_token:
                break
        
        # If we have only tokens and no remaining content, this is a token-only field
        if not content:
            # Like {{#red}} - this is a valid positional field with formatting
            self.positional_field_count += 1
            return FormatSection(
                field_name=f"__pos_{self.positional_field_count - 1}__",
                is_required=is_required,
                prefix=None,
                suffix=None,
                field_formatting_tokens={},
                function_name=function_name,
                whole_section_formatting_tokens=whole_section_tokens
            )
        
        # Parse remaining content (prefix;field;suffix pattern)
        parts = self._split_content(content)
        
        if len(parts) == 1:
            # Single part - could be just a field name or a field with inline formatting
            field_name, field_formatting = self._parse_field_with_formatting(parts[0])
            
            self.positional_field_count += 1
            return FormatSection(
                field_name=field_name or f"__pos_{self.positional_field_count - 1}__",
                is_required=is_required,
                prefix=None,
                suffix=None,
                field_formatting_tokens=field_formatting,
                function_name=function_name,
                whole_section_formatting_tokens=whole_section_tokens
            )
        elif len(parts) == 2:
            # Two parts - prefix;field
            prefix = self._parse_formatted_text(parts[0])
            field_name, field_formatting = self._parse_field_with_formatting(parts[1])
            
            self.positional_field_count += 1
            return FormatSection(
                field_name=field_name or f"__pos_{self.positional_field_count - 1}__",
                is_required=is_required,
                prefix=prefix,
                suffix=None,
                field_formatting_tokens=field_formatting,
                function_name=function_name,
                whole_section_formatting_tokens=whole_section_tokens
            )
        elif len(parts) >= 3:
            # Three or more parts - prefix;field;suffix
            prefix_text = parts[0]
            suffix_text = parts[-1]
            
            # Join middle parts as the field (handles cases where field contains delimiters)
            if len(parts) == 3:
                field_part = parts[1]
            else:
                # For 4+ parts, join the middle parts with the delimiter
                field_part = self.delimiter.join(parts[1:-1])
            
            field_name, field_formatting = self._parse_field_with_formatting(field_part)
            
            # Handle prefix and suffix functions
            prefix_func = None
            suffix_func = None
            processed_prefix = None
            processed_suffix = None
            
            if prefix_text.startswith('$'):
                prefix_func = prefix_text[1:]
            else:
                processed_prefix = self._parse_formatted_text(prefix_text)
            
            if suffix_text.startswith('$'):
                suffix_func = suffix_text[1:]
            else:
                processed_suffix = self._parse_formatted_text(suffix_text)
            
            self.positional_field_count += 1
            return FormatSection(
                field_name=field_name or f"__pos_{self.positional_field_count - 1}__",
                is_required=is_required,
                prefix=processed_prefix, 
                suffix=processed_suffix,
                field_formatting_tokens=field_formatting,
                function_name=function_name,
                prefix_function=prefix_func, 
                suffix_function=suffix_func,
                whole_section_formatting_tokens=whole_section_tokens
            )
        else:
            raise ParseError("Invalid template syntax: empty template content")
    
    def _parse_field_with_formatting(self, field_part: str) -> tuple[str, Dict[str, List]]:
        """Parse field that might have formatting at the start like {#red}field_name"""
        formatting_tokens = {}
        
        # Extract formatting tokens from the beginning
        while field_part.startswith('{'):
            found_token = False
            for token_char, formatter in self.token_formatters.items():
                if field_part.startswith('{' + token_char):
                    # Find the end of this token
                    end_pos = field_part.find('}')
                    if end_pos == -1:
                        break
                    
                    token_value = field_part[2:end_pos]  # Skip '{' and token_char
                    field_part = field_part[end_pos + 1:]  # Skip past '}'
                    
                    family_name = formatter.get_family_name()
                    if family_name not in formatting_tokens:
                        formatting_tokens[family_name] = []
                    
                    formatting_tokens[family_name].append(token_value)
                    found_token = True
                    break
            
            if not found_token:
                break
        
        return field_part, formatting_tokens
    
    def _parse_formatted_text(self, text: str) -> List[FormattedSpan]:
        """Parse text that may contain inline formatting"""
        if not text:
            return []
        
        spans = []
        i = 0
        current_text = ""
        
        while i < len(text):
            char = text[i]
            
            # Check for escaped braces
            if char == '\\' and i + 1 < len(text) and text[i + 1] in '{}':
                current_text += text[i + 1]
                i += 2
                continue
                
            if char == '{':
                # Look for inline formatting token
                found_token = False
                for token_char, formatter in self.token_formatters.items():
                    if text[i:].startswith('{' + token_char):
                        # Found an inline token like {#red} or {#random_color}
                        if current_text:
                            spans.append(FormattedSpan(current_text))
                            current_text = ""
                        
                        # Find the end of this token
                        end_pos = text.find('}', i)
                        if end_pos == -1:
                            # No closing brace found, treat as literal text
                            current_text += char
                            i += 1
                            break
                        
                        token_content = text[i + 2:end_pos]  # Skip '{' + token_char
                        
                        # Get the next character after the closing brace - that's what gets formatted
                        next_char_start = end_pos + 1
                        if next_char_start < len(text):
                            # Get exactly one character to format
                            formatted_char = text[next_char_start]
                            
                            family_name = formatter.get_family_name()
                            token_dict = {family_name: [token_content]} if token_content else {}
                            
                            spans.append(FormattedSpan(formatted_char, token_dict))
                            
                            # Move past the token and the formatted character
                            i = next_char_start + 1
                        else:
                            # No character to format, just move past the token
                            i = end_pos + 1
                        
                        found_token = True
                        break
                
                if not found_token:
                    current_text += char
                    i += 1
            else:
                current_text += char
                i += 1
        
        if current_text:
            spans.append(FormattedSpan(current_text))
        
        return spans if spans else [FormattedSpan("")]
    
    def _split_content(self, content: str) -> List[str]:
        """Split content by delimiter, handling escape sequences"""
        parts = []
        current_part = ""
        i = 0
        
        while i < len(content):
            if content[i:i+len(self.delimiter)] == self.delimiter:
                # Check if this delimiter is escaped
                num_backslashes = 0
                j = i - 1
                while j >= 0 and content[j] == '\\':
                    num_backslashes += 1
                    j -= 1
                
                if num_backslashes % 2 == 0:
                    # Even number of backslashes (including 0) means delimiter is not escaped
                    parts.append(current_part)
                    current_part = ""
                    i += len(self.delimiter)
                else:
                    # Odd number of backslashes means delimiter is escaped
                    current_part += content[i]
                    i += 1
            else:
                current_part += content[i]
                i += 1
        
        parts.append(current_part)
        return parts