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
    from .inline_formatting import InlineFormatting
    from .template_ast import TemplatePart
    from .token_handlers import TOKEN_REGISTRY
except ImportError:
    from parsing import TemplateParser
    from formatting import FormatApplier
    from token_handlers import create_token_handlers, ConditionalTokenHandler
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
        
        self.sections = self.parser.parse_template(template)
        self._bake_template()
        
    def _update_positions(self, format_list: List[InlineFormatting], offset: int):
        for fmt in format_list:
            fmt.adjust_position(offset)

    def _bake_template(self, *args, **kwargs) -> str:
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