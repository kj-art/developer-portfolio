"""
Dynamic Formatting Library - Fresh Implementation

Clean implementation with inline formatting support.
"""

import logging
from typing import Dict, Any, Callable, Optional, Union, List
from .formatters import TOKEN_FORMATTERS


class DynamicFormattingError(Exception):
    pass


class RequiredFieldError(DynamicFormattingError):
    pass


class FunctionNotFoundError(DynamicFormattingError):
    pass


class FormattedSpan:
    def __init__(self, text: str, token_type: str = None, token_value: str = None):
        self.text = text
        self.token_type = token_type
        self.token_value = token_value
        self.parsed_token = None
        
        if token_type and token_value and token_type in TOKEN_FORMATTERS:
            formatter = TOKEN_FORMATTERS[token_type]
            self.parsed_token = formatter.parse_token(token_value)


class FormatSection:
    def __init__(self, field_name: str, is_required: bool = False, 
                 prefix: Union[str, List[FormattedSpan]] = "", 
                 suffix: Union[str, List[FormattedSpan]] = "", 
                 field_formatting: Optional[FormattedSpan] = None,
                 function_name: Optional[str] = None,
                 prefix_function: Optional[str] = None,
                 suffix_function: Optional[str] = None,
                 whole_string_formatting: Optional[FormattedSpan] = None):
        self.field_name = field_name
        self.is_required = is_required
        self.prefix = prefix
        self.suffix = suffix
        self.field_formatting = field_formatting
        self.function_name = function_name
        self.prefix_function = prefix_function
        self.suffix_function = suffix_function
        self.whole_string_formatting = whole_string_formatting


class DynamicFormatter:
    def __init__(self, format_string: str, delimiter: str = ';', 
                 functions: Optional[Dict[str, Callable]] = None,
                 output_mode: str = 'console'):
        self.format_string = format_string
        self.delimiter = delimiter
        self.functions = functions or {}
        self.output_mode = output_mode
        self.sections = self._parse_format_string()
    
    def _parse_format_string(self) -> List[Union[str, FormatSection]]:
        sections = []
        i = 0
        current_literal = ""
        
        while i < len(self.format_string):
            char = self.format_string[i]
            
            if char == '{' and i + 1 < len(self.format_string) and self.format_string[i + 1] == '{':
                if current_literal:
                    sections.append(current_literal)
                    current_literal = ""
                
                i += 2  # Skip {{
                template_content = ""
                while i < len(self.format_string):
                    if (i + 1 < len(self.format_string) and 
                        self.format_string[i] == '}' and self.format_string[i + 1] == '}'):
                        break
                    template_content += self.format_string[i]
                    i += 1
                
                if i + 1 < len(self.format_string):
                    i += 2  # Skip }}
                
                section = self._parse_template_content(template_content)
                sections.append(section)
            else:
                current_literal += char
                i += 1
        
        if current_literal:
            sections.append(current_literal)
        
        return sections
    
    def _parse_template_content(self, content: str) -> FormatSection:
        # Handle required
        is_required = False
        if content.startswith('!'):
            is_required = True
            content = content[1:]
        
        # Extract tokens modularly
        function_name = None
        color_token = None
        
        while True:
            found_token = False
            
            # Look for function
            if content.startswith('$') and ';' in content:
                end_pos = content.find(';')
                function_name = content[1:end_pos]
                content = content[end_pos + 1:]
                found_token = True
                continue
            
            # Look for color token
            if content.startswith('#') and ';' in content:
                end_pos = content.find(';')
                color_value = content[1:end_pos]
                color_token = FormattedSpan("", '#', color_value)
                content = content[end_pos + 1:]
                found_token = True
                continue
            
            if not found_token:
                break
        
        # Parse remaining content
        parts = self._split_content(content)
        
        if len(parts) == 1:
            field_name, field_formatting = self._parse_field_with_formatting(parts[0])
            return FormatSection(
                field_name=field_name, 
                is_required=is_required,
                field_formatting=field_formatting,
                function_name=function_name,
                whole_string_formatting=color_token
            )
        elif len(parts) == 2:
            prefix = self._parse_formatted_text(parts[0])
            field_name, field_formatting = self._parse_field_with_formatting(parts[1])
            
            return FormatSection(
                field_name=field_name, 
                is_required=is_required,
                prefix=prefix,
                field_formatting=field_formatting,
                function_name=function_name,
                whole_string_formatting=color_token
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
                field_formatting=field_formatting,
                function_name=function_name,
                prefix_function=prefix_func, 
                suffix_function=suffix_func,
                whole_string_formatting=color_token
            )
        else:
            raise DynamicFormattingError(f"Invalid syntax: got {len(parts)} parts")
    
    def _parse_field_with_formatting(self, field_part: str) -> tuple[str, Optional[FormattedSpan]]:
        """Parse field that might have formatting at the start"""
        if field_part.startswith('{') and '}' in field_part:
            end_brace = field_part.find('}')
            token_content = field_part[1:end_brace]
            field_name = field_part[end_brace + 1:]
            
            if token_content and token_content[0] in TOKEN_FORMATTERS:
                token_type = token_content[0]
                token_value = token_content[1:]
                span = FormattedSpan("", token_type, token_value)
                return field_name, span
        
        return field_part, None
    
    def _parse_formatted_text(self, text: str) -> Union[str, List[FormattedSpan]]:
        """Parse text with inline formatting tokens"""
        if '{' not in text:
            return text
        
        spans = []
        current_text = ""
        i = 0
        
        while i < len(text):
            if text[i] == '{' and i + 1 < len(text):
                end_brace = text.find('}', i)
                if end_brace != -1:
                    if current_text:
                        spans.append(FormattedSpan(current_text))
                        current_text = ""
                    
                    token_content = text[i+1:end_brace]
                    if token_content and token_content[0] in TOKEN_FORMATTERS:
                        token_type = token_content[0]
                        token_value = token_content[1:]
                        
                        section_start = end_brace + 1
                        section_end = text.find('{', section_start)
                        if section_end == -1:
                            section_end = len(text)
                        
                        formatted_text = text[section_start:section_end]
                        spans.append(FormattedSpan(formatted_text, token_type, token_value))
                        
                        i = section_end
                    else:
                        current_text += text[i]
                        i += 1
                else:
                    current_text += text[i]
                    i += 1
            else:
                current_text += text[i]
                i += 1
        
        if current_text:
            spans.append(FormattedSpan(current_text))
        
        if len(spans) > 1 or (len(spans) == 1 and spans[0].token_type):
            return spans
        else:
            return text
    
    def _split_content(self, content: str) -> List[str]:
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
    
    def format(self, **data) -> str:
        result = ""
        
        for section in self.sections:
            if isinstance(section, str):
                result += section
            else:
                result += self._render_section(section, data)
        
        return result
    
    def _render_section(self, section: FormatSection, data: Dict[str, Any]) -> str:
        field_value = data.get(section.field_name)
        
        if field_value is None:
            if section.is_required:
                raise RequiredFieldError("Required field missing: " + section.field_name)
            return ""
        
        # Check conditional function
        if section.function_name:
            func = self.functions.get(section.function_name)
            if not func:
                raise FunctionNotFoundError("Function not found: " + section.function_name)
            
            if not func(field_value):
                return ""
        
        result_parts = []
        
        # Add prefix
        if section.prefix_function:
            func = self.functions.get(section.prefix_function)
            if not func:
                raise FunctionNotFoundError("Prefix function not found: " + section.prefix_function)
            result_parts.append(func(field_value))
        elif section.prefix:
            prefix_text = self._render_formatted_spans(section.prefix, section.whole_string_formatting)
            result_parts.append(prefix_text)
        
        # Add field value
        field_text = str(field_value)
        if section.field_formatting:
            field_text = self._apply_span_formatting(section.field_formatting, field_text)
        result_parts.append(field_text)
        
        # Add suffix
        if section.suffix_function:
            func = self.functions.get(section.suffix_function)
            if not func:
                raise FunctionNotFoundError("Suffix function not found: " + section.suffix_function)
            result_parts.append(func(field_value))
        elif section.suffix:
            suffix_text = self._render_formatted_spans(section.suffix, section.whole_string_formatting)
            result_parts.append(suffix_text)
        
        result = "".join(result_parts)
        
        # Apply whole-string formatting
        if section.whole_string_formatting:
            result = self._apply_span_formatting(section.whole_string_formatting, result)
        
        return result
    
    def _render_formatted_spans(self, spans: Union[str, List[FormattedSpan]], default_formatting: Optional[FormattedSpan] = None) -> str:
        """Render formatted spans with proper reset behavior"""
        if isinstance(spans, str):
            return spans
        
        result = ""
        for span in spans:
            if span.token_type and span.parsed_token:
                formatted_text = self._apply_span_formatting(span, span.text)
                result += formatted_text
            else:
                if default_formatting and default_formatting.token_type:
                    result += self._apply_span_formatting(default_formatting, span.text)
                else:
                    result += span.text
        
        return result
    
    def _apply_span_formatting(self, span: FormattedSpan, text: str) -> str:
        """Apply formatting from a span to text"""
        if not span.token_type or not span.parsed_token:
            return text
        
        formatter = TOKEN_FORMATTERS.get(span.token_type)
        if formatter:
            return formatter.apply_formatting(text, span.parsed_token, self.output_mode)
        
        return text


class DynamicLoggingFormatter(logging.Formatter):
    def __init__(self, format_string: str, delimiter: str = ';', 
                 functions: Optional[Dict[str, Callable]] = None,
                 output_mode: str = 'console'):
        super().__init__()
        self.formatter = DynamicFormatter(format_string, delimiter, functions, output_mode)
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'message': record.getMessage(),
            'levelname': record.levelname,
            'name': record.name,
            'funcName': record.funcName,
            'lineno': record.lineno,
            'asctime': self.formatTime(record),
        }
        
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_'):
                log_data[key] = value
        
        try:
            return self.formatter.format(**log_data)
        except DynamicFormattingError as e:
            return "[ERROR: " + str(e) + "] " + record.getMessage()


if __name__ == "__main__":
    print("=== Complete Dynamic Formatting Tests ===")
    
    # Basic functionality
    formatter = DynamicFormatter("{{#blue;Processing ;file_count; files}}")
    result = formatter.format(file_count=5)
    print(f"Basic: {result}")
    
    # Test modular tokens
    def has_items(count):
        return count > 0
    
    formatter = DynamicFormatter(
        "{{$has_items;#green;Found ;item_count; items}}",
        functions={'has_items': has_items}
    )
    print(f"Function first: {formatter.format(item_count=3)}")
    
    # Test inline colors in prefix
    formatter = DynamicFormatter("{{#blue;Status: O{#green}K {#red}errors ;error_count}}")
    result = formatter.format(error_count=5)
    print(f"Inline prefix: {result}")
    
    # Test field with formatting
    formatter = DynamicFormatter("{{Processing {#blue}file_count files}}")
    result = formatter.format(file_count=10)
    print(f"Field formatting: {result}")
    
    print("All tests completed!")