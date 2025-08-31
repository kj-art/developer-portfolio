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
- **Extensible**: Custom formatting functions, conditional logic, and token handlers
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

### Multi-Parameter Functions (Keyword Arguments Only)
When using keyword arguments, functions can access multiple fields by parameter name matching:

```python
def is_profitable(revenue, costs):
    return revenue and costs and float(revenue) > float(costs)

def risk_assessment(revenue, costs, debt_ratio):
    profit_margin = (float(revenue) - float(costs)) / float(revenue) * 100
    risk = "high" if float(debt_ratio) > 0.6 else "medium" if profit_margin < 10 else "low"
    return f"{risk} risk ({profit_margin:.1f}% margin)"

formatter = TemplateFormatter(
    "{{Company: ;company;}} {{(Revenue: $;revenue;M)}} {{?is_profitable; ✓ Profitable;revenue;}} {{Risk: ;risk_assessment;debt_ratio;}}", 
    functions={'is_profitable': is_profitable, 'risk_assessment': risk_assessment}
)

# All referenced fields must be provided in format() call
result = formatter.format(
    company="TechCorp", 
    revenue="150", 
    costs="120", 
    debt_ratio="0.3"
)
# Output: "Company: TechCorp (Revenue: $150M) ✓ Profitable Risk: low risk (20.0% margin)"
```

**Parameter Matching Rules:**
- Function parameters with names matching format() field names receive those values
- If any parameters are unmatched by field names, function receives the section's field value
- All referenced field names must be provided in the format() call
- Cannot mix positional and keyword arguments in the same format() call

### Positional Arguments
Use positional arguments to fill template sections in order, ignoring field names:

```python
formatter = TemplateFormatter("{{name}} is {{age}} years old from {{city}}")
result = formatter.format("Alice", 25, "Boston")  # "Alice is 25 years old from Boston"

# Custom functions with positional arguments receive only the section's value
def format_name(value):
    return value.upper()

formatter = TemplateFormatter("{{@format_name;;name}} lives in {{city}}", 
                            functions={'format_name': format_name})
result = formatter.format("alice", "boston")  # "ALICE lives in boston"
```

**Limitation**: Multi-parameter functions are not supported with positional arguments. 
Custom functions only receive the individual section's value, not access to other fields.
Use keyword arguments when functions need access to multiple field values.

## Extensibility

### Built-in Token Types
StringSmith includes these formatting token types:
- `#` - Color tokens (red, blue, #FF0000, custom functions)
- `@` - Emphasis tokens (bold, italic, underline, etc.)
- `?` - Conditional tokens (custom boolean functions)
- `$` - Literal tokens (custom text transformation functions)

### Custom Token Handlers
Extend StringSmith with custom token types using the registration decorator:

```python
from stringsmith.tokens import register_token_handler, BaseTokenHandler

@register_token_handler('%')
class CurrencyTokenHandler(BaseTokenHandler):
    """Handle currency formatting tokens like {%USD}."""
    
    RESET_ANSI = ''  # No ANSI codes for this token type
    
    def get_replacement_text(self, token_value: str) -> str:
        currency_symbols = {
            'USD': '$',
            'EUR': '€', 
            'GBP': '£',
            'JPY': '¥'
        }
        return currency_symbols.get(token_value.upper(), token_value)

# Now use in templates
formatter = TemplateFormatter("Price: {{%USD;amount;}}")
result = formatter.format(amount="99.99")  # "Price: $99.99"
```

**Custom Token Handler Requirements:**
- Must inherit from `BaseTokenHandler`
- Must define `RESET_ANSI` class attribute (empty string if no ANSI codes)
- Must implement `get_replacement_text(token_value: str) -> str` method
- Use `@register_token_handler(prefix)` decorator with single-character prefix
- Avoid conflicts with built-in prefixes (`#`, `@`, `?`, `$`)

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

**Argument Types:**

- **Positional arguments** (`*args`): Fill template sections in order, ignoring field names. Custom functions receive only the individual section's value. Use for simple templates where order is predictable.

- **Keyword arguments** (`**kwargs`): Enable field name matching and multi-parameter function support. Custom functions can access multiple field values through intelligent parameter matching. Use when functions need access to multiple fields or when template field order may vary.

- **Mixing restriction**: Cannot use both positional and keyword arguments in the same `format()` call. Raises `StringSmithError` if attempted.

**Custom Function Parameter Matching (Keyword Arguments Only):**
- Functions with parameter names matching format() field names receive those field values
- Functions with no matching parameter names receive the section's field value (legacy behavior)  
- All referenced field names must be provided in the format() call for multi-parameter functions to execute correctly

### Template Section Syntax

```
{{[formatting][prefix][;field_name][;suffix]}}
```

**Formatting tokens:**
- `#color`: Apply color (matplotlib colors, hex codes, or custom functions)
- `@emphasis`: Apply text styling (bold, italic, underline, strikethrough, dim)
- `?function`: Apply conditional function (section appears only if function returns True)
- `$function`: Apply literal transformation function (replace with function result)

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