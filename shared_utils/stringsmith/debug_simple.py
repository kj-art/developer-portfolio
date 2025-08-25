#!/usr/bin/env python3
"""
Simple debug script to understand StringSmith behavior.
"""

import sys
import os

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from formatter import TemplateFormatter


def debug_simple_positional():
    """Debug an even simpler case."""
    print("=== SIMPLE POSITIONAL DEBUG ===")
    
    # Even simpler test
    formatter = TemplateFormatter("{{;}}")
    
    print("Template: '{{;}}'")
    print("Arguments: 'test'")
    print()
    
    # Debug the parsing
    print("Parsed sections:")
    for i, section in enumerate(formatter.sections):
        print(f"  Section {i}: {section}")
        print(f"    field_name: '{section.field_name}'")
        print(f"    prefix: {section.prefix}")
        print(f"    suffix: {section.suffix}")
    print()
    
    # Debug the formatting
    print("Calling formatter.format('test')...")
    try:
        result = formatter.format("test")
        print(f"Result: '{result}'")
        print(f"Expected: 'test'")
        print(f"Match: {result == 'test'}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    print()


def debug_positional():
    """Debug the exact positional argument issue."""
    print("=== POSITIONAL DEBUG ===")
    
    # The failing test
    formatter = TemplateFormatter("{{;}} + {{;}} = {{;}}")
    
    print("Template: '{{;}} + {{;}} = {{;}}'")
    print("Arguments: '2', '3', '5'")
    print()
    
    # Debug the parsing
    print("Parsed sections:")
    for i, section in enumerate(formatter.sections):
        print(f"  Section {i}: {section}")
        print(f"    field_name: '{section.field_name}'")
        print(f"    prefix: {section.prefix}")
        print(f"    suffix: {section.suffix}")
    print()
    
    # Debug the formatting
    print("Calling formatter.format('2', '3', '5')...")
    try:
        result = formatter.format("2", "3", "5")
        print(f"Result: '{result}'")
        print(f"Expected: '2 + 3 = 5'")
        print(f"Match: {result == '2 + 3 = 5'}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    print()


if __name__ == "__main__":
    print("Starting debug...")
    debug_simple_positional()
    debug_positional()
    print("Debug complete.")