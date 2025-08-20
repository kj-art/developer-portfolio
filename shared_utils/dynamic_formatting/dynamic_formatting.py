"""
Core dynamic formatting functionality with robust error handling.

This module provides the main DynamicFormatter class and related functionality
for template-based string formatting with automatic missing data handling.
"""

import logging
from typing import Dict, List, Any, Union, Optional
from .config import FormatterConfig
from .template_parser import TemplateParser, ParseError
from .span_structures import FormatSection
from .formatters import TOKEN_FORMATTERS, FormatterError, FunctionExecutionError


class DynamicFormattingError(Exception):
    """Base exception for dynamic formatting operations"""
    
    def __init__(self, message: str, template: Optional[str] = None, 
                 context: Optional[str] = None):
        super().__init__(message)
        self.template = template
        self.context = context
    
    def __str__(self):
        parts = [super().__str__()]
        if self.context:
            parts.append(f"Context: {self.context}")
        if self.template:
            parts.append(f"Template: '{self.template}'")
        return "\n".join(parts)


class RequiredFieldError(DynamicFormattingError):
    """Exception raised when a required field is missing"""
    
    def __init__(self, message: str, field_name: str, template: Optional[str] = None):
        context = f"Required field '{field_name}' was marked as mandatory with '!' but no value was provided"
        super().__init__(message, template, context)
        self.field_name = field_name


class FunctionNotFoundError(DynamicFormattingError):
    """Exception raised when a required function is not found"""
    
    def __init__(self, message: str, function_name: str, template: Optional[str] = None,
                 available_functions: Optional[List[str]] = None):
        context_parts = [f"Function '{function_name}' is not registered"]
        if available_functions:
            context_parts.append(f"Available functions: {', '.join(available_functions)}")
        context = ". ".join(context_parts)
        super().__init__(message, template, context)
        self.function_name = function_name
        self.available_functions = available_functions or []


class DynamicFormatter:
    """
    Advanced string formatter with automatic missing data handling and rich formatting
    
    This formatter provides template-based string formatting where missing data
    causes entire sections to disappear, eliminating the need for manual null
    checking in application code.
    
    Key Features:
    - Automatic section removal for missing data
    - Rich color and text formatting support
    - Function-based conditional logic
    - Graceful error handling with configurable strictness
    - Support for both positional and keyword arguments
    """
    
    def __init__(self, format_string: str, config: Optional[FormatterConfig] = None, 
                 functions: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize the dynamic formatter
        
        Args:
            format_string: Template string with {{...}} sections
            config: Configuration object (defaults to basic config)
            functions: Dictionary of custom functions for conditionals and formatting
            **kwargs: Legacy support for direct configuration parameters
        """
        self.format_string = format_string
        
        # Handle configuration
        if config is None:
            config = FormatterConfig(**kwargs)
        if functions:
            config.functions.update(functions)
        self.config = config
        
        # Initialize formatter registry with functions
        self._setup_formatter_registry()
        
        # Parse the template
        parser = TemplateParser(
            delimiter=self.config.delimiter,
            token_formatters=TOKEN_FORMATTERS
        )
        try:
            self.sections = parser.parse_format_string(format_string)
        except ParseError as e:
            raise DynamicFormattingError(f"Template parsing failed: {e}", template=format_string)
        
        # Perform template validation if enabled
        self._validate_template()
    
    def _setup_formatter_registry(self) -> None:
        """Set up the formatter registry with functions and config"""
        for formatter in TOKEN_FORMATTERS.values():
            if hasattr(formatter, 'set_function_registry'):
                formatter.set_function_registry(self.config.functions)
            if hasattr(formatter, 'set_config'):
                formatter.set_config(self.config)
    
    def format(self, *args, **kwargs) -> str:
        """
        Format the template with provided data, supporting both positional and keyword arguments
        
        Core Feature: Missing fields cause their sections to disappear entirely,
        eliminating manual null checking and conditional string building.
        
        Args:
            *args: Positional arguments (mapped to template fields in order)
            **kwargs: Keyword arguments (mapped by field name)
        
        Returns:
            Formatted string with missing data sections removed
        
        Raises:
            DynamicFormattingError: If formatting fails and strict mode is enabled
            RequiredFieldError: If required field (marked with !) is missing
        """
        # Handle positional vs keyword arguments
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
                    # In non-strict mode, ignore extra arguments
                    args = args[:expected]
            
            # FIXED: Map positional arguments to field names correctly
            data = {}
            for i, arg in enumerate(args):
                if i < len(field_sections):
                    section = field_sections[i]
                    # For positional sections, use the positional field name
                    if section.field_name.startswith('__pos_'):
                        data[section.field_name] = arg
                    else:
                        # For named sections, use the actual field name
                        data[section.field_name] = arg
        else:
            # Use keyword arguments directly
            data = kwargs
        
        # Set error context for all formatters
        self._set_formatter_context(None)
        
        # Render all sections
        result = ""
        for section in self.sections:
            if isinstance(section, str):
                # Literal text - add as is
                result += section
            else:
                # Format section - render with data
                result += self._render_section(section, data)
        
        return result
    
    def validate_template(self) -> str:
        """
        Validate template syntax and return detailed validation report
        
        Returns:
            Human-readable validation report
        """
        # For now, return a simple message since we removed the validation import
        return "✅ Template validation not available (validation module not found)"
    
    def _validate_template(self) -> None:
        """Perform template validation during initialization"""
        # Skip validation since we don't have the validation module
        pass
    
    def _set_formatter_context(self, section: Optional[FormatSection]) -> None:
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
        """
        # FIXED: Get field value correctly
        field_value = data.get(section.field_name)
        
        # Handle required fields - only check if field is actually missing
        if section.is_required and section.field_name not in data:
            raise RequiredFieldError(
                f"Required field '{section.field_name}' is missing",
                field_name=section.field_name,
                template=self.format_string
            )
        
        # FIXED: Handle missing data gracefully - check if field exists in data
        if section.field_name not in data:
            return ""  # Core feature: missing data causes section to disappear
        
        # Handle conditional sections through the formatter system
        if '?' in section.whole_section_formatting_tokens:
            # Apply conditional formatting first - this will return empty string if condition fails
            conditional_result = self._apply_section_formatting("", {'?': section.whole_section_formatting_tokens['?']}, field_value)
            if conditional_result == "":
                return ""  # Condition failed, hide entire section
        
        # Handle simple vs complex sections differently for performance
        if section.is_simple_section():
            return self._render_simple_section(section, field_value)
        else:
            return self._render_complex_section(section, field_value)
    
    def _render_simple_section(self, section: FormatSection, field_value: Any) -> str:
        """
        Render a simple section (just prefix + field + suffix with optional formatting)
        """
        # Build the basic text content
        text_content = section.get_text_content(field_value)
        
        # Apply any whole-section formatting
        if section.has_formatting():
            text_content = self._apply_section_formatting(text_content, section.whole_section_formatting_tokens, field_value)
        
        return text_content
    
    def _render_complex_section(self, section: FormatSection, field_value: Any) -> str:
        """
        Render a complex section with multiple formatted spans
        """
        # For now, fall back to simple rendering
        # Complex span rendering would be implemented here
        return self._render_simple_section(section, field_value)
    
    def _apply_section_formatting(self, text: str, formatting_tokens: Dict[str, List[str]], field_value: Any) -> str:
        """
        Apply formatting tokens to text content
        """
        if not formatting_tokens:
            return text
        
        # FIXED: Process each formatter family with proper error handling
        for token_prefix, token_list in formatting_tokens.items():
            if token_prefix in TOKEN_FORMATTERS:
                formatter = TOKEN_FORMATTERS[token_prefix]
                
                # CRITICAL FIX: Ensure formatter has the function registry
                if hasattr(formatter, 'function_registry') and not formatter.function_registry:
                    formatter.set_function_registry(self.config.functions)
                if hasattr(formatter, 'config') and not formatter.config:
                    formatter.set_config(self.config)
                
                # Parse all tokens for this family
                parsed_tokens = []
                for token in token_list:
                    try:
                        parsed_token = formatter.parse_token(token, field_value)
                        parsed_tokens.append(parsed_token)
                    except (FormatterError, FunctionExecutionError) as e:
                        if self.config.is_strict_mode():
                            raise
                        # In graceful mode, skip invalid tokens
                        continue
                    except Exception as e:
                        # Catch any other errors in graceful mode
                        if self.config.is_strict_mode():
                            raise FormatterError(f"Token parsing failed for '{token}': {e}")
                        continue
                
                # Apply formatting for this family
                if parsed_tokens:
                    try:
                        text = formatter.apply_formatting(text, parsed_tokens, self.config.output_mode)
                    except Exception as e:
                        if self.config.is_strict_mode():
                            raise FormatterError(f"Failed to apply {token_prefix} formatting: {e}")
                        # In graceful mode, return unformatted text but don't fail completely
                        continue
        
        return text


class DynamicLoggingFormatter(logging.Formatter):
    """
    Logging formatter using dynamic formatting templates
    
    Provides professional logging with automatic field handling and graceful
    degradation for missing log record fields.
    """
    
    def __init__(self, format_string: str, config: Optional[FormatterConfig] = None,
                 functions: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize logging formatter
        
        Args:
            format_string: Template string for log formatting
            config: Configuration object for the formatter
            functions: Custom functions for conditional logic
            **kwargs: Additional configuration parameters
        """
        # Don't call super().__init__() as we handle formatting ourselves
        
        # Create the dynamic formatter with graceful defaults for logging
        if config is None:
            config = FormatterConfig.production(**kwargs)
        
        self.formatter = DynamicFormatter(format_string, config=config, functions=functions)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record using the dynamic formatter
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted log message
        """
        try:
            # Convert log record to dictionary, including standard fields and extra fields
            record_dict = record.__dict__.copy()
            
            # Ensure standard logging fields are available
            standard_fields = {
                'name': record.name,
                'levelname': record.levelname,
                'levelno': record.levelno,
                'pathname': record.pathname,
                'filename': record.filename,
                'module': record.module,
                'lineno': record.lineno,
                'funcName': record.funcName,
                'created': record.created,
                'msecs': record.msecs,
                'relativeCreated': record.relativeCreated,
                'thread': record.thread,
                'threadName': record.threadName,
                'processName': record.processName,
                'process': record.process,
                'getMessage': record.getMessage(),
                'message': record.getMessage(),
            }
            
            # Merge standard fields with any extra fields
            record_dict.update(standard_fields)
            
            # Format using the dynamic formatter
            return self.formatter.format(**record_dict)
            
        except Exception as e:
            # Fallback to basic formatting if dynamic formatting fails
            fallback_msg = f"[FORMATTING ERROR: {e}] {record.getMessage()}"
            return fallback_msg