r"""
Dynamic Formatting Library

A string formatting system that supports conditional sections with graceful handling of missing data.

Syntax:
    {{field}}                    - Simple substitution
    {{field|prefix|suffix}}      - Optional section with prefix/suffix
    {{!field|prefix|suffix}}     - Required section (error if missing)
    {{$func|field|prefix|suffix}} - Conditional section based on function result
    {{field|$prefix_func|suffix}} - Dynamic prefix based on function result
    {{field|prefix|$suffix_func}} - Dynamic suffix based on function result

Features:
    - Graceful handling of missing data
    - Pipe escaping with backslash (\|)
    - Custom function support for conditional rendering
    - Integration with Python logging
"""

import re
import logging
from typing import Dict, Any, Callable, Optional, Union, List


class DynamicFormattingError(Exception):
    """Base exception for formatting errors"""
    pass


class RequiredFieldError(DynamicFormattingError):
    """Raised when a required field (!) is missing"""
    pass


class FunctionNotFoundError(DynamicFormattingError):
    """Raised when a referenced function doesn't exist"""
    pass


class Token:
    """Represents a parsed token from the template"""
    def __init__(self, type_: str, value: str, position: int):
        self.type = type_
        self.value = value
        self.position = position
    
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.position})"


class FormatTokenizer:
    """Tokenizes formatting strings into tokens"""
    
    def __init__(self, template: str):
        self.template = template
        self.pos = 0
        self.length = len(template)
    
    def current_char(self) -> Optional[str]:
        """Get current character or None if at end"""
        if self.pos >= self.length:
            return None
        return self.template[self.pos]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Peek at character at current position + offset"""
        pos = self.pos + offset
        if pos >= self.length:
            return None
        return self.template[pos]
    
    def advance(self) -> None:
        """Move to next character"""
        self.pos += 1
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire template"""
        tokens = []
        
        while self.pos < self.length:
            if self.current_char() == '{' and self.peek_char() == '{':
                # Found template section
                template_token = self.parse_template_section()
                tokens.append(template_token)
            else:
                # Found literal text
                literal_token = self.parse_literal_text()
                if literal_token.value:  # Only add non-empty literals
                    tokens.append(literal_token)
        
        return tokens
    
    def parse_template_section(self) -> Token:
        """Parse a {{...}} template section"""
        start_pos = self.pos
        
        # Skip opening {{
        self.advance()  # {
        self.advance()  # {
        
        # Parse the content between {{ and }} - preserve escape sequences for now
        content = ""
        while self.pos < self.length:
            char = self.current_char()
            
            if char == '\\':
                # Preserve escape sequences - don't process them yet
                content += char
                self.advance()
                next_char = self.current_char()
                if next_char is not None:
                    content += next_char
                    self.advance()
            elif char == '}' and self.peek_char() == '}':
                # Found closing }}
                break
            else:
                content += char
                self.advance()
        
        # Skip closing }}
        if self.current_char() == '}' and self.peek_char() == '}':
            self.advance()  # }
            self.advance()  # }
        else:
            raise DynamicFormattingError(f"Unclosed format section at position {start_pos}")
        
        return Token('TEMPLATE', content, start_pos)
    
    def parse_literal_text(self) -> Token:
        """Parse literal text until we hit {{ or end of string"""
        start_pos = self.pos
        content = ""
        
        while self.pos < self.length:
            char = self.current_char()
            
            if char == '{' and self.peek_char() == '{':
                break
            
            content += char
            self.advance()
        
        return Token('LITERAL', content, start_pos)


class FormatSection:
    """Represents a parsed format section"""
    
    def __init__(self, field_name: str, is_required: bool = False, 
                 prefix: str = "", suffix: str = "", 
                 function_name: Optional[str] = None,
                 prefix_function: Optional[str] = None,
                 suffix_function: Optional[str] = None):
        self.field_name = field_name
        self.is_required = is_required
        self.prefix = prefix
        self.suffix = suffix
        self.function_name = function_name  # For conditional functions ($func|field)
        self.prefix_function = prefix_function  # For prefix functions (field|$func|suffix)
        self.suffix_function = suffix_function  # For suffix functions (field|prefix|$func)
    
    def __repr__(self):
        return (f"FormatSection(field={self.field_name!r}, "
                f"required={self.is_required}, prefix={self.prefix!r}, "
                f"suffix={self.suffix!r}, function={self.function_name!r}, "
                f"prefix_func={self.prefix_function!r}, suffix_func={self.suffix_function!r})")


class DynamicFormatter:
    """Main formatting class that handles parsing and rendering"""
    
    def __init__(self, format_string: str, functions: Optional[Dict[str, Callable]] = None):
        self.format_string = format_string
        self.functions = functions or {}
        self.sections = self._parse_format_string()
    
    def _parse_format_string(self) -> List[Union[str, FormatSection]]:
        """Parse format string into a list of literal strings and FormatSection objects"""
        tokenizer = FormatTokenizer(self.format_string)
        tokens = tokenizer.tokenize()
        sections = []
        
        for token in tokens:
            if token.type == 'LITERAL':
                sections.append(token.value)
            elif token.type == 'TEMPLATE':
                section = self._parse_format_content(token.value, token.position)
                sections.append(section)
        
        return sections
    
    def _parse_format_content(self, content: str, position: int) -> FormatSection:
        """Parse the content inside {{...}} into a FormatSection"""
        
        # Handle function syntax: $func|field|prefix|suffix
        if content.startswith('$'):
            return self._parse_function_section(content[1:], position)
        
        # Handle required syntax: !field|prefix|suffix
        is_required = content.startswith('!')
        if is_required:
            content = content[1:]
        
        # Split by unescaped pipes
        parts = self._split_by_unescaped_pipes(content)
        
        if len(parts) == 1:
            # Simple substitution: {{field}}
            return FormatSection(field_name=parts[0], is_required=is_required)
        elif len(parts) == 3:
            # Full syntax: {{field|prefix|suffix}} with possible function prefixes
            field_name, prefix, suffix = parts
            
            # Check if prefix or suffix are functions
            prefix_func = None
            suffix_func = None
            
            if prefix.startswith('$'):
                prefix_func = prefix[1:]  # Remove $ and store function name
                prefix = ""  # No static prefix
            
            if suffix.startswith('$'):
                suffix_func = suffix[1:]  # Remove $ and store function name  
                suffix = ""  # No static suffix
            
            return FormatSection(field_name=field_name, is_required=is_required,
                                 prefix=prefix, suffix=suffix,
                                 prefix_function=prefix_func, suffix_function=suffix_func)
        else:
            error_msg = f"Invalid format syntax at position {position}. Expected field, field|prefix|suffix, or !field|prefix|suffix"
            raise DynamicFormattingError(error_msg)
    
    def _parse_function_section(self, content: str, position: int) -> FormatSection:
        """Parse function syntax: func|field|prefix|suffix"""
        parts = self._split_by_unescaped_pipes(content)
        
        if len(parts) < 2:
            error_msg = f"Invalid function syntax at position {position}. Expected $function|field or $function|field|prefix|suffix"
            raise DynamicFormattingError(error_msg)
        
        function_name = parts[0]
        field_name = parts[1]
        prefix = parts[2] if len(parts) > 2 else ""
        suffix = parts[3] if len(parts) > 3 else ""
        
        if len(parts) > 4:
            error_msg = f"Too many parts in function format at position {position}"
            raise DynamicFormattingError(error_msg)
        
        return FormatSection(field_name=field_name, function_name=function_name,
                             prefix=prefix, suffix=suffix)
    
    def _process_escapes(self, text: str) -> str:
        """Process escape sequences in text"""
        result = ""
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if char == '\\' and i + 1 < len(text):
                next_char = text[i + 1]
                if next_char in ['|', '}', '{', '\\']:
                    result += next_char  # Add the escaped character
                    i += 2  # Skip both \ and the escaped char
                else:
                    result += char  # Keep the backslash if not escaping special char
                    i += 1
            else:
                result += char
                i += 1
        
        return result

    def _split_by_unescaped_pipes(self, text: str) -> List[str]:
        """Split text by pipes, but ignore escaped pipes (\\|)"""
        parts = []
        current_part = ""
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if char == '\\' and i + 1 < len(text) and text[i + 1] == '|':
                # Escaped pipe - add the escape sequence to current part (process later)
                current_part += '\\|'
                i += 2  # Skip both \ and |
            elif char == '|':
                # Unescaped pipe - split here
                parts.append(current_part)
                current_part = ""
                i += 1
            else:
                current_part += char
                i += 1
        
        # Add the last part
        parts.append(current_part)
        
        # Now process escapes in each part
        parts = [self._process_escapes(part) for part in parts]
        
        return parts
    
    def format(self, **data) -> str:
        """Format the string with provided data"""
        result = ""
        
        for section in self.sections:
            if isinstance(section, str):
                # Literal text
                result += section
            elif isinstance(section, FormatSection):
                # Format section
                rendered = self._render_section(section, data)
                result += rendered
        
        return result
    
    def _render_section(self, section: FormatSection, data: Dict[str, Any]) -> str:
        """Render a single formatting section"""
        field_value = data.get(section.field_name)
        
        # Handle missing data
        if field_value is None:
            if section.is_required:
                raise RequiredFieldError(f"Required field '{section.field_name}' is missing")
            else:
                return ""  # Gracefully omit optional sections with missing data
        
        # Handle function-based conditions (conditional rendering)
        if section.function_name:
            if section.function_name not in self.functions:
                raise FunctionNotFoundError(f"Function '{section.function_name}' not found")
            
            func = self.functions[section.function_name]
            try:
                should_render = func(field_value)
            except Exception as e:
                raise DynamicFormattingError(
                    f"Error calling function '{section.function_name}': {e}"
                )
            
            if not should_render:
                return ""  # Function returned False, omit this section
        
        # Determine prefix (static or function-generated)
        prefix = section.prefix
        if section.prefix_function:
            if section.prefix_function not in self.functions:
                raise FunctionNotFoundError(f"Prefix function '{section.prefix_function}' not found")
            
            prefix_func = self.functions[section.prefix_function]
            try:
                prefix = prefix_func(field_value)
            except Exception as e:
                raise DynamicFormattingError(
                    f"Error calling prefix function '{section.prefix_function}': {e}"
                )
        
        # Determine suffix (static or function-generated)
        suffix = section.suffix
        if section.suffix_function:
            if section.suffix_function not in self.functions:
                raise FunctionNotFoundError(f"Suffix function '{section.suffix_function}' not found")
            
            suffix_func = self.functions[section.suffix_function]
            try:
                suffix = suffix_func(field_value)
            except Exception as e:
                raise DynamicFormattingError(
                    f"Error calling suffix function '{section.suffix_function}': {e}"
                )
        
        # Render the section
        return f"{prefix}{field_value}{suffix}"


class DynamicLoggingFormatter(logging.Formatter):
    """Logging formatter that uses DynamicFormatter"""
    
    def __init__(self, format_string: str, functions: Optional[Dict[str, Callable]] = None):
        super().__init__()
        self.formatter = DynamicFormatter(format_string, functions)
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record using the dynamic formatter"""
        
        # Convert log record to dict for formatter rendering
        log_data = {
            'message': record.getMessage(),
            'levelname': record.levelname,
            'name': record.name,
            'funcName': record.funcName,
            'lineno': record.lineno,
            'asctime': self.formatTime(record),
        }
        
        # Add any extra data from the log record
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Add any other attributes from the record
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_'):
                log_data[key] = value
        
        try:
            return self.formatter.format(**log_data)
        except DynamicFormattingError as e:
            # Fallback to basic formatting if template fails
            return f"[FORMATTING ERROR: {e}] {record.getMessage()}"


# Example usage and tests
if __name__ == "__main__":
    # Basic examples
    print("=== Basic Examples ===")
    
    # Simple substitution
    formatter = DynamicFormatter("Hello {{name}}")
    print(formatter.format(name="World"))  # "Hello World"
    print(formatter.format())  # "Hello " (missing data handled gracefully)
    
    # Optional sections with prefix/suffix
    formatter = DynamicFormatter("{{file_size|File size: |MB}}{{file_count| (|files)}} processed")
    print(formatter.format(file_size=2.5, file_count=100))  # "File size: 2.5MB (100files) processed"
    print(formatter.format(file_size=2.5))  # "File size: 2.5MB processed"
    print(formatter.format(file_count=100))  # " (100files) processed"
    print(formatter.format())  # " processed"
    
    # Required sections
    formatter = DynamicFormatter("Processing {{!filename}}")
    print(formatter.format(filename="data.csv"))  # "Processing data.csv"
    try:
        print(formatter.format())  # Raises RequiredFieldError
    except RequiredFieldError as e:
        print(f"Error: {e}")
    
    # Function-based conditions
    def is_large_file(size):
        return size > 1.0
    
    def has_many_files(count):
        return count > 50
    
    formatter = DynamicFormatter(
        "{{$is_large_file|file_size|Large file: |MB }}{{$has_many_files|file_count|Batch of | files}}",
        functions={'is_large_file': is_large_file, 'has_many_files': has_many_files}
    )
    
    print(formatter.format(file_size=2.5, file_count=100))  # "Large file: 2.5MB Batch of 100 files"
    print(formatter.format(file_size=0.5, file_count=100))  # "Batch of 100 files"
    print(formatter.format(file_size=2.5, file_count=10))   # "Large file: 2.5MB"
    print(formatter.format(file_size=0.5, file_count=10))   # ""
    
    # Function-based prefix/suffix
    def size_prefix(size):
        return "Tiny: " if size < 0.5 else "Small: " if size < 2.0 else "Large: "
    
    def size_suffix(size):
        return "MB (backup worthy)" if size > 5.0 else "MB"
    
    formatter = DynamicFormatter(
        "{{file_size|$size_prefix|$size_suffix}}",
        functions={'size_prefix': size_prefix, 'size_suffix': size_suffix}
    )
    
    print(formatter.format(file_size=0.3))   # "Tiny: 0.3MB"
    print(formatter.format(file_size=1.5))   # "Small: 1.5MB" 
    print(formatter.format(file_size=6.2))   # "Large: 6.2MB (backup worthy)"
    
    # Mixed static and function
    formatter = DynamicFormatter(
        "{{file_size|File size: |$size_suffix}}",
        functions={'size_suffix': size_suffix}
    )
    
    print(formatter.format(file_size=3.2))   # "File size: 3.2MB"
    print(formatter.format(file_size=7.8))   # "File size: 7.8MB (backup worthy)"
    
    # Pipe escaping
    formatter = DynamicFormatter("{{command|Running: |}} {{args|Args: |\\|separated\\|values}}")
    print(formatter.format(command="process", args="file1"))  # "Running: process Args: file1|separated|values"
    
    print("\n=== Logging Integration ===")
    
    # Logging integration
    import logging
    
    # Set up logging with conditional formatter
    logger = logging.getLogger('test')
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    log_formatter = DynamicLoggingFormatter(
        "{{asctime}} - {{levelname}}{{funcName| - |()}} - {{message}}{{file_count| (|files)}}{{error_code| [Error: |]}}"
    )
    handler.setFormatter(log_formatter)
    logger.addHandler(handler)
    
    # Test logging
    logger.info("Processing started")
    logger.info("Files processed", extra={'extra_data': {'file_count': 42}})
    logger.error("Processing failed", extra={'extra_data': {'error_code': 'E001', 'file_count': 15}})