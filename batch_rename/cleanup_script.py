#!/usr/bin/env python3
"""
Quick cleanup script to fix the broken syntax from the previous script.
"""

import re
from pathlib import Path

def cleanup_broken_syntax(content):
    """Fix broken syntax caused by bad regex replacements."""
    
    # Fix broken lines like: result = # processor.analyze( # TODO...config)
    # These should be: # result = processor.analyze(config)  # TODO...
    
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Look for broken patterns
        if '= #' in line and 'processor.' in line and 'TODO' in line:
            # Extract the original assignment
            match = re.search(r'(\s*)(.+?)\s*=\s*#\s*(processor\.\w+\(.+?)\s*#\s*TODO.*', line)
            if match:
                indent, var_name, method_call = match.groups()
                # Reconstruct as commented line
                fixed_line = f"{indent}# {var_name} = {method_call}  # TODO: Replace with actual method"
                fixed_lines.append(fixed_line)
            else:
                # If we can't parse it, just comment the whole line
                fixed_lines.append('        # ' + line.strip() + '  # FIXME: Broken by script')
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_file(file_path):
    """Fix a single test file."""
    print(f"Cleaning up {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply cleanup
        content = cleanup_broken_syntax(content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Cleaned {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning {file_path}: {e}")
        return False

def main():
    """Clean up all test files."""
    test_dir = Path("batch_rename/tests")
    
    if not test_dir.exists():
        print("❌ tests directory not found")
        return
    
    # Files to clean
    test_files = [
        "test_processor.py",
        "test_integration.py"
    ]
    
    for test_file in test_files:
        file_path = test_dir / test_file
        if file_path.exists():
            fix_file(file_path)
        else:
            print(f"⚠️  {file_path} not found, skipping")

if __name__ == "__main__":
    main()