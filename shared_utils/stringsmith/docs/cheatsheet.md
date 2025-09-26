# StringSmith Cheat Sheet

Quick reference for professional template formatting with StringSmith.

---

## Basic Usage

```python
from stringsmith import TemplateFormatter

formatter = TemplateFormatter("Hello {{name}}!")
formatter.format(name="Alice")  # "Hello Alice!"
formatter.format()              # "Hello !" (section empty)
````

### Optional Sections with Prefix/Suffix

```python
formatter = TemplateFormatter("{{User: ;name;}} {{(Level ;level;)}}")
formatter.format(name="admin", level=5)  # "User: admin (Level 5)"
formatter.format(name="admin")           # "User: admin "
formatter.format()                       # ""
```

---

## Conditional & Mandatory Fields

* **Optional**: `field` → section hides if missing
* **Mandatory**: `!field` → raises `MissingMandatoryFieldError` if missing

```python
formatter = TemplateFormatter("{{!name}} logged in {{at ;timestamp;}}")
formatter.format(name="admin", timestamp="10:30")
```

---

## Colors & Text Emphasis

* Color: `#red`, `#FF5733`, or custom function
* Emphasis: `@bold`, `@italic`, etc.
* Combined: `#blue@italic`

```python
formatter = TemplateFormatter("{{#red@bold;Error: ;message;}}")
formatter.format(message="Failed")  # Red bold "Error: Failed"
```

---

## Custom Functions

* Use `$` for literal transformations
* Conditional `?function` → section shows if function returns `True`
* Multi-parameter functions match keyword args

```python
def is_urgent(priority): return int(priority) > 7
formatter = TemplateFormatter("{{?is_urgent;🚨 URGENT 🚨 ;}} {{message}}", functions={'is_urgent': is_urgent})
formatter.format(priority=9, message="Server down")
```

---

## Positional Arguments

```python
formatter = TemplateFormatter("{{name}} is {{age}} from {{city}}")
formatter.format("Alice", 25, "Boston")
```

**Note:** Positional args → functions only see section value, not other fields.

---

## Token Types

| Token | Purpose                                     |
| ----- | ------------------------------------------- |
| `#`   | Color (named, hex, or function)             |
| `@`   | Emphasis (bold, italic, etc., or function)  |
| `?`   | Conditional (custom boolean function)       |
| `$`   | Literal transformation function             |

---

## Extensibility

* Register custom token handler with `@register_token_handler(prefix)`
* Inherit from `BaseTokenHandler`
* Implement `get_replacement_text(token_value: str) -> str`

```python
@register_token_handler('%')
class CurrencyTokenHandler(BaseTokenHandler):
    RESET_ANSI = ''
    def get_replacement_text(self, token_value): return "$" if token_value=="USD" else token_value
```

---

## Professional Use Cases

### Logging

```python
formatter = TemplateFormatter(
    "{{#level_color;[;level;];}} {{timestamp}} {{module}} {{?has_user;(User: ;user_id;)}} {{message}}",
    functions={'level_color': level_color, 'has_user': has_user}
)
```

### Data Reporting

```python
formatter = TemplateFormatter(
    "{{Company: ;company;}} {{(Revenue: $;revenue;M)}} {{?is_profitable; ✓ Profitable;}} {{[Notes: ;notes;]}}",
    functions={'is_profitable': is_profitable}
)
```

---

## Escape Sequences

* Escape braces: `\{` and `\}`
* Custom delimiter: `TemplateFormatter(delimiter="|")`
* Custom escape char: `TemplateFormatter(escape_char="~")`
