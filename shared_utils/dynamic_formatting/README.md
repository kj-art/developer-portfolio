# Dynamic Formatting System

**The easy f-string that leaves out sections when arguments aren't supplied.**

Eliminates tedious conditional string building by automatically hiding template sections when their data is missing. No more manual null checking or building parts arrays.

## 🎯 Core Value: Automatic Missing Data Handling

**The primary benefit** - template sections disappear when data is missing:

```python
from shared_utils.dynamic_formatting import DynamicFormatter

# The old way - manual conditional building
parts = []
if error: parts.append(f"Error: {error}")
if count: parts.append(f"Processing {count} files") 
if duration: parts.append(f"Duration: {duration}s")
result = " ".join(parts)

# The new way - sections automatically disappear
formatter = DynamicFormatter("{{Error: ;error}} {{Processing ;count; files}} {{Duration: ;duration;s}}")

# All data present
result = formatter.format(error="Failed", count=25, duration=12.5)
# Output: "Error: Failed Processing 25 files Duration: 12.5s"

# Some data missing - sections automatically disappear
result = formatter.format(count=25)  # Only count provided
# Output: "Processing 25 files"

# No data - empty result
result = formatter.format()
# Output: ""
```

## 🚀 Positional Arguments - Even Simpler

**NEW**: Use `{{}}` instead of field names for ordered data:

```python
# Template with 4 sections
formatter = DynamicFormatter("{{Error: ;}} {{Processing ; files}} {{Duration: ;s}} {{Memory: ;MB}}")

# Supply 1 argument - only first section appears
result = formatter.format("Connection failed")
# Output: "Error: Connection failed"

# Supply 2 arguments - first two sections appear  
result = formatter.format("Connection failed", 25)
# Output: "Error: Connection failed Processing 25 files"

# Supply all 4 arguments - all sections appear
result = formatter.format("Connection failed", 25, 12.5, 128)
# Output: "Error: Connection failed Processing 25 files Duration: 12.5s Memory: 128MB"

# This is the core design: fewer arguments = fewer sections, automatically
```

### **All Valid Positional Patterns**

The system recognizes these patterns for positional arguments:

```python
# Basic patterns
DynamicFormatter("{{}}")                        # Empty field - positional only
DynamicFormatter("{{#red}}")                    # Token only - positional with formatting
DynamicFormatter("{{field_name}}")              # Single field - works for both positional/keyword

# Prefix/suffix patterns  
DynamicFormatter("{{my_field;}}")               # Field as prefix (my_field;)
DynamicFormatter("{{prefix;field_name}}")       # Prefix;field pattern
DynamicFormatter("{{prefix;field_name;suffix}}") # Prefix;field;suffix pattern

# With formatting tokens
DynamicFormatter("{{#red;field_name}}")         # Token;field pattern
DynamicFormatter("{{#red@bold;prefix;field_name}}")        # Token;prefix;field pattern  
DynamicFormatter("{{#red@bold;prefix;field_name;suffix}}") # Full token;prefix;field;suffix pattern
```

**Key rule**: For positional arguments, field names are ignored - the system maps arguments by position regardless of what the field is named in the template.

## 🎨 Color & Formatting Support

All formatting features work with both positional and keyword arguments:

```python
# Colors and styles work with both argument types
formatter = DynamicFormatter("{{#red@bold;ERROR: ;}} {{#green;Count: ;}}")

# Keyword arguments
result = formatter.format(error="Failed", count=42)

# Positional arguments (same template, cleaner call)
result = formatter.format("Failed", 42)
# Both output: red bold "ERROR: Failed" green "Count: 42"

# Missing data still works
result = formatter.format("Failed")  # Only first argument
# Output: red bold "ERROR: Failed"

# Advanced patterns with positional args
formatter = DynamicFormatter("{{#status_color@bold;[;]}} {{}} {{Code: ;}}")

# Function fallback for dynamic formatting
def status_color(status):
    return {'ERROR': 'red', 'SUCCESS': 'green', 'WARNING': 'yellow'}[status]

formatter = DynamicFormatter("{{#status_color@bold;[;]}} {{}} {{Code: ;}}", 
                           functions={'status_color': status_color})

result = formatter.format("ERROR", "Database failed", 500)
# Output: red bold "[ERROR] Database failed Code: 500"

result = formatter.format("SUCCESS", "Login completed")  # No error code
# Output: green bold "[SUCCESS] Login completed"
```

## 🔧 Quick Start

```python
from shared_utils.dynamic_formatting import DynamicFormatter

# Basic usage
formatter = DynamicFormatter("{{Status: ;status}} {{Count: ;count}}")
result = formatter.format(status="OK")  # count section disappears
# Output: "Status: OK"

# Positional version
formatter = DynamicFormatter("{{Status: ;}} {{Count: ;}}")
result = formatter.format("OK")  # second section disappears
# Output: "Status: OK"

# With colors
formatter = DynamicFormatter("{{#green@bold;SUCCESS: ;}} {{Records: ;}}")
result = formatter.format("Complete", 150)
# Output: green bold "SUCCESS: Complete Records: 150"
```

## 🔌 Real-World Integration

### Logging Integration
```python
import logging
from shared_utils.dynamic_formatting import DynamicLoggingFormatter

def level_color(level):
    return {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'green'}[level]

# Automatic missing field handling - duration, error_count only appear when present
handler = logging.StreamHandler()
handler.setFormatter(DynamicLoggingFormatter(
    "{{#level_color@bold;[;levelname;]}} {{message}} {{Duration: ;duration;s}} {{Errors: ;error_count}}",
    functions={'level_color': level_color}
))
```

### CLI Progress Reporting
```python
def show_progress(processed, total, errors=None, duration=None):
    # Only shows error count when errors > 0, duration when provided
    formatter = DynamicFormatter(
        "{{#green;Progress:}} {{processed}}/{{total}} {{Errors: ;errors}} {{Duration: ;duration;s}}"
    )
    print(formatter.format(processed=processed, total=total, errors=errors, duration=duration))

# Positional version - even cleaner
def show_progress_positional(*args):
    formatter = DynamicFormatter(
        "{{#green;Progress:}} {{}}/{{}} {{Errors: ;}} {{Duration: ;s}}"
    )
    print(formatter.format(*args))

# Usage examples
show_progress_positional(150, 200)                    # "Progress: 150/200"
show_progress_positional(150, 200, 5)                 # "Progress: 150/200 Errors: 5"  
show_progress_positional(150, 200, 5, 12.3)          # "Progress: 150/200 Errors: 5 Duration: 12.3s"
```

### API Response Formatting
```python
# Handles incomplete API responses gracefully
formatter = DynamicFormatter(
    "{{#blue;API Response:}} {{Success - ; records}} {{Errors: ;}} {{Duration: ;ms}}"
)

# All data present
result = formatter.format(150, 0, 245)
# Output: "API Response: Success - 150 records Duration: 245ms"

# Partial data - missing sections disappear automatically
result = formatter.format(150)
# Output: "API Response: Success - 150 records"
```

## 🎯 Key Features

### **Graceful Missing Data Handling** ⭐ **CORE FEATURE**
- Template sections automatically disappear when data is missing
- No manual null checking or conditional string building required
- Works with both keyword and positional arguments
- Clean, declarative templates that handle incomplete data gracefully

### **Positional Arguments Support** 🆕
- Simplified syntax using empty field names: `{{}}` instead of `{{field_name}}`
- Perfect for ordered data (tuples, API responses, function arguments)
- Fewer arguments = fewer sections (automatic truncation)
- All formatting features work with positional args

### **Colors & Text Formatting**
- ANSI colors: `#red`, `#green`, `#blue`, etc.
- Hex colors: `#FF5733`, `#00FF00`, etc.  
- Text styles: `@bold`, `@italic`, `@underline`
- Combinations: `#red@bold`, `#00FF00@italic@underline`

### **Conditional Sections**
- Function-controlled visibility: `{{?show_debug;Debug info: ;value}}`
- Section-level and inline conditionals
- Dynamic formatting based on runtime conditions

### **Output Modes**
- `console`: Full ANSI color codes for terminals
- `file`: Plain text with formatting stripped for log files

## 🏗️ Architecture Highlights

### **Template Compilation**
Parse once, format many times for performance:
```python
formatter = DynamicFormatter("{{Error: ;}} {{Count: ;}}")  # Parsed once
result1 = formatter.format("Failed", 42)                   # Fast formatting
result2 = formatter.format("Timeout")                      # Fast formatting
```

### **Missing Data Detection**
Sections return empty strings when required data is missing:
```python
# Template: "{{Status: ;}} {{Count: ;}}"
# Args: ["OK"] (missing second argument)
# Result: "Status: OK" (second section disappears)
```

### **Family-Based State Management**
Colors, text styles, and conditionals operate independently:
```python
"{{#red@bold;Text}} {{#blue@normal;More}} {{@italic;End}}"
# "Text" = red+bold, "More" = blue+normal, "End" = blue+italic  
```

## 📖 More Examples

See `examples.py` for comprehensive demonstrations:
- All color and formatting features
- Advanced logging setups
- CLI progress reporting patterns
- API response formatting
- Error handling examples
- Performance optimization techniques

Run the examples: `python shared_utils/dynamic_formatting/examples.py`

## 🧪 Testing

Run the comprehensive test suite to verify all functionality:
```bash
python shared_utils/dynamic_formatting/test_positional_regression.py
```

## 🚀 Getting Started

1. **Copy** the `shared_utils/dynamic_formatting/` package to your project
2. **Import**: `from shared_utils.dynamic_formatting import DynamicFormatter`  
3. **Create**: `formatter = DynamicFormatter("{{Error: ;}} {{Count: ;}}")`
4. **Format**: `result = formatter.format("Failed")  # Missing count section disappears`

---

**Built for the common scenario where data completeness varies and you're tired of writing conditional string building logic. The core innovation is automatic missing data handling - template sections simply disappear when their data isn't provided.**