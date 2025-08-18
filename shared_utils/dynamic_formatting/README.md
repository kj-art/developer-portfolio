# Dynamic Formatting System

A sophisticated string formatting system that **gracefully handles missing data** - template sections automatically disappear when their required data isn't provided, eliminating manual null checking. Also features conditional sections, function fallback, positional arguments, and family-based formatting state management.

## 🎯 Core Value Proposition

**Automatic missing data handling** - the primary benefit that eliminates tedious conditional string building:

```python
from shared_utils.dynamic_formatting import DynamicFormatter

# Template sections disappear when data is missing - no manual null checking required
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

# Compare to manual approach:
# parts = []
# if message: parts.append(f"Error: {message}")
# if file_count: parts.append(f"Processing {file_count} files") 
# if seconds: parts.append(f"Duration: {seconds}s")
# result = " ".join(parts)
```

## 🚀 Quick Start

```python
from shared_utils.dynamic_formatting import DynamicFormatter

# Basic usage - sections disappear when data is missing
formatter = DynamicFormatter("{{#red@bold;ERROR: ;message}}")
result = formatter.format(message="File not found")
# Output: red bold "ERROR: File not found"

# NEW: Positional arguments for simpler syntax
formatter = DynamicFormatter("{{#red@bold;ERROR: ;}}")
result = formatter.format("File not found")
# Output: red bold "ERROR: File not found"

# Function fallback for dynamic formatting
def level_color(level):
    return {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'green'}[level]

# Keyword arguments (original)
formatter = DynamicFormatter(
    "{{#level_color@bold;[;level;]}} {{message}}",
    functions={'level_color': level_color}
)
result = formatter.format(level="ERROR", message="Something failed")

# Positional arguments (new)
formatter = DynamicFormatter(
    "{{#level_color@bold;[;]}} {{}}",
    functions={'level_color': level_color}
)
result = formatter.format("ERROR", "Something failed")
# Both output: red bold "[ERROR] Something failed"
```

## 🎯 Key Features

### **Graceful Missing Data Handling**
- **Core Feature**: Template sections automatically disappear when data is missing
- No manual null checking or conditional string building required
- Clean, declarative templates that handle incomplete data gracefully
- **NEW**: Works with both keyword and positional arguments

### **Positional Arguments Support**
- **NEW**: Simplified syntax using empty field names: `{{}}` instead of `{{field_name}}`
- Cleaner templates for ordered data (tuples, API responses, etc.)
- All formatting features work with positional args (colors, functions, conditionals)
- Cannot mix positional and keyword arguments in same call

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

### Field Types
```
# Keyword arguments (original)
{{field_name}}        - Named field
{{prefix;field_name}}  - Named field with prefix

# Positional arguments (NEW)
{{}}                   - Positional field (matched by order)
{{prefix;}}            - Positional field with prefix
{{prefix;;suffix}}     - Positional field with prefix and suffix
```

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

### Logging with Graceful Missing Data
```python
from shared_utils.dynamic_formatting import DynamicLoggingFormatter

def level_color(level):
    return {'ERROR': 'red', 'INFO': 'green', 'WARNING': 'yellow'}[level]

# Sections automatically disappear when duration, error_count, etc. are missing
formatter = DynamicLoggingFormatter(
    "{{#level_color@bold;[;levelname;]}} {{message}} {{Duration: ;duration;s}} {{Errors: ;error_count}}",
    functions={'level_color': level_color}
)
```

### CLI Progress Reporting
```python
def status_color(status):
    return 'green' if status == 'success' else 'red'

# Only shows error count when errors > 0, duration when provided, etc.
formatter = DynamicFormatter(
    "{{#status_color;Status: ;status}} {{Processed: ;processed}}/{{total}} {{Errors: ;error_count}} {{Duration: ;duration;s}}",
    functions={'status_color': status_color}
)
```

### API Response Formatting
```python
# Gracefully handles responses with missing fields
# Keyword style
formatter = DynamicFormatter(
    "{{#blue;API Response:}} {{Success - ;record_count; records}} {{Errors: ;error_count}} {{Duration: ;response_time;ms}}"
)

# Positional style (NEW)
formatter = DynamicFormatter(
    "{{#blue;API Response:}} {{Success - ; records}} {{Errors: ;}} {{Duration: ;ms}}"
)

# All sections appear when data is complete
response1 = formatter.format(150, 0, 245)  # Using positional args
# "API Response: Success - 150 records Duration: 245ms"

# Missing sections disappear automatically  
response2 = formatter.format(150)  # Only record count provided
# "API Response: Success - 150 records"
```

## 🏗️ Architecture Highlights

### **1. Automatic Missing Data Handling**
The core innovation - template sections return empty strings when their required field is missing:
```python
formatter = DynamicFormatter("{{Status: ;status}} {{Count: ;count}}")

# Missing status field - only count section appears
result = formatter.format(count=42)  # "Count: 42"

# Missing count field - only status section appears  
result = formatter.format(status="OK")  # "Status: OK"

# All missing - empty result
result = formatter.format()  # ""
```

### **2. Positional Arguments Implementation**
Converts positional args to synthetic keyword args internally:
```python
# Template with empty fields
formatter = DynamicFormatter("{{Error: ;}} {{Count: ;}}")

# Positional args converted to: {'__pos_0__': 'Failed', '__pos_1__': 42}
result = formatter.format("Failed", 42)  # "Error: Failed Count: 42"

# Graceful handling of missing positional args
result = formatter.format("Failed")  # "Error: Failed"
```

### **3. Family-Based State Management**
Colors, text styles, and conditionals operate in separate "families":
```python
"{{#red@bold;Text}} {#blue@normal;More}} {@italic;End}}"
# "Text" = red+bold, "More" = blue+normal, "End" = blue+italic
```

### **4. Performance Optimizations**
- **Simple sections**: Efficient string concatenation for basic templates
- **Complex sections**: Optimized span rendering with minimal resets for advanced formatting
- **Template compilation**: Parse once, format many times
- **Lazy formatting**: ANSI codes only applied for console output

### **5. Comprehensive Error Handling**
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
    "{{#level_color@bold;[;levelname;]}} {{message}} {{Duration: ;duration;s}} {{Memory: ;memory_mb;MB}}"
))
```

### Web Framework Integration
```python
def format_api_response(data):
    formatter = DynamicFormatter(
        "{{#status_color;HTTP ;status_code}} {{Records: ;count}} {{Errors: ;error_count}} {{Duration: ;response_time;ms}}"
    )
    return formatter.format(**data)  # Missing fields automatically omitted
```

### CLI Tool Integration  
```python
def show_progress(processed, total, errors=None, duration=None):
    formatter = DynamicFormatter(
        "{{#green;Progress:}} {{processed}}/{{total}} {{Errors: ;errors}} {{Duration: ;duration;s}}"
    )
    print(formatter.format(processed=processed, total=total, errors=errors, duration=duration))

# Positional version
def show_progress_positional(*args):
    formatter = DynamicFormatter(
        "{{#green;Progress:}} {{}}/{{}} {{Errors: ;}} {{Duration: ;s}}"
    )
    print(formatter.format(*args))
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

## 🆕 What's New in v2.1.0

### Positional Arguments Support
- **New Syntax**: Use `{{}}` instead of `{{field_name}}` for positional matching
- **Cleaner Templates**: Better for ordered data like tuples, API responses
- **Full Feature Support**: Colors, functions, conditionals all work with positional args
- **Error Handling**: User-friendly error messages convert internal field names to "position 1", "position 2", etc.

### Examples
```python
# Before (keyword only)
formatter = DynamicFormatter("{{#red;Error: ;message}} {{Code: ;code}}")
result = formatter.format(message="Failed", code=404)

# After (positional support)
formatter = DynamicFormatter("{{#red;Error: ;}} {{Code: ;}}")
result = formatter.format("Failed", 404)
# Same output: red "Error: Failed Code: 404"

# Mixed templates (positional + named fields)
formatter = DynamicFormatter("{{#red;Alert: ;}} {{details: ;named_field}}")
result = formatter.format("System down")  # named_field section disappears
# Output: red "Alert: System down"
```

## 🚀 Getting Started

1. **Install**: Copy the `shared_utils/dynamic_formatting/` package to your project
2. **Import**: `from shared_utils.dynamic_formatting import DynamicFormatter`
3. **Create**: `formatter = DynamicFormatter("{{Status: ;status}} {{Count: ;count}}")`
4. **Format**: `result = formatter.format(status="OK")  # Missing count field ignored`

## 📖 More Examples

See `examples.py` for comprehensive real-world usage examples including:
- Graceful missing data handling (core feature)
- **NEW**: Positional arguments demonstrations
- Advanced logging setups
- CLI progress reporting
- API response formatting
- Error handling patterns
- Performance optimization techniques

Run the examples: `python shared_utils/dynamic_formatting/examples.py`

## 🧪 Testing

Run the comprehensive regression test suite:
```bash
python shared_utils/dynamic_formatting/test_positional_regression.py
```

This ensures all existing functionality remains intact while testing the new positional arguments feature.

---

**Built for enterprise environments where data completeness varies and manual null checking becomes tedious. The primary benefit is eliminating conditional string building through automatic missing data handling, now enhanced with positional arguments for cleaner, more readable templates.**