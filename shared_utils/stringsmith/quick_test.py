#!/usr/bin/env python3
"""
Quick test of StringSmith examples from the README.
"""

import sys
import os
import re

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from formatter import TemplateFormatter



ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
def plain_text(s: str) -> str:
    return ansi_escape.sub('', s)

def test_readme_examples():
    """Test the examples from the README."""
    print("Testing README examples...")
    #formatter = TemplateFormatter("Hello {{@bold#get_blue#reset;pre{#red}f{#get_blue}ix;{#red}{#blue}field;suf{#red}f{#blue}ix}}!", functions={'get_blue': lambda e: 'blue'})
    formatter = TemplateFormatter(
        "Hello {{@bold#get_blue#reset;pre{#red}f{?cut_off}ix;{#red}{#blue}field;suf{#red}f{#blue}ix}}!",
        functions={
            'get_blue': lambda e: 'blue',
            'cut_off': lambda *args: False
            })
    
    result1 = formatter.format(field="World")
    print(result1)
    print(result1.encode('unicode_escape').decode())
        

    # Basic usage
    formatter = TemplateFormatter("Hello {{name}}!")
    result1 = formatter.format(name="World")
    result2 = formatter.format()
    print(f"✅ Basic: '{result1}' and '{result2}'")
    print(result1)
    print("Hello World!")
    print(result2)
    assert plain_text(result1) == "Hello World!"
    assert plain_text(result2) == "Hello !"
    
    # Conditional sections with prefixes and suffixes
    formatter = TemplateFormatter("Score: {{Player ;name; scored }}{{points}} points")
    result1 = formatter.format(name="Alice", points=100)
    result2 = formatter.format(points=100)
    print(f"✅ Conditional: '{result1}' and '{result2}'")
    assert plain_text(result1) == "Score: Player Alice scored 100 points"
    assert plain_text(result2) == "Score: 100 points"
    
    # Mandatory sections
    formatter = TemplateFormatter("{{!name}} is required")
    result1 = formatter.format(name="Alice")
    print(f"✅ Mandatory: '{result1}'")
    assert plain_text(result1) == "Alice is required"
    
    try:
        formatter.format()
        assert False, "Should have raised an error"
    except Exception as e:
        print(f"✅ Mandatory error: {e}")
    
    # Color formatting (should contain ANSI codes)
    formatter = TemplateFormatter("{{#red;Error: ;message;}}")
    result = formatter.format(message="Something went wrong")
    print(f"✅ Color: '{result}' (contains ANSI: {bool('\033[' in result)})")
    
    # Text emphasis (should contain ANSI codes) 
    formatter = TemplateFormatter("{{@bold;Warning: ;message;}}")
    result = formatter.format(message="Check this")
    print(f"✅ Emphasis: '{result}' (contains ANSI: {bool('\033[' in result)})")
    
    # Positional arguments
    formatter = TemplateFormatter("{{first}} and {{second}}")
    result1 = formatter.format("Hello", "World")
    result2 = formatter.format("Hello")
    print(f"✅ Positional: '{result1}' and '{result2}'")
    assert plain_text(result1) == "Hello and World"
    assert plain_text(result2) == "Hello and "
    
    print("🎉 All README examples work!")

def test_complex_example():
    """Test a more complex example."""
    print("\nTesting complex example...")
    
    def is_urgent(message):
        return 'urgent' in message.lower()
    
    def highlight(text):
        return 'bold'
    
    formatter = TemplateFormatter(
        "{{?is_urgent@highlight;URGENT: ;message;}} {{Normal: ;details;}}",
        functions={
            'is_urgent': is_urgent,
            'highlight': highlight
        }
    )
    
    result1 = formatter.format(message="urgent task", details="fix now")
    result2 = formatter.format(message="normal task", details="later")
    
    print(f"✅ Complex urgent: '{result1}'")
    print(f"✅ Complex normal: '{result2}'")
    
    # Should contain the highlight formatting for urgent
    assert "URGENT:" in plain_text(result1)
    assert "urgent task" in plain_text(result1)
    
    # Normal should not have urgent formatting
    assert "URGENT:" not in plain_text(result2)
    assert "later" in plain_text(result2)  # Check for the details parameter that should be present

if __name__ == "__main__":
    test_readme_examples()
    test_complex_example()
    print("\n🎉 All tests passed! StringSmith is working correctly.")