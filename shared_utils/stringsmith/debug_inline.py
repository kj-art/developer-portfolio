#!/usr/bin/env python3
"""
Debug inline formatting.
"""

import sys
import os

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from formatter import TemplateFormatter
import random

def debug_simple_inline():
    """Test simple inline formatting."""
    print("=== Simple Inline Test ===")
    
    formatter = TemplateFormatter("{{Status: {#green}OK{#normal};message;}}")
    result = formatter.format(message="test")
    print(f"Result: '{result}'")
    print(f"Length: {len(result)}")
    print(f"Repr: {repr(result)}")
    print()

def debug_random_color():
    """Test the random color issue."""
    print("=== Random Color Debug ===")
    
    def random_color():
        color = random.choice(['red', 'green', 'blue'])
        print(f"Function called, returning: {color}")
        return color
    
    # Test simple case first
    formatter = TemplateFormatter("{{A{#random_color}B;field;}}", 
                                functions={'random_color': random_color})
    result = formatter.format(field="TEST")
    print(f"Simple result: '{result}'")
    print(f"Simple repr: {repr(result)}")
    print()
    
    # Test the full case
    rc = "{#random_color}"
    template_string = f"{{{{{rc}A{rc}B{rc}C ;{rc}field; {rc}X{rc}Y{rc}Z}}}}"
    print(f"Template: {template_string}")
    
    try:
        formatter = TemplateFormatter(template_string, functions={'random_color': random_color})
        print("Template parsed successfully")
        print(f"Number of sections: {len(formatter.sections)}")
        for i, section in enumerate(formatter.sections):
            print(f"  Section {i}: {section}")
        
        result = formatter.format(field="FIELD")
        print(f"Full result: '{result}'")
        print(f"Full repr: {repr(result)}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    print()

if __name__ == "__main__":
    debug_simple_inline()
    debug_random_color()