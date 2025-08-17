"""
Test to see if your console actually displays ANSI formatting.

This will help determine if your terminal supports colored/formatted output.
"""

import sys
import os

def test_console_formatting():
    print("=== Console Formatting Test ===")
    print()
    
    # Test 1: Basic ANSI codes
    print("1. Raw ANSI codes:")
    print("   Normal text")
    print("   \033[31mThis should be RED\033[0m")
    print("   \033[32mThis should be GREEN\033[0m") 
    print("   \033[1mThis should be BOLD\033[0m")
    print("   \033[31m\033[1mThis should be RED and BOLD\033[0m")
    print()
    
    # Test 2: Check environment
    print("2. Environment check:")
    print(f"   Platform: {sys.platform}")
    print(f"   TERM: {os.environ.get('TERM', 'Not set')}")
    print(f"   COLORTERM: {os.environ.get('COLORTERM', 'Not set')}")
    print(f"   stdout.isatty(): {sys.stdout.isatty()}")
    print()
    
    # Test 3: Try with dynamic formatting
    try:
        sys.path.insert(0, str(__file__).replace('console_test.py', ''))
        from shared_utils.dynamic_formatting import DynamicFormatter
        
        print("3. Dynamic formatting test:")
        
        formatter = DynamicFormatter("{{#red@bold;ERROR: ;message}}")
        result = formatter.format(message="This should be red and bold")
        print(f"   Result: {result}")
        print(f"   Raw: {repr(result)}")
        
        # Test different colors
        colors = ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta']
        for color in colors:
            formatter = DynamicFormatter(f"{{#{color};This is ;color}}")
            result = formatter.format(color=color.upper())
            print(f"   {result}")
        
    except ImportError as e:
        print(f"   Could not import dynamic formatting: {e}")
    
    print()
    print("=== What You Should See ===")
    print("If your console supports formatting:")
    print("- Text should appear in different colors")
    print("- Bold text should be thicker/brighter")
    print("- Raw codes should be hidden")
    print()
    print("If you only see escape codes like \\033[31m:")
    print("- Your console doesn't support ANSI formatting")
    print("- This is common in some Windows terminals")
    print("- Try Windows Terminal, PowerShell, or VS Code terminal")

def test_windows_specific():
    """Windows-specific terminal tests"""
    if sys.platform == "win32":
        print("\n=== Windows Terminal Test ===")
        
        # Try enabling ANSI support on Windows
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            print("✓ Enabled Windows ANSI support")
            
            print("Testing after enabling ANSI:")
            print("\033[31mThis should now be RED on Windows\033[0m")
            
        except Exception as e:
            print(f"✗ Could not enable Windows ANSI support: {e}")
            print("Try running in Windows Terminal or PowerShell")

def main():
    test_console_formatting()
    test_windows_specific()
    
    print("\n=== Recommendations ===")
    print("Best terminals for colored output:")
    print("• Windows: Windows Terminal, PowerShell, VS Code integrated terminal")
    print("• macOS: Terminal.app, iTerm2") 
    print("• Linux: Most terminals support colors by default")
    print()
    print("If you don't see colors:")
    print("1. Try a different terminal")
    print("2. Check terminal settings for ANSI/color support")
    print("3. The formatting still works - just not visually displayed")

if __name__ == "__main__":
    main()