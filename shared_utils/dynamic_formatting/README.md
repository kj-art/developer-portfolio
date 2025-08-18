# Dynamic Formatting System

A sophisticated string formatting system with conditional sections, function fallback, and family-based formatting state management. Designed for enterprise logging, CLI tools, and dynamic text generation.

## 🚀 Quick Start

```python
from shared_utils.dynamic_formatting import DynamicFormatter

# Basic formatting with colors and styles
formatter = DynamicFormatter("{{#red@bold;ERROR: ;message}}")
result = formatter.format(message="File not found")
# Output: red bold "ERROR: File not found"

# Function fallback for dynamic formatting
def level_color(level):
    return {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'green'}[level]

formatter = DynamicFormatter(
    "{{#level_color@bold;[;level;]}} {{message}}",
    functions={'level_color': level_color}
)
result = formatter.format(level="ERROR", message="Something failed")
# Output: red bold "[ERROR] Something failed"
```

## 🎯 Key Features

### **Family-Based Architecture**
- **Colors** (`#red`, `#blue`, `#hex_color`)
- **Text Styles** (`@bold`, `@italic`, `@underline`) 
- **Conditionals** (`?function_name`)
- Each family operates independently, preventing conflicts

### **Function Fallback System**
- If `#level_color` isn't a built-in color, automatically calls `level_color()` function
- Functions receive field values as parameters
- Results are recursively parsed as formatting tokens

### **Two-Level Conditionals**
```python
# Section-level: Show/hide entire sections
"{{Processing}} {{?has_errors;ERROR COUNT: ;error_count}}"

# Inline: Show/hide parts within sections  
"{{Processing{?has_files} files{?is_urgent} URGENT: ;status}}"
```

### **Comprehensive Escape Handling**
```python
"{{Use \\{brackets\\} for: ;syntax}}"  # → "Use {brackets} for: variables"
```

## 📋 Syntax Reference

### Template Structure
```
{{[!][?condition][#color][@text][prefix;]field[;suffix]}}
```

- `!` = Required field (throws error if missing)
- `?function` = Conditional (show section only if function returns True)
- `#token` = Color formatting (red, blue, hex, or function name)
- `@token` = Text formatting (bold, italic, underline, or function name)

### Inline Formatting
```
{#red}text     - Color this text red
{@bold}text    - Make this text bold  
{?func}text    - Show text only if func returns True
```

### Escape Sequences
```
\{  → literal {
\}  → literal }
\;  → literal ;
```

## 🔧 Common Use Cases

### Advanced Logging
```python
from shared_utils.dynamic_formatting import DynamicLoggingFormatter

def level_color(level):
    return {'ERROR': 'red', 'INFO': 'green', 'WARNING': 'yellow'}[level]

formatter = DynamicLoggingFormatter(
    "{{#level_color@bold;[;levelname;]}} {{message}} {{?has_duration;in ;duration;s}}",
    functions={'level_color': level_color, 'has_duration': lambda d: d > 0}
)
```

### CLI Progress Reporting
```python
def status_color(status):
    return 'green' if status == 'success' else 'red'

formatter = DynamicFormatter(
    "{{#status_color;Status: ;status}} - {{processed}}/{{total}} {{?has_errors;(;errors; errors)}}",
    functions={'status_color': status_color, 'has_errors': lambda e: e > 0}
)
```

### Data Processing Summaries
```python
formatter = DynamicFormatter(
    "{{@bold;Summary:}} {{processed}} records {{#severity_color;(;errors; errors)}} "
    "{{?has_warnings;with ;warnings; warnings}}",
    functions={
        'severity_color': lambda e: 'red' if e > 0 else 'green',
        'has_warnings': lambda w: w > 0
    }
)
```

## 🏗️ Architecture Highlights

### **1. Family-Based State Management**
Colors, text styles, and conditionals operate in separate "families":
```python
"{{#red@bold;Text}} {#blue@normal;More}} {@italic;End}}"
# "Text" = red+bold, "More" = blue+normal, "End" = blue+italic
```

### **2. Performance Optimizations**
- **Simple sections**: Efficient string concatenation
- **Complex sections**: Optimized span rendering with minimal resets
- **Template compilation**: Parse once, format many times
- **Lazy formatting**: ANSI codes only applied for console output

### **3. Comprehensive Error Handling**
```python
try:
    result = formatter.format(**data)
except RequiredFieldError:
    # Handle missing required fields
except FunctionNotFoundError:
    # Handle missing conditional functions  
except DynamicFormattingError:
    # Handle other formatting errors
```

## 📊 Performance Characteristics

- **Parse Time**: O(n) where n = template length
- **Format Time**: O(m) where m = output length  
- **Memory**: O(spans) for complex templates, minimal for simple ones
- **Best Practice**: Reuse formatter instances for repeated formatting

```python
# ✅ GOOD: Reuse formatter
formatter = DynamicFormatter(template)
for record in dataset:
    result = formatter.format(**record)

# ❌ BAD: Recreate formatter  
for record in dataset:
    formatter = DynamicFormatter(template)  # Expensive!
    result = formatter.format(**record)
```

## 🔌 Integration Examples

### Logging Integration
```python
import logging
handler = logging.StreamHandler()
handler.setFormatter(DynamicLoggingFormatter(
    "{{#level_color@bold;[;levelname;]}} {{message}}"
))
```

### Web Framework Integration
```python
def format_api_response(data):
    formatter = DynamicFormatter(
        "{{#status_color;HTTP ;status_code}} {{?has_data;- ;count; records}}"
    )
    return formatter.format(**data)
```

### CLI Tool Integration  
```python
def show_progress(processed, total, errors):
    formatter = DynamicFormatter(
        "{{#green;Progress:}} {{processed}}/{{total}} {{?has_errors;(;errors; errors)}}"
    )
    print(formatter.format(processed=processed, total=total, errors=errors))
```

## 🎨 Output Modes

- **`console`**: Full ANSI color codes and formatting for terminals
- **`file`**: Plain text with formatting stripped for log files

```python
formatter = DynamicFormatter(template, output_mode='file')
```

## 🛠️ Extending the System

### Adding Custom Formatters
```python
from shared_utils.dynamic_formatting.formatters import FormatterBase

class CustomFormatter(FormatterBase):
    def get_family_name(self) -> str:
        return 'custom'
    
    def parse_token(self, token_value: str, field_value=None):
        # Your parsing logic
        pass
    
    def apply_formatting(self, text: str, parsed_tokens: List, output_mode: str = 'console'):
        # Your formatting logic  
        pass

# Register with system
from shared_utils.dynamic_formatting.formatters import TOKEN_FORMATTERS
TOKEN_FORMATTERS['%'] = CustomFormatter()
```

## 📚 Exception Reference

- **`DynamicFormattingError`** - Base exception
- **`RequiredFieldError`** - Missing required field (marked with `!`)
- **`FunctionNotFoundError`** - Conditional function not provided
- **`ParseError`** - Malformed template syntax
- **`FormatterError`** - Invalid color/style token
- **`FunctionExecutionError`** - Function execution failed
- **`StackingError`** - Invalid formatting combination

## 🚀 Getting Started

1. **Install**: Copy the `shared_utils/dynamic_formatting/` package to your project
2. **Import**: `from shared_utils.dynamic_formatting import DynamicFormatter`
3. **Create**: `formatter = DynamicFormatter("{{#red;Hello ;name}}")`
4. **Format**: `result = formatter.format(name="World")`

## 📖 More Examples

See `examples.py` for comprehensive real-world usage examples including:
- Advanced logging setups
- CLI progress reporting
- Data processing summaries
- API response formatting
- Error handling patterns
- Performance optimization techniques

---

**Built for enterprise environments with performance, reliability, and extensibility in mind.**