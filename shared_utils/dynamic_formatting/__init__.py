"""
Dynamic Formatting Package

A sophisticated string formatting system that gracefully handles missing data - template sections 
automatically disappear when their required data isn't provided, eliminating tedious manual null 
checking. Also supports conditional sections, plus extensible token-based formatting for colors 
and text formatting with function fallback support and **positional argument support**.

CORE VALUE: Sections automatically disappear when data is missing - no manual null checking required

CORE FEATURES:
- **Graceful missing data handling** - template sections vanish when fields aren't provided
- **Positional argument support** - simplified syntax for common use cases
- Family-based formatting (colors, text styles, conditionals operate independently)
- Function fallback system for dynamic token resolution
- Conditional formatting at section and inline levels
- Comprehensive escape sequence handling
- Performance-optimized rendering with console/file output modes
- Enterprise-grade error handling with specific exception types

QUICK START - GRACEFUL MISSING DATA:
    from shared_utils.dynamic_formatting import DynamicFormatter
    
    # Core feature: sections disappear when data is missing
    formatter = DynamicFormatter("{{Error: ;message}} {{Processing ;file_count; files}} {{Duration: ;seconds;s}}")
    
    # All data present
    result = formatter.format(message="Failed", file_count=25, seconds=12.5)
    # Output: "Error: Failed Processing 25 files Duration: 12.5s"
    
    # Some data missing - sections automatically disappear
    result = formatter.format(file_count=25)  # Only file_count provided
    # Output: "Processing 25 files"
    
    # No data - empty result  
    result = formatter.format()
    # Output: ""

QUICK START - POSITIONAL ARGUMENTS (NEW):
    # Simple positional syntax - no field names needed
    formatter = DynamicFormatter("{{}} {{Count: ;}}")
    result = formatter.format("Processing", 150)
    # Output: "Processing Count: 150"
    
    # Even simpler
    formatter = DynamicFormatter("{{}} {{}}")
    result = formatter.format("Hello", "World")
    # Output: "Hello World"
    
    # With formatting
    formatter = DynamicFormatter("{{#red@bold;ERROR: ;;}} {{#blue;}}")
    result = formatter.format("System failure", "Details")
    # Output: red bold "ERROR: System failure" blue "Details"

QUICK START - ADVANCED FORMATTING:
    # Basic formatting with colors and styles
    formatter = DynamicFormatter("{{#red@bold;ERROR: ;message}}")
    result = formatter.format(message="File not found")
    # Output: red bold "ERROR: File not found"

SYNTAX REFERENCE:
    Template Structure (Keyword):
        {{[!][?condition][#color][@text][prefix;]field[;suffix]}}
        
    Template Structure (Positional):
        {{[!][?condition][#color][@text][prefix;;suffix]}}
        
        ! = Required field (throws RequiredFieldError if missing)
        ?function = Conditional (show section only if function returns True)
        #token = Color formatting (red, blue, hex colors, or function name)
        @token = Text formatting (bold, italic, underline, or function name)
        Empty field = positional argument slot
        
    Inline Formatting:
        {#red}text     - Color this text red
        {@bold}text    - Make this text bold  
        {?func}text    - Show text only if func returns True
        
    Escape Sequences:
        \\{  → literal {
        \\}  → literal }
        \\;  → literal ;

COMPREHENSIVE EXAMPLES:

1. GRACEFUL MISSING DATA (CORE FEATURE):
    formatter = DynamicFormatter("{{Status: ;status}} {{Count: ;count}} {{Duration: ;duration;s}}")
    
    # Complete data
    result = formatter.format(status="OK", count=42, duration=1.5)
    # Output: "Status: OK Count: 42 Duration: 1.5s"
    
    # Partial data - missing sections disappear automatically
    result = formatter.format(status="OK")
    # Output: "Status: OK"
    
    # No manual null checking required!

2. POSITIONAL ARGUMENTS (NEW):
    # Basic positional
    formatter = DynamicFormatter("{{Error: ;;}} {{Count: ;}}")
    result = formatter.format("Connection failed", 25)
    # Output: "Error: Connection failed Count: 25"
    
    # With formatting
    formatter = DynamicFormatter("{{#red@bold;;}} {{#green;}}")
    result = formatter.format("CRITICAL", "OK")
    # Output: red bold "CRITICAL" green "OK"
    
    # Mixed with conditionals
    def has_value(val):
        return bool(val)
    
    formatter = DynamicFormatter("{{Status: ;;}} {{?has_value;Details: ;}}", 
                                functions={'has_value': has_value})
    result = formatter.format("Running", "All systems operational")
    # Output: "Status: Running Details: All systems operational"

3. FUNCTION FALLBACK SYSTEM:
    def level_color(level_name):
        '''Function that returns color based on log level'''
        return {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'green'}.get(level_name, 'white')
    
    def has_items(count):
        '''Conditional function for showing item counts'''
        return count > 0
    
    # Keyword version
    formatter = DynamicFormatter(
        "{{#level_color@bold;[;levelname;]}} {{message}} {{?has_items;(;file_count; files)}}",
        functions={'level_color': level_color, 'has_items': has_items}
    )
    result = formatter.format(levelname="ERROR", message="Processing failed", file_count=25)
    # Output: red bold "[ERROR] Processing failed (25 files)"
    
    # Positional version
    formatter = DynamicFormatter(
        "{{#level_color@bold;[;;]}} {{}} {{?has_items;(;;files)}}",
        functions={'level_color': level_color, 'has_items': has_items}
    )
    result = formatter.format("ERROR", "Processing failed", 25)
    # Output: red bold "[ERROR] Processing failed (25 files)"

4. CONDITIONAL FORMATTING:
    # Section-level conditionals (show/hide entire sections)
    formatter = DynamicFormatter(
        "{{Processing}} {{?has_errors;ERROR COUNT: ;error_count}} {{?is_slow;SLOW OPERATION;duration}}"
    )
    
    # Inline conditionals (show/hide parts of text within sections)
    formatter = DynamicFormatter(
        "{{Processing{?has_files} files{?is_urgent} URGENT{?has_errors} - ERRORS: ;status}}"
    )

5. MIXED FORMATTING FAMILIES:
    # Colors and text styles operate independently - later colors override earlier ones
    formatter = DynamicFormatter("{{#red#blue@bold@italic;Multi-format: ;field}}")
    # Result: blue, bold, italic text (blue overrides red)
    
    # Reset individual families
    formatter = DynamicFormatter("{{#red@bold;Start} {#blue@normal;Middle} {@italic;End: ;field}}")
    # "Start" = red+bold, "Middle" = blue+normal, "End" = blue+italic

6. ESCAPE SEQUENCES:
    # Literal braces in output
    formatter = DynamicFormatter("{{Use \\{brackets\\} for: ;syntax}}")
    result = formatter.format(syntax="variables")
    # Output: "Use {brackets} for: variables"
    
    # Positional with escaped braces
    formatter = DynamicFormatter("{{Config \\{key\\}=\\{value\\}: ;}}")
    result = formatter.format("debug=true")
    # Output: "Config {key}={value}: debug=true"

7. ERROR HANDLING WITH POSITIONAL ARGUMENTS:
    # Too many arguments
    formatter = DynamicFormatter("{{}} {{}}")
    try:
        result = formatter.format("a", "b", "c")  # Too many
    except DynamicFormattingError as e:
        # "Too many positional arguments: expected 2, got 3"
    
    # Mixed argument types
    try:
        result = formatter.format("positional", keyword="value")
    except DynamicFormattingError as e:
        # "Cannot mix positional and keyword arguments"
    
    # Required fields with user-friendly errors
    formatter = DynamicFormatter("{{!;}}")
    try:
        result = formatter.format()
    except RequiredFieldError as e:
        # "Required field missing: position 1" (not internal "__pos_0__")

INTEGRATION EXAMPLES:

1. LOGGING INTEGRATION:
    import logging
    from shared_utils.dynamic_formatting import DynamicLoggingFormatter
    
    def level_color(level):
        return {'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow', 
                'ERROR': 'red', 'CRITICAL': 'magenta'}[level]
    
    # Sections automatically disappear when duration, file_count, etc. are missing
    formatter = DynamicLoggingFormatter(
        "{{#level_color@bold;[;levelname;]}} {{message}} {{Duration: ;duration;s}} {{Files: ;file_count}}",
        functions={'level_color': level_color}
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

2. CLI PROGRESS REPORTING:
    def status_color(status):
        return 'green' if status == 'success' else 'red' if status == 'error' else 'yellow'
    
    def has_errors(count):
        return count > 0
    
    # Positional for main data, keyword for optional details
    formatter = DynamicFormatter(
        "{{#status_color;;}} {{;;}}/{{;;}} {{?has_errors;(;error_count; errors)}} {{Duration: ;duration;s}}",
        functions={'status_color': status_color, 'has_errors': has_errors}
    )
    
    # Usage examples
    print(formatter.format("success", 95, 100, duration=12.5))  # No errors
    print(formatter.format("error", 67, 100, error_count=3))    # No duration
    print(formatter.format("running", 45, 100))                 # Minimal data

3. WEB FRAMEWORK INTEGRATION:
    def format_api_response(status, message, **optional_data):
        formatter = DynamicFormatter(
            "{{#status_color;;}} {{}} {{Records: ;record_count}} {{Errors: ;error_count}} {{Duration: ;response_time;ms}}"
        )
        return formatter.format(status, message, **optional_data)  # Missing fields automatically omitted
    
    # Usage
    response1 = format_api_response("OK", "Request successful", record_count=150, response_time=245)
    response2 = format_api_response("ERROR", "Request failed", error_count=1)  # No records or time

ERROR HANDLING:

Exception Hierarchy:
    DynamicFormattingError (base)
    ├── RequiredFieldError      - Missing required field (marked with !)
    ├── FunctionNotFoundError   - Conditional function not provided  
    ├── ParseError             - Malformed template syntax
    ├── FormatterError         - Invalid color/style token
    └── FunctionExecutionError - Function execution failed

Best Practices:
    try:
        result = formatter.format("arg1", "arg2")  # Positional
        # or
        result = formatter.format(field1="arg1", field2="arg2")  # Keyword
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
    - Positional conversion: O(1) synthetic field mapping

Memory Usage:
    - Simple sections: Minimal overhead (string concatenation)
    - Complex sections: O(spans) temporary state objects
    - Automatic cleanup with proper reset handling

Large Dataset Recommendations:
    # DO: Pre-compile formatters
    formatter = DynamicFormatter("{{Status: ;;}} {{Count: ;}}")
    for record in large_dataset:
        result = formatter.format(record.status, record.count)
    
    # DON'T: Recompile templates in loops
    for record in large_dataset:
        formatter = DynamicFormatter("{{Status: ;;}} {{Count: ;}}")  # Expensive!
        result = formatter.format(record.status, record.count)

ARCHITECTURAL HIGHLIGHTS:

1. Graceful Missing Data Handling:
   The core innovation - template sections automatically return empty strings when their 
   required field is missing from the format data, eliminating manual null checking.
   
2. Positional Argument Support:
   Empty field names in templates ({{}} or {{prefix;;suffix}}) are automatically converted
   to positional argument slots. Arguments are mapped to synthetic field names internally,
   allowing full reuse of existing rendering logic.
   
3. Family-Based State Management:
   Colors, text styles, and conditionals operate in separate "families". Later
   tokens within the same family override earlier ones naturally via ANSI codes:
   {{#red#blue@bold@italic;Text}} → blue, bold, italic text
   
4. Function Fallback System:
   If a token like #level_color isn't a built-in color, the system automatically
   tries to execute it as a function and re-parse the result.
   
5. Two-Level Conditionals:
   - Section level: ?function controls entire template sections
   - Inline level: {?function} controls parts of text within sections
   
6. Escape-Aware Parsing:
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

BACKWARD COMPATIBILITY:
    All existing keyword-based templates continue to work exactly as before.
    Positional argument support is purely additive and only activates when:
    1. Field names are empty in the template ({{}} or {{prefix;;suffix}})
    2. Positional arguments are provided to format()
    
    Cannot mix positional and keyword arguments in a single format() call.
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
        FormattingState
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
        FormattingState
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
    'ParseError',
    
    # Advanced classes for extension
    'TOKEN_FORMATTERS',
    'FormattingState',
    'TemplateParser',
    'FormattedSpan',
    'FormatSection'
]

__version__ = '2.1.0'  # Updated for positional argument support