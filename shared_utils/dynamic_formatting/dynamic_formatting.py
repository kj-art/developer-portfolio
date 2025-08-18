"""
Main dynamic formatting classes with function fallback support.

This module contains the primary DynamicFormatter and DynamicLoggingFormatter
classes that orchestrate the entire formatting system.

CORE RESPONSIBILITIES:
    - Template compilation and caching
    - Function registry management  
    - Section rendering with conditional logic
    - State management across formatting families
    - Error handling and graceful degradation
    - Output mode switching (console vs file)

RENDERING PIPELINE:
    1. Parse template into sections during initialization
    2. For each section during formatting:
       - Check conditional functions (section-level show/hide)
       - Build base formatting state from section tokens
       - Render prefix, field, and suffix with proper state isolation
       - Apply resets and cleanup formatting codes
    
PERFORMANCE OPTIMIZATIONS:
    - Simple sections use efficient string concatenation
    - Complex sections use span-based rendering with minimal resets
    - Lazy ANSI code application based on output mode
    - Efficient state copying for span isolation
"""

import logging
from typing import Dict, Any, Callable, Optional, Union, List

from .formatters import TOKEN_FORMATTERS, FormatterError, FunctionExecutionError
from .token_parsing import TemplateParser, DynamicFormattingError, ParseError
from .span_structures import FormattedSpan, FormatSection
from .formatting_state import FormattingState, StackingError


class RequiredFieldError(DynamicFormattingError):
    """Raised when a required field is missing"""
    pass


class FunctionNotFoundError(DynamicFormattingError):
    """Raised when a conditional function is not found"""
    pass


class DynamicFormatter:
    """Main dynamic formatter with function fallback and enhanced error handling"""
    
    def __init__(self, format_string: str, delimiter: str = ';', 
                 functions: Optional[Dict[str, Callable]] = None,
                 output_mode: str = 'console'):
        self.format_string = format_string
        self.delimiter = delimiter
        self.functions = functions or {}
        self.output_mode = output_mode
        
        # Set up function registry for formatters
        for formatter in TOKEN_FORMATTERS.values():
            formatter.set_function_registry(self.functions)
        
        # Parse the format string
        try:
            parser = TemplateParser(delimiter, TOKEN_FORMATTERS)
            self.sections = parser.parse_format_string(format_string)
        except ParseError as e:
            raise DynamicFormattingError(f"Failed to parse format string: {e}")
    
    def format(self, **data) -> str:
        """Format the template with provided data"""
        result = ""
        
        try:
            for section in self.sections:
                if isinstance(section, str):
                    result += section
                else:
                    result += self._render_section(section, data)
        except (FormatterError, FunctionExecutionError) as e:
            raise DynamicFormattingError(f"Formatting failed: {e}")
        
        return result
    
    def _render_section(self, section: FormatSection, data: Dict[str, Any]) -> str:
        """Render a complete format section"""
        field_value = data.get(section.field_name)
        
        if field_value is None:
            if section.is_required:
                raise RequiredFieldError(f"Required field missing: {section.field_name}")
            return ""
        
        # Check conditional function
        if section.function_name:
            if section.function_name not in self.functions:
                raise FunctionNotFoundError(f"Conditional function not found: {section.function_name}")
            
            try:
                func = self.functions[section.function_name]
                if not func(field_value):
                    return ""
            except Exception as e:
                raise FunctionExecutionError(f"Conditional function '{section.function_name}' failed: {e}")
        
        # Build base formatting state for the whole section
        base_section_state = self._build_formatting_state(
            section.whole_section_formatting_tokens, field_value
        )
        
        # Handle simple vs complex sections differently for performance
        if section.is_simple_section():
            return self._render_simple_section(section, field_value, base_section_state)
        else:
            return self._render_complex_section(section, field_value, base_section_state)
    
    def _render_simple_section(self, section: FormatSection, field_value: Any, 
                             base_state: FormattingState) -> str:
        """Render a simple section (no inline formatting) efficiently"""
        # Build complete text and apply formatting once
        text_parts = []
        
        if section.prefix_function:
            func = self.functions.get(section.prefix_function)
            if not func:
                raise FunctionNotFoundError(f"Prefix function not found: {section.prefix_function}")
            try:
                text_parts.append(func(field_value))
            except Exception as e:
                raise FunctionExecutionError(f"Prefix function '{section.prefix_function}' failed: {e}")
        elif isinstance(section.prefix, str) and section.prefix:
            text_parts.append(section.prefix)
        
        text_parts.append(str(field_value))
        
        if section.suffix_function:
            func = self.functions.get(section.suffix_function)
            if not func:
                raise FunctionNotFoundError(f"Suffix function not found: {section.suffix_function}")
            try:
                text_parts.append(func(field_value))
            except Exception as e:
                raise FunctionExecutionError(f"Suffix function '{section.suffix_function}' failed: {e}")
        elif isinstance(section.suffix, str) and section.suffix:
            text_parts.append(section.suffix)
        
        complete_text = ''.join(text_parts)
        return self._apply_formatting_with_reset(complete_text, base_state)
    
    def _render_complex_section(self, section: FormatSection, field_value: Any, 
                              base_state: FormattingState) -> str:
        """Render a complex section with inline formatting"""
        result_parts = []
        has_any_formatting = False
        
        # Render prefix
        if section.prefix_function:
            func = self.functions.get(section.prefix_function)
            if not func:
                raise FunctionNotFoundError(f"Prefix function not found: {section.prefix_function}")
            try:
                prefix_text = func(field_value)
                prefix_result = self._apply_formatting_no_reset(prefix_text, base_state)
                result_parts.append(prefix_result)
                if base_state.has_active_formatting():
                    has_any_formatting = True
            except Exception as e:
                raise FunctionExecutionError(f"Prefix function '{section.prefix_function}' failed: {e}")
        elif section.prefix:
            prefix_result = self._render_formatted_spans_no_reset(
                section.prefix, base_state, field_value
            )
            result_parts.append(prefix_result)
            if prefix_result != (section.prefix if isinstance(section.prefix, str) else ""):
                has_any_formatting = True
        
        # Render field with combined formatting
        field_state = base_state.copy()
        if section.field_formatting_tokens:
            self._add_parsed_tokens_to_state(
                field_state, section.field_formatting_tokens, field_value
            )
        
        field_result = self._apply_formatting_no_reset(str(field_value), field_state)
        result_parts.append(field_result)
        if field_state.has_active_formatting():
            has_any_formatting = True
        
        # Render suffix
        if section.suffix_function:
            func = self.functions.get(section.suffix_function)
            if not func:
                raise FunctionNotFoundError(f"Suffix function not found: {section.suffix_function}")
            try:
                suffix_text = func(field_value)
                suffix_result = self._apply_formatting_no_reset(suffix_text, base_state)
                result_parts.append(suffix_result)
                if base_state.has_active_formatting():
                    has_any_formatting = True
            except Exception as e:
                raise FunctionExecutionError(f"Suffix function '{section.suffix_function}' failed: {e}")
        elif section.suffix:
            suffix_result = self._render_formatted_spans_no_reset(
                section.suffix, base_state, field_value
            )
            result_parts.append(suffix_result)
            if suffix_result != (section.suffix if isinstance(section.suffix, str) else ""):
                has_any_formatting = True
        
        # Add single reset at the end if any formatting was applied
        result = ''.join(result_parts)
        if has_any_formatting and self.output_mode == 'console':
            result += '\033[0m'
        
        return result
    
    def _build_formatting_state(self, token_dict: Dict[str, List], field_value: Any) -> FormattingState:
        """Build a formatting state from raw token dictionary"""
        state = FormattingState()
        self._add_parsed_tokens_to_state(state, token_dict, field_value)
        return state
    
    def _add_parsed_tokens_to_state(self, state: FormattingState, token_dict: Dict[str, List], 
                                   field_value: Any):
        """Parse and add tokens to formatting state"""
        for family_name, raw_tokens in token_dict.items():
            formatter = self._get_formatter_by_family(family_name)
            parsed_tokens = []
            
            for raw_token in raw_tokens:
                try:
                    parsed_token = formatter.parse_token(str(raw_token), field_value)
                    parsed_tokens.append(parsed_token)
                except FormatterError as e:
                    raise DynamicFormattingError(f"Token parsing failed for '{raw_token}': {e}")
            
            try:
                state.add_tokens(family_name, parsed_tokens, formatter.self_stacking)
            except StackingError as e:
                raise DynamicFormattingError(f"Stacking error: {e}")
    
    def _render_formatted_spans_no_reset(self, spans: Union[str, List[FormattedSpan]], 
                                       base_state: FormattingState, field_value: Any) -> str:
        """Render formatted spans with proper isolation between spans"""
        if isinstance(spans, str):
            return self._apply_formatting_no_reset(spans, base_state)
        
        result = ""
        
        for span in spans:
            # Check conditionals first - if any say to hide, skip this span
            should_show_span = True
            if 'conditional' in span.formatting_tokens:
                conditional_formatter = self._get_formatter_by_family('conditional')
                for raw_token in span.formatting_tokens['conditional']:
                    try:
                        parsed_token = conditional_formatter.parse_token(str(raw_token), field_value)
                        if parsed_token == 'hide':
                            should_show_span = False
                            break
                    except FormatterError:
                        # If conditional function fails, hide the span (safe default)
                        should_show_span = False
                        break
            
            if not should_show_span:
                continue  # Skip this span entirely
            
            # Start with base state
            span_state = base_state.copy()
            
            # Apply span-specific formatting - REPLACE families, don't add to them
            for family_name, raw_tokens in span.formatting_tokens.items():
                # Skip conditional tokens - they were already processed
                if family_name == 'conditional':
                    continue
                    
                span_state.clear_family(family_name)
                formatter = self._get_formatter_by_family(family_name)
                
                parsed_tokens = []
                for raw_token in raw_tokens:
                    try:
                        parsed_token = formatter.parse_token(str(raw_token), field_value)
                        parsed_tokens.append(parsed_token)
                    except FormatterError as e:
                        raise DynamicFormattingError(f"Span token parsing failed for '{raw_token}': {e}")
                
                # Handle reset specially
                if parsed_tokens and str(parsed_tokens[0]) == 'reset':
                    # Reset means this family should have NO formatting for this span
                    continue  # Keep family cleared
                else:
                    # Add new tokens
                    try:
                        span_state.add_tokens(family_name, parsed_tokens, formatter.self_stacking)
                    except StackingError as e:
                        raise DynamicFormattingError(f"Span stacking error: {e}")
            
            # Format this span with individual reset to prevent bleeding
            if span_state.has_active_formatting() and self.output_mode == 'console':
                format_codes = self._get_formatting_codes(span_state)
                formatted_span = format_codes + span.text + '\033[0m'
            else:
                formatted_span = span.text
            
            result += formatted_span
        
        return result
    
    def _apply_formatting_with_reset(self, text: str, formatting_state: FormattingState) -> str:
        """Apply formatting to text with proper reset handling"""
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
        format_codes = []
        
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


class DynamicLoggingFormatter(logging.Formatter):
    """Logging formatter that uses dynamic formatting with proper error handling"""
    
    def __init__(self, format_string: str, delimiter: str = ';', 
                 functions: Optional[Dict[str, Callable]] = None,
                 output_mode: str = 'console'):
        super().__init__()
        try:
            self.formatter = DynamicFormatter(format_string, delimiter, functions, output_mode)
        except DynamicFormattingError as e:
            # Fall back to a basic formatter if dynamic formatting fails
            logging.getLogger(__name__).error(f"Dynamic formatting setup failed: {e}")
            self.formatter = None
            self.fallback_format = format_string
    
    def format(self, record: logging.LogRecord) -> str:
        # If dynamic formatter failed to initialize, use basic formatting
        if self.formatter is None:
            return f"[FORMATTING ERROR] {record.getMessage()}"
        
        # Build log data dictionary
        log_data = {
            'message': record.getMessage(),
            'levelname': record.levelname,
            'name': record.name,
            'funcName': record.funcName,
            'lineno': record.lineno,
            'asctime': self.formatTime(record),
        }
        
        # Add extra data if present
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Add other record attributes (excluding private ones)
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_'):
                log_data[key] = value
        
        try:
            return self.formatter.format(**log_data)
        except DynamicFormattingError as e:
            # Return error message with original log message
            return f"[FORMATTING ERROR: {e}] {record.getMessage()}"