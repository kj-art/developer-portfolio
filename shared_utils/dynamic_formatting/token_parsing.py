"""
Template parsing logic for dynamic formatting system.

This module handles parsing of format strings into structured format sections and spans.
The parser supports:
- Template sections with {{...}} syntax
- Inline formatting tokens (#color, @style, ?conditional)
- Comprehensive escape sequence handling (\{, \}, \;)
- Function fallback integration
- Family-based formatting state management

PARSING ARCHITECTURE:
    1. Top-level parsing splits format strings into literal text and template sections
    2. Template content parsing extracts functions, formatting tokens, and field references  
    3. Formatted text parsing handles inline formatting within text spans
    4. Escape sequence processing converts \{ → { throughout all levels

PERFORMANCE:
    - Single-pass parsing with O(n) time complexity
    - Efficient escape sequence handling
    - Minimal object creation for simple cases
"""

from typing import Dict, List, Union, Callable, Optional
from .span_structures import FormattedSpan, FormatSection
from .formatting_state import StackingError


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
            if content.startswith('?') and ';' in content:
                end_pos = content.find(';')
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
                        if char == ';':
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
                    if content.startswith(';'):
                        content = content[1:]
                    
                    found_token = True
                    break
            
            if not found_token:
                break
        
        # Parse remaining content (prefix;field;suffix pattern)
        parts = self._split_content(content)
        
        if len(parts) == 1:
            field_name, field_formatting = self._parse_field_with_formatting(parts[0])
            return FormatSection(
                field_name=field_name, 
                is_required=is_required,
                field_formatting_tokens=field_formatting,
                function_name=function_name,
                whole_section_formatting_tokens=whole_section_tokens
            )
        elif len(parts) == 2:
            prefix = self._parse_formatted_text(parts[0])
            field_name, field_formatting = self._parse_field_with_formatting(parts[1])
            
            return FormatSection(
                field_name=field_name, 
                is_required=is_required,
                prefix=prefix,
                field_formatting_tokens=field_formatting,
                function_name=function_name,
                whole_section_formatting_tokens=whole_section_tokens
            )
        elif len(parts) == 3:
            prefix_text, field_part, suffix_text = parts
            
            field_name, field_formatting = self._parse_field_with_formatting(field_part)
            
            prefix_func = None
            suffix_func = None
            processed_prefix = ""
            processed_suffix = ""
            
            if prefix_text.startswith('$'):
                prefix_func = prefix_text[1:]
            else:
                processed_prefix = self._parse_formatted_text(prefix_text)
            
            if suffix_text.startswith('$'):
                suffix_func = suffix_text[1:]
            else:
                processed_suffix = self._parse_formatted_text(suffix_text)
            
            return FormatSection(
                field_name=field_name, 
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
            raise ParseError(f"Invalid template syntax: expected 1-3 parts, got {len(parts)}")
    
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
                    
                    # Store raw token value - will be parsed with field_value later
                    formatting_tokens[family_name].append(token_value)
                    found_token = True
                    break
            
            if not found_token:
                break
        
        return field_part, formatting_tokens
    
    def _parse_formatted_text(self, text: str) -> Union[str, List[FormattedSpan]]:
        """Parse text with inline formatting tokens including conditionals, handling escape sequences"""
        if '{' not in text:
            return text
        
        spans = []
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # Handle escaped braces
            if char == '\\' and i + 1 < len(text) and text[i + 1] in '{}':
                # Add escaped brace to current span or create new unformatted span
                if not spans or spans[-1].formatting_tokens:
                    spans.append(FormattedSpan(text[i + 1]))  # Add the literal brace
                else:
                    spans[-1].text += text[i + 1]  # Add to existing unformatted span
                i += 2  # Skip both backslash and brace
                continue
            
            if char == '{':
                # Look for formatting tokens or conditionals
                token_end = text.find('}', i)
                if token_end == -1:
                    # No closing brace, treat as literal
                    if not spans or spans[-1].formatting_tokens:
                        spans.append(FormattedSpan(text[i:]))
                    else:
                        spans[-1].text += text[i:]
                    break
                
                token_content = text[i+1:token_end]
                
                # Check if this is a conditional token
                if token_content.startswith('?'):
                    # This is an inline conditional: {?function}
                    function_name = token_content[1:]  # Remove the '?'
                    
                    # Find the text that this conditional controls
                    # Everything from after the } until the next unescaped { or end of string
                    controlled_start = token_end + 1
                    controlled_end = self._find_next_unescaped_brace(text, controlled_start)
                    
                    controlled_text = text[controlled_start:controlled_end]
                    
                    # Process escape sequences in the controlled text
                    processed_controlled_text = self._process_escape_sequences(controlled_text)
                    
                    # Create a span for the controlled text with conditional formatting
                    if processed_controlled_text:
                        conditional_tokens = {'conditional': [function_name]}
                        spans.append(FormattedSpan(processed_controlled_text, conditional_tokens))
                    
                    # Move past the controlled text
                    i = controlled_end
                    continue
                
                else:
                    # Regular formatting tokens like #red, @bold
                    formatting_tokens = {}
                    
                    # Parse multiple consecutive tokens within {} like {@italic@bold}
                    token_pos = 0
                    while token_pos < len(token_content):
                        found_token = False
                        for token_char, formatter in self.token_formatters.items():
                            if token_content[token_pos:token_pos+1] == token_char:
                                # Find the end of this specific token
                                value_start = token_pos + 1
                                value_end = value_start
                                
                                # Read until we hit another token char or end
                                while value_end < len(token_content):
                                    if token_content[value_end] in self.token_formatters:
                                        break
                                    value_end += 1
                                
                                token_value = token_content[value_start:value_end]
                                if token_value:  # Only if we found a value
                                    family_name = formatter.get_family_name()
                                    if family_name not in formatting_tokens:
                                        formatting_tokens[family_name] = []
                                    formatting_tokens[family_name].append(token_value)
                                    
                                    token_pos = value_end
                                    found_token = True
                                    break
                        
                        if not found_token:
                            token_pos += 1
                    
                    # Find the text that this formatting controls
                    section_start = token_end + 1
                    section_end = self._find_next_unescaped_brace(text, section_start)
                    
                    formatted_text = text[section_start:section_end]
                    
                    # Process escape sequences in the formatted text
                    processed_formatted_text = self._process_escape_sequences(formatted_text)
                    
                    if processed_formatted_text or formatting_tokens:
                        spans.append(FormattedSpan(processed_formatted_text, formatting_tokens))
                    
                    # Move past the formatted text
                    i = section_end
                    continue
            else:
                # Regular character - add to current span or create new span
                if not spans or spans[-1].formatting_tokens:
                    # Need a new unformatted span
                    spans.append(FormattedSpan(text[i]))
                else:
                    # Add to existing unformatted span
                    spans[-1].text += text[i]
                i += 1
        
        # Return simple string if no formatting
        if len(spans) == 1 and not spans[0].formatting_tokens:
            return spans[0].text
        
        return spans
    
    def _find_next_unescaped_brace(self, text: str, start_pos: int) -> int:
        """Find the next unescaped { character starting from start_pos"""
        i = start_pos
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text) and text[i + 1] in '{}':
                # Skip escaped brace
                i += 2
                continue
            elif text[i] == '{':
                return i
            else:
                i += 1
        
        return len(text)  # No more braces found
    
    def _process_escape_sequences(self, text: str) -> str:
        """Process escape sequences in text, converting \\{ to { and \\} to }"""
        result = ""
        i = 0
        
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text) and text[i + 1] in '{}':
                # Convert escaped brace to literal brace
                result += text[i + 1]
                i += 2
            else:
                result += text[i]
                i += 1
        
        return result
    
    def _split_content(self, content: str) -> List[str]:
        """Split content by delimiter, handling escaped delimiters"""
        parts = []
        current = ""
        i = 0
        
        while i < len(content):
            char = content[i]
            
            if char == '\\' and i + 1 < len(content) and content[i + 1] == self.delimiter:
                current += self.delimiter
                i += 2
            elif char == self.delimiter:
                parts.append(current)
                current = ""
                i += 1
            else:
                current += char
                i += 1
        
        parts.append(current)
        return parts