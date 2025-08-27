"""
Core template formatter implementation for StringSmith.

This module contains the main TemplateFormatter class which provides the primary 
public interface for StringSmith's conditional template formatting capabilities.
"""

from typing import Dict, Callable, Optional, List, Any

from .parser import TemplateParser
from ..tokens import create_token_handlers, TOKEN_REGISTRY, RESET_ANSI
from ..exceptions import StringSmithError, MissingMandatoryFieldError
from .inline_formatting import InlineFormatting
from .ast import TemplatePart, TemplateSection
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
        
        self.token_handlers = create_token_handlers(self.functions)

        self.sections = TemplateParser(delimiter, escape_char).parse_template(template)
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
            str_len = (len(section.prefix.content), 0, len(section.suffix.content))

            # Apply sectional formatting
            for tkn in section.section_formatting:
                self.sections[s] = self.token_handlers[tkn].apply_sectional_formatting(self.sections[s])
            
            section = self.sections[s]
            for p, part in enumerate(section.get_parts()):
                self._update_positions(part.inline_formatting, len(part.content) - str_len[p])
                self._bake_inline_formatting(part)

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
        
        get_var = self._set_up_variable_accessor(args, kwargs)
        result_parts = []
        
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
                self._apply_runtime_inline_formatting(new_section, field_value)
                if self._finalize_section(new_section, field_value):
                    print('add field value')
                    new_section.field.content += str(field_value)
                
                # Apply sectional formatting that requires runtime field values
                for tkn in new_section.section_formatting:
                    if not len(new_section.section_formatting[tkn]):
                        continue
                    handler = self.token_handlers[tkn]
                    new_section = handler.apply_sectional_formatting(new_section, field_value)
                
                # Add reset codes to parts with actual content    
                result_parts.append(self._assemble_section_with_resets(new_section))
        return ''.join(result_parts)
    
    def _apply_runtime_inline_formatting(self, section: TemplateSection, field_value: Any):
        """Apply runtime inline formatting to a template section."""
        for part in section.get_parts():
            for f in range(len(part.inline_formatting) - 1, -1, -1):
                fmt = part.inline_formatting[f]
                part.content, applied = self.token_handlers[fmt.type].apply_inline_formatting(
                    part.content,
                    fmt.position,
                    fmt.value,
                    field_value)
                if applied:
                    part.inline_formatting.pop(f)
                
    def _finalize_section(self, section: TemplateSection, field_value: Any) -> bool:
        add_suffix = True
        for f in TOKEN_REGISTRY:
            add_suffix = self.token_handlers[f].finalize(section, field_value) and add_suffix
        return add_suffix
    
    def _set_up_variable_accessor(self, args, kwargs):
        """Create variable accessor function based on argument type."""
        if args:
            arg_index = 0
            def get_var(field_name=None):
                nonlocal arg_index
                if arg_index >= len(args):
                    return None
                arg = args[arg_index]
                arg_index += 1
                return arg
            return get_var
        else:
            def get_var(field_name):
                return None if field_name == '' else kwargs.get(field_name)
            return get_var

    def _assemble_section_with_resets(self, section: TemplateSection):
        """Assemble section parts with proper reset codes between formatted parts."""
        result = ''
        for part in section.get_parts():
            if has_non_ansi(part.content):
                part.content += RESET_ANSI
            else:
                part.content = ''
            result += part.content
            
        return result
    
    def get_template_info(self) -> Dict[str, any]:
        """
        Get information about this template's structure.
        
        Returns:
            Dict[str, any]: Template metadata and structure information.
            
        Examples:
            >>> formatter = TemplateFormatter("{{#red;Error: ;message;}}")
            >>> info = formatter.get_template_info()
            >>> info['field_count']
            1
            >>> info['has_formatting']
            True
        """
        field_sections = [s for s in self.sections if s.field_name is not None]
        
        return {
            'template': self.template,
            'total_sections': len(self.sections),
            'field_count': len(field_sections),
            'literal_sections': len(self.sections) - len(field_sections),
            'mandatory_fields': [s.field_name for s in field_sections if s.is_mandatory],
            'optional_fields': [s.field_name for s in field_sections if not s.is_mandatory],
            'has_formatting': any(s.section_formatting for s in field_sections),
            'has_inline_formatting': any(
                part.inline_formatting 
                for s in field_sections 
                for part in s.get_parts() 
                if part is not None
            ),
            'delimiter': self.delimiter,
            'escape_char': self.escape_char,
            'custom_functions': list(self.functions.keys())
        }