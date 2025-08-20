"""
Core dynamic formatting system with automatic missing data handling.

This module provides the main DynamicFormatter class and related functionality
for professional string formatting with graceful degradation.
"""

import logging
from typing import Dict, Any, Optional, Union, List
from pathlib import Path

from .config import FormatterConfig, ValidationMode, ValidationLevel
from .template_parser import TemplateParser, FormatSection
from .formatters import TOKEN_FORMATTERS, FormatterError, FunctionExecutionError


class DynamicFormattingError(Exception):
    """Base exception for dynamic formatting errors"""
    
    def __init__(self, message: str, template: Optional[str] = None, **kwargs):
        super().__init__(message)
        self.template = template
        for key, value in kwargs.items():
            setattr(self, key, value)


class RequiredFieldError(DynamicFormattingError):
    """Exception raised when a required field is missing"""
    
    def __init__(self, message: str, field_name: str, template: str):
        super().__init__(message, template=template)
        self.field_name = field_name
    
    def __str__(self):
        base_msg = super().__str__()
        if self.field_name.startswith('__pos_'):
            # This is a positional field
            pos_num = self.field_name.replace('__pos_', '').replace('__', '')
            context = f"Required field at position {int(pos_num) + 1} was marked as mandatory with '!' but no argument was provided"
        else:
            context = f"Required field '{self.field_name}' was marked as mandatory with '!' but no value was provided"
        
        return f"{base_msg}\nContext: {context}\nTemplate: '{self.template}'"


class FunctionNotFoundError(DynamicFormattingError):
    """Exception raised when a function is not found"""
    
    def __init__(self, message: str, function_name: str, template: str, available_functions: Optional[List[str]] = None):
        super().__init__(message, template=template)
        self.function_name = function_name
        self.available_functions = available_functions or []


class DynamicFormatter:
    """
    Advanced string formatter with automatic missing data handling.
    
    Core Features:
    - Automatic section removal for missing data (eliminates manual null checking)
    - Function fallback for dynamic formatting logic
    - Positional and keyword argument support
    - Configurable validation modes (strict/graceful/auto-correct)
    - Professional error context for debugging
    """
    
    def __init__(
        self,
        format_string: str,
        config: Optional[FormatterConfig] = None,
        # Legacy parameters for backward compatibility
        delimiter: Optional[str] = None,
        output_mode: Optional[str] = None,
        functions: Optional[Dict[str, Any]] = None,
        validate: Optional[bool] = None,
        validation_level: Optional[str] = None
    ):
        """
        Initialize DynamicFormatter
        
        Args:
            format_string: Template string with {{field}} placeholders
            config: FormatterConfig instance (preferred)
            delimiter: Field delimiter (legacy, use config instead)
            output_mode: Output mode (legacy, use config instead) 
            functions: Function registry (legacy, use config instead)
            validate: Enable validation (legacy, use config instead)
            validation_level: Validation level (legacy, use config instead)
        """
        # Configuration takes precedence
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
        
        # Parse template into sections
        parser = TemplateParser(self.config.delimiter, TOKEN_FORMATTERS)
        self.sections = parser.parse_format_string(format_string)
    
    @classmethod
    def from_config_file(cls, format_string: str, config_path: Union[str, Path]) -> 'DynamicFormatter':
        """
        Create DynamicFormatter instance from JSON configuration file
        
        Args:
            format_string: Template string to format
            config_path: Path to JSON configuration file
            
        Returns:
            DynamicFormatter instance with loaded configuration
        """
        config = FormatterConfig.from_config_file(config_path)
        return cls(format_string, config=config)
    
    @classmethod
    def from_config(cls, format_string: str, config: Union[FormatterConfig, Dict[str, Any], str, Path]) -> 'DynamicFormatter':
        """
        Create DynamicFormatter instance from various config sources
        
        Args:
            format_string: Template string to format
            config: Configuration as FormatterConfig, dict, or file path
            
        Returns:
            DynamicFormatter instance
        """
        if isinstance(config, FormatterConfig):
            return cls(format_string, config=config)
        elif isinstance(config, dict):
            formatter_config = FormatterConfig(**config)
            return cls(format_string, config=formatter_config)
        elif isinstance(config, (str, Path)):
            return cls.from_config_file(format_string, config)
        else:
            raise ValueError(f"Unsupported config type: {type(config)}")
    
    @classmethod
    def from_environment(cls, format_string: str, prefix: str = "FORMATTER") -> 'DynamicFormatter':
        """
        Create DynamicFormatter instance from environment variables
        
        Args:
            format_string: Template string to format
            prefix: Environment variable prefix
            
        Returns:
            DynamicFormatter instance with environment configuration
        """
        config = FormatterConfig.from_environment(prefix)
        return cls(format_string, config=config)
    
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
            
            # Map positional arguments to field names
            data = {}
            for i, arg in enumerate(args):
                if i < len(field_sections):
                    section = field_sections[i]
                    # Use the actual field name from the section
                    field_name = section.field_name if section.field_name else f"__pos_{i}__"
                    data[field_name] = arg
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
        # Get field value
        field_value = data.get(section.field_name)
        
        # Handle required fields - only check if field is actually missing
        if section.is_required and section.field_name not in data:
            raise RequiredFieldError(
                f"Required field '{section.field_name}' is missing",
                field_name=section.field_name,
                template=self.format_string
            )
        
        # Handle missing data gracefully
        if field_value is None and not section.is_required:
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
        
        # Process each formatter family
        for token_prefix, token_list in formatting_tokens.items():
            if token_prefix in TOKEN_FORMATTERS:
                formatter = TOKEN_FORMATTERS[token_prefix]
                
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
                
                # Apply formatting for this family
                if parsed_tokens:
                    text = formatter.apply_formatting(text, parsed_tokens, self.config.output_mode)
        
        return text


class DynamicLoggingFormatter(logging.Formatter):
    """
    Logging formatter using dynamic formatting templates
    
    Provides professional logging with automatic field handling and graceful
    degradation for missing log record fields.
    """
    
    def __init__(self, format_string: str, config: Optional[FormatterConfig] = None):
        """
        Initialize logging formatter
        
        Args:
            format_string: Dynamic formatting template
            config: FormatterConfig instance (defaults to graceful mode)
        """
        super().__init__()
        
        if config is None:
            # Use graceful configuration for logging to prevent crashes
            config = FormatterConfig(
                validation_mode=ValidationMode.GRACEFUL,
                validation_level=ValidationLevel.ERROR,
                enable_validation=False  # Skip validation for logging
            )
        
        self.formatter = DynamicFormatter(format_string, config=config)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record using dynamic formatting
        
        Args:
            record: LogRecord to format
            
        Returns:
            Formatted log message
        """
        try:
            # Convert log record to dictionary
            record_dict = vars(record).copy()
            
            # Add computed fields
            record_dict['message'] = record.getMessage()
            
            # Format using dynamic formatter
            return self.formatter.format(**record_dict)
            
        except Exception as e:
            # Fallback formatting if dynamic formatting fails
            fallback_msg = f"[FORMATTING ERROR: {e}] {record.getMessage()}"
            return fallback_msg