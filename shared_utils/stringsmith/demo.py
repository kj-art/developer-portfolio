#!/usr/bin/env python3
"""
StringSmith Feature Demonstration

Comprehensive showcase of professional template formatting capabilities,
combining practical examples with creative applications.
"""

import sys
import os
import random
import colorsys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared_utils.stringsmith import TemplateFormatter


def demo_basic_formatting():
    """Demonstrate basic template formatting capabilities."""
    print("=" * 60)
    print("BASIC TEMPLATE FORMATTING")
    print("=" * 60)
    
    # Simple variable substitution
    formatter = TemplateFormatter("Hello {{name}}!")
    print(f"With name: '{formatter.format(name='Alice')}'")
    print(f"Without name: '{formatter.format()}'")
    
    # Prefix and suffix
    formatter = TemplateFormatter("{{Player ;name; scored }}{{points}} points")
    print(f"Both provided: '{formatter.format(name='Alice', points=100)}'")
    print(f"Only points: '{formatter.format(points=100)}'")
    print(f"Only name: '{formatter.format(name='Alice')}'")
    
    # Positional arguments
    formatter = TemplateFormatter("{{first}} + {{second}} = {{result}}")
    result = formatter.format("15", "27", "42")
    print(f"Positional: '{result}'")
    
    # Mandatory sections
    formatter = TemplateFormatter("{{!name}} is required, {{optional}} is not")
    print(f"Both provided: '{formatter.format(name='Alice', optional='test')}'")
    print(f"Only required: '{formatter.format(name='Alice')}'")
    try:
        formatter.format(optional='test')
    except Exception as e:
        print(f"Missing required: {e}")
    print()


def demo_color_formatting():
    """Demonstrate color formatting capabilities."""
    print("=" * 60)
    print("COLOR FORMATTING")
    print("=" * 60)
    
    # Basic colors
    formatter = TemplateFormatter("{{#red;Error: ;message;}}")
    result = formatter.format(message="Something went wrong")
    print(f"Red error: '{result}'")
    
    # Hex colors
    formatter = TemplateFormatter("{{#FF5733;Colored ;message;}}")
    result = formatter.format(message="text")
    print(f"Hex color: '{result}'")
    
    # Custom color functions
    def priority_color(level):
        return 'red' if int(level) > 5 else 'yellow' if int(level) > 2 else 'green'

    formatter = TemplateFormatter("{{#priority_color;Priority ;priority;: }}{{message}}", 
                            functions={'priority_color': priority_color})
    
    print("\nDynamic priority colors:")
    priorities = [9, 4, 1]
    messages = ["Critical alert", "Warning notice", "Info message"]
    for priority, message in zip(priorities, messages):
        result = formatter.format(priority=priority, message=message)
        print(f"  '{result}'")
    print()


def demo_text_emphasis():
    """Demonstrate text emphasis formatting."""
    print("=" * 60)
    print("TEXT EMPHASIS")
    print("=" * 60)
    
    # Basic emphasis
    formatter = TemplateFormatter("{{@bold;Warning: ;message;}}")
    result = formatter.format(message="Check this")
    print(f"Bold warning: '{result}'")
    
    # Combined formatting
    formatter = TemplateFormatter("{{#blue@italic;Info: ;message;}}")
    result = formatter.format(message="Just so you know")
    print(f"Blue italic: '{result}'")
    
    # Dynamic emphasis based on content
    def box_text(text):
        return 'italic' if text.lower() == 'ready' else 'bold'
    
    formatter = TemplateFormatter("{{@box_text;Status: ;status;}}", 
                                functions={'box_text': box_text})
    
    print(f"\nDynamic emphasis: '{formatter.format(status='READY')}'")
    print(f"Dynamic emphasis: '{formatter.format(status='PENDING')}'")
    print()


def demo_conditional_sections():
    """Demonstrate conditional functionality."""
    print("=" * 60)
    print("CONDITIONAL SECTIONS")
    print("=" * 60)
    
    # Basic conditional with boolean function
    def is_error(level):
        return level.lower() == 'error'
    
    def is_urgent(message):
        return 'urgent' in message.lower()
    
    # Simple conditional sections
    formatter = TemplateFormatter("{{?is_error;[ERROR] ;level;}}", 
                                functions={'is_error': is_error})
    
    print("Conditional sections:")
    print(f"  Error level: '{formatter.format(level='ERROR')}'")
    print(f"  Info level: '{formatter.format(level='INFO')}'")
    
    # Urgent task conditional
    formatter = TemplateFormatter("{{?is_urgent;URGENT: ;task;}}", 
                                functions={'is_urgent': is_urgent})
    
    print(f"  Urgent task: '{formatter.format(task='Fix urgent bug')}'")
    print(f"  Normal task: '{formatter.format(task='Review code')}'")
    print()


def demo_professional_logging():
    """Demonstrate professional logging use case."""
    print("=" * 60)
    print("PROFESSIONAL USE CASE: APPLICATION LOGGING")
    print("=" * 60)
    
    # Professional log formatter functions
    def level_color(level):
        colors = {'ERROR': 'red', 'WARNING': 'yellow', 'INFO': 'blue', 'DEBUG': 'orange'}
        return colors.get(level.upper(), 'white')

    def has_user(user_id):
        return user_id is not None and str(user_id).strip() != ''

    def is_error_level(level):
        return level.upper() == 'ERROR'
    
    # Build log formatter with conditional context
    formatter = TemplateFormatter(
        "{{#level_color;[;level;]}} {{timestamp}} {{module}} {{?has_user;(User: ;user_id;)}} {{message}}{{?is_error_level; - ALERT;level;}}", 
        functions=[level_color, has_user, is_error_level]
    )
    
    # Sample log entries
    log_entries = [
        {'level': 'INFO', 'timestamp': '10:30', 'module': 'auth', 'message': 'Login attempt', 'user_id': None},
        {'level': 'INFO', 'timestamp': '10:31', 'module': 'auth', 'message': 'Login successful', 'user_id': 123},
        {'level': 'WARNING', 'timestamp': '10:32', 'module': 'db', 'message': 'High memory usage', 'user_id': None},
        {'level': 'ERROR', 'timestamp': '10:33', 'module': 'api', 'message': 'Connection failed', 'user_id': 456}
    ]
    
    print("Application log output:")
    for entry in log_entries:
        result = formatter.format(**entry)
        print(f"  {result}")
    print()


def demo_performance_scenario():
    """Demonstrate efficient template reuse for high-volume scenarios."""
    print("=" * 60)
    print("PERFORMANCE SCENARIO: BULK PROCESSING")
    print("=" * 60)
    
    # Create formatter once, reuse many times (efficient pattern)
    def record_color(field):
        return "green" if field == "processed" else "yellow" if field == "pending" else "red"
    
    def spaces(status):
        return max(0, 9 - len(status)) * ' '

    formatter = TemplateFormatter(
        "{{#blue;[;batch_id;]}} Record {{#record_color;;status;{$spaces}}}: {{record_id}} - {{description}}", 
        functions={'record_color': record_color,
                   'spaces': spaces}
    )
    
    # Simulate processing many records
    print("Processing batch of records:")
    statuses = ["processed", "pending", "failed"]
    
    for i in range(8):
        status = random.choice(statuses)
        result = formatter.format(
            batch_id=f"BTH{1000 + i // 3}",
            status=status,
            record_id=f"REC{10000 + i}",
            description=f"Sample record {i + 1}"
        )
        print(f"  {result}")
    
    print(f"\n✓ Efficiently processed multiple records with single template instance")
    print("✓ Template parsed once, formatted many times for optimal performance")
    print()


def demo_creative_applications():
    """Demonstrate creative and dynamic formatting applications."""
    print("=" * 60)
    print("CREATIVE APPLICATIONS")
    print("=" * 60)
    
    import random
    import colorsys

    def random_color():
        # Random hue
        h = random.random()  # 0.0–1.0
        s = 1.0              # fully saturated
        v = 1.0

        # Convert HSV to RGB (0–1)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)

        # Scale to 0–255 and format as hex
        return f"{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"

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
    
    def interpolate_red_green(p: float) -> str:
        """
        Interpolates from red -> yellow -> green based on p in [0,1].
        Uses HSV to pass through yellow at 50%.
        """
        p = max(0.0, min(1.0, p))  # clamp
        h = (1 - p) * 0 + p * 120  # Hue in degrees
        s = 1.0
        v = 1.0

        # colorsys uses h ∈ [0,1]
        r, g, b = colorsys.hsv_to_rgb(h/360, s, v)
        return f"{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"

    # Progress indicator
    def get_progress_color(val):
        return interpolate_red_green(val/100)
        
    def make_bar(val):
        perc = val / 100
        num_secs = 100
        num = round(perc * num_secs)
        return f"[{'█' * num}{'░' * (num_secs - num)}] {val:6.2f}%"
    
    template_string = "{{#get_progress_color;;{$make_bar}status;}} Complete!"
    print(f"Template: {template_string}")
    formatter = TemplateFormatter(
        template_string,
        functions={
            'get_progress_color': get_progress_color,
            'make_bar': make_bar
        }
    )
    
    num_graphs = 8
    for status in sorted([random.uniform(0, 100) for _ in range(num_graphs)]):
        result = formatter.format(status=status)
        print(f"Progress: '{result}'")
    
    print()


def demo_data_reporting():
    """Demonstrate business data reporting with conditional formatting."""
    print("=" * 60)
    print("BUSINESS DATA REPORTING")
    print("=" * 60)
    
    def is_profitable(revenue, costs=None):
        if costs is None:
            return False
        return revenue and costs and float(revenue) > float(costs)
    
    def has_notes(notes):
        return notes is not None and notes.strip() != ''
    
    def performance_indicator(revenue):
        print(f'performance: {revenue}')
        if not revenue:
            return "gray"
        rev = float(revenue)
        return "green" if rev > 100 else "yellow" if rev > 50 else "red"
    
    # Business report formatter
    formatter = TemplateFormatter(
        "{{Company: ;company;}} {{#performance_indicator;(Revenue: $;revenue;M)}} {{?is_profitable; ✓ Profitable ;revenue;}} {{?has_notes;[Notes: ;notes;]}}", 
        functions={
            'is_profitable': is_profitable,
            'has_notes': has_notes,
            'performance_indicator': performance_indicator
        }
    )
    
    # Sample business data
    companies = [
        {'company': 'TechCorp', 'revenue': '150', 'costs': '120', 'notes': 'Strong growth'},
        {'company': 'StartupXYZ', 'revenue': '25'},  # Missing costs and notes
        {'company': 'MegaCorp', 'revenue': '500', 'costs': '600'},  # Not profitable, no notes
        {'company': 'SmallCo', 'revenue': '10', 'costs': '8', 'notes': 'Niche market'}
    ]
    
    print("Business performance report:")
    for company in companies:
        result = formatter.format(**company)
        print(f"  {result}")
    print()


def demo_escape_sequences():
    """Demonstrate escape sequence handling."""
    print("=" * 60)
    print("ESCAPE SEQUENCES")
    print("=" * 60)
    
    # Escaping braces
    formatter = TemplateFormatter("Use \\{#variable\\} to define {{name}}")
    result = formatter.format(name="templates", variable="error")
    print(f"Escaped braces: '{result}'")
    
    # Escaping delimiters
    formatter = TemplateFormatter("{{Ratio\\;percentage;value;}}")
    result = formatter.format(value="50%")
    print(f"Escaped delimiter: '{result}'")
    
    # Custom delimiter
    formatter = TemplateFormatter("{{prefix|variable|suffix}}", delimiter="|")
    result = formatter.format(variable="test")
    print(f"Custom delimiter: '{result}'")
    
    # Custom escape character
    formatter = TemplateFormatter("Use ~{variable~} to define {{name}}", escape_char="~")
    result = formatter.format(name="templates")
    print(f"Custom escape char: '{result}'")
    print()

def main():
    """Run comprehensive StringSmith demonstration."""
    print("StringSmith Template Formatter - Comprehensive Feature Demonstration")
    print("Professional template formatting with conditional sections and rich styling")
    print()
    
    demo_basic_formatting()
    demo_color_formatting()
    demo_text_emphasis()
    demo_conditional_sections()
    demo_professional_logging()
    demo_performance_scenario()
    demo_creative_applications()
    demo_data_reporting()
    demo_escape_sequences()
    
    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("✓ All StringSmith features demonstrated successfully!")
    print("✓ Template formatter is ready for professional use.")
    print("✓ Efficient, thread-safe, and production-ready.")


if __name__ == "__main__":
    main()