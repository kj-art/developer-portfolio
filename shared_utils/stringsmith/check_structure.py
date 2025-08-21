#!/usr/bin/env python3
"""
Check the directory structure of StringSmith.
"""

import os

def check_structure():
    """Check what files exist in the current directory structure."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")
    print()
    
    print("Files in current directory:")
    for item in sorted(os.listdir(script_dir)):
        item_path = os.path.join(script_dir, item)
        if os.path.isdir(item_path):
            print(f"  📁 {item}/")
            # Show contents of directories
            try:
                contents = os.listdir(item_path)
                for subitem in sorted(contents):
                    print(f"    📄 {subitem}")
            except PermissionError:
                print(f"    (Permission denied)")
        else:
            print(f"  📄 {item}")
    
    print()
    
    # Check if stringsmith package exists
    stringsmith_dir = os.path.join(script_dir, "stringsmith")
    if os.path.exists(stringsmith_dir):
        print(f"✅ stringsmith directory exists at: {stringsmith_dir}")
        
        init_file = os.path.join(stringsmith_dir, "__init__.py")
        if os.path.exists(init_file):
            print("✅ __init__.py exists")
            
            # Try to read it
            try:
                with open(init_file, 'r') as f:
                    content = f.read()
                print(f"📄 __init__.py content preview:\n{content[:200]}...")
            except Exception as e:
                print(f"❌ Could not read __init__.py: {e}")
        else:
            print("❌ __init__.py missing")
    else:
        print("❌ stringsmith directory not found")
        
        # Look for individual .py files
        py_files = [f for f in os.listdir(script_dir) if f.endswith('.py')]
        if py_files:
            print(f"Found Python files: {py_files}")

if __name__ == "__main__":
    check_structure()