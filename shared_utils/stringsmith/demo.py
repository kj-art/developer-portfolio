#!/usr/bin/env python3
"""
StringSmith Feature Demonstration

Showcases all major features with practical examples that would be used
in professional environments.
"""

import sys
import os
import random

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from formatter import TemplateFormatter


def demo_basic_formatting():
    """Demonstrate basic template formatting capabilities."""
    print("=" * 60)
    print("BASIC TEMPLATE FORMATTING")
    print("=" * 60)
    
    # Simple substitution
    formatter = TemplateFormatter("Welcome {{;name;}}")
    result = formatter.format("Alice")
    print(f"Simple: {result}")
    
    # Multiple fields with prefix/suffix
    formatter = TemplateFormatter("{{User: ;username;}} ({{ID: ;user_id;}})")
    result = formatter.format(username="admin", user_id=12345)
    print(f"Multiple fields: {result}")
    
    # Positional arguments
    formatter = TemplateFormatter("{{;}} + {{;}} = {{;}}")
    result = formatter.format("15", "27", "42")
    print(f"Positional: {result}")
    
    print()


def demo_conditional_sections():
    """Demonstrate conditional section behavior."""
    print("=" * 60)
    print("CONDITIONAL SECTIONS")
    print("=" * 60)
    
    # Optional sections
    template = "{{Base content}}{{[ (Optional: ;optional;)]}}"
    formatter = TemplateFormatter(template)
    
    print("Optional sections:")
    print(f"  With optional: {formatter.format(optional='present')}")
    print(f"  Without optional: {formatter.format()}")
    
    # Section-level conditionals
    def is_admin(field):
        return field == "admin"
    
    template = "{{Welcome ;username;}}{{?is_admin ( - Admin Access)}}"
    formatter = TemplateFormatter(template, functions={'is_admin': is_admin})
    
    print("\nSection conditionals:")
    print(f"  Admin user: {formatter.format(username='admin')}")
    print(f"  Regular user: {formatter.format(username='guest')}")
    
    print()


def demo_color_formatting():
    """Demonstrate color formatting with Rich integration."""
    print("=" * 60)
    print("COLOR FORMATTING")
    print("=" * 60)
    
    # Basic colors
    formatter = TemplateFormatter("{{[{#green}SUCCESS{#normal}] ;message;}}")
    result = formatter.format(message="Operation completed")
    print(f"Basic color: {result}")
    
    # Custom color functions
    def status_color(field):
        colors = {
            "success": "green",
            "warning": "yellow", 
            "error": "red",
            "info": "blue"
        }
        return colors.get(field.lower(), "white")
    
    formatter = TemplateFormatter(
        "{{[{#status_color}●{#normal}] ;message;}}", 
        functions={'status_color': status_color}
    )
    
    print("\nDynamic colors:")
    statuses = ["success", "warning", "error", "info"]
    for status in statuses:
        result = formatter.format(status=status, message=f"This is a {status} message")
        print(f"  {result}")
    
    # Hex colors
    formatter = TemplateFormatter("{{[{#FF6B35}ALERT{#normal}] ;msg;}}")
    result = formatter.format(msg="Custom hex color")
    print(f"\nHex color: {result}")
    
    print()


def demo_text_emphasis():
    """Demonstrate text emphasis formatting.""" 
    print("=" * 60)
    print("TEXT EMPHASIS")
    print("=" * 60)
    
    # Basic emphasis
    formatter = TemplateFormatter("{{Task: {@bold};task;{@normal}} - {{Status: {@italic};status;{@normal}}}")
    result = formatter.format(task="Deploy Application", status="In Progress")
    print(f"Basic emphasis: {result}")
    
    # Stacked emphasis
    formatter = TemplateFormatter("{{[@bold@underline}IMPORTANT{@normal}]: ;message;}}")
    result = formatter.format(message="Please read carefully")
    print(f"Stacked emphasis: {result}")
    
    # Dynamic emphasis based on content
    def priority_style(field):
        styles = {
            "critical": "bold",
            "high": "underline",
            "medium": "normal",
            "low": "dim"
        }
        return styles.get(field.lower(), "normal")
    
    formatter = TemplateFormatter(
        "{{Priority: {@priority_style};priority;{@normal}} - ;task;}}", 
        functions={'priority_style': priority_style}
    )
    
    print("\nDynamic emphasis:")
    priorities = ["critical", "high", "medium", "low"]
    for priority in priorities:
        result = formatter.format(priority=priority, task=f"Task with {priority} priority")
        print(f"  {result}")
    
    print()


def demo_inline_conditionals():
    """Demonstrate inline conditional formatting."""
    print("=" * 60)
    print("INLINE CONDITIONALS")
    print("=" * 60)
    
    # Simple inline conditional
    def has_errors(field):
        return int(field) > 0
    
    formatter = TemplateFormatter(
        "{{Status: OK{?has_errors} - {#red};error_count; errors{#normal};error_count;}}", 
        functions={'has_errors': has_errors}
    )
    
    print("Simple inline conditional:")
    print(f"  No errors: {formatter.format(error_count='0')}")
    print(f"  With errors: {formatter.format(error_count='3')}")
    
    # Multiple conditionals in sequence
    def show_warnings(field):
        return "warn" in field.lower()
    
    def show_errors(field):
        return "error" in field.lower()
    
    formatter = TemplateFormatter(
        "{{Status:{?show_warnings} {#yellow}WARNINGS{#normal}{?show_errors} {#red}ERRORS{#normal}{?default} - All clear;status;}}", 
        functions={'show_warnings': show_warnings, 'show_errors': show_errors}
    )
    
    print("\nMultiple inline conditionals:")
    test_statuses = ["normal", "warnings detected", "errors found", "warnings and errors"]
    for status in test_statuses:
        result = formatter.format(status=status)
        print(f"  '{status}': {result}")
    
    # Complex example from the original issue
    def check_condition(field):
        return field == "show_prefix"
    
    formatter = TemplateFormatter(
        "{{pre{?check_condition}fix is {?default}here;field;}}", 
        functions={'check_condition': check_condition}
    )
    
    print("\nComplex conditional example:")
    print(f"  Condition true: {formatter.format(field='show_prefix')}")
    print(f"  Condition false: {formatter.format(field='other')}")
    
    print()


def demo_professional_use_case():
    """Demonstrate a realistic professional logging/monitoring use case."""
    print("=" * 60)
    print("PROFESSIONAL USE CASE: SYSTEM MONITORING")
    print("=" * 60)
    
    # Define helper functions
    def severity_color(field):
        colors = {
            "critical": "bright_red",
            "error": "red", 
            "warning": "yellow",
            "info": "blue",
            "debug": "dim"
        }
        return colors.get(field.lower(), "white")
    
    def severity_style(field):
        if field.lower() in ["critical", "error"]:
            return "bold"
        return "normal"
    
    def show_timestamp(field):
        return field.lower() in ["error", "critical", "warning"]
    
    def show_details(field):
        return field.lower() in ["critical", "error"]
    
    # Complex monitoring template
    template = (
        "{{[{#severity_color}{@severity_style};severity;{@normal}{#normal}]"
        "{?show_timestamp} ;timestamp;"
        " - ;message;"
        "{?show_details} (Details: ;details;);details;}}"
    )
    
    formatter = TemplateFormatter(template, functions={
        'severity_color': severity_color,
        'severity_style': severity_style,
        'show_timestamp': show_timestamp,
        'show_details': show_details
    })
    
    # Sample log entries
    log_entries = [
        {
            "severity": "info",
            "timestamp": "2024-01-15 10:30:15",
            "message": "User login successful",
            "details": "user_id=12345"
        },
        {
            "severity": "warning", 
            "timestamp": "2024-01-15 10:31:42",
            "message": "High memory usage detected",
            "details": "memory_usage=87%"
        },
        {
            "severity": "error",
            "timestamp": "2024-01-15 10:32:08", 
            "message": "Database connection failed",
            "details": "timeout after 30s"
        },
        {
            "severity": "critical",
            "timestamp": "2024-01-15 10:32:15",
            "message": "System overload detected",
            "details": "cpu=98% memory=95% disk=89%"
        }
    ]
    
    print("System monitoring output:")
    for entry in log_entries:
        result = formatter.format(**entry)
        print(f"  {result}")
    
    print()


def demo_performance_scenario():
    """Demonstrate efficient template reuse for high-volume scenarios."""
    print("=" * 60)
    print("PERFORMANCE SCENARIO: BULK PROCESSING")
    print("=" * 60)
    
    # Create a formatter once, reuse many times
    def record_color(field):
        return "green" if field == "processed" else "yellow" if field == "pending" else "red"
    
    formatter = TemplateFormatter(
        "{{[{#blue};batch_id;{#normal}] Record {#record_color};status;{#normal}: ;record_id; - ;description;}}", 
        functions={'record_color': record_color}
    )
    
    # Simulate processing many records
    print("Processing batch of records:")
    statuses = ["processed", "pending", "failed"]
    
    for i in range(10):
        status = random.choice(statuses)
        result = formatter.format(
            batch_id=f"BTH{1000 + i // 3}",
            status=status,
            record_id=f"REC{10000 + i}",
            description=f"Sample record {i + 1}"
        )
        print(f"  {result}")
    
    print(f"\n✓ Efficiently processed multiple records with single template instance")
    print()


def main():
    """Run all demonstrations."""
    print("StringSmith Template Formatter - Feature Demonstration")
    print("A comprehensive showcase of professional template formatting capabilities")
    print()
    
    demo_basic_formatting()
    demo_conditional_sections()
    demo_color_formatting()
    demo_text_emphasis()
    demo_inline_conditionals()
    demo_professional_use_case()
    demo_performance_scenario()
    
    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("All features demonstrated successfully!")
    print("Template formatter is ready for professional use.")


if __name__ == "__main__":
    main()