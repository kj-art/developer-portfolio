#!/usr/bin/env python3
"""
Examples demonstrating StringSmith functionality.
"""

import sys
import os

# Add current directory to path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared_utils.stringsmith import TemplateFormatter


def basic_examples():
    """Demonstrate basic functionality."""
    print("=== Basic Examples ===")
    
    # Simple variable substitution
    formatter = TemplateFormatter("Hello {{name}}!")
    print(f"With name: '{formatter.format(name='Alice')}'")
    print(f"Without name: '{formatter.format()}'")
    
    # Prefix and suffix
    formatter = TemplateFormatter("{{Player ;name; scored }}{{points}} points")
    print(f"Both provided: '{formatter.format(name='Alice', points=100)}'")
    print(f"Only points: '{formatter.format(points=100)}'")
    print(f"Only name: '{formatter.format(name='Alice')}'")
    
    # Mandatory sections
    formatter = TemplateFormatter("{{!name}} is required, {{optional}} is not")
    print(f"Both provided: '{formatter.format(name='Alice', optional='test')}'")
    print(f"Only required: '{formatter.format(name='Alice')}'")
    try:
        formatter.format(optional='test')
    except Exception as e:
        print(f"Missing required: {e}")
    print()


def positional_examples():
    """Demonstrate positional arguments."""
    print("=== Positional Arguments ===")
    
    formatter = TemplateFormatter("{{greeting}} {{name}}!")
    print(f"Positional: '{formatter.format('Hello', 'World')}'")
    print(f"Partial: '{formatter.format('Hello')}'")
    
    # With mandatory
    formatter = TemplateFormatter("{{!first}} and {{second}}")
    print(f"Both: '{formatter.format('Alpha', 'Beta')}'")
    print(f"First only: '{formatter.format('Alpha')}'")
    try:
        formatter.format()
    except Exception as e:
        print(f"None provided: {e}")
    print()


def formatting_examples():
    """Demonstrate formatting functionality."""
    print("=== Formatting Examples ===")
    
    # Color formatting
    formatter = TemplateFormatter("{{#red;Error: ;message;}}")
    result = formatter.format(message="Something went wrong")
    print(f"Red error: '{result}'")
    
    # Text emphasis
    formatter = TemplateFormatter("{{@bold;Warning: ;message;}}")
    result = formatter.format(message="Check this")
    print(f"Bold warning: '{result}'")
    
    # Combined formatting
    formatter = TemplateFormatter("{{#blue@italic;Info: ;message;}}")
    result = formatter.format(message="Just so you know")
    print(f"Blue italic: '{result}'")
    
    # Hex colors
    formatter = TemplateFormatter("{{#FF5733;Colored ;message;}}")
    result = formatter.format(message="text")
    print(f"Hex color: '{result}'")
    print()


def inline_formatting_examples():
    """Demonstrate inline formatting."""
    print("=== Inline Formatting ===")
    
    # Color changes within a part
    formatter = TemplateFormatter("{{Status: {#green}OK{#normal};message;}}")
    result = formatter.format(message="All systems operational")
    print(f"Inline color: '{result}'")
    
    # Emphasis changes
    formatter = TemplateFormatter("{{Result: {@bold}SUCCESS{@normal};details;}}")
    result = formatter.format(details="Task completed")
    print(f"Inline emphasis: '{result}'")
    
    # Multiple inline changes
    formatter = TemplateFormatter("{{Log: {#red}ERROR{#normal} {@bold}Critical{@normal};message;}}")
    result = formatter.format(message="System failure")
    print(f"Multiple inline: '{result}'")
    print()


def conditional_examples():
    """Demonstrate conditional functionality."""
    print("=== Conditional Examples ===")
    
    # Boolean functions
    def is_error(level):
        return level.lower() == 'error'
    
    def is_warning(level):
        return level.lower() == 'warning'
    
    def is_urgent(message):
        return 'urgent' in message.lower()
    
    # Section-level conditions (simplified for now)
    formatter = TemplateFormatter(
        "{{?is_error;[ERROR] ;level;}} {{?is_warning;[WARN] ;level;}} {{message}}",
        functions={
            'is_error': is_error,
            'is_warning': is_warning
        }
    )

    print(formatter.get_template_info())
    
    print(f"Error: '{formatter.format(level='error', message='Something broke')}'")
    print(f"Warning: '{formatter.format(level='warning', message='Check this')}'")
    print(f"Info: '{formatter.format(level='info', message='All good')}'")
    
    # Basic conditional
    formatter = TemplateFormatter(
        "{{?is_urgent;URGENT: ;task;}}",
        functions={'is_urgent': is_urgent}
    )
    
    print(f"Urgent task: '{formatter.format(task='Fix urgent bug')}'")
    print(f"Normal task: '{formatter.format(task='Review code')}'")
    print()


def custom_function_examples():
    """Demonstrate custom functions."""
    print("=== Custom Functions ===")
    
    # Custom formatting function
    def highlight(text):
        return f">>> {text} <<<"
    
    def box_text(text):
        return f"[{text}]"
    
    # Custom condition function
    def has_numbers(text):
        return any(c.isdigit() for c in str(text))
    
    # Separate sections for different formatting (simplified)
    formatter = TemplateFormatter(
        "{{#highlight;Important: ;message;}} {{?has_numbers;Code: ;code;}}",
        functions={
            'highlight': highlight,
            'has_numbers': has_numbers
        }
    )
    
    print(f"With code: '{formatter.format(message='Server down', code='ERR123')}'")
    print(f"No code: '{formatter.format(message='Server down', code='UNKNOWN')}'")
    
    # Box text function with emphasis
    formatter = TemplateFormatter(
        "{{@box_text;Status: ;status;}}",
        functions={'box_text': box_text}
    )
    
    print(f"Boxed status: '{formatter.format(status='READY')}'")
    print()


def fun_examples():
    """Demonstrate fun and creative uses."""
    print("=== Fun Examples ===")
    
    import random
    
    # Random color function
    def random_color(field):
        return random.choice(['red', 'green', 'blue', 'yellow', 'cyan', 'magenta'])
    
    # Your original example - now working with inline formatting!
    rc = "{#random_color}"
    template_string = f"{{{{{rc}A{rc}B{rc}C ;{rc}field; {rc}X{rc}Y{rc}Z}}}}"
    print(f"Template: {template_string}")
    
    formatter = TemplateFormatter(
        template_string,
        functions={'random_color': random_color}
    )
    
    def same_code_different_colors():
        return formatter.format(field="FIELD_VALUE")
    
    results = [same_code_different_colors(), same_code_different_colors(), same_code_different_colors()]
    print(f"1. Random character colors: \n\ta. {results[0]} \n\tb. {results[1]} \n\tc. {results[2]}")
    
    # Progress indicator
    def get_progress_color():
        return random.choice(['green', 'yellow', 'red'])
    
    def make_bar(text):
        return f"[{'█' * len(text)}{'░' * (10 - len(text))}]"
    
    formatter = TemplateFormatter(
        "{{#get_progress_color@make_bar;Progress: ;status;}} Complete!",
        functions={
            'get_progress_color': get_progress_color,
            'make_bar': make_bar
        }
    )
    
    for status in ['25%', '50%', '100%']:
        result = formatter.format(status=status)
        print(f"Progress: '{result}'")
    
    print()


def complex_example():
    """Demonstrate a complex real-world example."""
    print("=== Complex Example: Log Formatter ===")
    
    def is_error(level):
        return level.upper() == 'ERROR'
    
    def is_warning(level):
        return level.upper() == 'WARNING'
    
    def has_user(user):
        return user is not None and user.strip() != ''
    
    def format_timestamp(ts):
        return f"\033[90m{ts}\033[0m"  # Dim gray
    
    # Simplified log entry formatter using only working syntax
    formatter = TemplateFormatter(
        "{{@format_timestamp;timestamp}} {{?is_error;[ERROR] ;level;}}{{?is_warning;[WARN] ;level;}}{{?has_user;User ;user;: }}{{message}}",
        functions={
            'is_error': is_error,
            'is_warning': is_warning,
            'has_user': has_user,
            'format_timestamp': format_timestamp
        }
    )
    
    # Different log scenarios
    logs = [
        {'timestamp': '2024-01-15 10:30:00', 'level': 'ERROR', 'user': 'alice', 
         'message': 'Database connection failed'},
        {'timestamp': '2024-01-15 10:31:00', 'level': 'WARNING', 'user': None, 
         'message': 'High memory usage detected'},
        {'timestamp': '2024-01-15 10:32:00', 'level': 'INFO', 'user': 'bob', 
         'message': 'User login successful'},
        {'timestamp': '2024-01-15 10:33:00', 'level': 'INFO', 'user': None, 
         'message': 'System startup complete'}
    ]
    
    for log in logs:
        result = formatter.format(**log)
        print(f"Log: '{result}'")
    
    print()


def escape_examples():
    """Demonstrate escape sequences."""
    print("=== Escape Examples ===")
    
    # Escaping braces with default backslash
    formatter = TemplateFormatter("Use \\{variable\\} to define {{name}}")
    result = formatter.format(name="templates")
    print(f"Escaped braces: '{result}'")
    
    # Escaping delimiters with default backslash
    formatter = TemplateFormatter("{{Ratio\\;percentage;value;}}")
    result = formatter.format(value="50%")
    print(f"Escaped delimiter: '{result}'")
    
    # Custom escape character (cleaner)
    formatter = TemplateFormatter("Use ~{variable~} to define {{name}}", escape_char="~")
    result = formatter.format(name="templates")
    print(f"Custom escape char: '{result}'")
    
    # Escaping the custom escape character itself
    formatter = TemplateFormatter("Path: ~~{{path}}", escape_char="~")
    result = formatter.format(path="home/user")
    print(f"Escaped escape char: '{result}'")
    
    # Custom delimiter
    formatter = TemplateFormatter("{{prefix|variable|suffix}}", delimiter="|")
    result = formatter.format(variable="test")
    print(f"Custom delimiter: '{result}'")
    
    # Both custom delimiter and escape char
    formatter = TemplateFormatter("{{prefix~|data|variable|suffix}}", delimiter="|", escape_char="~")
    result = formatter.format(variable="test")
    print(f"Both custom: '{result}'")
    print()


if __name__ == "__main__":
    basic_examples()
    positional_examples() 
    formatting_examples()
    inline_formatting_examples()
    conditional_examples()
    custom_function_examples()
    fun_examples()
    complex_example()
    escape_examples()
    
    print("All examples completed!")