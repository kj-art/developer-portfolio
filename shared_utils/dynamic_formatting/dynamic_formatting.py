"""
Main dynamic formatting classes with enhanced error context, function fallback support,
and proactive template validation.

PRIMARY BENEFIT: Template sections gracefully disappear when required data is missing,
eliminating tedious manual null checking and conditional string building.

ENHANCED: Template validation catches issues at creation time with helpful suggestions,
plus detailed error messages with context for easier debugging and development.
"""

import logging
from typing import Dict, Any, Callable, Optional, Union, List

from .formatters import TOKEN_FORMATTERS, FormatterError, FunctionExecutionError
from .template_parser import TemplateParser, DynamicFormattingError, ParseError
from .span_structures import FormattedSpan, FormatSection
from .formatting_state import FormattingState
from .template_validation import TemplateValidator, ValidationLevel, create_validation_summary


class RequiredFieldError(DynamicFormattingError):
    """Raised when a required field is missing with enhanced context"""
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 template: Optional[str] = None, position: Optional[int] = None):
        self.field_name = field_name
        
        # Enhanced message for required fields
        if field_name and field_name.startswith('__pos_'):
            # Convert synthetic field name to user-friendly position
            import re
            match = re.match(r'__pos_(\d+)__', field_name)
            if match:
                pos_num = int(match.group(1)) + 1
                enhanced_message = f"Required field missing: position {pos_num}"
            else:
                enhanced_message = message
        else:
            enhanced_message = f"Required field missing: {field_name}" if field_name else message
            
        super().__init__(
            enhanced_message, 
            template, 
            position, 
            f"Field '{field_name}' is marked as required with '!' but no value was provided"
        )


class FunctionNotFoundError(DynamicFormattingError):
    """Raised when a conditional or formatting function is not found with enhanced context"""
    def __init__(self, message: str, function_name: Optional[str] = None,
                 template: Optional[str] = None, position: Optional[int] = None,
                 available_functions: Optional[List[str]] = None):
        self.function_name = function_name
        self.available_functions = available_functions or []
        
        context = f"Function '{function_name}' not found in function registry"
        if self.available_functions:
            context += f". Available functions: {', '.join(sorted(self.available_functions))}"
        else:
            context += ". No functions are registered."
            
        super().__init__(message, template, position, context)


class DynamicFormatter:
    """
    Main dynamic formatter with graceful missing data handling, enhanced error context,
    and proactive template validation
    
    Core Feature: Template sections automatically disappear when their required data
    isn't provided, eliminating the need for manual null checking and conditional
    string building throughout your codebase.
    
    New Feature: Positional arguments support using empty field names in templates.
    Use {{}} instead of {{field_name}} to enable positional argument matching.
    
    Enhanced: Detailed error messages with template context and position information
    for easier debugging and development.
    
    Professional: Template validation catches common issues at creation time with
    helpful suggestions and best practice recommendations.
    """
    
    def __init__(self, format_string: str, delimiter: str = ';', 
                 functions: Optional[Dict[str, Callable]] = None,
                 output_mode: str = 'console',
                 validate: bool = True,
                 validation_level: str = 'warning') -> None:
        """
        Initialize DynamicFormatter with optional template validation
        
        Args:
            format_string: Template string to format
            delimiter: Character used to separate template parts
            functions: Dictionary of functions for fallback execution
            output_mode: 'console' for ANSI codes, 'file' for plain text
            validate: Whether to perform template validation
            validation_level: 'error', 'warning', or 'info' - minimum level to report
        """
        self.format_string = format_string
        self.delimiter = delimiter
        self.functions = functions or {}
        self.output_mode = output_mode
        self.validate = validate
        self.validation_level = validation_level
        
        # Set up function registry for formatters
        for formatter in TOKEN_FORMATTERS.values():
            formatter.set_function_registry(self.functions)
        
        # Perform template validation if requested
        if validate:
            self._validate_template()
        
        # Parse the format string with enhanced error context
        try:
            self.parser = TemplateParser(delimiter, TOKEN_FORMATTERS)
            self.sections = self.parser.parse_format_string(format_string)
        except ParseError as e:
            raise DynamicFormattingError(f"Failed to parse format string: {e}")
    
    def _validate_template(self) -> None:
        """Perform template validation and report issues"""
        validator = TemplateValidator(TOKEN_FORMATTERS, self.functions)
        warnings = validator.validate_template(self.format_string)
        
        if not warnings:
            return
        
        # Filter warnings by specified level
        level_order = {'error': 0, 'warning': 1, 'info': 2}
        min_level = level_order.get(self.validation_level.lower(), 1)
        
        filtered_warnings = [
            w for w in warnings 
            if level_order.get(w.level.value, 1) <= min_level
        ]
        
        if not filtered_warnings:
            return
        
        # Report validation results
        summary = create_validation_summary(filtered_warnings)
        
        # Decide how to handle validation results
        error_warnings = [w for w in filtered_warnings if w.level == ValidationLevel.ERROR]
        
        if error_warnings:
            # For errors, we might want to raise an exception in strict mode
            # For now, just print and continue (graceful degradation)
            print(f"\n🚨 Template Validation Errors Found:")
            for warning in error_warnings:
                print(f"   {warning}")
            print(f"\n💡 Template will still work, but please fix these issues for best results.\n")
        else:
            # For warnings and info, just print them
            if self.validation_level.lower() in ['warning', 'info']:
                print(f"\n{summary}")
    
    def format(self, *args: Any, **kwargs: Any) -> str:
        """
        Format the template with provided data using either positional or keyword arguments
        
        Core Feature: Missing fields cause their template sections to disappear
        automatically, eliminating the need for manual null checking.
        
        Args:
            *args: Positional arguments for templates with empty field names
            **kwargs: Keyword arguments for templates with named fields
            
        Returns:
            Formatted string with missing data sections automatically omitted
            
        Raises:
            DynamicFormattingError: If arguments are invalid or formatting fails with context
            RequiredFieldError: If a required field is missing with enhanced context
        """
        # Argument validation
        if args and kwargs:
            # Use basic DynamicFormattingError for backward compatibility
            raise DynamicFormattingError(
                "Cannot mix positional and keyword arguments. "
                "Use either positional args format(a, b, c) or keyword args format(key=value)"
            )
        
        # Convert positional args to kwargs
        if args:
            # Count actual field sections (not string literals)
            field_sections = [s for s in self.sections if isinstance(s, FormatSection)]
            
            if len(args) > len(field_sections):
                expected = len(field_sections)
                got = len(args)
                raise DynamicFormattingError(
                    f"Too many positional arguments: expected {expected}, got {got}. "
                    f"Template has {expected} field sections but {got} arguments were provided"
                )
            
            data: Dict[str, Any] = {}
            # Map positional arguments to field sections in order
            for i, arg in enumerate(args):
                if i < len(field_sections):
                    data[field_sections[i].field_name] = arg
        else:
            data = kwargs
        
        result = ""
        
        try:
            for section in self.sections:
                if isinstance(section, str):
                    result += section
                else:
                    # Set error context for formatters
                    self._set_formatter_context(section)
                    result += self._render_section(section, data)
        except (FormatterError, FunctionExecutionError) as e:
            # Make error messages user-friendly for positional arguments
            error_msg = self._make_error_user_friendly(str(e))
            raise DynamicFormattingError(f"Formatting failed: {error_msg}")
        
        return result
    
    def get_validation_report(self) -> str:
        """
        Get a detailed validation report for this template
        
        Returns:
            Formatted validation report string
        """
        if not self.validate:
            return "Template validation is disabled for this formatter."
        
        validator = TemplateValidator(TOKEN_FORMATTERS, self.functions)
        warnings = validator.validate_template(self.format_string)
        
        if not warnings:
            return "✅ Template validation passed - no issues found!"
        
        return create_validation_summary(warnings)
    
    def _set_formatter_context(self, section: FormatSection) -> None:
        """Set error context for all formatters based on current section"""
        # We don't have exact position info, but we can provide the template
        for formatter in TOKEN_FORMATTERS.values():
            if hasattr(formatter, 'set_error_context'):
                formatter.set_error_context(self.format_string, None)
    
    def _render_section(self, section: FormatSection, data: Dict[str, Any]) -> str:
        """
        Render a complete format section with enhanced error context
        
        Core Feature Implementation: Returns empty string when the required field
        is missing from the data dictionary, causing the entire section to disappear.
        
        Args:
            section: Format section to render
            data: Data dictionary containing field values
            
        Returns:
            Rendered section text or empty string if field missing
            
        Raises:
            RequiredFieldError: If required field is missing with enhanced context
            FunctionNotFoundError: If conditional function not found with enhanced context
            FunctionExecutionError: If function execution fails with enhanced context
        """
        field_value = data.get(section.field_name)
        
        # Core feature: graceful missing data handling
        # If field is missing and not required, section disappears (returns empty string)
        if field_value is None:
            if section.is_required:
                raise RequiredFieldError(
                    f"Required field missing: {self._make_error_user_friendly(section.field_name)}",
                    field_name=section.field_name,
                    template=self.format_string
                )
            return ""  # Section disappears when field is missing - core feature
        
        # Check conditional function
        if section.function_name:
            if section.function_name not in self.functions:
                raise FunctionNotFoundError(
                    f"Conditional function not found: {section.function_name}",
                    function_name=section.function_name,
                    template=self.format_string,
                    available_functions=list(self.functions.keys())
                )
            
            try:
                func = self.functions[section.function_name]
                if not func(field_value):
                    return ""
            except Exception as e:
                raise FunctionExecutionError(
                    f"Conditional function '{section.function_name}' failed: {e}",
                    function_name=section.function_name,
                    original_error=e,
                    template=self.format_string
                )
        
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
        text_parts: List[str] = []
        
        if section.prefix_function:
            func = self.functions.get(section.prefix_function)
            if not func:
                raise FunctionNotFoundError(
                    f"Prefix function not found: {section.prefix_function}",
                    function_name=section.prefix_function,
                    template=self.format_string,
                    available_functions=list(self.functions.keys())
                )
            try:
                text_parts.append(func(field_value))
            except Exception as e:
                raise FunctionExecutionError(
                    f"Prefix function '{section.prefix_function}' failed: {e}",
                    function_name=section.prefix_function,
                    original_error=e,
                    template=self.format_string
                )
        elif isinstance(section.prefix, str) and section.prefix:
            text_parts.append(section.prefix)
        
        text_parts.append(str(field_value))
        
        if section.suffix_function:
            func = self.functions.get(section.suffix_function)
            if not func:
                raise FunctionNotFoundError(
                    f"Suffix function not found: {section.suffix_function}",
                    function_name=section.suffix_function,
                    template=self.format_string,
                    available_functions=list(self.functions.keys())
                )
            try:
                text_parts.append(func(field_value))
            except Exception as e:
                raise FunctionExecutionError(
                    f"Suffix function '{section.suffix_function}' failed: {e}",
                    function_name=section.suffix_function,
                    original_error=e,
                    template=self.format_string
                )
        elif isinstance(section.suffix, str) and section.suffix:
            text_parts.append(section.suffix)
        
        complete_text = ''.join(text_parts)
        return self._apply_formatting_with_reset(complete_text, base_state)
    
    def _render_complex_section(self, section: FormatSection, field_value: Any, 
                              base_state: FormattingState) -> str:
        """Render a complex section with inline formatting"""
        result_parts: List[str] = []
        has_any_formatting = False
        
        # Render prefix
        if section.prefix_function:
            func = self.functions.get(section.prefix_function)
            if not func:
                raise FunctionNotFoundError(
                    f"Prefix function not found: {section.prefix_function}",
                    function_name=section.prefix_function,
                    template=self.format_string,
                    available_functions=list(self.functions.keys())
                )
            try:
                prefix_text = func(field_value)
                prefix_result = self._apply_formatting_no_reset(prefix_text, base_state)
                result_parts.append(prefix_result)
                if base_state.has_active_formatting():
                    has_any_formatting = True
            except Exception as e:
                raise FunctionExecutionError(
                    f"Prefix function '{section.prefix_function}' failed: {e}",
                    function_name=section.prefix_function,
                    original_error=e,
                    template=self.format_string
                )
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
                raise FunctionNotFoundError(
                    f"Suffix function not found: {section.suffix_function}",
                    function_name=section.suffix_function,
                    template=self.format_string,
                    available_functions=list(self.functions.keys())
                )
            try:
                suffix_text = func(field_value)
                suffix_result = self._apply_formatting_no_reset(suffix_text, base_state)
                result_parts.append(suffix_result)
                if base_state.has_active_formatting():
                    has_any_formatting = True
            except Exception as e:
                raise FunctionExecutionError(
                    f"Suffix function '{section.suffix_function}' failed: {e}",
                    function_name=section.suffix_function,
                    original_error=e,
                    template=self.format_string
                )
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
                                   field_value: Any) -> None:
        """Parse and add tokens to formatting state with enhanced error context"""
        for family_name, raw_tokens in token_dict.items():
            formatter = self._get_formatter_by_family(family_name)
            parsed_tokens: List[Union[str, int, bool]] = []
            
            for raw_token in raw_tokens:
                try:
                    parsed_token = formatter.parse_token(str(raw_token), field_value)
                    parsed_tokens.append(parsed_token)
                except FormatterError as e:
                    # Re-raise with additional context
                    raise DynamicFormattingError(
                        f"Token parsing failed for '{raw_token}' in {family_name} family: {e}"
                    )
            
            state.add_tokens(family_name, parsed_tokens)
    
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
                
                parsed_tokens: List[Union[str, int, bool]] = []
                for raw_token in raw_tokens:
                    try:
                        parsed_token = formatter.parse_token(str(raw_token), field_value)
                        parsed_tokens.append(parsed_token)
                    except FormatterError as e:
                        raise DynamicFormattingError(
                            f"Span token parsing failed for '{raw_token}' in {family_name} family: {e}"
                        )
                
                # Handle reset specially
                if parsed_tokens and str(parsed_tokens[0]) == 'reset':
                    # Reset means this family should have NO formatting for this span
                    continue  # Keep family cleared
                else:
                    # Add new tokens
                    span_state.add_tokens(family_name, parsed_tokens)
            
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
    Logging formatter that uses dynamic formatting with graceful missing data handling,
    enhanced error context, and optional template validation
    
    Automatically handles missing log fields - if duration, error_count, file_count, etc.
    are not present in the log record, their corresponding template sections simply
    disappear from the output without requiring manual null checking.
    
    Supports both keyword-style templates ({{field_name}}) and positional-style 
    templates ({{}}) for different logging scenarios.
    
    Enhanced: Provides detailed error information when template formatting fails,
    but gracefully degrades to ensure logging always works.
    
    Professional: Optional template validation helps catch logging template issues
    during development.
    """
    
    def __init__(self, format_string: str, delimiter: str = ';', 
                 functions: Optional[Dict[str, Callable]] = None,
                 output_mode: str = 'console',
                 validate: bool = False,  # Default False for logging to avoid startup spam
                 validation_level: str = 'error') -> None:
        super().__init__()
        try:
            self.formatter = DynamicFormatter(
                format_string, delimiter, functions, output_mode, 
                validate, validation_level
            )
        except DynamicFormattingError as e:
            # Fall back to a basic formatter if dynamic formatting fails
            logging.getLogger(__name__).error(f"Dynamic formatting setup failed: {e}")
            self.formatter: Optional[DynamicFormatter] = None
            self.fallback_format = format_string
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record using dynamic formatting with enhanced error handling"""
        # If dynamic formatter failed to initialize, use basic formatting
        if self.formatter is None:
            return f"[FORMATTING ERROR] {record.getMessage()}"
        
        # Build log data dictionary
        log_data: Dict[str, Any] = {
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
            # Core feature in action: missing fields (duration, file_count, etc.) 
            # cause their template sections to disappear automatically
            return self.formatter.format(**log_data)
        except DynamicFormattingError as e:
            # Return error message with original log message and enhanced context
            error_details = f"Template: {self.formatter.format_string[:50]}..." if len(self.formatter.format_string) > 50 else self.formatter.format_string
            return f"[FORMATTING ERROR: {e}] {record.getMessage()} (Template: {error_details})"