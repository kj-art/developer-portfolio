"""
Core template formatter implementation.
"""

import re
from typing import Dict, Callable, Any, Optional, Union, List, Tuple

# Handle both relative and absolute imports
try:
    from .parsing import TemplateParser
    from .formatting import FormatApplier
    from .token_handlers import create_token_handlers, ConditionalTokenHandler
    from .exceptions import StringSmithError, MissingMandatoryFieldError
except ImportError:
    from parsing import TemplateParser
    from formatting import FormatApplier
    from token_handlers import create_token_handlers, ConditionalTokenHandler
    from exceptions import StringSmithError, MissingMandatoryFieldError


class TemplateFormatter:
    """
    Advanced template formatter with conditional sections and rich formatting.
    
    Supports:
    - Conditional sections that disappear when variables are missing
    - Mandatory sections that throw errors when variables are missing
    - Color formatting using matplotlib colors or hex codes
    - Text emphasis (bold, italic, strikethrough, etc.)
    - Custom formatting functions
    - Boolean conditional functions
    - Inline formatting within sections
    - Both positional and keyword arguments (but not mixed)
    """
    
    def __init__(self, template: str, delimiter: str = ";", escape_char: str = "\\", functions: Optional[Dict[str, Callable]] = None):
        """
        Initialize the template formatter.
        
        Args:
            template: Template string with {{}} sections
            delimiter: Character to separate parts within sections (default: ";")
            escape_char: Character used for escaping special characters (default: "\\")
            functions: Optional dictionary of custom functions for formatting and conditionals
        """
        self.template = template
        self.delimiter = delimiter
        self.escape_char = escape_char
        self.functions = functions or {}
        
        self.parser = TemplateParser(delimiter, escape_char)
        self.format_applier = FormatApplier(self.functions)
        self.token_handlers = create_token_handlers(self.functions)
        
        # Parse the template once at initialization
        self.sections = self.parser.parse_template(template)
    
    def format(self, *args, **kwargs) -> str:
        """
        Format the template with provided variables.
        
        Args:
            *args: Positional arguments (cannot be mixed with kwargs)
            **kwargs: Keyword arguments (cannot be mixed with args)
            
        Returns:
            Formatted string with conditional sections applied
            
        Raises:
            StringSmithError: If args and kwargs are mixed
            MissingMandatoryFieldError: If mandatory fields are missing
        """
        if args and kwargs:
            raise StringSmithError("Cannot mix positional and keyword arguments")
        
        # Convert positional args to synthetic field names
        if args:
            variables = {f"__pos_{i}__": arg for i, arg in enumerate(args)}
            using_positional = True
        else:
            variables = kwargs
            using_positional = False
        
        result_parts = []
        
        for section in self.sections:
            try:
                section_result = self._format_section(section, variables, using_positional)
                if section_result is not None:
                    result_parts.append(section_result)
            except MissingMandatoryFieldError as e:
                # Re-raise with better error message for positional args
                if not kwargs and not section.field_name.startswith("__pos_"):
                    # Count variable sections before this one to get the position
                    pos_index = 0
                    for s in self.sections:
                        if s is section:
                            break
                        if s.field_name:  # Only count sections with field names
                            pos_index += 1
                    raise MissingMandatoryFieldError(f"Required positional argument {pos_index} not provided")
                raise
        
        return "".join(result_parts)
    
    def _format_section(self, section, variables: Dict[str, Any], using_positional: bool = False) -> Optional[str]:
        """
        Format a single section.
        
        Returns None if the section should be omitted.
        """
        # Handle literal text sections (no field name)
        if not section.field_name:
            # This is a literal text section, just return the prefix content
            if section.prefix:
                return section.prefix.content
            return ""
        
        # For positional arguments, map field names to positional indices
        field_name = section.field_name
        if using_positional and field_name and not field_name.startswith("__pos_"):
            # We need to figure out which positional argument this corresponds to
            # Count how many variable sections we've seen so far
            section_index = 0
            for s in self.sections:
                if s is section:
                    break
                if s.field_name and not s.field_name.startswith("__pos_"):
                    section_index += 1
            field_name = f"__pos_{section_index}__"
        
        # Get the field value
        field_value = variables.get(field_name)
        
        # Handle missing field
        if field_value is None:
            if section.is_mandatory:
                raise MissingMandatoryFieldError(f"Required field '{field_name}' not provided")
            return None  # Omit optional sections with missing fields
        
        # Check section-level boolean condition
        if section.section_condition:
            try:
                condition_result = self._evaluate_function(section.section_condition, field_value)
                if not condition_result:
                    return None  # Omit section if condition fails
            except Exception as e:
                raise StringSmithError(f"Error evaluating section condition '{section.section_condition}': {e}")
        
        # Build the section content with proper inline formatting
        parts = []
        
        # Add prefix if present
        if section.prefix is not None and section.prefix.content:
            formatted_prefix = self._format_part_with_inline_content(section.prefix, section.prefix.content, field_value, section.section_formatting)
            if formatted_prefix is not None:
                parts.append(formatted_prefix)
        
        # Add field value
        field_str = str(field_value)
        # Apply section formatting to field (inline formatting on field part not common but possible)
        if section.field_part.inline_formatting:
            formatted_field = self._format_part_with_inline_content(section.field_part, field_str, field_value, section.section_formatting)
        else:
            formatted_field = self.format_applier.apply_formatting(field_str, section.section_formatting)
        parts.append(formatted_field)
        
        # Add suffix if present
        if section.suffix is not None and section.suffix.content:
            formatted_suffix = self._format_part_with_inline_content(section.suffix, section.suffix.content, field_value, section.section_formatting)
            if formatted_suffix is not None:
                parts.append(formatted_suffix)
        
        return "".join(parts)
    
    def _format_part_with_inline_content(self, part, content: str, field_value: Any, section_formatting: List[str]) -> str:
        """Format content with inline formatting applied using token handlers."""
        if not part.inline_formatting:
            # No inline formatting, just apply section formatting
            return self.format_applier.apply_formatting(content, section_formatting)
        
        # Start with section-level formatting
        current_formatting = section_formatting[:]
        result_parts = []
        
        # Process inline formatting
        i = 0
        text = content
        
        for inline_format in part.inline_formatting:
            # Add text before this formatting change
            if i < inline_format.position:
                text_segment = text[i:inline_format.position]
                if text_segment:
                    # Check if we should show this text based on conditionals
                    conditional_handler = self.token_handlers['condition']
                    if isinstance(conditional_handler, ConditionalTokenHandler):
                        if conditional_handler.should_show_text(current_formatting):
                            formatted_segment = self.format_applier.apply_formatting(text_segment, current_formatting)
                            result_parts.append(formatted_segment)
                i = inline_format.position
            
            # Handle the inline formatting change using token handlers
            if inline_format.type in self.token_handlers:
                handler = self.token_handlers[inline_format.type]
                try:
                    current_formatting = handler.handle_token(inline_format.value, current_formatting, field_value)
                    
                    # Special handling for conditionals - if they say hide, skip the rest
                    if inline_format.type == "condition":
                        conditional_handler = self.token_handlers['condition']
                        if isinstance(conditional_handler, ConditionalTokenHandler):
                            if not conditional_handler.should_show_text(current_formatting):
                                # Skip the rest of this part
                                break
                except Exception as e:
                    raise StringSmithError(f"Error handling inline {inline_format.type} token '{inline_format.value}': {e}")
        
        # Add remaining text
        if i < len(text):
            remaining_text = text[i:]
            if remaining_text:
                # Check if we should show this text based on conditionals
                conditional_handler = self.token_handlers['condition']
                if isinstance(conditional_handler, ConditionalTokenHandler):
                    if conditional_handler.should_show_text(current_formatting):
                        formatted_segment = self.format_applier.apply_formatting(remaining_text, current_formatting)
                        result_parts.append(formatted_segment)
        
        return "".join(result_parts)
    
    def _evaluate_function(self, function_name: str, field_value: Any) -> Any:
        """
        Evaluate a custom function with the field value.
        """
        if function_name not in self.functions:
            raise StringSmithError(f"Unknown function: {function_name}")
        
        func = self.functions[function_name]
        return func(field_value)