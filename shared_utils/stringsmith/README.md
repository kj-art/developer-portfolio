# StringSmith: Professional Template Formatting

Advanced Python library for conditional template formatting with rich styling and dynamic content control. Templates automatically adapt based on available data, eliminating manual null checks and conditional logic.

## Quick Start

```python
from stringsmith import TemplateFormatter

# Basic conditional formatting
formatter = TemplateFormatter("{{Hello ;name;}}")
print(formatter.format(name="World"))  # "Hello World"
print(formatter.format())               # "" (section disappears when data missing)

# Rich formatting with colors and emphasis
formatter = TemplateFormatter("{{#red@bold;Error: ;message;}}")
print(formatter.format(message="Failed"))  # Bold red "Error: Failed"
```

## Key Features

### Conditional Sections
Template sections automatically disappear when their data is missing, enabling clean output without manual checks.

```python
formatter = TemplateFormatter("{{User: ;name;}} {{(Level ;level;)}}")
formatter.format(name="admin", level=5)  # "User: admin (Level 5)"
formatter.format(name="admin")           # "User: admin " (level section gone)
formatter.format()                       # "" (both sections gone)
```

### Rich Formatting
Full support for ANSI colors, text emphasis, and hex color codes.

```python
# Named colors and emphasis
formatter = TemplateFormatter("{{#red@bold;Critical: ;message;}}")

# Hex colors  
formatter = TemplateFormatter("{{#FF5733@italic;Status: ;status;}}")

# Combined styles
formatter = TemplateFormatter("{{#blue@underline;Info: ;details;}}")
```

### Custom Functions
Dynamic formatting and conditional logic through user-defined functions.

```python
def priority_color(level):
    return 'red' if int(level) > 5 else 'yellow' if int(level) > 2 else 'green'

def is_urgent(priority):
    return int(priority) > 7

formatter = TemplateFormatter(
    "{{#priority_color;[;priority;]}} {{?is_urgent;🚨 URGENT 🚨 ;}} {{message}}",
    functions={'priority_color': priority_color, 'is_urgent': is_urgent}
)

print(formatter.format(priority="9", message="Server down"))
# Red "[9] 🚨 URGENT 🚨 Server down"
```

### Multi-Parameter Functions
Functions can access multiple template fields through parameter name matching.

```python
def is_profitable(revenue, costs):
    return revenue and costs and float(revenue) > float(costs)

formatter = TemplateFormatter(
    "{{Company: ;company;}} {{?is_profitable; ✓ Profitable;revenue;}}",
    functions={'is_profitable': is_profitable}
)

formatter.format(company="TechCorp", revenue="150", costs="100")
# "TechCorp ✓ Profitable"
```

### Mandatory Fields
Enforce required data with the `!` prefix.

```python
formatter = TemplateFormatter("{{!username}} logged in {{at ;timestamp;}}")
formatter.format(username="admin", timestamp="10:30")  # "admin logged in at 10:30"
formatter.format(username="admin")                     # "admin logged in "
# formatter.format() raises MissingMandatoryFieldError
```

## Token Types

| Token | Purpose | Examples |
|-------|---------|----------|
| `#` | Colors | `#red`, `#FF0000`, custom color functions |
| `@` | Text emphasis | `@bold`, `@italic`, `@underline` |
| `?` | Conditionals | Show section only if function returns True |
| `$` | Literal transforms | Replace content with function result |

## Professional Use Cases

### Application Logging

```python
def level_color(level):
    return {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'blue'}.get(level.upper(), 'white')

def has_user(user_id):
    return user_id is not None and str(user_id).strip()

log_formatter = TemplateFormatter(
    "{{#level_color;[;level;]}} {{timestamp}} {{module}} {{?has_user;(User: ;user_id;) }}{{message}}",
    functions={'level_color': level_color, 'has_user': has_user}
)

# Produces contextual log entries:
# [ERROR] 10:30 auth (User: 123) Login failed
# [INFO] 10:31 system Backup completed
```

### Business Reporting

```python
def performance_color(revenue):
    rev = float(revenue) if revenue else 0
    return 'green' if rev > 100 else 'yellow' if rev > 50 else 'red'

def has_notes(notes):
    return notes and notes.strip()

report_formatter = TemplateFormatter(
    "{{Company: ;company;}} {{#performance_color;(Revenue: $;revenue;M)}} {{?has_notes;[Notes: ;notes;]}}",
    functions={'performance_color': performance_color, 'has_notes': has_notes}
)
```

### CLI Status Messages

```python
def status_icon(status):
    return {'running': '⏳', 'complete': '✅', 'failed': '❌'}.get(status, '❓')

def progress_color(percent):
    return 'green' if percent > 75 else 'yellow' if percent > 25 else 'red'

status_formatter = TemplateFormatter(
    "{{$status_icon;status}} {{task}} {{#progress_color;[;progress;%]}} {{?has_eta;ETA: ;eta;}}",
    functions={'status_icon': status_icon, 'progress_color': progress_color, 'has_eta': lambda eta: eta}
)
```

## Advanced Features

### Positional Arguments
Use empty field names for ordered data input.

```python
formatter = TemplateFormatter("{{}} + {{}} = {{}}")
formatter.format("15", "27", "42")  # "15 + 27 = 42"
```

### Custom Delimiters and Escaping

```python
# Custom delimiter
formatter = TemplateFormatter("{{prefix|field|suffix}}", delimiter="|")

# Escape sequences
formatter = TemplateFormatter("Use \\{name\\} for {{name}}")
formatter.format(name="variables")  # "Use {name} for variables"

# Custom escape character
formatter = TemplateFormatter("Use ~{name~} for {{name}}", escape_char="~")
```

### Inline Formatting
Apply formatting to specific text spans within template parts.

```python
formatter = TemplateFormatter("{{Status: {#green}OK{#normal} ;message;}}")
formatter.format(message="All systems operational")
```

## Performance

- **Template Parsing**: Done once during initialization for fast formatting
- **Runtime Complexity**: O(n) where n is the number of template sections
- **Thread Safety**: Immutable after creation, safe for concurrent use
- **Memory Efficient**: Minimal overhead, suitable for high-frequency formatting

## Installation

```bash
pip install stringsmith
pip install "stringsmith[colors]"  # Extended color support via Rich
```

**Requirements**: Python 3.7+

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

**Methods:**
- `format(*args, **kwargs) -> str`: Format template with provided data
- `get_template_info() -> Dict`: Get template structure information

**Arguments:**
- Use `*args` for positional field values (simple cases)
- Use `**kwargs` for named field values (enables multi-parameter functions)
- Cannot mix positional and keyword arguments in a single call

## Error Handling

```python
from stringsmith import StringSmithError, MissingMandatoryFieldError

try:
    result = formatter.format(**data)
except MissingMandatoryFieldError as e:
    print(f"Required field missing: {e}")
except StringSmithError as e:
    print(f"Template error: {e}")
```

## Extension System

Create custom token handlers for specialized formatting needs:

```python
from stringsmith.tokens import BaseTokenHandler, register_token_handler

@register_token_handler('%', reset_ansi='')
class CurrencyTokenHandler(BaseTokenHandler):
    def get_replacement_text(self, token_value: str) -> str:
        return f"${token_value}" if token_value == "USD" else token_value
```

---

**StringSmith** eliminates the complexity of conditional string formatting while providing professional-grade styling capabilities. Perfect for logging systems, CLI applications, business reporting, and any scenario where clean, adaptive text output is essential.