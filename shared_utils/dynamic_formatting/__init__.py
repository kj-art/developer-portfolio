"""
Dynamic Formatting Package

A sophisticated string formatting system that supports conditional sections with graceful handling 
of missing data, plus extensible token-based formatting for colors and text formatting with 
function fallback support.

CORE FEATURES:
- Family-based formatting (colors, text styles, conditionals operate independently)
- Function fallback system for dynamic token resolution
- Conditional formatting at section and inline levels
- Comprehensive escape sequence handling
- Performance-optimized rendering with console/file output modes
- Enterprise-grade error handling with specific exception types

QUICK START:
    from shared_utils.dynamic_formatting import DynamicFormatter
    
    # Basic formatting
    formatter = DynamicFormatter("{{#red@bold;ERROR: ;message}}")
    result = formatter.format(message="File not found")
    # Output: colored and bold "ERROR: File not found"

SYNTAX REFERENCE:
    Template Structure:
        {{[!][?condition][#color][@text][prefix;]field[;suffix]}}
        
        ! = Required field (throws RequiredFieldError if missing)
        ?function = Conditional (show section only if function returns True)
        #token = Color formatting (red, blue, hex colors, or function name)
        @token = Text formatting (bold, italic, underline, or function name)
        
    Inline Formatting:
        {#red}text     - Color this text red
        {@bold}text    - Make this text bold  
        {?func}text    - Show text only if func returns True
        
    Escape Sequences:
        \\{  → literal {
        \\}  → literal }
        \\;  → literal ;

COMPREHENSIVE EXAMPLES:

1. FUNCTION FALLBACK SYSTEM:
    def level_color(level_name):
        '''Function that returns color based on log level'''
        return {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'green'}.get(level_name, 'white')
    
    def has_items(count):
        '''Conditional function for showing item counts'''
        return count > 0
    
    formatter = DynamicFormatter(
        "{{#level_color@bold;[;levelname;]}} {{message}} {{?has_items;(;file_count; files)}}",
        functions={'level_color': level_color, 'has_items': has_items}
    )
    
    result = formatter.format(levelname="ERROR", message="Processing failed", file_count=25)
    # Output: red bold "[ERROR] Processing failed (25 files)"

2. CONDITIONAL FORMATTING:
    # Section-level conditionals (show/hide entire sections)
    formatter = DynamicFormatter(
        "{{Processing}} {{?has_errors;ERROR COUNT: ;error_count}} {{?is_slow;SLOW OPERATION;duration}}"
    )
    
    # Inline conditionals (show/hide parts of text within sections)
    formatter = DynamicFormatter(
        "{{Processing{?has_files} files{?is_urgent} URGENT{?has_errors} - ERRORS: ;status}}"
    )

3. MIXED FORMATTING FAMILIES:
    # Colors and text styles operate independently
    formatter = DynamicFormatter("{{#red@bold@italic;Multi-format: ;field}}")
    
    # Reset individual families
    formatter = DynamicFormatter("{{#red@bold;Start} {#blue@normal;Middle} {@italic;End: ;field}}")
    # "Start" = red+bold, "Middle" = blue+normal, "End" = blue+italic

4. ESCAPE SEQUENCES:
    # Literal braces in output
    formatter = DynamicFormatter("{{Use \\{brackets\\} for: ;syntax}}")
    result = formatter.format(syntax="variables")
    # Output: "Use {brackets} for: variables"
    
    # Conditional with escaped braces
    formatter = DynamicFormatter(
        "{{Processing{?has_files} \\{found files\\}: ;file_count}}", 
        functions={'has_files': lambda x: x > 0}
    )

5. ADVANCED FEATURES:
    # Function-based prefix/suffix
    def get_prefix(value):
        return ">>>" if value == "important" else "---"
    
    formatter = DynamicFormatter(
        "{{$get_prefix;Message: ;message;!}}", 
        functions={'get_prefix': get_prefix}
    )
    
    # Required fields with complex formatting
    formatter = DynamicFormatter("{{!#red@bold;CRITICAL ERROR in ;module;:}}")

INTEGRATION EXAMPLES:

1. LOGGING INTEGRATION:
    import logging
    from shared_utils.dynamic_formatting import DynamicLoggingFormatter
    
    def level_color(level):
        return {'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow', 
                'ERROR': 'red', 'CRITICAL': 'magenta'}[level]
    
    def has_duration(duration):
        return duration and duration > 0
    
    formatter = DynamicLoggingFormatter(
        "{{#level_color@bold;[;levelname;]}} {{message}} {{?has_duration;in ;duration;s}}",
        functions={'level_color': level_color, 'has_duration': has_duration}
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

2. CLI PROGRESS REPORTING:
    def status_color(status):
        return 'green' if status == 'success' else 'red' if status == 'error' else 'yellow'
    
    def has_errors(count):
        return count > 0
    
    formatter = DynamicFormatter(
        "{{#status_color;Status: ;status}} - {{processed}}/{{total}} files {{?has_errors;(;error_count; errors)}}",
        functions={'status_color': status_color, 'has_errors': has_errors}
    )
    
    print(formatter.format(status="success", processed=95, total=100, error_count=0))

3. WEB FRAMEWORK INTEGRATION:
    def format_api_response(data):
        formatter = DynamicFormatter(
            "{{#blue;API Response:}} {{?has_data;Success - ;record_count; records}} {{?has_errors;Errors: ;error_count}}"
        )
        return formatter.format(**data)

ERROR HANDLING:

Exception Hierarchy:
    DynamicFormattingError (base)
    ├── RequiredFieldError      - Missing required field (marked with !)
    ├── FunctionNotFoundError   - Conditional function not provided  
    ├── ParseError             - Malformed template syntax
    ├── FormatterError         - Invalid color/style token
    ├── FunctionExecutionError - Function execution failed
    └── StackingError          - Invalid formatting combination

Best Practices:
    try:
        result = formatter.format(**data)
    except RequiredFieldError as e:
        logger.error(f"Missing required field: {e}")
        return fallback_format(**data)
    except DynamicFormattingError as e:
        logger.error(f"Formatting failed: {e}")
        return str(data)  # Fallback to simple representation

PERFORMANCE CONSIDERATIONS:

Template Compilation:
    - Templates are parsed once during DynamicFormatter creation
    - Reuse formatter instances for repeated formatting
    - Parsing: O(n) where n = template length
    - Formatting: O(m) where m = output length

Memory Usage:
    - Simple sections: Minimal overhead (string concatenation)
    - Complex sections: O(spans) temporary state objects
    - Automatic cleanup with proper reset handling

Large Dataset Recommendations:
    # DO: Pre-compile formatters
    formatter = DynamicFormatter(template)
    for record in large_dataset:
        result = formatter.format(**record)
    
    # DON'T: Recompile templates in loops
    for record in large_dataset:
        formatter = DynamicFormatter(template)  # Expensive!
        result = formatter.format(**record)

ARCHITECTURAL HIGHLIGHTS:

1. Family-Based State Management:
   Colors, text styles, and conditionals operate in separate "families" to prevent
   interference. This allows sophisticated combinations like:
   {{#red@bold;Text}} {#blue@normal;More}} {@italic;End}}
   
2. Function Fallback System:
   If a token like #level_color isn't a built-in color, the system automatically
   tries to execute it as a function and re-parse the result.
   
3. Two-Level Conditionals:
   - Section level: ?function controls entire template sections
   - Inline level: {?function} controls parts of text within sections
   
4. Escape-Aware Parsing:
   Comprehensive handling of escape sequences at all parsing levels with
   single-pass efficiency.

OUTPUT MODES:
    'console' - Full ANSI color codes and formatting for terminal display
    'file'    - Plain text output with formatting stripped for log files
    
    formatter = DynamicFormatter(template, output_mode='file')

EXTENDING THE SYSTEM:

Adding Custom Formatters:
    from shared_utils.dynamic_formatting.formatters import FormatterBase
    
    class CustomFormatter(FormatterBase):
        def get_family_name(self) -> str:
            return 'custom'
        
        def parse_token(self, token_value: str, field_value: Any = None) -> Any:
            # Your parsing logic
            pass
        
        def apply_formatting(self, text: str, parsed_tokens: List[Any], 
                           output_mode: str = 'console') -> str:
            # Your formatting logic
            pass
    
    # Register with system
    TOKEN_FORMATTERS['%'] = CustomFormatter()
"""

# Import the main classes that users will actually need
try:
    # Try relative imports first (when used as package)
    from .dynamic_formatting import (
        DynamicFormatter,
        DynamicLoggingFormatter,
        DynamicFormattingError,
        RequiredFieldError,
        FunctionNotFoundError
    )

    from .formatters import (
        TOKEN_FORMATTERS,
        FormatterError,
        FunctionExecutionError
    )

    from .formatting_state import (
        FormattingState,
        StackingError
    )

    from .token_parsing import (
        TemplateParser,
        ParseError
    )

    from .span_structures import (
        FormattedSpan,
        FormatSection
    )
except ImportError:
    # Fall back to absolute imports (when files are in same directory)
    from dynamic_formatting import (
        DynamicFormatter,
        DynamicLoggingFormatter,
        DynamicFormattingError,
        RequiredFieldError,
        FunctionNotFoundError
    )

    from formatters import (
        TOKEN_FORMATTERS,
        FormatterError,
        FunctionExecutionError
    )

    from formatting_state import (
        FormattingState,
        StackingError
    )

    from token_parsing import (
        TemplateParser,
        ParseError
    )

    from span_structures import (
        FormattedSpan,
        FormatSection
    )

__all__ = [
    # Main user-facing classes
    'DynamicFormatter',
    'DynamicLoggingFormatter',
    
    # Exception classes
    'DynamicFormattingError',
    'RequiredFieldError', 
    'FunctionNotFoundError',
    'FormatterError',
    'FunctionExecutionError',
    'StackingError',
    'ParseError',
    
    # Advanced classes for extension
    'TOKEN_FORMATTERS',
    'FormattingState',
    'TemplateParser',
    'FormattedSpan',
    'FormatSection'
]

__version__ = '2.0.0'
#python -m shared_utils.dynamic_formatting.dynamic_formatting