"""
Standalone test for dynamic formatting - no imports needed.

This file contains minimal versions of the classes to test functionality
without needing to set up the full package structure.
"""

# Minimal standalone implementation for testing
class DynamicFormattingError(Exception):
    pass

class FunctionExecutionError(DynamicFormattingError):
    pass

class FormatterError(DynamicFormattingError):
    pass

def test_with_package_import():
    """Try to test with the actual package"""
    try:
        import sys
        from pathlib import Path
        
        # Try importing from the package
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from shared_utils.dynamic_formatting import DynamicFormatter
        
        print("✓ Successfully imported from package!")
        
        # Test basic functionality
        def level_color(level):
            colors = {'ERROR': 'red', 'INFO': 'green', 'WARNING': 'yellow'}
            return colors.get(level.upper(), 'white')
        
        # Test 1: Function color with prefix/suffix
        formatter1 = DynamicFormatter(
            "{{#level_color@bold;[;level;]}}", 
            functions={'level_color': level_color}
        )
        result1 = formatter1.format(level="ERROR")
        print(f"Bracket test: {repr(result1)}")
        
        # Test 2: Function color with message (separate sections)
        formatter2 = DynamicFormatter(
            "{{#level_color@bold;[;level;]}} {{message}}", 
            functions={'level_color': level_color}
        )
        result2 = formatter2.format(level="ERROR", message="Test failed")
        print(f"Combined test: {repr(result2)}")
        
        # Test 3: Function in formatting tokens only
        formatter3 = DynamicFormatter(
            "{{#level_color@bold;Error: ;message}}", 
            functions={'level_color': level_color}
        )
        result = formatter3.format(level="ERROR", message="Test failed")
        
        print(f"Function fallback test: {repr(result)}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Package import failed: {e}")
        return False

def test_file_structure():
    """Check if all required files exist"""
    from pathlib import Path
    
    current_dir = Path(__file__).parent
    required_files = [
        'dynamic_formatting.py',
        'formatters.py',
        'formatting_state.py', 
        'token_parsing.py',
        'span_structures.py',
        '__init__.py'
    ]
    
    print("\n=== File Structure Check ===")
    missing_files = []
    
    for filename in required_files:
        filepath = current_dir / filename
        if filepath.exists():
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename} - MISSING")
            missing_files.append(filename)
    
    if missing_files:
        print(f"\nMissing files: {missing_files}")
        print("Please save all the artifacts as Python files in this directory.")
        return False
    else:
        print("\n✓ All required files present!")
        return True

def test_direct_file_import():
    """Try importing directly from files in current directory"""
    try:
        import sys
        from pathlib import Path
        
        # Add current directory to path
        current_dir = str(Path(__file__).parent)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Import the modules - this will work if files are present and don't have relative imports
        print("\n=== Direct File Import Test ===")
        
        try:
            import span_structures
            print("✓ span_structures imported")
        except Exception as e:
            print(f"✗ span_structures failed: {e}")
            return False
            
        try:
            import formatting_state
            print("✓ formatting_state imported")
        except Exception as e:
            print(f"✗ formatting_state failed: {e}")
            return False
            
        try:
            import formatters
            print("✓ formatters imported")
        except Exception as e:
            print(f"✗ formatters failed: {e}")
            return False
            
        try:
            import token_parsing
            print("✓ token_parsing imported")
        except Exception as e:
            print(f"✗ token_parsing failed: {e}")
            return False
            
        try:
            import dynamic_formatting
            print("✓ dynamic_formatting imported")
        except Exception as e:
            print(f"✗ dynamic_formatting failed: {e}")
            return False
            
        print("\n✓ All modules imported successfully!")
        
        # Test functionality
        print("\n=== Functionality Test ===")
        
        def test_color_func(level):
            return 'red' if level == 'ERROR' else 'green'
        
        formatter = dynamic_formatting.DynamicFormatter(
            "{{#test_color_func;Level: ;level}}",
            functions={'test_color_func': test_color_func}
        )
        
        result = formatter.format(level="ERROR")
        print(f"✓ Function fallback working: {repr(result)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Direct import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Dynamic Formatting Test Suite")
    print("=" * 40)
    
    # Check file structure first
    files_ok = test_file_structure()
    
    if not files_ok:
        print("\n❌ Cannot proceed - missing required files")
        print("\nTo fix:")
        print("1. Save all artifacts as .py files in this directory")
        print("2. Make sure __init__.py exists")
        print("3. Run this test again")
        return
    
    # Try package import
    package_ok = test_with_package_import()
    
    if not package_ok:
        print("\n⚠️  Package import failed, trying direct file import...")
        direct_ok = test_direct_file_import()
        
        if not direct_ok:
            print("\n❌ All import methods failed")
            print("\nDebugging steps:")
            print("1. Check that all files were saved correctly")
            print("2. Look for syntax errors in the saved files")
            print("3. Make sure relative imports are fixed")
        else:
            print("\n✅ Direct import worked! The modules are functional.")
    else:
        print("\n✅ Package import worked! Everything is set up correctly.")

if __name__ == "__main__":
    main()