"""
Core template formatter implementation for StringSmith.

This module contains the main TemplateFormatter class which provides the primary 
public interface for StringSmith's conditional template formatting capabilities.
"""

from typing import Dict, Callable, Optional
from .parser import TemplateParser
from ..tokens import create_token_handlers
from ..exceptions import StringSmithError, MissingMandatoryFieldError
from .ast import TemplateSection
from ..utils import has_non_ansi

class TemplateFormatter:
    """
    Professional template formatter with conditional sections and rich formatting.

    TemplateFormatter provides f-string-like functionality with conditional sections
    that automatically disappear when variables are missing, plus rich formatting
    options including colors and text emphasis. Templates are optimized during
    initialization for efficient runtime formatting operations.

    Core Features:
        - **Conditional Sections**: Sections disappear when variables are missing
        - **Mandatory Validation**: Required fields (prefixed with '!') enforce data presence
        - **Rich Formatting**: ANSI colors, text emphasis, and custom styling functions  
        - **Custom Functions**: User-defined functions for formatting and conditionals
        - **Multi-Parameter Functions**: Functions can access multiple template fields
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
        - $function: Apply literal transformation function (replaces content with result)
    
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
        ...     functions=[priority_color]
        ... )
        >>> formatter.format(priority=8, message="Critical")  # Red "Level 8: Critical"
        
        Multi-parameter functions:
        >>> def is_profitable(revenue, costs):
        ...     return float(revenue) > float(costs)
        >>> formatter = TemplateFormatter("{{?is_profitable; ✓ Profitable;revenue;}}", 
        ...                             functions=[is_profitable])
        >>> formatter.format(revenue="150", costs="100")  # " ✓ Profitable"
        
        Mandatory fields with validation:
        >>> formatter = TemplateFormatter("{{!name}} is required")
        >>> formatter.format(name="Alice")  # "Alice is required"  
        >>> formatter.format()  # Raises MissingMandatoryFieldError
        
        Positional arguments:
        >>> formatter = TemplateFormatter("{{}} + {{}} = {{}}")
        >>> formatter.format("15", "27", "42")  # "15 + 27 = 42"
    
    Performance Notes:
        - Template parsing is performed during initialization for faster formatting
        - Format operations are O(m) where m is the number of template sections
        - Recommended to create formatters once and reuse for multiple format operations
        - Thread-safe after initialization for concurrent formatting operations
    """
    
    def __init__(self, 
                 template: str, 
                 delimiter: str = ';', 
                 escape_char: str = '\\', 
                 functions: list[Callable] | dict[str, Callable] | None = None,
                 skip_empty=False):
        """
        Initialize a template formatter with conditional sections and rich formatting.
        
        Templates are optimized during initialization by parsing structure, validating
        tokens, and pre-computing static formatting elements. This front-loads work
        for optimal runtime performance during format operations.
        
        Args:
            template (str): Template string using {{}} sections for conditional content.
            delimiter (str, optional): Character(s) separating parts within sections. 
                                    Defaults to ';'.
            escape_char (str, optional): Character(s) for escaping special sequences.
                                    Defaults to '\\'.
            functions (Dict[str, Callable], optional): Custom functions for formatting
                                                    and conditionals.
            skip_empty (bool, optional): If True, treat empty strings the same as None
                                    for section visibility. If False, only None values
                                    cause sections to disappear. Defaults to False.
        
        Raises:
            StringSmithError: If template contains invalid formatting tokens or syntax errors.
            ParseError: If template structure is malformed or contains unsupported constructs.
        """
        self.template = template
        self.delimiter = delimiter
        self.escape_char = escape_char
        self.skip_empty = skip_empty
        if functions is None:
            self._functions = {}
        elif isinstance(functions, list):
            self._functions = {f.__name__: f for f in functions}
        else:
            self._functions = functions


        # Initialize parser with template-specific settings
        self.parser = TemplateParser()
        self.parser.delimiter = delimiter
        self.parser.escape_char = escape_char

        # Create token handlers organized by processing priority
        handler_passes = create_token_handlers(self._functions)
        self.token_handlers = {}
        self.flat_token_handlers = {}

        # Build regex patterns and handler mappings for each processing pass
        for handler_list in handler_passes:
            pass_regex = self.parser.create_token_regex(*[cls.token for cls in handler_list])
            handlers = {inst.token: inst for inst in handler_list}
            self.token_handlers[pass_regex] = handlers
            self.flat_token_handlers.update(handlers)

        # Parse template structure into AST
        self.sections = self.parser.parse_template(template)
        self._has_inline_formatting = False

        # Optimize template for runtime performance
        self._bake_template()

    def _bake_template(self, *args, **kwargs) -> str:
        """
        Pre-process template sections for optimal runtime performance.
        
        Template baking applies all formatting operations that don't require runtime data,
        including token validation and static ANSI code generation. This approach trades
        initialization time for significantly faster format operations.
        
        Processing steps:
        1. Extract and validate all formatting tokens
        2. Pre-compute static ANSI codes for non-function tokens  
        3. Apply section-level formatting prefixes
        4. Process inline formatting tokens within template parts
        5. Build consolidated reset sequences for cleanup
        
        Invalid formatting tokens are caught during this phase rather than at runtime,
        providing early error detection and better debugging experience.
        """
        tokens_used = set()
        for s, section in enumerate(self.sections):
            # Skip literal text sections (no formatting to process)
            if section.parts.suffix == None:
                continue

            part_prefix = ''

            # Apply static section-level formatting
            for token, values in section.section_formatting.items():
                tokens_used.add(token)

                # Process values in reverse to maintain order when removing processed items
                for v in range(len(values) - 1, -1, -1):
                    replacement_text = self.flat_token_handlers[token].get_static_formatting(values[v])
                    if not replacement_text:
                        continue
                    part_prefix += replacement_text
                    values.pop(v)   # Remove processed static formatting
            
            # Process inline formatting within each template part
            for p, part in section.parts.iter_fields():
                if not part and p != 'field':
                    continue

                # Apply formatting from each token handler pass
                for regex, handlers_dict in self.token_handlers.items():
                    split_part = self.parser.split_tokens(section.parts[p], regex)
                    result = ''

                    # Process each token or text fragment
                    while len(split_part):
                        part_fragment = split_part.pop(0)
                        if isinstance(part_fragment, str):
                            result += part_fragment
                            continue

                        # Process formatting token
                        self._has_inline_formatting = True
                        token, token_value = part_fragment
                        tokens_used.add(token)
                        replacement_text = handlers_dict[token].get_static_formatting(token_value)

                        # Keep dynamic tokens for runtime processing, apply static ones immediately
                        result += f'{{{token}{token_value}}}' if replacement_text is None else replacement_text

                    section.parts[p] = result

                # Apply section-level formatting prefix to this part   
                section.parts[p] = part_prefix + section.parts[p]

        # Build consolidated reset sequence for all used token types
        self._construct_reset_suffix(tokens_used)
    
    def _construct_reset_suffix(self, tokens_used: set[str]):
        """
        Build consolidated ANSI reset sequence for all token types used in template.
        
        Constructs a single reset sequence that clears all formatting applied by
        any token handlers used in the template. This is more efficient than
        applying individual resets for each formatting operation.
        
        Args:
            tokens_used: Set of token prefixes that appear in the template
        """
        reset_ansis = []
        for token in tokens_used:
            reset_ansis.append(self.flat_token_handlers[token].reset_ansi)
        self._reset_ansi = ''.join(reset_ansis)

    def format(self, *args, **kwargs) -> str:
        """
        Format template with provided variables using conditional section logic.
        
        Core behavior: Sections automatically disappear when their field variables
        are missing, eliminating manual null checking and conditional string building.
        Mandatory sections (prefixed with '!') throw errors when variables are missing.
        
        Multi-Parameter Function Support:
            Custom functions can access multiple field values through parameter name matching.
            Function parameters with names matching format() arguments receive those values.
            Functions with no matching parameters receive the section's field value.
        
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
        
        # Set up variable accessor based on argument type
        get_var = self._set_up_variable_accessor(args, kwargs)
        result_parts = []
        
        # Process each template section
        for section in self.sections:
            if section.field_name is None:
                # Literal text section - no variable substitution needed
                result_parts.append(section.parts.prefix)
                continue

            # Get field value for this section
            field_value = get_var(section.field_name)
            if field_value is None or (field_value == '' and self.skip_empty):
                # No value provided for this section's field
                if section.is_mandatory:
                    raise MissingMandatoryFieldError(f"Required field '{section.field_name}' not provided")
                continue    # Skip optional sections with missing data (core graceful degradation)
            
            # Create working copy for formatting operations
            new_section = section.copy()
            show_field = True

            # Apply formatting from each token handler pass
            for regex, handlers_dict in self.token_handlers.items():
                # Apply section-level formatting
                for token, handler in handlers_dict.items():
                    if new_section.section_formatting and len(new_section.section_formatting[token]):
                        show_field = handler.apply_section_formatting(new_section, field_value, kwargs) and show_field
                
                # Apply inline formatting to each part
                for part_key, part_content in new_section.parts.iter_fields():
                    if not part_content:
                        continue
                    
                    # Split part content on tokens for processing
                    split_part = self.parser.split_tokens(part_content, regex)

                    # Process tokens with appropriate handlers
                    for token, handler in handlers_dict.items():
                        split_part, c_show_field = handler.apply_inline_formatting(split_part, part_key, field_value, kwargs)
                        show_field = show_field and c_show_field

                    # Reconstruct part from processed fragments
                    new_section.parts[part_key] = ''.join(split_part)

            # Add field value if not suppressed by conditional logic
            if show_field:
                new_section.parts.field += str(field_value)
            
            # Assemble section with proper ANSI reset codes
            result_parts.append(self._assemble_section_with_resets(new_section))
            
        return ''.join(result_parts)
    
    def _raw_ansi(self, s):
        return s.encode('unicode_escape').decode('ascii')


    def _set_up_variable_accessor(self, args, kwargs):
        """
        Create variable accessor function based on argument type.
        
        Returns a closure that provides consistent variable access regardless
        of whether positional or keyword arguments were used in the format call.
        
        Args:
            args: Positional arguments from format() call
            kwargs: Keyword arguments from format() call
            
        Returns:
            Callable: Function that retrieves variable values by field name
        """
        if args:
            # Positional argument accessor with index tracking
            arg_index = 0
            def get_var(field_name=None):
                nonlocal arg_index
                if arg_index >= len(args):
                    return None
                arg = args[arg_index]
                arg_index += 1
                return arg
        else:
            # Keyword argument accessor with name-based lookup
            def get_var(field_name):
                return None if field_name == '' else kwargs.get(field_name)
        return get_var

    def _assemble_section_with_resets(self, section: TemplateSection):
        """
        Assemble section parts with proper ANSI reset codes for formatting cleanup.
        
        Applies consolidated reset sequences to parts containing actual content
        (not just ANSI codes) to ensure proper formatting termination between
        section parts and to prevent interference with subsequent template sections.
        
        Args:
            section: Template section with processed formatting
            
        Returns:
            str: Assembled section text with appropriate reset sequences
        """
        result = ''
        for part_key, part_content in section.parts.iter_fields():
            if has_non_ansi(part_content):
                # Part has actual content - add reset codes and unescape
                section.parts[part_key] = self.parser.unescape_part(section.parts[part_key]) + self._reset_ansi
            else:
                # Part is empty or ANSI-only - clear it
                section.parts[part_key] = ''
            result += section.parts[part_key]
            
        return result
    
    def get_template_info(self) -> Dict[str, any]:
        """
        Get comprehensive information about this template's structure and capabilities.
        
        Returns:
            Dict[str, any]: Template metadata including field counts, formatting flags,
                          configuration settings, and available functions.
            
        Examples:
            >>> formatter = TemplateFormatter("{{#red;Error: ;message;}}")
            >>> info = formatter.get_template_info()
            >>> info['field_count']
            1
            >>> info['has_inline_formatting']
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
            'has_inline_formatting': self._has_inline_formatting,
            'delimiter': self.delimiter,
            'escape_char': self.escape_char,
            'custom_functions': list(self._functions.keys())
        }
