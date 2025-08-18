"""
Debug escape sequence issues
"""

import sys
from pathlib import Path

# Add the project root to path so we can import as a package
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared_utils.dynamic_formatting import DynamicFormatter
    print("✓ Successfully imported DynamicFormatter!")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)


def debug_conditional_escaping():
    """Debug the conditional escaping issue"""
    print("=== Debug Conditional Escaping ===")
    
    def has_value(value):
        return bool(value)
    
    functions = {'has_value': has_value}
    
    # Let's trace through the parsing manually
    test_string = "Use{?has_value} \\{brackets\\} for: "
    print(f"Original string: '{test_string}'")
    
    # Let's manually check what should happen:
    # 1. "Use" - normal text
    # 2. "{?has_value}" - conditional token
    # 3. " \\{brackets\\} for: " - should ALL be controlled by the conditional
    
    # But we're getting:
    # 1. "Use" - normal text  
    # 2. " \\" - conditional text (WRONG - should be much longer)
    # 3. " for: " - separate span (WRONG - should be part of conditional)
    
    print(f"\nManual analysis:")
    print(f"Position 0-2: 'Use' (normal)")
    print(f"Position 3-14: '{{?has_value}}' (conditional token)")
    print(f"Position 15+: ' \\{{brackets\\}} for: ' (should be ALL conditional)")
    
    # The issue must be that after processing the conditional at pos 15,
    # the parser is finding the \\{ at position 16-17 and thinking it's a new formatting token
    
    # Let's see what happens with a simpler case
    print(f"\nTesting simpler case...")
    simple_formatter = DynamicFormatter("{{Test{?has_value}ABC;field}}", functions=functions)
    
    print("Simple case sections:")
    for i, section in enumerate(simple_formatter.sections):
        if hasattr(section, 'prefix') and hasattr(section.prefix, '__iter__') and not isinstance(section.prefix, str):
            for j, span in enumerate(section.prefix):
                print(f"    Span {j}: text='{span.text}', tokens={span.formatting_tokens}")
    
    simple_result = simple_formatter.format(field="test")
    print(f"Simple result: {repr(simple_result)}")
    
    # Original complex case
    formatter = DynamicFormatter(
        "{{Use{?has_value} \\{brackets\\} for: ;syntax}}",
        functions=functions
    )
    
    print(f"\nComplex case sections:")
    for i, section in enumerate(formatter.sections):
        if hasattr(section, 'prefix') and hasattr(section.prefix, '__iter__') and not isinstance(section.prefix, str):
            for j, span in enumerate(section.prefix):
                print(f"    Span {j}: text='{span.text}', tokens={span.formatting_tokens}")
    
    result1 = formatter.format(syntax="variables")
    print(f"Complex result: {repr(result1)}")


def debug_simple_escaping():
    """Test the simplest possible escape case"""
    print("\n=== Debug Simple Escaping ===")
    
    # Test escape sequences directly in format strings
    test_cases = [
        ("Simple escape", "\\{brackets\\}"),
        ("Mixed text", "before\\{middle\\}after"), 
        ("Opening only", "\\{text"),
        ("Closing only", "text\\}"),
        ("No escapes", "normal text")
    ]
    
    for name, test_str in test_cases:
        try:
            formatter = DynamicFormatter(test_str)
            result = formatter.format()
            print(f"{name}: '{test_str}' → '{result}'")
        except Exception as e:
            print(f"{name}: '{test_str}' → ERROR: {e}")
    
    # Test in template context
    print("\nIn template context:")
    try:
        formatter = DynamicFormatter("{{\\{escaped\\}: ;value}}")
        result = formatter.format(value="test")
        print(f"Template escape: {repr(result)}")
    except Exception as e:
        print(f"Template escape: ERROR: {e}")


if __name__ == "__main__":
    debug_simple_escaping()
    debug_conditional_escaping()

#python shared_utils/dynamic_formatting/debug_escape.py  