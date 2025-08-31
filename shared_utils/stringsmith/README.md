# **StringSmith: Professional Template Formatting**

Advanced Python library for conditional template formatting with rich styling. Automatically hides template sections when data is missing, eliminating manual null checks and verbose conditional logic.

---

## **Quick Example**

```python
from stringsmith import TemplateFormatter

# Basic conditional sections
formatter = TemplateFormatter("Hello {{name}}!")
print(formatter.format(name="World"))  # "Hello World!"
print(formatter.format())               # "Hello !" (section empty)

# Sections with prefix/suffix disappear when variable is missing
formatter = TemplateFormatter("{{User: ;name;}} {{(Level ;level;)}}")
print(formatter.format(name="admin", level=5))  # "User: admin (Level 5)"
print(formatter.format(name="admin"))           # "User: admin " (level section gone)
print(formatter.format())                       # "" (both sections gone)
```

---

## **Core Features**

### 1. **Conditional Sections**

Sections automatically hide if the variable is missing.

```python
formatter = TemplateFormatter("{{Welcome ;name;}}{{, you have ;count; messages}}")
formatter.format(name="Alice", count=5)  # "Welcome Alice, you have 5 messages"
formatter.format(name="Alice")           # "Welcome Alice"
formatter.format()                       # "" (entire template hidden)
```

### 2. **Mandatory Fields**

Use `!` to require a variable.

```python
formatter = TemplateFormatter("{{!name}} logged in {{at ;timestamp;}}")
formatter.format(name="admin", timestamp="10:30")  # "admin logged in at 10:30"
# Missing mandatory field raises MissingMandatoryFieldError
```

### 3. **Rich Formatting**

Supports ANSI colors, text emphasis, combined styles, and hex codes.

```python
formatter = TemplateFormatter("{{#red@bold;Error: ;message;}}")
print(formatter.format(message="Failed"))  # Bold red "Error: Failed"

formatter = TemplateFormatter("{{#FF5733@italic;Status: ;status;}}")
print(formatter.format(status="Active"))  # Orange italic "Status: Active"
```

### 4. **Custom Functions**

Use keyword-argument functions for dynamic formatting and conditionals.

```python
def priority_color(level): return 'red' if int(level) > 5 else 'yellow' if int(level) > 2 else 'green'
def is_urgent(level): return int(level) > 7

formatter = TemplateFormatter(
    "{{#priority_color;[;priority;];}} {{?is_urgent;🚨 URGENT 🚨 ;}} {{message}}",
    functions={'priority_color': priority_color, 'is_urgent': is_urgent}
)

print(formatter.format(priority="9", message="Server down"))
# Red "[9] 🚨 URGENT 🚨 Server down"
```

* Multi-field functions supported via keyword arguments.
* Positional arguments only fill the section’s value (no multi-field access).
* Cannot mix positional and keyword arguments in one call.

### 5. **Token Types**

* `#` → Color (named, hex, or function)
* `@` → Text emphasis (bold, italic, underline, etc.)
* `?` → Conditional (section shown only if function returns True)
* `$` → Literal transformation (function replaces section content)

Custom tokens can be added via `BaseTokenHandler` and `@register_token_handler`.

---

## **Advanced Use Cases**

### **Application Logging**

```python
def level_color(level):
    return {'ERROR':'red','WARNING':'yellow','INFO':'blue','DEBUG':'dim'}.get(level.upper(), 'white')
def has_user(user_id): return user_id is not None

log_fmt = TemplateFormatter(
    "{{#level_color;[;level;];}} {{timestamp}} {{module}} {{?has_user;(User: ;user_id;) ;}} {{message}}",
    functions={'level_color': level_color, 'has_user': has_user}
)

print(log_fmt.format(level="INFO", timestamp="10:30", module="auth", message="Login attempt"))
print(log_fmt.format(level="INFO", timestamp="10:30", module="auth", user_id=123, message="Login successful"))
```

### **Data Reporting**

```python
def is_profitable(revenue, costs): return revenue and costs and float(revenue) > float(costs)

report_fmt = TemplateFormatter(
    "{{Company: ;company;}} {{(Revenue: $;revenue;M)}} {{?is_profitable; ✓ Profitable;}} {{[Notes: ;notes;]}}",
    functions={'is_profitable': is_profitable}
)

companies = [
    {'company': 'TechCorp', 'revenue': '150', 'costs': '120', 'notes': 'Strong growth'},
    {'company': 'StartupXYZ', 'revenue': '50'},  
    {'company': 'MegaCorp', 'revenue': '500', 'costs': '600'}
]

for company in companies:
    print(report_fmt.format(**company))
```

---

## **Performance & Production Features**

* **Efficient:** Templates parsed once, reusable for bulk formatting.
* **Thread safe:** Immutable, safe for concurrent use.
* **Extensible:** Custom token types, functions, and conditional logic.
* **Error handling:** Structured exceptions with context.

---

## **Installation**

```bash
pip install -e .
pip install -e ".[colors]"  # Optional color support
pip install -e ".[dev]"     # Development tools
```

**Requirements:** Python 3.7+, optional `rich>=10.0.0` for color support.

---

## **API Reference**

```python
TemplateFormatter(
    template: str,
    delimiter: str = ";",
    escape_char: str = "\\",
    functions: Optional[Dict[str, Callable]] = None
)

# Formatting
format(*args, **kwargs) -> str
```

* `*args` → positional section values, simple usage.
* `**kwargs` → keyword-matched values for multi-field functions.
* Mixing `*args` and `**kwargs` in a call raises `StringSmithError`.