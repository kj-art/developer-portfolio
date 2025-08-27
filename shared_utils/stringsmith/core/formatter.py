"""
Core template formatter implementation for StringSmith.

This module contains the main TemplateFormatter class which provides the primary 
public interface for StringSmith's conditional template formatting capabilities.
"""

from typing import Dict, Callable, Optional, List

from .parser import TemplateParser
from ..tokens import create_token_handlers, TOKEN_REGISTRY
from ..exceptions import StringSmithError, MissingMandatoryFieldError
from .inline_formatting import InlineFormatting
from .ast import TemplatePart
from ..utils import has_non_ansi


class TemplateFormatter:
    """
    Advanced template formatter with conditional sections and rich formatting.
    
    TemplateFormatter is the main public API for StringSmith's conditional template
    formatting capabilities. It provides f-string-like functionality with conditional
    sections that automatically disappear when variables are missing, plus rich 
    formatting options including colors and text emphasis.
    
    Core Features:
        - **Conditional Sections**: Sections disappear when variables are missing
        - **Mandatory Validation**: Required fields (prefixed with '!') enforce data presence
        - **Rich Formatting**: ANSI colors, text emphasis, and custom styling functions  
        - **Custom Functions**: User-defined functions for formatting and conditionals
        - **Flexible Arguments**: Support for both positional and keyword arguments
        - **Performance Optimized**: Template parsing done once, formatting is fast
        - **Thread Safe**: Immutable after creation, safe for concurrent use
    
    Template Syntax:
        Templates use double-brace sections with optional formatting and delimiters:
        
        Basic syntax: {{field_name}}
        With prefix/suffix: {{prefix;field_name;suffix}}  
        With formatting: {{#color@emphasis;prefix;field_name;suffix}}
        Mandatory fields: {{!field_name}} (throws error if missing)
        Positional args: {{}} (uses positional arguments in order)
        
        Formatting tokens:
        - #color: Apply color (red, blue, #FF0000, or custom function)
        - @emphasis: Apply text styling (bold, italic, underline, etc.)
        - ?function: Apply conditional function (section appears only if function returns True)
    
    Examples:
        Basic conditional sections:
        >>> formatter = TemplateFormatter("{{Hello ;name;}}")
        >>> formatter.format(name="World")  # "Hello World"
        >>> formatter.format()              # "" (section disappears)
        
        Rich formatting with colors and emphasis:
        >>> formatter = TemplateFormatter("{{#red@bold;ERROR: ;message;}}")
        >>> formatter.format(message="Failed")  # Red bold "ERROR: Failed"
        
        Custom functions for dynamic behavior:
        >>> def priority_color(level):
        ...     return 'red' if int(level) > 5 else 'yellow'
        >>> formatter = TemplateFormatter(
        ...     "{{#priority_color;Level ;priority;: ;message;}}", 
        ...     functions={'priority_color': priority_color}
        ... )
        >>> formatter.format(priority=8, message="Critical")  # Red "Level 8: Critical"
        
        Mandatory fields with validation:
        >>> formatter = TemplateFormatter("{{!name}} is required")
        >>> formatter.format(name="Alice")  # "Alice is required"  
        >>> formatter.format()  # Raises MissingMandatoryFieldError
        
        Positional arguments:
        >>> formatter = TemplateFormatter("{{}} + {{}} = {{}}")
        >>> formatter.format("15", "27", "42")  # "15 + 27 = 42"
    
    Performance Notes:
        - Template parsing is front-loaded during initialization for faster formatting
        - Format operations are O(m) where m is the number of template sections
        - Recommended to create formatters once and reuse for multiple format operations
    """
    
    def __init__(self, 
                 template: str, 
                 delimiter: str = ';', 
                 escape_char: str = '\\', 
                 functions: Optional[Dict[str, Callable]] = None):
        """
        Initialize a template formatter with conditional sections and rich formatting.
        
        Templates are "baked" during initialization - formatting tokens are parsed,
        validated, and cached for optimal runtime performance. Invalid colors/emphasis 
        styles are caught at creation time rather than during formatting operations.
        
        Args:
            template (str): Template string using {{}} sections for conditional content.
            delimiter (str, optional): Character(s) separating parts within sections. 
                                     Defaults to ';'.
            escape_char (str, optional): Character(s) for escaping special sequences.
                                       Defaults to '\\'.
            functions (Dict[str, Callable], optional): Custom functions for formatting
                                                     and conditionals.
        
        Raises:
            StringSmithError: If template contains invalid formatting tokens or syntax errors.
            ParseError: If template structure is malformed or contains unsupported constructs.
        """
        self.template = template
        self.delimiter = delimiter
        self.escape_char = escape_char
        self.functions = functions or {}
        
        self.parser = TemplateParser(delimiter, escape_char)
        self.token_handlers = create_token_handlers(self.functions)
        
        self.sections = self.parser.parse_template(template)
        self._bake_template()
        
    def _update_positions(self, format_list: List[InlineFormatting], offset: int):
        """Update position information for inline formatting tokens after text changes."""
        for fmt in format_list:
            fmt.adjust_position(offset)

    def _bake_template(self, *args, **kwargs) -> str:
        """
        Pre-process template sections for optimal runtime performance.
        
        The "baking" process applies all possible formatting operations that don't
        depend on runtime data, including token validation, ANSI code generation,
        and position management.
        """
        for s, section in enumerate(self.sections):
            # Skip literal text sections (no formatting to bake)
            if section.suffix == None:
                continue
            
            # Clear field content for clean formatting application
            section.field.content = ''
            str_len = (len(section.prefix.content), len(section.suffix.content))

            # Apply sectional formatting
            for tkn in section.section_formatting:
                self.sections[s] = self.token_handlers[tkn].apply_sectional_formatting(self.sections[s])
            
            section = self.sections[s]

            # Update inline formatting positions after sectional formatting changes
            self._update_positions(section.prefix.inline_formatting, len(section.prefix.content) - str_len[0])
            self._update_positions(section.field.inline_formatting, len(section.field.content))
            self._update_positions(section.suffix.inline_formatting, len(section.suffix.content) - str_len[1])
            
            # Apply inline formatting that can be baked
            self._bake_inline_formatting(section.prefix)
            self._bake_inline_formatting(section.field)
            self._bake_inline_formatting(section.suffix)

    def _bake_inline_formatting(self, template_part: TemplatePart):
        """Apply inline formatting tokens that don't require runtime data."""
        for f in range(len(template_part.inline_formatting) - 1, -1 , -1):
            fmt = template_part.inline_formatting[f]
            str_len = len(template_part.content)
            template_part.content, replaced = self.token_handlers[fmt.type].apply_inline_formatting(template_part.content,
                                                                                                        fmt.position,
                                                                                                        fmt.value
                                                                                                        )
            if replaced:
                template_part.inline_formatting.pop(f)
                self._update_positions(template_part.inline_formatting[f:], len(template_part.content) - str_len)

    def format(self, *args, **kwargs) -> str:
        """
        Format template with provided variables using conditional section logic.
        
        Core behavior: Sections automatically disappear when their field variables
        are missing, eliminating manual null checking and conditional string building.
        Mandatory sections (prefixed with '!') throw errors when variables are missing.
        
        Args:
            *args: Positional arguments mapped to template fields in order.
            **kwargs: Keyword arguments mapped to template fields by name.
            
        Returns:
            str: Formatted string with missing data sections omitted.
        
        Raises:
            StringSmithError: If positional and keyword arguments are mixed.
            MissingMandatoryFieldError: If mandatory field (marked with '!') is missing.
            
        Examples:
            >>> formatter = TemplateFormatter("{{User: ;username;}} {{(ID: ;user_id;)}}")
            >>> formatter.format(username="admin")      # "User: admin "
            >>> formatter.format(user_id=123)          # " (ID: 123)"
            >>> formatter.format()                     # ""
            
            >>> formatter = TemplateFormatter("{{}} + {{}} = {{}}")
            >>> formatter.format("15", "27", "42")     # "15 + 27 = 42"
            
            >>> formatter = TemplateFormatter("{{!name}} logged in")
            >>> formatter.format(name="admin")         # "admin logged in"
            >>> formatter.format()                     # Raises MissingMandatoryFieldError
        """
        if args and kwargs:
            raise StringSmithError('Cannot mix positional and keyword arguments')
        
        # Set up variable access function based on argument type
        if args:
            arg_index = 0
            def get_var(field_name=None):
                nonlocal arg_index
                if arg_index >= len(args):
                    return None
                arg = args[arg_index]
                arg_index += 1
                return arg
        else:
            def get_var(field_name):
                return None if field_name == '' else kwargs.get(field_name)

        result_parts = []
        reset_ansi = ''

        # Build combined reset code from all token handlers
        for token in TOKEN_REGISTRY:
            reset_ansi += self.token_handlers[token].get_reset_ansi()
        
        # Process each template section
        for section in self.sections:
            if section.field_name is None:
                # Literal text section
                result_parts.append(section.prefix.content)
                continue
            else:
                field_value = get_var(section.field_name)
                if field_value is None: # no value provided for this section's field - skip this section
                    if section.is_mandatory:
                        raise MissingMandatoryFieldError(f"Required field '{section.field_name}' not provided")
                    continue  # Skip optional sections with missing data
                
                # Create working copy for this formatting operation
                new_section = section.copy()

                # Apply runtime inline formatting
                for f in range(len(section.prefix.inline_formatting) - 1, -1, -1):
                    fmt = section.prefix.inline_formatting[f]
                    new_section.prefix.content, *_ = self.token_handlers[fmt.type].apply_inline_formatting(
                        new_section.prefix.content,
                        fmt.position,
                        fmt.value,
                        field_value)
                for f in range(len(section.field.inline_formatting) - 1, -1, -1):
                    fmt = section.field.inline_formatting[f]
                    new_section.field.content, *_ = self.token_handlers[fmt.type].apply_inline_formatting(
                        new_section.field.content,
                        fmt.position,
                        fmt.value,
                        field_value)
                for f in range(len(section.suffix.inline_formatting) - 1, -1, -1):
                    fmt = section.suffix.inline_formatting[f]
                    new_section.suffix.content, *_ = self.token_handlers[fmt.type].apply_inline_formatting(
                        new_section.suffix.content,
                        fmt.position,
                        fmt.value,
                        field_value)
                    
                # Finalize each part through all token handlers
                for f in TOKEN_REGISTRY:
                    handler = self.token_handlers[f]
                    new_section.prefix.content = handler.finalize(new_section.prefix, field_value)
                    new_section.field.content = handler.finalize(new_section.field, field_value)
                    new_section.suffix.content = handler.finalize(new_section.suffix, field_value)
                
                # Add actual field value
                new_section.field.content += str(field_value)
                
                # Apply sectional formatting that requires runtime field values
                for tkn in new_section.section_formatting:
                    if not len(new_section.section_formatting[tkn]):
                        continue
                    handler = self.token_handlers[tkn]
                    new_section = handler.apply_sectional_formatting(new_section, field_value)
                
                # Add reset codes to parts with actual content
                if has_non_ansi(new_section.prefix.content):
                    new_section.prefix.content += reset_ansi
                else:
                    new_section.prefix.content = ''
                if has_non_ansi(new_section.field.content):
                    new_section.field.content += reset_ansi
                else:
                    new_section.field.content = ''
                if has_non_ansi(new_section.suffix.content):
                    new_section.suffix.content += reset_ansi
                else:
                    new_section.suffix.content = ''    
                result_parts.append(
                    new_section.prefix.content + 
                    new_section.field.content +  
                    new_section.suffix.content
                )
        return ''.join(result_parts)
    
    def apply_inline_formatting(self, text_segment: str, formatting: List[InlineFormatting], field_value: str):
        """Apply a list of inline formatting tokens to a text segment."""
        for f in range(len(formatting) - 1, -1, -1):
            fmt = formatting[f]
            text_segment = self.token_handlers[fmt.type].apply_inline_formatting(text_segment, fmt.position, fmt.value, field_value)

        return text_segment