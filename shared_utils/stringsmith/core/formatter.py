"""
Core template formatter implementation for StringSmith.

This module contains the main TemplateFormatter class which provides the primary 
public interface for StringSmith's conditional template formatting capabilities.
"""

from typing import Dict, Callable, Optional, List, Any

from .parser import TemplateParser
from ..tokens import create_token_handlers, RESET_ANSI
from ..exceptions import StringSmithError, MissingMandatoryFieldError
from .ast import TemplateSection
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
        
        self.token_handlers = create_token_handlers(escape_char, self.functions)
        self.parser = TemplateParser(delimiter, escape_char)
        self.sections = self.parser.parse_template(template)
        self._bake_template()

    def _bake_template(self, *args, **kwargs) -> str:
        """
        Pre-process template sections for optimal runtime performance.
        
        "Baking" applies all formatting operations that don't require runtime data,
        including token validation and static ANSI code generation. Inline token
        parsing is deferred to format() to avoid complex position management during
        this phase. Invalid formatting tokens are caught here rather than at runtime.
        
        Design Note: This approach trades some repeated parsing work for significantly
        simpler implementation and better maintainability.
        """
        for s, section in enumerate(self.sections):
            # Skip literal text sections (no formatting to bake)
            if section.parts.suffix == None:
                continue
            
            # Apply formatting
            for handler in self.token_handlers.values():
                self.sections[s] = handler.apply_sectional_formatting(section)
                handler.apply_inline_formatting(section.parts)
    
    def format(self, *args, **kwargs) -> str:
        """
        Format template with provided variables using conditional section logic.
        
        Core behavior: Sections automatically disappear when their field variables
        are missing, eliminating manual null checking and conditional string building.
        Mandatory sections (prefixed with '!') throw errors when variables are missing.
        
        Multi-Parameter Function Support:
            Custom functions can access multiple field values through parameter name matching.
            Function parameters with names matching format() arguments receive those values.
            Functions with no matching parameters fall back to receiving the section's field value.
        
        Args:
            *args: Positional arguments mapped to template fields in order.
            **kwargs: Keyword arguments mapped to template fields by name.
            
        Returns:
            str: Formatted string with missing data sections omitted.
        
        Raises:
            StringSmithError: If positional and keyword arguments are mixed.
            MissingMandatoryFieldError: If mandatory field (marked with '!') is missing.
            
        Examples:
            Basic conditional sections:
            >>> formatter = TemplateFormatter("{{User: ;username;}} {{(ID: ;user_id;)}}")
            >>> formatter.format(username="admin")      # "User: admin "
            >>> formatter.format(user_id=123)          # " (ID: 123)"
            >>> formatter.format()                     # ""
            
            Multi-parameter functions:
            >>> def is_profitable(revenue, costs):
            ...     return float(revenue) > float(costs)
            >>> formatter = TemplateFormatter("{{?is_profitable; ✓ Profitable;revenue;}}", 
            ...                             functions={'is_profitable': is_profitable})
            >>> formatter.format(revenue="150", costs="100")  # " ✓ Profitable"
            >>> formatter.format(revenue="50", costs="100")   # ""
            
            Positional arguments:
            >>> formatter = TemplateFormatter("{{}} + {{}} = {{}}")
            >>> formatter.format("15", "27", "42")     # "15 + 27 = 42"
            
            Mandatory fields:
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
                # Literal text section - no variable substitution needed
                result_parts.append(section.parts.prefix)
                continue
            else:
                field_value = get_var(section.field_name)
                if field_value is None: # no value provided for this section's field - skip this section
                    if section.is_mandatory:
                        raise MissingMandatoryFieldError(f"Required field '{section.field_name}' not provided")
                    continue  # Skip optional sections with missing data - core graceful degradation feature
                
                # Apply both sectional and inline formatting at runtime
                # This deferred approach avoids complex position tracking during baking
                new_section = section.copy()
                show_field = True
                for handler in self.token_handlers.values():
                    new_section = handler.apply_sectional_formatting(new_section, field_value, kwargs)
                    show_field = handler.apply_inline_formatting(new_section.parts, field_value, kwargs) and show_field
                
                if show_field:
                    new_section.parts.field += str(field_value)
                
                # Add reset codes to parts with actual content    
                result_parts.append(self._assemble_section_with_resets(new_section))
        return ''.join(result_parts)
    
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
        for p, part in section.parts.iter_fields():
            if has_non_ansi(part):
                section.parts[p] = self.parser.unescape_part(section.parts[p]) + RESET_ANSI
            else:
                section.parts[p] = ''
            result += section.parts[p]
            
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
            'has_inline_formatting': self._has_inline_formatting(),
            'delimiter': self.delimiter,
            'escape_char': self.escape_char,
            'custom_functions': list(self.functions.keys())
        }
    
    def _has_inline_formatting(self) -> bool:
        for section in self.sections:
            if section.field_name is not None:  # Skip literal text sections
                for handler in self.token_handlers.values():
                    if handler.has_inline_formatting(section.parts):
                        return True
        return False