"""
Core template formatter implementation.
"""

import re
from typing import Dict, Callable, Optional, List

# Handle both relative and absolute imports
try:
    from .parsing import TemplateParser
    from .token_handlers import create_token_handlers
    from .exceptions import StringSmithError, MissingMandatoryFieldError
    from .inline_formatting import InlineFormatting
    from .template_ast import TemplatePart
    from .token_handlers import TOKEN_REGISTRY
except ImportError:
    from parsing import TemplateParser
    from token_handlers import create_token_handlers
    from exceptions import StringSmithError, MissingMandatoryFieldError
    from inline_formatting import InlineFormatting
    from template_ast import TemplatePart
    from token_handlers import TOKEN_REGISTRY

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

    _ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
    
    def __init__(self, template: str, delimiter: str = ';', escape_char: str = '\\', functions: Optional[Dict[str, Callable]] = None):
        """
        Initialize a template formatter with conditional sections and rich formatting.
        
        Templates are "baked" during initialization - formatting tokens are parsed,
        validated, and cached for optimal runtime performance. Invalid colors/emphasis 
        styles are caught at creation time rather than during formatting operations.
        
        Args:
            template (str): Template string using {{}} sections for conditional content.
                        Sections can include formatting tokens (#color, @emphasis, ?conditional),
                        prefixes, field names, and suffixes separated by the delimiter.
            delimiter (str, optional): Character separating parts within sections. 
                                    Defaults to ';'. Common alternatives: '|', ':'.
            escape_char (str, optional): Character for escaping special sequences.
                                    Defaults to '\\'. Use to include literal braces.
            functions (Dict[str, Callable], optional): Custom functions for formatting
                                                    and conditionals. Function names become
                                                    available as formatting tokens.
        
        Raises:
            StringSmithError: If template contains invalid formatting tokens or syntax errors.
            
        Examples:
            >>> # Basic conditional sections
            >>> formatter = TemplateFormatter("{{Hello ;name;}}")
            >>> formatter.format(name="World")  # "Hello World"
            >>> formatter.format()              # "" (section disappears)
            
            >>> # Color and emphasis formatting
            >>> formatter = TemplateFormatter("{{#red@bold;ERROR: ;message;}}")
            >>> formatter.format(message="Failed")  # Red bold "ERROR: Failed"
            
            >>> # Custom functions
            >>> def priority_color(level):
            ...     return 'red' if level > 5 else 'yellow'
            >>> formatter = TemplateFormatter("{{#priority_color;Level ;priority;: ;message;}}",
            ...                             functions={'priority_color': priority_color})
            >>> formatter.format(priority=8, message="Critical")  # Red "Level 8: Critical"
        
        Performance Notes:
            - Template parsing is front-loaded during initialization for faster formatting
            - Color/emphasis validation happens once at creation, not per format() call
            - Recommended to create formatters once and reuse for multiple format operations
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
        for fmt in format_list:
            fmt.adjust_position(offset)

    def _bake_template(self, *args, **kwargs) -> str:
        """
        Pre-process template sections for performance.
        
        This "baking" process:
        - Validates all formatting tokens (colors, emphasis, functions)
        - Caches ANSI codes and formatting state
        - Applies sectional formatting that doesn't depend on runtime data
        - Raises errors for invalid tokens at creation time, not format() time
        """
        for s, section in enumerate(self.sections):
            # skip literal sections of string
            if section.suffix == None:
                continue
            
            # turn field blank so formatting prefixes can be added and field_value can be added as a suffix without issue
            section.field.content = ''
            str_len = (len(section.prefix.content), len(section.suffix.content))

            # bake sectional formatting
            # if some sectional formatting is baked and others aren't, this may mess with the order sectional formatting appears in
            # but the user really shouldn't be unstacking, mutually exclusive sectional formatting anyways, so it shouldn't matter 
            
            for tkn in section.section_formatting:
                self.sections[s] = self.token_handlers[tkn].apply_sectional_formatting(self.sections[s])
            
            section = self.sections[s]

            # update remaining formatting positions
            self._update_positions(section.prefix.inline_formatting, len(section.prefix.content) - str_len[0])
            self._update_positions(section.field.inline_formatting, len(section.field.content))
            self._update_positions(section.suffix.inline_formatting, len(section.suffix.content) - str_len[1])
            
            # bake inline formatting
            self._bake_inline_formatting(section.prefix)
            self._bake_inline_formatting(section.field)
            self._bake_inline_formatting(section.suffix)

    def _bake_inline_formatting(self, template_part: TemplatePart):
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

    def _has_non_ansi(self, text: str) -> bool:
        # Remove all ANSI sequences
        stripped = TemplateFormatter._ANSI_ESCAPE.sub('', text)
        # Check if there's anything left
        return bool(stripped)

    def format(self, *args, **kwargs) -> str:
        """
        Format template with provided variables using conditional section logic.
        
        Core behavior: Sections automatically disappear when their field variables
        are missing, eliminating manual null checking and conditional string building.
        Mandatory sections (prefixed with '!') throw errors when variables are missing.
        
        Args:
            *args: Positional arguments mapped to template fields in order.
                Field names in template are ignored when using positional args.
            **kwargs: Keyword arguments mapped to template fields by name.
            
        Returns:
            str: Formatted string with ANSI color codes (if formatting used) and
                missing data sections omitted. Empty string if no sections render.
        
        Raises:
            StringSmithError: If positional and keyword arguments are mixed.
            MissingMandatoryFieldError: If mandatory field (marked with '!') is missing.
            
        Examples:
            >>> # Conditional sections disappear gracefully
            >>> formatter = TemplateFormatter("{{User: ;username;}} {{(ID: ;user_id;)}}")
            >>> formatter.format(username="admin")      # "User: admin "
            >>> formatter.format(user_id=123)          # " (ID: 123)"
            >>> formatter.format()                     # ""
            
            >>> # Positional arguments
            >>> formatter = TemplateFormatter("{{first}} + {{second}} = {{result}}")
            >>> formatter.format("15", "27", "42")     # "15 + 27 = 42"
            >>> formatter.format("15", "27")           # "15 + 27 = "
            
            >>> # Mandatory sections enforce required data
            >>> formatter = TemplateFormatter("{{!name}} logged in {{at ;timestamp;}}")
            >>> formatter.format(name="admin", timestamp="10:30")  # "admin logged in at 10:30"
            >>> formatter.format(timestamp="10:30")    # Raises MissingMandatoryFieldError
        
        Professional Use Cases:
            - Logging: Status messages with optional context that varies by log level
            - Reporting: Data displays where some fields may be missing or null
            - CLI output: User notifications with conditional additional information
            - Data processing: Template-based output generation with sparse datasets
        """
        if args and kwargs:
            raise StringSmithError('Cannot mix positional and keyword arguments')
        
        # Get field value based on position or keyword
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
        for token in TOKEN_REGISTRY:
            reset_ansi += self.token_handlers[token].get_reset_ansi()
        
        for section in self.sections:
            if section.field_name is None:
                result_parts.append(section.prefix.content)
                continue
            else:
                field_value = get_var(section.field_name)
                if field_value is None: # no value provided for this section's field - skip this section
                    if section.is_mandatory:
                        raise MissingMandatoryFieldError(f"Required field '{section.field_name}' not provided")
                    continue  # Skip optional sections
                
                new_section = section.copy()

                # apply inline formatting
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
                    
                
                for f in TOKEN_REGISTRY:
                    handler = self.token_handlers[f]
                    new_section.prefix.content = handler.finalize(new_section.prefix, field_value)
                    new_section.field.content = handler.finalize(new_section.field, field_value)
                    new_section.suffix.content = handler.finalize(new_section.suffix, field_value)
                
                new_section.field.content += str(field_value)
                
                # apply sectional formatting
                for tkn in new_section.section_formatting:
                    if not len(new_section.section_formatting[tkn]):
                        continue
                    handler = self.token_handlers[tkn]
                    new_section = handler.apply_sectional_formatting(new_section, field_value)
                
                if self._has_non_ansi(new_section.prefix.content):
                    new_section.prefix.content += reset_ansi
                else:
                    new_section.prefix.content = ''
                if self._has_non_ansi(new_section.field.content):
                    new_section.field.content += reset_ansi
                else:
                    new_section.field.content = ''
                if self._has_non_ansi(new_section.suffix.content):
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
        for f in range(len(formatting) - 1, -1, -1):
            fmt = formatting[f]
            text_segment = self.token_handlers[fmt.type].apply_inline_formatting(text_segment, fmt.position, fmt.value, field_value)

        return text_segment