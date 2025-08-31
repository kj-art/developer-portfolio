# StringSmith: Professional Template Formatting

Advanced Python library for conditional template formatting with rich styling support. StringSmith eliminates manual null checking and conditional string building by automatically hiding template sections when their required data isn't available.

## Why StringSmith?

**Problem**: Traditional string formatting requires verbose conditional logic:
```python
# Traditional approach - verbose and error-prone
parts = []
if user_name:
    parts.append(f"User: {user_name}")
if user_id:
    parts.append(f"(ID: {user_id})")
message = " ".join(parts) if parts else "No user data"
```

**Solution**: Declarative conditional formatting:
```python
# StringSmith approach - clean and maintainable  
formatter = TemplateFormatter("{{User: ;user_name;}} {{(ID: ;user_id;)}}")
message = formatter.format(user_name=name, user_id=uid)  # Sections auto-hide when data missing
```

## Enterprise Features

- **Conditional Sections**: Template sections disappear when variables are missing
- **Mandatory Validation**: Required fields (marked with `!`) enforce data presence  
- **Rich Formatting**: ANSI colors, text emphasis, and custom styling functions
- **Performance Optimized**: Templates parsed once, formatted many times efficiently
- **Thread Safe**: Immutable formatters safe for concurrent use
- **Extensible**: Custom formatting functions and conditional logic
- **Professional Error Handling**: Structured exceptions with context for debugging

## Design Philosophy

**Deferred Inline Parsing**: StringSmith uses a hybrid parsing approach where template structure is parsed during initialization, but inline formatting tokens are resolved during format() calls. This design choice prioritizes code simplicity and maintainability over micro-optimizations, making the codebase easier to understand and extend.

**Graceful Degradation**: The core innovation is automatic section hiding when variables are missing. This eliminates the need for manual null checking and conditional string building throughout your application code.

**Performance Characteristics**: Templates are "baked" during initialization to validate syntax and prepare static formatting. Runtime formatting is O(m) where m is the number of template sections. For applications doing frequent formatting with the same template, create the formatter once and reuse it.

## Quick Start

```python
from stringsmith import TemplateFormatter

# Basic conditional sections
formatter = TemplateFormatter("Hello {{name}}!")
print(formatter.format(name="World"))  # "Hello World!"
print(formatter.format())              # "Hello !" (section remains but empty)

# Sections with prefix/suffix disappear entirely when field is missing
formatter = TemplateFormatter("{{User: ;name;}} {{(Level ;level;)}}")  
print(formatter.format(name="admin", level=5))  # "User: admin (Level 5)"
print(formatter.format(name="admin"))           # "User: admin " (level section gone)
print(formatter.format())                       # "" (both sections gone)
```

## Core Features

### Conditional Sections
Template sections automatically hide when their variables are missing:

```python
formatter = TemplateFormatter("{{Welcome ;name;}}{{, you have ;count; messages}}")
formatter.format(name="Alice", count=5)  # "Welcome Alice, you have 5 messages"  
formatter.format(name="Alice")           # "Welcome Alice" (message count hidden)
formatter.format()                       # "" (entire template hidden)
```

### Mandatory Fields
Use `!` prefix to require specific variables:

```python
formatter = TemplateFormatter("{{!name}} logged in {{at ;timestamp;}}")
formatter.format(name="admin", timestamp="10:30")  # "admin logged in at 10:30"
formatter.format(name="admin")                      # "admin logged in " 
# formatter.format(timestamp="10:30")               # Raises MissingMandatoryFieldError
```

### Rich Color Formatting
Support for matplotlib colors, hex codes, and text emphasis:

```python
# Color formatting
formatter = TemplateFormatter("{{#red;Error: ;message;}}")
print(formatter.format(message="Failed"))  # Red "Error: Failed"

# Text emphasis  
formatter = TemplateFormatter("{{@bold;Warning: ;message;}}")
print(formatter.format(message="Check this"))  # Bold "Warning: Check this"

# Combined formatting
formatter = TemplateFormatter("{{#blue@italic;Info: ;message;}}")
print(formatter.format(message="Just so you know"))  # Blue italic "Info: Just so you know"

# Hex colors
formatter = TemplateFormatter("{{#FF5733;Status: ;status;}}")
print(formatter.format(status="Active"))  # Orange "Status: Active"
```

### Custom Functions
Integrate custom formatting and conditional logic:

```python
def priority_color(level):
    return 'red' if int(level) > 5 else 'yellow' if int(level) > 2 else 'green'

def is_urgent(priority):
    return int(priority) > 7

formatter = TemplateFormatter(
    "{{#priority_color;[;priority;];}} {{?is_urgent;🚨 URGENT 🚨 ;}} {{message}}",
    functions={'priority_color': priority_color, 'is_urgent': is_urgent}
)

print(formatter.format(priority="9", message="Server down"))
# Red "[9] 🚨 URGENT 🚨 Server down"

print(formatter.format(priority="3", message="Minor issue"))  
# Yellow "[3] Minor issue" (no urgent flag)
```

### Multi-Parameter Functions
Functions can access multiple fields by matching parameter names to field names:

```python
def is_profitable(revenue, costs):
    return revenue and costs and float(revenue) > float(costs)

def status_summary(status, error_count, warning_count):
    if status == 'error':
        return f"Failed with {error_count} errors"
    elif warning_count > 0:
        return f"Completed with {warning_count} warnings"
    return "Success"

formatter = TemplateFormatter(
    "{{Company: ;company;}} {{?is_profitable; ✓ Profitable;revenue;}} {{Summary: ;status_summary;)}}", 
    functions={'is_profitable': is_profitable, 'status_summary': status_summary}
)

# All referenced fields must be provided in format() call
result = formatter.format(
    company="TechCorp", 
    revenue="150", 
    costs="120", 
    status="complete",
    error_count=0,
    warning_count=2
)
# Output: "Company: TechCorp ✓ Profitable Summary: Completed with 2 warnings"
```

**Parameter Matching Rules:**
- Function parameters with names matching format() arguments receive those values
- If no parameters match field names, the function receives the section's field value (backward compatibility)
- All referenced field names must be provided in the format() call
- Functions with unmatched parameter names receive `None` for those parameters

### Positional Arguments
Use positional arguments with empty field names:

```python
formatter = TemplateFormatter("{{first}} + {{second}} = {{result}}")
result = formatter.format("15", "27", "42")  # "15 + 27 = 42"

# Mix with mandatory fields
formatter = TemplateFormatter("{{!}} and {{}} are {{?both_given;both;}} provided")
result = formatter.format("Alpha", "Beta")  # "Alpha and Beta are both provided"
```

## Production Use Cases

### Application Logging
```python
# Log formatter adapts to available context data
def level_color(level):
    colors = {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'blue', 'DEBUG': 'dim'}
    return colors.get(level.upper(), 'white')

def has_user(user_id):
    return user_id is not None

log_formatter = TemplateFormatter(
    "{{#level_color;[;level;];}} {{timestamp}} {{module}} {{?has_user;(User: ;user_id;) ;}} {{message}}",
    functions={'level_color': level_color, 'has_user': has_user}
)

# Automatically includes user context when available, omits when not
print(log_formatter.format(level="INFO", timestamp="10:30", module="auth", message="Login attempt"))
print(log_formatter.format(level="INFO", timestamp="10:30", module="auth", user_id=123, message="Login successful"))
```

### Data Reporting  
```python
def is_profitable(revenue, costs):
    return revenue and costs and float(revenue) > float(costs)

report_formatter = TemplateFormatter(
    "{{Company: ;company;}} {{(Revenue: $;revenue;M)}} {{?is_profitable; ✓ Profitable;}} {{[Notes: ;notes;]}}",
    functions={'is_profitable': is_profitable}
)

# Works whether data is complete or partial
companies = [
    {'company': 'TechCorp', 'revenue': '150', 'costs': '120', 'notes': 'Strong growth'},
    {'company': 'StartupXYZ', 'revenue': '50'},  # Missing costs and notes
    {'company': 'MegaCorp', 'revenue': '500', 'costs': '600'},  # Not profitable, no notes
]

for company in companies:
    print(report_formatter.format(**company))
# Output:
# Company: TechCorp (Revenue: $150M) ✓ Profitable [Notes: Strong growth]  
# Company: StartupXYZ (Revenue: $50M)
# Company: MegaCorp (Revenue: $500M)
```

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
- `template`: Template string with `{{}}` sections for conditional content
- `delimiter`: Character separating parts within sections (default: `;`)
- `escape_char`: Character for escaping special sequences (default: `\\`)
- `functions`: Dictionary of custom functions for formatting and conditionals

**Methods:**
- `format(*args, **kwargs) -> str`: Format template with variables

### Template Section Syntax

```
{{[formatting][prefix][;field_name][;suffix]}}
```

**Formatting tokens:**
- `#color`: Apply color (matplotlib colors, hex codes, or custom functions)
- `@emphasis`: Apply text styling (bold, italic, underline, strikethrough, dim)
- `?function`: Apply conditional function (section appears only if function returns True)

**Field modifiers:**
- `!field`: Mandatory field (raises error if missing)
- `field`: Optional field (section disappears if missing)
- Empty field: Use positional arguments

## Installation

```python
# Install from source
pip install -e .

# With extended color support
pip install -e ".[colors]"

# With development tools
pip install -e ".[dev]"
```

## Requirements

- Python 3.7+
- No required dependencies for basic functionality
- Optional: `rich>=10.0.0` for comprehensive color support

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=stringsmith

# Run specific test categories
pytest -m "not slow"
```

## License

MIT License - see LICENSE file for details.