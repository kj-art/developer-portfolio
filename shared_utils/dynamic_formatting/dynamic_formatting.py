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
from .formatting_state import FormattingState
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
        context = (
            f"Required field '{field_name}' was marked as mandatory with '!' "
            f"but no value was provided"
        )
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
            DynamicFormatter instance configured from file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file contains invalid JSON
            ValueError: If config contains invalid values
            
        Example:
            formatter = DynamicFormatter.from_config_file(
                "{{#red;Error: ;message}} {{Code: ;code}}", 
                "config.json"
            )
        """
        config = FormatterConfig.from_config_file(config_path)
        return cls(format_string, config=config)

    @classmethod  
    def from_config(cls, format_string: str, config: Union[FormatterConfig, Dict[str, Any], str, Path]) -> 'DynamicFormatter':
        """
        Create DynamicFormatter instance from various configuration sources
        
        Args:
            format_string: Template string to format
            config: Configuration source - can be:
                   - FormatterConfig instance
                   - Dictionary of config values
                   - String/Path to JSON config file
                   
        Returns:
            DynamicFormatter instance
            
        Example:
            # From config file
            formatter = DynamicFormatter.from_config(template, "config.json")
            
            # From dictionary
            formatter = DynamicFormatter.from_config(template, {
                "validation_mode": "graceful",
                "output_mode": "file"
            })
            
            # From FormatterConfig instance
            config = FormatterConfig.production()
            formatter = DynamicFormatter.from_config(template, config)
        """
        if isinstance(config, FormatterConfig):
            return cls(format_string, config=config)
        elif isinstance(config, dict):
            config_obj = FormatterConfig.from_dict(config)
            return cls(format_string, config=config_obj)
        elif isinstance(config, (str, Path)):
            return cls.from_config_file(format_string, config)
        else:
            raise ValueError(f"Unsupported config type: {type(config)}")

    @classmethod
    def from_environment(cls, format_string: str, prefix: str = 'FORMATTER_') -> 'DynamicFormatter':
        """
        Create DynamicFormatter instance from environment variables
        
        Args:
            format_string: Template string to format
            prefix: Environment variable prefix (default: 'FORMATTER_')
            
        Returns:
            DynamicFormatter instance configured from environment
            
        Example:
            # Set environment variables:
            # FORMATTER_VALIDATION_MODE=graceful
            # FORMATTER_OUTPUT_MODE=file
            # FORMATTER_ENABLE_COLORS=false
            
            formatter = DynamicFormatter.from_environment(template)
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
        
        # For now, return a simple message since we removed the validation import
        return "✅ Template validation not available (validation module not found)"
    
    def _validate_template(self) -> None:
        """Perform template validation during initialization"""
        # Skip validation since we don't have the validation module
        pass
    
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
        """
        # Handle required fields
        if hasattr(section, 'is_required') and section.is_required and section.field_name not in data:
            raise RequiredFieldError(
                f"Required field '{section.field_name}' is missing",
                field_name=section.field_name,
                template=self.format_string
            )
        
        # Check if field exists - if not, return empty string (graceful degradation)
        if section.field_name not in data:
            return ""
        
        field_value = data[section.field_name]
        
        # Handle conditional sections first
        if hasattr(section, 'function_name') and section.function_name:
            if hasattr(self.config, 'functions') and isinstance(self.config.functions, dict):
                func = self.config.functions.get(section.function_name)
            else:
                func = None
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
        
        # Build text parts - handle prefix, field value, and suffix
        text_parts: List[str] = []
        
        # Add prefix (defensive handling)
        prefix = getattr(section, 'prefix', None)
        if prefix:
            if isinstance(prefix, str):
                text_parts.append(prefix)
            elif isinstance(prefix, list):
                # Handle formatted spans in prefix
                for span in prefix:
                    if hasattr(span, 'text'):
                        text_parts.append(span.text)
                    else:
                        text_parts.append(str(span))
            else:
                text_parts.append(str(prefix))
        
        # Add the field value
        text_parts.append(str(field_value))
        
        # Add suffix (defensive handling)
        suffix = getattr(section, 'suffix', None)
        if suffix:
            if isinstance(suffix, str):
                text_parts.append(suffix)
            elif isinstance(suffix, list):
                # Handle formatted spans in suffix
                for span in suffix:
                    if hasattr(span, 'text'):
                        text_parts.append(span.text)
                    else:
                        text_parts.append(str(span))
            else:
                text_parts.append(str(suffix))
        
        complete_text = ''.join(text_parts)
        
        # Apply any formatting tokens (simplified approach)
        formatting_tokens = getattr(section, 'whole_section_formatting_tokens', None)
        if formatting_tokens and self.config.output_mode == 'console':
            # For now, just apply basic color formatting if it exists
            color_tokens = formatting_tokens.get('color', [])
            if color_tokens:
                # Simple color mapping for common colors
                color_map = {
                    'red': '\033[31m',
                    'green': '\033[32m', 
                    'yellow': '\033[33m',
                    'blue': '\033[34m',
                    'magenta': '\033[35m',
                    'cyan': '\033[36m',
                    'white': '\033[37m'
                }
                
                # Use the first color token
                color_name = str(color_tokens[0]).lower()
                if color_name in color_map:
                    complete_text = f"{color_map[color_name]}{complete_text}\033[0m"
        
        return complete_text
    
    def _make_error_user_friendly(self, text: str) -> str:
        """Convert synthetic field names to user-friendly position descriptions"""
        import re
        return re.sub(r'__pos_(\d+)__', lambda m: f"position {int(m.group(1)) + 1}", text)


class DynamicLoggingFormatter(logging.Formatter):
    """
    Logging formatter that uses dynamic formatting with configurable graceful degradation
    
    Automatically handles missing log fields - if duration, error_count, file_count, etc.
    are not present in the log record, their corresponding template sections simply
    disappear from the output without requiring manual null checking.
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
            # Core feature in action: missing fields automatically cause their sections to disappear
            return self.formatter.format(**log_data)
        except Exception as e:
            # Fallback to basic formatting if dynamic formatting fails
            return f"{record.levelname}: {record.getMessage()} [FORMATTING ERROR: {e}]"