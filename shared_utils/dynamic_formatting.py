"""
Dynamic Formatting Library

A string formatting system that supports conditional sections with graceful handling of missing data.

Syntax:
    {{field}}                    - Simple substitution
    {{prefix;field;suffix}}      - Optional section with prefix/suffix
    {{!prefix;field;suffix}}     - Required section (error if missing)
    {{$func;prefix;field;suffix}} - Conditional section based on function result
    {{$prefix_func;field;suffix}} - Dynamic prefix based on function result
    {{prefix;field;$suffix_func}} - Dynamic suffix based on function result

Features:
    - Graceful handling of missing data
    - Configurable delimiter (default: semicolon) with escaping support
    - Custom function support for conditional rendering
    - Integration with Python logging
"""

import logging
from typing import Dict, Any, Callable, Optional, Union, List


class DynamicFormattingError(Exception):
    pass


class RequiredFieldError(DynamicFormattingError):
    pass


class FunctionNotFoundError(DynamicFormattingError):
    pass


class Token:
    def __init__(self, type_: str, value: str, position: int):
        self.type = type_
        self.value = value
        self.position = position


class FormatSection:
    def __init__(self, field_name: str, is_required: bool = False, 
                 prefix: str = "", suffix: str = "", 
                 function_name: Optional[str] = None,
                 prefix_function: Optional[str] = None,
                 suffix_function: Optional[str] = None):
        self.field_name = field_name
        self.is_required = is_required
        self.prefix = prefix
        self.suffix = suffix
        self.function_name = function_name
        self.prefix_function = prefix_function
        self.suffix_function = suffix_function


class DynamicFormatter:
    def __init__(self, format_string: str, delimiter: str = ';', functions: Optional[Dict[str, Callable]] = None):
        self.format_string = format_string
        self.delimiter = delimiter
        self.functions = functions or {}
        self.sections = self._parse_format_string()
    
    def _parse_format_string(self) -> List[Union[str, FormatSection]]:
        sections = []
        i = 0
        current_literal = ""
        
        while i < len(self.format_string):
            char = self.format_string[i]
            
            if char == '{' and i + 1 < len(self.format_string) and self.format_string[i + 1] == '{':
                # Found template start
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
                
                # Parse template content
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
        
        # Split by delimiter
        parts = self._split_content(content)
        
        # Check if it's a conditional function
        if content.startswith('$') and (len(parts) == 2 or len(parts) == 4):
            return self._parse_conditional_function(parts)
        
        if len(parts) == 1:
            # Simple field
            return FormatSection(field_name=parts[0], is_required=is_required)
        elif len(parts) == 3:
            # prefix;field;suffix
            prefix, field_name, suffix = parts
            
            prefix_func = None
            suffix_func = None
            
            if prefix.startswith('$'):
                prefix_func = prefix[1:]
                prefix = ""
            
            if suffix.startswith('$'):
                suffix_func = suffix[1:]
                suffix = ""
            
            return FormatSection(
                field_name=field_name, 
                is_required=is_required,
                prefix=prefix, 
                suffix=suffix,
                prefix_function=prefix_func, 
                suffix_function=suffix_func
            )
        else:
            raise DynamicFormattingError("Invalid template syntax")
    
    def _parse_conditional_function(self, parts: List[str]) -> FormatSection:
        function_name = parts[0][1:]  # Remove $
        
        if len(parts) == 2:
            # $func;field
            return FormatSection(field_name=parts[1], function_name=function_name)
        else:
            # $func;prefix;field;suffix
            return FormatSection(
                field_name=parts[2], 
                function_name=function_name,
                prefix=parts[1], 
                suffix=parts[3]
            )
    
    def _split_content(self, content: str) -> List[str]:
        parts = []
        current = ""
        i = 0
        
        while i < len(content):
            char = content[i]
            
            if char == '\\' and i + 1 < len(content) and content[i + 1] == self.delimiter:
                # Escaped delimiter
                current += self.delimiter
                i += 2
            elif char == self.delimiter:
                # Split here
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
        
        # Get prefix
        prefix = section.prefix
        if section.prefix_function:
            func = self.functions.get(section.prefix_function)
            if not func:
                raise FunctionNotFoundError("Prefix function not found: " + section.prefix_function)
            prefix = func(field_value)
        
        # Get suffix
        suffix = section.suffix
        if section.suffix_function:
            func = self.functions.get(section.suffix_function)
            if not func:
                raise FunctionNotFoundError("Suffix function not found: " + section.suffix_function)
            suffix = func(field_value)
        
        return prefix + str(field_value) + suffix


class DynamicLoggingFormatter(logging.Formatter):
    def __init__(self, format_string: str, delimiter: str = ';', functions: Optional[Dict[str, Callable]] = None):
        super().__init__()
        self.formatter = DynamicFormatter(format_string, delimiter, functions)
    
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
    print("=== Dynamic Formatting Tests ===")
    
    # Basic test
    formatter = DynamicFormatter("Hello {{name}}")
    print(formatter.format(name="World"))     # "Hello World"
    print(formatter.format())                 # "Hello "
    
    # Prefix/suffix test - NEW SYNTAX
    formatter = DynamicFormatter("{{File size: ;file_size;MB }}{{(;file_count;files) }}processed")
    print(formatter.format(file_size=2.5, file_count=100))  # "File size: 2.5MB (100files) processed"
    print(formatter.format(file_size=2.5))                  # "File size: 2.5MB processed"
    print(formatter.format(file_count=100))                 # "(100files) processed"
    print(formatter.format())                               # "processed"
    
    # Required sections
    formatter = DynamicFormatter("Processing {{!filename}}")
    print(formatter.format(filename="data.csv"))  # "Processing data.csv"
    try:
        print(formatter.format())  # Raises RequiredFieldError
    except RequiredFieldError as e:
        print("Error: " + str(e))
    
    # Function-based conditions - NEW SYNTAX
    def is_large_file(size):
        return size > 1.0
    
    def has_many_files(count):
        return count > 50
    
    formatter = DynamicFormatter(
        "{{$is_large_file;Large file: ;file_size;MB }}{{$has_many_files;Batch of ;file_count; files}}",
        functions={'is_large_file': is_large_file, 'has_many_files': has_many_files}
    )
    
    print(formatter.format(file_size=2.5, file_count=100))  # "Large file: 2.5MB Batch of 100 files"
    print(formatter.format(file_size=0.5, file_count=100))  # "Batch of 100 files"
    print(formatter.format(file_size=2.5, file_count=10))   # "Large file: 2.5MB"
    print(formatter.format(file_size=0.5, file_count=10))   # ""
    
    # Function prefix/suffix
    def size_prefix(size):
        return "Big: " if size > 1.0 else "Small: "
    
    def size_suffix(size):
        return "MB (backup worthy)" if size > 5.0 else "MB"
    
    formatter = DynamicFormatter(
        "{{$size_prefix;file_size;$size_suffix}}", 
        functions={'size_prefix': size_prefix, 'size_suffix': size_suffix}
    )
    print(formatter.format(file_size=2.5))   # "Big: 2.5MB"
    print(formatter.format(file_size=0.5))   # "Small: 0.5MB"
    print(formatter.format(file_size=6.2))   # "Big: 6.2MB (backup worthy)"
    
    # Mixed static and function - NEW SYNTAX  
    formatter = DynamicFormatter(
        "{{File size: ;file_size;$size_suffix}}",
        functions={'size_suffix': size_suffix}
    )
    print(formatter.format(file_size=3.2))   # "File size: 3.2MB"
    print(formatter.format(file_size=7.8))   # "File size: 7.8MB (backup worthy)"
    
    print("All tests completed!")