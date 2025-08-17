"""
Template parsing logic for dynamic formatting system.

This module handles parsing of format strings into structured
format sections and spans.
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
        """Parse a format string into sections"""
        sections = []
        i = 0
        current_literal = ""
        
        while i < len(format_string):
            char = format_string[i]
            
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
            
            # Look for conditional function ($function_name)
            if content.startswith('$') and ';' in content:
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
        """Parse text with inline formatting tokens like 'prefix{@bold}text{@normal}suffix'"""
        if '{' not in text:
            return text
        
        spans = []
        current_span = FormattedSpan("")
        i = 0
        
        while i < len(text):
            if text[i] == '{':
                # Look for formatting tokens
                formatting_tokens = {}
                token_end = text.find('}', i)
                if token_end == -1:
                    current_span.text += text[i]
                    i += 1
                    continue
                
                token_content = text[i+1:token_end]
                
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
                                
                                # Store raw token value - will be parsed with field_value later
                                formatting_tokens[family_name].append(token_value)
                                
                                token_pos = value_end
                                found_token = True
                                break
                    
                    if not found_token:
                        token_pos += 1
                
                # Find the end of this formatted section
                section_start = token_end + 1
                section_end = text.find('{', section_start)
                if section_end == -1:
                    section_end = len(text)
                
                # Save current span if it has text
                if current_span.text:
                    spans.append(current_span)
                
                # Create formatted span
                formatted_text = text[section_start:section_end]
                spans.append(FormattedSpan(formatted_text, formatting_tokens))
                
                # Start new span
                current_span = FormattedSpan("")
                i = section_end
            else:
                current_span.text += text[i]
                i += 1
        
        # Add final span if it has content
        if current_span.text:
            spans.append(current_span)
        
        # Return simple string if no formatting
        if len(spans) == 1 and not spans[0].formatting_tokens:
            return spans[0].text
        
        return spans
    
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