"""
Dynamic formatting system with graceful missing data handling and positional arguments support.

CORE RESPONSIBILITIES:
    - Template compilation and caching
    - Function registry management  
    - Section rendering with conditional logic
    - **Graceful missing data handling** - sections return empty strings for missing fields
    - State management across formatting families
    - Error handling and graceful degradation
    - Output mode switching (console vs file)
    - **Positional arguments support** - convert positional args to synthetic kwargs

RENDERING PIPELINE:
    1. Parse template into sections during initialization
    2. For each section during formatting:
       - **Check if required field exists in data** - return "" if missing (core feature)
       - Check conditional functions (section-level show/hide)
       - Build base formatting state from section tokens
       - Render prefix, field, and suffix with proper state isolation
       - Apply resets and cleanup formatting codes
    
PERFORMANCE OPTIMIZATIONS:
    - Simple sections use efficient string concatenation
    - Complex sections use span-based rendering with minimal resets
    - Lazy ANSI code application based on output mode
    - Efficient state copying for span isolation

GRACEFUL MISSING DATA EXAMPLES:
    formatter = DynamicFormatter("{{Error: ;message}} {{Count: ;count}}")
    
    # Missing message field - only count section appears
    result = formatter.format(count=42)  # "Count: 42"
    
    # Missing count field - only message section appears
    result = formatter.format(message="Failed")  # "Error: Failed"
    
    # All missing - empty result
    result = formatter.format()  # ""

POSITIONAL ARGUMENTS EXAMPLES:
    formatter = DynamicFormatter("{{Error: ;}} {{Count: ;}}")
    
    # All arguments present
    result = formatter.format("Failed", 42)  # "Error: Failed Count: 42"
    
    # Missing arguments - later sections disappear
    result = formatter.format("Failed")  # "Error: Failed"

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
"""

import logging
from typing import Dict, Any, Callable, Optional, Union, List

from .formatters import TOKEN_FORMATTERS, FormatterError, FunctionExecutionError
from .token_parsing import TemplateParser, DynamicFormattingError, ParseError
from .span_structures import FormattedSpan, FormatSection
from .formatting_state import FormattingState


class RequiredFieldError(DynamicFormattingError):
    """Raised when a required field is missing"""
    pass


class FunctionNotFoundError(DynamicFormattingError):
    """Raised when a conditional function is not found"""
    pass


class DynamicFormatter:
    """
    Main dynamic formatter with graceful missing data handling and function fallback
    
    Core Feature: Template sections automatically disappear when their required data
    isn't provided, eliminating the need for manual null checking and conditional
    string building throughout your codebase.
    
    New Feature: Positional arguments support using empty field names in templates.
    """
    
    def __init__(self, template: str, output_mode: str = 'console', 
                 functions: Optional[Dict[str, Callable]] = None,
                 delimiter: str = ';'):
        """
        Initialize the dynamic formatter
        
        Args:
            template: Format template string with {{...}} sections
            output_mode: 'console' for ANSI colors, 'file' for plain text
            functions: Optional dictionary of functions for conditional and dynamic formatting
            delimiter: Delimiter for separating template parts (default: ';')
        """
        self.template = template
        self.output_mode = output_mode
        self.functions = functions or {}
        self.delimiter = delimiter
        
        # Parse the template
        self.parser = TemplateParser(delimiter=delimiter, token_formatters=TOKEN_FORMATTERS)
        try:
            self.sections = self.parser.parse_format_string(template)
        except ParseError as e:
            raise DynamicFormattingError(f"Template parsing failed: {e}")
        
        # Count positional field sections for validation
        self.positional_field_count = self.parser.positional_field_count
    
    def format(self, *args, **kwargs) -> str:
        """
        Format the template with provided data, supporting both positional and keyword arguments
        
        Core Feature: Missing fields cause their sections to disappear entirely,
        eliminating manual null checking and conditional string building.
        
        Positional Arguments:
            Use empty field names in template: {{}} {{prefix;;suffix}}
            Arguments are matched by position to empty field sections
            
        Keyword Arguments:  
            Use named field names in template: {{message}} {{count}}
            Arguments are matched by field name
        
        Examples:
            # Keyword arguments (original behavior)
            formatter = DynamicFormatter("{{Error: ;message}} {{Count: ;count}}")
            result = formatter.format(message="Failed", count=42)
            # Returns: "Error: Failed Count: 42"
            
            # Positional arguments (new behavior)
            formatter = DynamicFormatter("{{Error: ;}} {{Count: ;}}")
            result = formatter.format("Failed", 42)
            # Returns: "Error: Failed Count: 42"
            
            # Missing fields cause sections to disappear automatically
            result = formatter.format("Failed")  # Only first argument
            # Returns: "Error: Failed"
        """
        # Argument validation
        if args and kwargs:
            raise DynamicFormattingError("Cannot mix positional and keyword arguments")
        
        # Handle positional arguments
        if args:
            # Empty template with no field sections - silently ignore arguments and return empty string
            if self.positional_field_count == 0:
                return ""
            
            # Validate we don't have too many positional arguments
            if len(args) > self.positional_field_count:
                raise DynamicFormattingError(
                    f"Too many positional arguments: expected {self.positional_field_count}, got {len(args)}"
                )
            
            # Convert positional args to synthetic field mapping
            data = {}
            for i, arg in enumerate(args):
                synthetic_field = f"__pos_{i}__"
                data[synthetic_field] = arg
                
            # For mixed templates (with named fields), also map to original field names
            # This allows templates like {{my_field}} to work with both positional and keyword args
            field_index = 0
            for section in self.sections:
                if isinstance(section, FormatSection):
                    if field_index < len(args):
                        # If this section has a non-synthetic field name, also map the positional arg to it
                        if not section.field_name.startswith('__pos_'):
                            data[section.field_name] = args[field_index]
                        field_index += 1
        else:
            data = kwargs
        
        result = ""
        
        try:
            for section in self.sections:
                if isinstance(section, str):
                    result += section
                else:
                    result += self._render_section(section, data)
        except (FormatterError, FunctionExecutionError) as e:
            # Make error messages user-friendly for positional arguments
            error_msg = self._make_error_user_friendly(str(e))
            raise DynamicFormattingError(f"Formatting failed: {error_msg}")
        
        return result
    
    def _render_section(self, section: FormatSection, data: Dict[str, Any]) -> str:
        """
        Render a complete format section
        
        Core Feature Implementation: Returns empty string when the required field
        is missing from the data dictionary, causing the entire section to disappear.
        """
        field_value = data.get(section.field_name)
        
        # Core feature: graceful missing data handling
        if field_value is None:
            if section.is_required:
                # Convert synthetic field names to user-friendly position descriptions for error messages
                friendly_field = self._make_error_user_friendly(section.field_name)
                raise RequiredFieldError(f"Required field '{friendly_field}' is missing")
            else:
                # Missing data - section disappears (core feature)
                return ""
        
        # Check section-level conditional function
        if section.function_name:
            if section.function_name not in self.functions:
                raise FunctionNotFoundError(f"Conditional function '{section.function_name}' not found")
            
            try:
                if not self.functions[section.function_name](field_value):
                    return ""  # Function returned False - hide this section
            except Exception as e:
                raise FunctionExecutionError(f"Error executing function '{section.function_name}': {e}")
        
        # Section will be rendered - build formatting state and render
        return self._render_section_with_state(section, field_value, data)
    
    def _render_section_with_state(self, section: FormatSection, field_value: Any, data: Dict[str, Any]) -> str:
        """Render section with proper formatting state management"""
        # Check if this is a simple section (no complex formatting)
        has_complex_formatting = (
            section.whole_section_formatting_tokens or
            section.field_formatting_tokens or
            (section.prefix and any(span.formatting_tokens for span in section.prefix)) or
            (section.suffix and any(span.formatting_tokens for span in section.suffix))
        )
        
        if not has_complex_formatting:
            # Simple section - use efficient string concatenation
            result = ""
            if section.prefix:
                result += "".join(span.text for span in section.prefix)
            if section.prefix_function:
                result += self._execute_function(section.prefix_function, field_value)
            result += str(field_value)
            if section.suffix:
                result += "".join(span.text for span in section.suffix)
            if section.suffix_function:
                result += self._execute_function(section.suffix_function, field_value)
            return result
        else:
            # Complex section - use span-based rendering with state management
            return self._render_complex_section(section, field_value, data)
    
    def _render_complex_section(self, section: FormatSection, field_value: Any, data: Dict[str, Any]) -> str:
        """Render complex section with full formatting state management"""
        # Build base formatting state from section tokens
        formatting_state = FormattingState()
        
        # Apply whole-section formatting tokens
        for family_name, tokens in section.whole_section_formatting_tokens.items():
            formatter = self._get_formatter_by_family(family_name)
            for token in tokens:
                try:
                    parsed_token = formatter.parse_token(token, field_value)
                    formatting_state.add_tokens(family_name, [parsed_token])
                except FormatterError:
                    # Function fallback - try executing token as function
                    if token in self.functions:
                        try:
                            function_result = self.functions[token](field_value)
                            parsed_token = formatter.parse_token(str(function_result), field_value)
                            formatting_state.add_tokens(family_name, [parsed_token])
                        except Exception as e:
                            raise FunctionExecutionError(f"Error executing function '{token}': {e}")
                    else:
                        raise FormatterError(f"Unknown token '{token}' and no matching function found")
        
        spans = []
        
        # Render prefix spans
        if section.prefix:
            for span in section.prefix:
                spans.append(self._render_span(span, formatting_state.copy(), field_value))
        
        # Render prefix function
        if section.prefix_function:
            prefix_text = self._execute_function(section.prefix_function, field_value)
            spans.append(self._apply_formatting(prefix_text, formatting_state))
        
        # Render field value with field-specific formatting
        field_state = formatting_state.copy()
        for family_name, tokens in section.field_formatting_tokens.items():
            formatter = self._get_formatter_by_family(family_name)
            for token in tokens:
                try:
                    parsed_token = formatter.parse_token(token, field_value)
                    field_state.add_tokens(family_name, [parsed_token])
                except FormatterError:
                    # Function fallback
                    if token in self.functions:
                        try:
                            function_result = self.functions[token](field_value)
                            parsed_token = formatter.parse_token(str(function_result), field_value)
                            field_state.add_tokens(family_name, [parsed_token])
                        except Exception as e:
                            raise FunctionExecutionError(f"Error executing function '{token}': {e}")
                    else:
                        raise FormatterError(f"Unknown token '{token}' and no matching function found")
        
        field_text = self._apply_formatting(str(field_value), field_state)
        spans.append(field_text)
        
        # Render suffix spans
        if section.suffix:
            for span in section.suffix:
                spans.append(self._render_span(span, formatting_state.copy(), field_value))
        
        # Render suffix function
        if section.suffix_function:
            suffix_text = self._execute_function(section.suffix_function, field_value)
            spans.append(self._apply_formatting(suffix_text, formatting_state))
        
        return "".join(spans)
    
    def _render_span(self, span: FormattedSpan, base_state: FormattingState, field_value: Any = None) -> str:
        """Render a formatted text span with state management"""
        if not span.formatting_tokens:
            return self._apply_formatting(span.text, base_state)
        
        # Apply span-specific formatting tokens
        span_state = base_state.copy()
        for family_name, tokens in span.formatting_tokens.items():
            formatter = self._get_formatter_by_family(family_name)
            for token in tokens:
                try:
                    # For span-level functions, we need to call them for EACH character/span
                    # not just once for the field value
                    parsed_token = formatter.parse_token(token, span.text)
                    span_state.add_tokens(family_name, [parsed_token])
                except FormatterError:
                    # Function fallback - call function with span text, not field value
                    if token in self.functions:
                        try:
                            # Pass the span text to the function, not the field value
                            function_result = self.functions[token](span.text) if span.text else self.functions[token]()
                            parsed_token = formatter.parse_token(str(function_result), span.text)
                            span_state.add_tokens(family_name, [parsed_token])
                        except Exception as e:
                            raise FunctionExecutionError(f"Error executing function '{token}': {e}")
                    else:
                        raise FormatterError(f"Unknown token '{token}' and no matching function found")
        
        return self._apply_formatting(span.text, span_state)
    
    def _execute_function(self, function_name: str, field_value: Any) -> str:
        """Execute a function and return its string result"""
        if function_name not in self.functions:
            raise FunctionNotFoundError(f"Function '{function_name}' not found")
        
        try:
            result = self.functions[function_name](field_value)
            return str(result)
        except Exception as e:
            raise FunctionExecutionError(f"Error executing function '{function_name}': {e}")
    
    def _apply_formatting(self, text: str, formatting_state: FormattingState) -> str:
        """Apply formatting to text with automatic reset handling"""
        if not text:
            return text
        
        if formatting_state.has_active_formatting():
            format_codes = self._get_formatting_codes(formatting_state)
            if format_codes and self.output_mode == 'console':
                return format_codes + text + '\033[0m'
            else:
                return text
        else:
            return text
    
    def _apply_formatting_no_reset(self, text: str, formatting_state: FormattingState) -> str:
        """Apply formatting to text without adding reset"""
        if not text:
            return text
        
        if formatting_state.has_active_formatting():
            format_codes = self._get_formatting_codes(formatting_state)
            return format_codes + text
        else:
            return text
    
    def _get_formatting_codes(self, formatting_state: FormattingState) -> str:
        """Extract formatting codes from a formatting state"""
        format_codes: List[str] = []
        
        for family_name, tokens in formatting_state.family_states.items():
            if tokens:
                formatter = self._get_formatter_by_family(family_name)
                # Get the formatting codes by applying to a marker and extracting
                temp_result = formatter.apply_formatting("###MARKER###", tokens, self.output_mode)
                if temp_result and self.output_mode == 'console':
                    marker_pos = temp_result.find("###MARKER###")
                    if marker_pos != -1:
                        codes = temp_result[:marker_pos]
                        if codes:
                            format_codes.append(codes)
        
        return ''.join(format_codes)
    
    def _get_formatter_by_family(self, family_name: str):
        """Get formatter instance by family name"""
        for formatter in TOKEN_FORMATTERS.values():
            if formatter.get_family_name() == family_name:
                return formatter
        raise ValueError(f"No formatter found for family: {family_name}")
    
    def _make_error_user_friendly(self, text: str) -> str:
        """Convert synthetic field names to user-friendly position descriptions"""
        import re
        return re.sub(r'__pos_(\d+)__', lambda m: f"position {int(m.group(1)) + 1}", text)


class DynamicLoggingFormatter(logging.Formatter):
    """
    Logging formatter that uses dynamic formatting with configurable graceful degradation,
    enhanced error context, and optional template validation
    
    Automatically handles missing log fields - if duration, error_count, file_count, etc.
    are not present in the log record, their corresponding template sections simply
    disappear from the output without requiring manual null checking.
    
    Supports both keyword-style templates ({{field_name}}) and positional-style 
    templates ({{}}) for different logging scenarios.
    
    Enhanced: Configurable validation modes for different deployment scenarios.
    Production logging uses graceful mode to ensure logging never fails.
    """
    
    def __init__(self, template: str, output_mode: str = 'console',
                 functions: Optional[Dict[str, Callable]] = None,
                 delimiter: str = ';'):
        """
        Initialize logging formatter
        
        Args:
            template: Dynamic format template
            output_mode: 'console' or 'file'
            functions: Optional functions for conditional formatting
            delimiter: Template delimiter (default ';')
        """
        super().__init__()
        self.formatter = DynamicFormatter(
            template=template,
            output_mode=output_mode,
            functions=functions,
            delimiter=delimiter
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record using dynamic formatting"""
        try:
            # Convert log record to dictionary
            record_dict = record.__dict__.copy()
            
            # Add some commonly needed derived fields
            if hasattr(record, 'levelname'):
                record_dict['level'] = record.levelname.lower()
            
            return self.formatter.format(**record_dict)
        except Exception as e:
            # Fallback to basic formatting if dynamic formatting fails
            return f"[FORMATTING ERROR: {e}] {record.getMessage()}"