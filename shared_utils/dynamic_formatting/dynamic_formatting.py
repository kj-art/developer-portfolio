"""
Dynamic Formatting Library - Main Module

Clean, working version with modular token parsing.
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
                 prefix: str = "", suffix: str = "", 
                 function_name: Optional[str] = None,
                 prefix_function: Optional[str] = None,
                 suffix_function: Optional[str] = None,
                 whole_string_formatting: Optional[FormattedSpan] = None):
        self.field_name = field_name
        self.is_required = is_required
        self.prefix = prefix
        self.suffix = suffix
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
                
                # Find template end
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
        
        # Keep extracting until no more tokens
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
            return FormatSection(
                field_name=parts[0], 
                is_required=is_required,
                function_name=function_name,
                whole_string_formatting=color_token
            )
        elif len(parts) == 2:
            # Handle 2 parts: treat as prefix;field
            return FormatSection(
                field_name=parts[1], 
                is_required=is_required,
                prefix=parts[0],
                function_name=function_name,
                whole_string_formatting=color_token
            )
        elif len(parts) == 3:
            prefix, field_name, suffix = parts
            
            prefix_func = None
            suffix_func = None
            
            # Check for function prefixes
            if prefix.startswith('$'):
                prefix_func = prefix[1:]
                prefix = ""
            
            # Check for function suffixes  
            if suffix.startswith('$'):
                suffix_func = suffix[1:]
                suffix = ""
            
            return FormatSection(
                field_name=field_name, 
                is_required=is_required,
                prefix=prefix, 
                suffix=suffix,
                function_name=function_name,
                prefix_function=prefix_func, 
                suffix_function=suffix_func,
                whole_string_formatting=color_token
            )
        else:
            raise DynamicFormattingError(f"Invalid syntax: got {len(parts)} parts")
    
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
        
        # Build result
        result_parts = []
        
        # Add prefix
        if section.prefix_function:
            func = self.functions.get(section.prefix_function)
            if not func:
                raise FunctionNotFoundError("Prefix function not found: " + section.prefix_function)
            result_parts.append(func(field_value))
        elif section.prefix:
            result_parts.append(str(section.prefix))
        
        # Add field value
        result_parts.append(str(field_value))
        
        # Add suffix
        if section.suffix_function:
            func = self.functions.get(section.suffix_function)
            if not func:
                raise FunctionNotFoundError("Suffix function not found: " + section.suffix_function)
            result_parts.append(func(field_value))
        elif section.suffix:
            result_parts.append(str(section.suffix))
        
        result = "".join(result_parts)
        
        # Apply formatting
        if section.whole_string_formatting:
            formatter = TOKEN_FORMATTERS.get(section.whole_string_formatting.token_type)
            if formatter:
                result = formatter.apply_formatting(
                    result, 
                    section.whole_string_formatting.parsed_token, 
                    self.output_mode
                )
        
        return result


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
    print("=== Clean Modular Tests ===")
    
    # Basic functionality
    formatter = DynamicFormatter("{{#blue;Processing ;file_count; files}}")
    result = formatter.format(file_count=5)
    print(f"Basic: {result}")
    print(f"Raw: {repr(result)}")
    
    # Test both orders with debug
    def has_items(count):
        return count > 0
    
    # Function first (3 parts - debug this one)
    formatter = DynamicFormatter(
        "{{$has_items;#green;Found ;item_count; items}}",
        functions={'has_items': has_items}
    )
    print(f"Function first: {formatter.format(item_count=3)}")
    print(f"Function first raw: {repr(formatter.format(item_count=3))}")
    
    # Simple green test
    formatter = DynamicFormatter("{{#green;item_count}}")
    print(f"Simple green: {formatter.format(item_count=3)}")
    print(f"Simple green raw: {repr(formatter.format(item_count=3))}")
    
    # Color first (2 parts)
    formatter = DynamicFormatter(
        "{{#red;$has_items;Error ;error_count}}",
        functions={'has_items': has_items}
    )
    print(f"Color first: {formatter.format(error_count=2)}")
    
    print("Tests completed!")