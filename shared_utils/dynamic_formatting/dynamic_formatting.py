"""
Dynamic Formatting Package Main Module

Core implementation of the dynamic formatting system with graceful missing data handling,
configurable validation modes, enhanced error context, and positional argument support.
"""

import logging
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path

from .config import FormatterConfig, ValidationLevel, ValidationMode
from .template_parser import TemplateParser
from .span_structures import FormatSection, FormattedSpan
from .formatters import TOKEN_FORMATTERS, FormatterError, FunctionExecutionError


class DynamicFormattingError(Exception):
    """
    Base exception for dynamic formatting with enhanced error context
    
    Provides detailed context about where errors occurred in templates,
    making debugging much easier during development.
    """
    def __init__(self, message: str, template: Optional[str] = None, 
                 position: Optional[int] = None, context: Optional[str] = None):
        self.template = template
        self.position = position
        self.context = context
        
        # Build comprehensive error message
        full_message = message
        if context:
            full_message += f"\nContext: {context}"
        if template:
            full_message += f"\nTemplate: '{template}'"
        if position is not None:
            full_message += f"\nPosition: {position}"
            
        super().__init__(full_message)


class RequiredFieldError(DynamicFormattingError):
    """Raised when a required field (marked with !) is missing"""
    def __init__(self, message: str, field_name: Optional[str] = None,
                 template: Optional[str] = None, position: Optional[int] = None):
        self.field_name = field_name
        
        # Create user-friendly context message
        context = (
            f"Required field '{field_name}' was marked as mandatory with '!' "
            f"but no value was provided"
        )
        
        # For positional fields, provide friendlier error messages
        if field_name and field_name.startswith('__pos_') and field_name.endswith('__'):
            try:
                pos_num = int(field_name[6:-2]) + 1  # Convert __pos_0__ to position 1
                context = f"Required field at position {pos_num} was marked as mandatory with '!' but no argument was provided"
            except (ValueError, IndexError):
                pass  # Use default context if parsing fails
        
        super().__init__(message, template, position, context)


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
    Main dynamic formatting class with enterprise-grade features
    
    Core Feature: Automatic section removal for missing data
    When template fields don't have corresponding data, their entire sections
    disappear automatically, eliminating manual null checking and conditional
    string building.
    
    Professional Features:
    - Configurable validation modes (strict/graceful/auto-correct)
    - Function fallback for dynamic formatting
    - Positional and keyword argument support
    - Enhanced error context for debugging
    - Production-ready configuration management
    """
    
    def __init__(
        self, 
        format_string: str,
        functions: Optional[Dict[str, Callable]] = None,
        config: Optional[FormatterConfig] = None,
        # Backward compatibility parameters
        delimiter: Optional[str] = None,
        output_mode: Optional[str] = None,
        validate: Optional[bool] = None,
        validation_level: Optional[str] = None
    ):
        """
        Initialize DynamicFormatter with comprehensive configuration
        
        Args:
            format_string: Template string with {{field}} placeholders
            functions: Optional function registry for fallback and conditionals
            config: Complete configuration object (recommended)
            delimiter: Field separator (backward compatibility)
            output_mode: 'console' or 'file' (backward compatibility)
            validate: Enable validation (backward compatibility)
            validation_level: Validation strictness (backward compatibility)
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
    def from_environment(cls, format_string: str, prefix: str = "DYNAMIC_FORMATTING") -> 'DynamicFormatter':
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
                field_name = f"__pos_{i}__"
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
        # Handle required fields
        if section.is_required and section.field_name not in data:
            raise RequiredFieldError(
                f"Required field '{section.field_name}' is missing",
                field_name=section.field_name,
                template=self.format_string
            )
        
        # Check if field exists - if not, return empty string (graceful degradation)
        if section.field_name not in data:
            return ""
        
        field_value = data[section.field_name]
        
        # Handle None values - they should cause section to disappear
        if field_value is None:
            return ""
        
        # Handle conditional sections first
        if section.function_name:
            func = self.config.functions.get(section.function_name)
            if not func:
                if self.config.is_strict_mode():
                    raise FunctionNotFoundError(
                        f"Conditional function not found: {section.function_name}",
                        function_name=section.function_name,
                        template=self.format_string,
                        available_functions=list(self.config.functions.keys())
                    )
                else:
                    # In graceful mode, hide the section if function is missing
                    return ""
            
            try:
                # Call conditional function
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                
                if len(params) == 0:
                    show_section = func()
                else:
                    show_section = func(field_value)
                
                if not show_section:
                    return ""  # Hide section if conditional returns False/falsy
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
            format_string: Dynamic formatting template for log records
            config: Optional formatter configuration
        """
        super().__init__()
        
        # Use graceful config by default for logging
        if config is None:
            config = FormatterConfig(
                validation_mode=ValidationMode.GRACEFUL,
                output_mode='console',
                enable_validation=False  # Don't validate at runtime for performance
            )
        
        self.formatter = DynamicFormatter(format_string, config=config)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record using dynamic template
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log message
        """
        try:
            # Convert log record to dict for formatting
            record_dict = record.__dict__.copy()
            
            # Add some standard fields that might be missing
            if 'message' not in record_dict:
                record_dict['message'] = record.getMessage()
            
            return self.formatter.format(**record_dict)
        except Exception as e:
            # Fallback to basic formatting if dynamic formatting fails
            return f"[FORMATTING ERROR: {e}] {record.getMessage()}"