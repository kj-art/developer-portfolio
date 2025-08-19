"""
Main dynamic formatting classes with configurable graceful degradation,
enhanced error context, function fallback support, and proactive template validation.

PRIMARY BENEFIT: Template sections gracefully disappear when required data is missing,
eliminating tedious manual null checking and conditional string building.

ENHANCED: Configurable validation modes for professional deployment scenarios:
- Development: strict mode with full validation for catching issues early
- Production: graceful mode with minimal validation for reliability  
- Assisted Development: auto-correct mode for productivity

PROFESSIONAL: Template validation catches issues at creation time with helpful suggestions,
plus detailed error messages with context for easier debugging and development.
"""

import logging
from typing import Dict, Any, Callable, Optional, Union, List

from .formatters import TOKEN_FORMATTERS, FormatterError, FunctionExecutionError
from .template_parser import TemplateParser, DynamicFormattingError, ParseError
from .span_structures import FormattedSpan, FormatSection
from .formatting_state import FormattingState
from .template_validation import TemplateValidator, create_validation_summary
from .config import FormatterConfig, ValidationMode, ValidationLevel


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
    Main dynamic formatter with configurable graceful degradation, enhanced error context,
    and proactive template validation
    
    Core Feature: Template sections automatically disappear when their required data
    isn't provided, eliminating the need for manual null checking and conditional
    string building throughout your codebase.
    
    New Feature: Positional arguments support using empty field names in templates.
    Use {{}} instead of {{field_name}} to enable positional argument matching.
    
    Enhanced: Configurable validation modes for different deployment scenarios:
    - STRICT: Invalid tokens cause runtime errors (development)
    - GRACEFUL: Invalid tokens fall back to safe defaults (production)
    - AUTO_CORRECT: Invalid tokens auto-correct to suggestions (assisted development)
    
    Professional: Template validation catches issues at creation time with helpful suggestions,
    plus detailed error messages with context for easier debugging and development.
    """
    
    def __init__(self, format_string: str, 
                 delimiter: str = None,
                 functions: Optional[Dict[str, Callable]] = None,
                 output_mode: str = None,
                 validate: bool = None,
                 validation_level: str = None,
                 config: Optional[FormatterConfig] = None) -> None:
        """
        Initialize DynamicFormatter with comprehensive configuration support
        
        Args:
            format_string: Template string to format
            delimiter: Character used to separate template parts (deprecated - use config)
            functions: Dictionary of functions for fallback execution (deprecated - use config)
            output_mode: 'console' for ANSI codes, 'file' for plain text (deprecated - use config)
            validate: Whether to perform template validation (deprecated - use config)
            validation_level: 'error', 'warning', or 'info' (deprecated - use config)
            config: FormatterConfig instance for comprehensive configuration
            
        Note: Individual parameters are maintained for backward compatibility but
              using FormatterConfig is recommended for new code.
        """
        # Handle configuration - new config system takes precedence
        if config is not None:
            self.config = config
        else:
            # Build config from individual parameters for backward compatibility
            self.config = FormatterConfig(
                delimiter=delimiter or ';',
                output_mode=output_mode or 'console',
                enable_validation=validate if validate is not None else True,
                validation_level=ValidationLevel(validation_level or 'warning'),
                functions=functions or {}
            )
        
        # Store template
        self.format_string = format_string
        
        # Set up function registry for formatters and pass config
        for formatter in TOKEN_FORMATTERS.values():
            formatter.set_function_registry(self.config.functions)
            if hasattr(formatter, 'set_config'):
                formatter.set_config(self.config)
        
        # Perform template validation if requested
        if self.config.should_validate():
            self._validate_template()
        
        # Parse the format string with enhanced error context
        try:
            self.parser = TemplateParser(self.config.delimiter, TOKEN_FORMATTERS)
            self.sections = self.parser.parse_format_string(format_string)
        except ParseError as e:
            raise DynamicFormattingError(f"Failed to parse format string: {e}")
    
    def _validate_template(self) -> None:
        """Perform template validation and report issues"""
        validator = TemplateValidator(TOKEN_FORMATTERS, self.config.functions)
        warnings = validator.validate_template(self.format_string)
        
        if not warnings:
            return
        
        # Filter warnings by specified level
        level_order = {'error': 0, 'warning': 1, 'info': 2}
        min_level = level_order.get(self.config.validation_level.value, 1)
        
        filtered_warnings = [
            w for w in warnings 
            if level_order.get(w.level.value, 1) <= min_level
        ]
        
        if not filtered_warnings:
            return
        
        # Report validation results
        summary = create_validation_summary(filtered_warnings)
        
        # Decide how to handle validation results based on mode
        error_warnings = [w for w in filtered_warnings if w.level == ValidationLevel.ERROR]
        
        if error_warnings and self.config.is_strict_mode():
            # In strict mode, errors could raise exceptions
            # For now, just print and continue for compatibility
            print(f"\n🚨 Template Validation Errors Found:")
            for warning in error_warnings:
                print(f"   {warning}")
            print(f"\n💡 Fix these issues for best results.\n")
        else:
            # For other modes, just print summary if validation level allows
            if self.config.validation_level != ValidationLevel.NONE:
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
            if self.config.strict_argument_validation:
                raise DynamicFormattingError(
                    "Cannot mix positional and keyword arguments. "
                    "Use either positional args format(a, b, c) or keyword args format(key=value)"
                )
            else:
                # In non-strict mode, prefer keyword args and ignore positional
                pass
        
        # Convert positional args to kwargs
        if args and not kwargs:
            # Count actual field sections (not string literals)
            field_sections = [s for s in self.sections if isinstance(s, FormatSection)]
            
            if len(args) > len(field_sections):
                expected = len(field_sections)
                got = len(args)
                if self.config.strict_argument_validation:
                    raise DynamicFormattingError(
                        f"Too many positional arguments: expected {expected}, got {got}. "
                        f"Template has {expected} field sections but {got} arguments were provided"
                    )
                else:
                    # In non-strict mode, just use the first N arguments
                    args = args[:expected]
            
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
            
            # Handle based on validation mode
            if self.config.is_strict_mode():
                raise DynamicFormattingError(f"Formatting failed: {error_msg}")
            else:
                # In graceful mode, return partial result with error indication
                return result + f"[FORMATTING ERROR: {error_msg}]"
        
        return result
    
    def get_validation_report(self) -> str:
        """
        Get a detailed validation report for this template
        
        Returns:
            Formatted validation report string
        """
        if not self.config.enable_validation:
            return "Template validation is disabled for this formatter."
        
        validator = TemplateValidator(TOKEN_FORMATTERS, self.config.functions)
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
        Render a complete format section with configurable graceful degradation
        
        Core Feature Implementation: Returns empty string when the required field
        is missing from the data dictionary, causing the entire section to disappear.
        
        Args:
            section: Format section to render
            data: Data dictionary containing field values
            
        Returns:
            Rendered section text or empty string if field missing
            
        Raises:
            RequiredFieldError: If required field is missing (strict mode only)
            FunctionNotFoundError: If conditional function not found (strict mode only)
            FunctionExecutionError: If function execution fails (strict mode only)
        """
        field_value = data.get(section.field_name)
        
        # Core feature: graceful missing data handling
        # If field is missing and not required, section disappears (returns empty string)
        if field_value is None:
            if section.is_required:
                if self.config.is_strict_mode():
                    raise RequiredFieldError(
                        f"Required field missing: {self._make_error_user_friendly(section.field_name)}",
                        field_name=section.field_name,
                        template=self.format_string
                    )
                else:
                    # In graceful mode, even required fields just disappear
                    return ""
            return ""  # Section disappears when field is missing - core feature
        
        # Check conditional function with graceful degradation
        if section.function_name:
            # The conditional formatter will handle graceful degradation based on config
            try:
                conditional_formatter = self._get_formatter_by_family('conditional')
                parsed_result = conditional_formatter.parse_token(section.function_name, field_value)
                if parsed_result == 'hide':
                    return ""
            except FormatterError as e:
                if self.config.is_strict_mode():
                    # Convert to appropriate exception type for strict mode
                    raise FunctionNotFoundError(
                        f"Conditional function not found: {section.function_name}",
                        function_name=section.function_name,
                        template=self.format_string,
                        available_functions=list(self.config.functions.keys())
                    )
                else:
                    # In graceful mode, hide the section if conditional fails
                    return ""
            except Exception as e:
                if self.config.is_strict_mode():
                    raise FunctionExecutionError(
                        f"Conditional function '{section.function_name}' failed: {e}",
                        function_name=section.function_name,
                        original_error=e,
                        template=self.format_string
                    )
                else:
                    # In graceful mode, hide the section if conditional fails
                    return ""
        
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
            func = self.config.functions.get(section.prefix_function)
            if not func:
                if self.config.is_strict_mode():
                    raise FunctionNotFoundError(
                        f"Prefix function not found: {section.prefix_function}",
                        function_name=section.prefix_function,
                        template=self.format_string,
                        available_functions=list(self.config.functions.keys())
                    )
                else:
                    # In graceful mode, skip missing function
                    pass
            else:
                try:
                    text_parts.append(func(field_value))
                except Exception as e:
                    if self.config.is_strict_mode():
                        raise FunctionExecutionError(
                            f"Prefix function '{section.prefix_function}' failed: {e}",
                            function_name=section.prefix_function,
                            original_error=e,
                            template=self.format_string
                        )
                    else:
                        # In graceful mode, skip failed function
                        pass
        elif isinstance(section.prefix, str) and section.prefix:
            text_parts.append(section.prefix)
        
        text_parts.append(str(field_value))
        
        if section.suffix_function:
            func = self.config.functions.get(section.suffix_function)
            if not func:
                if self.config.is_strict_mode():
                    raise FunctionNotFoundError(
                        f"Suffix function not found: {section.suffix_function}",
                        function_name=section.suffix_function,
                        template=self.format_string,
                        available_functions=list(self.config.functions.keys())
                    )
                else:
                    # In graceful mode, skip missing function
                    pass
            else:
                try:
                    text_parts.append(func(field_value))
                except Exception as e:
                    if self.config.is_strict_mode():
                        raise FunctionExecutionError(
                            f"Suffix function '{section.suffix_function}' failed: {e}",
                            function_name=section.suffix_function,
                            original_error=e,
                            template=self.format_string
                        )
                    else:
                        # In graceful mode, skip failed function
                        pass
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
            func = self.config.functions.get(section.prefix_function)
            if not func:
                if self.config.is_strict_mode():
                    raise FunctionNotFoundError(
                        f"Prefix function not found: {section.prefix_function}",
                        function_name=section.prefix_function,
                        template=self.format_string,
                        available_functions=list(self.config.functions.keys())
                    )
                # In graceful mode, skip missing function
            else:
                try:
                    prefix_text = func(field_value)
                    prefix_result = self._apply_formatting_no_reset(prefix_text, base_state)
                    result_parts.append(prefix_result)
                    if base_state.has_active_formatting():
                        has_any_formatting = True
                except Exception as e:
                    if self.config.is_strict_mode():
                        raise FunctionExecutionError(
                            f"Prefix function '{section.prefix_function}' failed: {e}",
                            function_name=section.prefix_function,
                            original_error=e,
                            template=self.format_string
                        )
                    # In graceful mode, skip failed function
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
        
        # Render suffix (similar to prefix)
        if section.suffix_function:
            func = self.config.functions.get(section.suffix_function)
            if not func:
                if self.config.is_strict_mode():
                    raise FunctionNotFoundError(
                        f"Suffix function not found: {section.suffix_function}",
                        function_name=section.suffix_function,
                        template=self.format_string,
                        available_functions=list(self.config.functions.keys())
                    )
                # In graceful mode, skip missing function
            else:
                try:
                    suffix_text = func(field_value)
                    suffix_result = self._apply_formatting_no_reset(suffix_text, base_state)
                    result_parts.append(suffix_result)
                    if base_state.has_active_formatting():
                        has_any_formatting = True
                except Exception as e:
                    if self.config.is_strict_mode():
                        raise FunctionExecutionError(
                            f"Suffix function '{section.suffix_function}' failed: {e}",
                            function_name=section.suffix_function,
                            original_error=e,
                            template=self.format_string
                        )
                    # In graceful mode, skip failed function
        elif section.suffix:
            suffix_result = self._render_formatted_spans_no_reset(
                section.suffix, base_state, field_value
            )
            result_parts.append(suffix_result)
            if suffix_result != (section.suffix if isinstance(section.suffix, str) else ""):
                has_any_formatting = True
        
        # Add single reset at the end if any formatting was applied
        result = ''.join(result_parts)
        if has_any_formatting and self.config.output_mode == 'console':
            result += '\033[0m'
        
        return result
    
    def _build_formatting_state(self, token_dict: Dict[str, List], field_value: Any) -> FormattingState:
        """Build a formatting state from raw token dictionary"""
        state = FormattingState()
        self._add_parsed_tokens_to_state(state, token_dict, field_value)
        return state
    
    def _add_parsed_tokens_to_state(self, state: FormattingState, token_dict: Dict[str, List], 
                                   field_value: Any) -> None:
        """Parse and add tokens to formatting state with configurable error handling"""
        for family_name, raw_tokens in token_dict.items():
            formatter = self._get_formatter_by_family(family_name)
            parsed_tokens: List[Union[str, int, bool]] = []
            
            for raw_token in raw_tokens:
                try:
                    parsed_token = formatter.parse_token(str(raw_token), field_value)
                    parsed_tokens.append(parsed_token)
                except FormatterError as e:
                    if self.config.is_strict_mode():
                        # Re-raise with additional context in strict mode
                        raise DynamicFormattingError(
                            f"Token parsing failed for '{raw_token}' in {family_name} family: {e}"
                        )
                    else:
                        # In graceful mode, skip invalid tokens
                        continue
            
            if parsed_tokens:  # Only add if we have valid tokens
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
                        # If conditional function fails, behavior depends on mode
                        if self.config.is_strict_mode():
                            raise
                        else:
                            # In graceful mode, hide the span (safe default)
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
                        if self.config.is_strict_mode():
                            raise DynamicFormattingError(
                                f"Span token parsing failed for '{raw_token}' in {family_name} family: {e}"
                            )
                        else:
                            # In graceful mode, skip invalid tokens
                            continue
                
                # Handle reset specially
                if parsed_tokens and str(parsed_tokens[0]) == 'reset':
                    # Reset means this family should have NO formatting for this span
                    continue  # Keep family cleared
                else:
                    # Add new tokens
                    if parsed_tokens:  # Only add if we have valid tokens
                        span_state.add_tokens(family_name, parsed_tokens)
            
            # Format this span with individual reset to prevent bleeding
            if span_state.has_active_formatting() and self.config.output_mode == 'console':
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
            if format_codes and self.config.output_mode == 'console':
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
                temp_result = formatter.apply_formatting("###MARKER###", tokens, self.config.output_mode)
                if temp_result and self.config.output_mode == 'console':
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
    
    Professional: Optional template validation helps catch logging template issues
    during development.
    """
    
    def __init__(self, format_string: str, 
                 delimiter: str = None,
                 functions: Optional[Dict[str, Callable]] = None,
                 output_mode: str = None,
                 validate: bool = None,
                 validation_level: str = None,
                 config: Optional[FormatterConfig] = None) -> None:
        super().__init__()
        
        # Use production config as default for logging (graceful mode)
        if config is None:
            config = FormatterConfig.production(
                delimiter=delimiter or ';',
                output_mode=output_mode or 'console',
                enable_validation=validate if validate is not None else False,  # Default False for logging
                validation_level=ValidationLevel(validation_level or 'error'),
                functions=functions or {}
            )
        
        try:
            self.formatter = DynamicFormatter(format_string, config=config)
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
            # Logging should never fail, even in strict mode
            # Return error message with original log message and enhanced context
            error_details = f"Template: {self.formatter.format_string[:50]}..." if len(self.formatter.format_string) > 50 else self.formatter.format_string
            return f"[FORMATTING ERROR: {e}] {record.getMessage()} (Template: {error_details})"