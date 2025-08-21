# StringSmith

Advanced template formatting with conditional sections and inline formatting for Python.

StringSmith provides f-string-like functionality with powerful conditional sections that are completely omitted when variables aren't provided, plus rich formatting options including colors and text emphasis.

## Features

- **Conditional Sections**: Sections disappear entirely when variables are missing
- **Mandatory Sections**: Throw errors when required variables are missing  
- **Color Formatting**: Support for matplotlib colors and hex codes
- **Text Emphasis**: Bold, italic, underline, strikethrough, and more
- **Custom Functions**: User-defined formatting and conditional functions
- **Inline Formatting**: Apply formatting to specific parts within sections
- **Flexible Arguments**: Support for both positional and keyword arguments
- **Escape Sequences**: Include literal braces and delimiters when needed

## Quick Start

```python
from stringsmith import TemplateFormatter

# Basic usage
formatter = TemplateFormatter("Hello {{name}}!")
print(formatter.format(name="World"))  # "Hello World!"
print(formatter.format())  # "Hello !" (section partially omitted)

# Conditional sections with prefixes and suffixes
formatter = TemplateFormatter("Score: {{Player ;name; scored }}{{points}} points")
print(formatter.format(name="Alice", points=100))  # "Score: Player Alice scored 100 points"
print(formatter.format(points=100))  # "Score: 100 points" (first section omitted)

# Mandatory sections
formatter = TemplateFormatter("{{!name}} is required")
print(formatter.format(name="Alice"))  # "Alice is required"
print(formatter.format())  # Raises MissingMandatoryFieldError

# Color formatting
formatter = TemplateFormatter("{{#red;Error: ;message;}}")
print(formatter.format(message="Something went wrong"))  # Red colored text

# Text emphasis
formatter = TemplateFormatter("{{@bold;Warning: ;message;}}")
print(formatter.format(message="Check this"))  # Bold text

# Positional arguments
formatter = TemplateFormatter("{{first}} and {{second}}")
print(formatter.format("Hello", "World"))  # "Hello and World"
print(formatter.format("Hello"))  # "Hello and " (second section omitted)

# Custom delimiters and escape characters
formatter = TemplateFormatter("Use ~{name~} for {{name}}", escape_char="~")
print(formatter.format(name="variables"))  # "Use {name} for variables"
```

## Template Syntax

### Basic Sections

- `{{variable}}` - Simple variable substitution
- `{{prefix;variable}}` - Variable with prefix text
- `{{prefix;variable;suffix}}` - Variable with prefix and suffix text

### Mandatory Sections

Add `!` immediately after `{{` to make a section mandatory:

- `{{!variable}}` - Required variable (throws error if missing)
- `{{!prefix;variable;suffix}}` - Required variable with prefix and suffix

### Formatting Sections

Add formatting tokens after the optional `!`:

- `{{#color;variable}}` - Apply color formatting
- `{{@emphasis;variable}}` - Apply text emphasis
- `{{?condition;variable}}` - Apply boolean condition

### Color Formatting

Colors can be specified as:
- **Named colors**: `red`, `blue`, `green`, `yellow`, `cyan`, `magenta`, `white`, `black`
- **Extended named colors** (with optional dependencies): `orange`, `coral`, `crimson`, `navy`, `teal`, etc.
- **Hex codes**: `FF0000`, `#FF0000`, `00FF00`
- **Custom functions**: User-defined functions that return color names, hex codes, or ANSI codes

```python
formatter = TemplateFormatter("{{#red;Error: ;message;}}")
formatter = TemplateFormatter("{{#FF0000;Error: ;message;}}")
formatter = TemplateFormatter("{{#coral;Important: ;message;}}")  # Requires extended colors

def get_alert_color():
    return 'orange'  # Can return any valid color format

formatter = TemplateFormatter("{{#get_alert_color;Alert: ;message;}}", 
                            functions={'get_alert_color': get_alert_color})
```

### Text Emphasis

Supported emphasis styles:
- `bold` - Bold text
- `italic` - Italic text  
- `underline` - Underlined text
- `strikethrough` - Strikethrough text
- `dim` - Dimmed text

```python
formatter = TemplateFormatter("{{@bold;Warning: ;message;}}")
formatter = TemplateFormatter("{{@italic;Note: ;message;}}")
```

### Inline Formatting

Apply formatting to specific parts within a section:

```python
# Inline color changes
formatter = TemplateFormatter("{{Status: {#green}OK{#normal} - ;message;}}")

# Inline emphasis
formatter = TemplateFormatter("{{Result: {@bold}SUCCESS{@normal} - ;details;}}")

# Inline conditions
formatter = TemplateFormatter("{{Status{?is_urgent}: URGENT{@normal};message;}}")
```

Inline formatting rules:
- `{#color}` - Change color from this point forward
- `{@emphasis}` - Add emphasis from this point forward  
- `{?function}` - Apply boolean condition (rest of part disappears if false)
- `{#normal}` or `{@normal}` - Reset formatting family to default
- Formatting resets between parts (prefix/field/suffix are independent)
- Emphasis can stack (e.g., bold + italic), colors override each other

### Custom Functions

Define custom formatting and conditional functions:

```python
def highlight_errors(text):
    return f'>>> {text} <<<'  # Custom text wrapping

def is_urgent(message):
    return 'urgent' in message.lower()

def get_status_color():
    return 'orange'  # Return color name, hex code, or ANSI

formatter = TemplateFormatter(
    "{{#get_status_color@highlight_errors;Alert: ;message;}} {{?is_urgent;Priority: HIGH}}",
    functions={
        'highlight_errors': highlight_errors,
        'is_urgent': is_urgent,
        'get_status_color': get_status_color
    }
)
```

Functions can:
- **Color functions** (`#`): Return color names, hex codes (`#FF0000`), or ANSI codes
- **Emphasis functions** (`@`): Return formatted text or ANSI codes
- **Conditional functions** (`?`): Return `True`/`False` to show/hide sections

### Delimiters and Escape Characters

Change the delimiter and escape character used in templates:

```python
# Custom delimiter
formatter = TemplateFormatter("{{prefix|variable|suffix}}", delimiter="|")

# Custom escape character (default is backslash)
formatter = TemplateFormatter("Use ~{name~} for {{name}}", escape_char="~")

# Both custom
formatter = TemplateFormatter("Use ~{name~} for {{name}}", delimiter="|", escape_char="~")
```

### Escape Sequences

Include literal characters that would otherwise be interpreted as syntax:

```python
# Literal braces (default backslash escaping)
formatter = TemplateFormatter("Use \\{name\\} for {{name}}")
print(formatter.format(name="variables"))  # "Use {name} for variables"

# Literal delimiters
formatter = TemplateFormatter("{{Ratio\\;percentage;value;}}")
print(formatter.format(value="50%"))  # "Ratio;percentage50%"

# Custom escape character (cleaner syntax)
formatter = TemplateFormatter("Use ~{name~} for {{name}}", escape_char="~")
print(formatter.format(name="variables"))  # "Use {name} for variables"

# Escape the escape character itself
formatter = TemplateFormatter("Path: ~~{{path}}", escape_char="~")
print(formatter.format(path="home/user"))  # "Path: ~home/user"
```

## Arguments

### Keyword Arguments

Pass variables by name:

```python
formatter = TemplateFormatter("{{greeting}} {{name}}!")
result = formatter.format(greeting="Hello", name="Alice")  # "Hello Alice!"
```

### Positional Arguments

Pass variables by position (field names in template are ignored):

```python
formatter = TemplateFormatter("{{first}} {{second}}")
result = formatter.format("Hello", "World")  # "Hello World"

# Mandatory positional
formatter = TemplateFormatter("{{!first}} {{second}}")
result = formatter.format("Hello")  # "Hello " (second omitted)
result = formatter.format()  # Error: "Required positional argument 0 not provided"
```

**Important**: Cannot mix positional and keyword arguments in the same call.

## API Reference

### TemplateFormatter

```python
TemplateFormatter(
    template: str,
    delimiter: str = ";",
    escape_char: str = "\\", 
    functions: Optional[Dict[str, Callable]] = None
)
```

**Parameters:**
- `template`: Template string with `{{}}` sections
- `delimiter`: Character to separate parts within sections (default: `;`)
- `escape_char`: Character used for escaping special characters (default: `\\`)
- `functions`: Dictionary of custom functions for formatting and conditionals

**Methods:**
- `format(*args, **kwargs) -> str`: Format template with variables

## Advanced Examples

### Complex Conditional Formatting

```python
def is_error(level):
    return level.lower() == 'error'

def is_warning(level):
    return level.lower() == 'warning'

formatter = TemplateFormatter(
    "{{?is_error;#red@bold;[ERROR];level;}} {{?is_warning;#yellow;[WARN];level;}} {{message}}",
    functions={'is_error': is_error, 'is_warning': is_warning}
)

print(formatter.format(level="error", message="Something broke"))
# Output: [ERROR] Something broke (in red bold)

print(formatter.format(level="info", message="All good"))  
# Output: All good (no level prefix)
```

### Status Reports with Inline Formatting

```python
def is_success(status):
    return status == "success"

formatter = TemplateFormatter(
    "{{Task {?is_success}{#green}✓{#normal}{@normal}: ;task;}} {{Status{?is_success}: ;status;}}"
    functions={'is_success': is_success}
)

print(formatter.format(task="Deploy", status="success"))
# Output: Task ✓: Deploy Status: success (with green checkmark)

print(formatter.format(task="Deploy", status="failed"))
# Output: Task : Deploy Status: failed (no checkmark)
```

## Installation

```bash
pip install stringsmith
```

For extended color support with hundreds of named colors:

```bash
pip install stringsmith[colors]
```

This installs `rich` for comprehensive color support including:
- All CSS4 named colors (140+ colors like `coral`, `crimson`, `navy`, `teal`)
- Hex color codes (`#FF0000`, `ff0000`)
- RGB values (`rgb(255,0,0)`)
- HSL values (`hsl(0,100%,50%)`)
- Automatic color format conversion and optimal ANSI generation

## Requirements

- Python 3.7+
- No required dependencies for basic functionality
- Optional: `rich>=10.0.0` for comprehensive color support

## License

MIT License - see LICENSE file for details.