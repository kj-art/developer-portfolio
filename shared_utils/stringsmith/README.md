# StringSmith: Professional Template Formatting

**Production-ready Python library for conditional template formatting with rich styling and dynamic content control.**

StringSmith eliminates manual null checking and conditional string building by automatically adapting templates based on available data. Template sections disappear when their variables are missing, while rich formatting options provide professional-grade output for logging systems, CLI applications, and business reporting.

## Quick Start

```python
from stringsmith import TemplateFormatter

# Basic conditional sections - sections disappear when data is missing
formatter = TemplateFormatter("{{Hello ;name;}}")
print(formatter.format(name="World"))  # "Hello World"
print(formatter.format())               # "" (section disappears)

# Rich formatting with colors and emphasis
formatter = TemplateFormatter("{{#red@bold;ERROR: ;message;}}")
print(formatter.format(message="Failed"))  # Red bold "ERROR: Failed"

# Custom functions for dynamic behavior
def priority_color(level):
    return 'red' if int(level) > 5 else 'yellow'

formatter = TemplateFormatter(
    "{{#priority_color;Level ;priority;: ;message;}}", 
    functions=[priority_color]
)
print(formatter.format(priority=8, message="Critical"))  # Red "Level 8: Critical"
```

## Key Features

### Conditional Sections with Graceful Degradation
Template sections automatically disappear when their data is missing, enabling clean output without manual checks.

```python
formatter = TemplateFormatter("{{User: ;name;}} {{(Level ;level;)}}")
formatter.format(name="admin", level=5)  # "User: admin (Level 5)"
formatter.format(name="admin")           # "User: admin " (level section gone)
formatter.format()                       # "" (both sections gone)
```

### Rich ANSI Formatting
Full support for colors, text emphasis, and hex color codes with automatic reset handling.

```python
# Named colors and emphasis
formatter = TemplateFormatter("{{#red@bold;Critical: ;message;}}")

# Hex colors  
formatter = TemplateFormatter("{{#FF5733@italic;Status: ;status;}}")

# Combined styles
formatter = TemplateFormatter("{{#blue@underline;Info: ;details;}}")
```

### Multi-Parameter Custom Functions
Dynamic formatting and conditional logic through user-defined functions with intelligent parameter matching.

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

### Mandatory Field Validation
Enforce required data with the `!` prefix for critical template sections.

```python
formatter = TemplateFormatter("{{!username}} logged in {{at ;timestamp;}}")
formatter.format(username="admin", timestamp="10:30")  # "admin logged in at 10:30"
formatter.format(username="admin")                     # "admin logged in "
# formatter.format() raises MissingMandatoryFieldError
```

## Comprehensive Feature Demonstration

Run the full feature demonstration to see StringSmith's capabilities in action:

```bash
python -m shared_utils.stringsmith.demo
```

The demo showcases:
- **Professional logging systems** with conditional context
- **Business reporting** with dynamic formatting
- **Creative applications** like sparkline charts and progress indicators
- **Real-time status displays** for GUI applications
- **Performance monitoring** with memory usage visualization
- **Advanced formatting patterns** for enterprise use cases

## Professional Use Cases

### Application Logging with Contextual Information
```python
def level_color(level):
    return {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'blue'}.get(level.upper(), 'white')

def has_user(user_id):
    return user_id is not None and str(user_id).strip()

log_formatter = TemplateFormatter(
    "{{#level_color;[;level;]}} {{timestamp}} {{module}} {{?has_user;(User: ;user_id;) }}{{message}}",
    functions=[level_color, has_user]
)

# Produces contextual log entries:
# [ERROR] 10:30 auth (User: 123) Login failed
# [INFO] 10:31 system Backup completed
```

### Business Intelligence Reporting
```python
def performance_color(revenue):
    rev = float(revenue) if revenue else 0
    return 'green' if rev > 100 else 'yellow' if rev > 50 else 'red'

def has_notes(notes):
    return notes and notes.strip()

report_formatter = TemplateFormatter(
    "{{Company: ;company;}} {{#performance_color;(Revenue: $;revenue;M)}} {{?has_notes;[Notes: ;notes;]}}",
    functions=[performance_color, has_notes]
)
```

### CLI Status Messages with Dynamic Indicators
```python
def status_icon(status):
    return {'running': '⏳', 'complete': '✅', 'failed': '❌'}.get(status, '❓')

def progress_color(percent):
    return 'green' if percent > 75 else 'yellow' if percent > 25 else 'red'

status_formatter = TemplateFormatter(
    "{{$status_icon;status}} {{task}} {{#progress_color;[;progress;%]}} {{?has_eta;ETA: ;eta;}}",
    functions=[status_icon, progress_color, lambda eta: eta]
)
```

## Template Syntax Reference

### Section Structure
```
{{[!][formatting;]prefix;field_name;suffix}}
```

- `!` - Mandatory field (throws error if missing)
- `formatting` - Optional color/emphasis tokens
- `prefix` - Text before field value
- `field_name` - Variable name (empty for positional args)
- `suffix` - Text after field value

### Formatting Tokens
| Token | Purpose | Examples |
|-------|---------|----------|
| `#` | Colors | `#red`, `#FF0000`, custom color functions |
| `@` | Text emphasis | `@bold`, `@italic`, `@underline` |
| `?` | Conditionals | Show section only if function returns True |
| `$` | Literal transforms | Replace content with function result |

### Custom Functions
Functions can access multiple template fields through parameter name matching:

```python
# Multi-parameter function receives matched values
def is_profitable(revenue, costs): 
    return float(revenue) > float(costs)

# Single-parameter function receives field value
def priority_color(level): 
    return 'red' if int(level) > 5 else 'green'

# No-parameter function receives nothing
def random_color():
    return choice(['red', 'blue', 'green'])
```

## Advanced Features

### Positional Arguments
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
Apply formatting to specific text spans within template parts:

```python
formatter = TemplateFormatter("{{Status: {#green}OK{#normal} ;message;}}")
formatter.format(message="All systems operational")
```

## Performance & Architecture

- **Template Parsing**: Done once during initialization for fast formatting
- **Runtime Complexity**: O(n) where n is the number of template sections
- **Thread Safety**: Immutable after creation, safe for concurrent use
- **Memory Efficient**: Minimal overhead, suitable for high-frequency formatting
- **Production Ready**: Comprehensive error handling and graceful degradation

## Installation

```bash
pip install -r requirements.txt
```

**Requirements**: Python 3.7+

## API Reference

### TemplateFormatter

```python
TemplateFormatter(
    template: str,
    delimiter: str = ";",
    escape_char: str = "\\", 
    functions: list[Callable] | dict[str, Callable] | None = None
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

**StringSmith** demonstrates professional API design with enterprise-grade conditional formatting capabilities. Perfect for logging systems, CLI applications, business reporting, and any scenario requiring adaptive, formatted text output with zero manual null checking.