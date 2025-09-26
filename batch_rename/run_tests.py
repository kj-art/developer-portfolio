#!/usr/bin/env python3
"""
Test runner script for batch rename project.

Provides convenient commands for running different test suites.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, cwd=Path(__file__).parent)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install pytest")
        return False


def run_all_tests():
    """Run all tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-v"]
    return run_command(cmd, "All tests")


def run_unit_tests():
    """Run only unit tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-v", "-m", "unit or not integration"]
    return run_command(cmd, "Unit tests")


def run_integration_tests():
    """Run only integration tests."""
    cmd = ["python", "-m", "pytest", "tests/test_integration.py", "-v"]
    return run_command(cmd, "Integration tests")


def run_specific_module(module_name):
    """Run tests for a specific module."""
    test_file = f"tests/test_{module_name}.py"
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    cmd = ["python", "-m", "pytest", test_file, "-v"]
    return run_command(cmd, f"Tests for {module_name}")


def run_with_coverage():
    """Run tests with coverage report."""
    cmd = [
        "python", "-m", "pytest", "tests/", 
        "--cov=core", 
        "--cov-report=html", 
        "--cov-report=term-missing",
        "-v"
    ]
    return run_command(cmd, "Tests with coverage")


def run_performance_tests():
    """Run performance tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-v", "-m", "performance"]
    return run_command(cmd, "Performance tests")


def run_quick_tests():
    """Run quick tests (excluding slow ones)."""
    cmd = ["python", "-m", "pytest", "tests/", "-v", "-m", "not slow"]
    return run_command(cmd, "Quick tests")


def check_test_structure():
    """Check test file structure and imports."""
    print("\n" + "="*60)
    print("Checking test structure...")
    print("="*60)
    
    test_dir = Path("tests")
    if not test_dir.exists():
        print("❌ Tests directory not found")
        return False
    
    test_files = list(test_dir.glob("test_*.py"))
    if not test_files:
        print("❌ No test files found")
        return False
    
    print(f"✅ Found {len(test_files)} test files:")
    for test_file in sorted(test_files):
        print(f"  - {test_file.name}")
    
    # Check for conftest.py
    conftest = test_dir / "conftest.py"
    if conftest.exists():
        print(f"✅ Found conftest.py")
    else:
        print(f"⚠️  conftest.py not found (fixtures may not work)")
    
    # Check for __init__.py
    init_file = test_dir / "__init__.py"
    if not init_file.exists():
        print("ℹ️  Creating __init__.py for tests package")
        init_file.write_text("# Tests package\n")
    
    return True


def lint_tests():
    """Run linting on test files."""
    cmd = ["python", "-m", "flake8", "tests/", "--max-line-length=100"]
    return run_command(cmd, "Test linting")


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Test runner for batch rename project")
    parser.add_argument(
        "command", 
        nargs="?", 
        default="all",
        choices=[
            "all", "unit", "integration", "coverage", "performance", 
            "quick", "check", "lint", "extractors", "converters", 
            "filters", "templates", "processor", "config"
        ],
        help="Test command to run"
    )
    
    args = parser.parse_args()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return 1
    
    print(f"🐍 Using Python {sys.version}")
    
    success = True
    
    if args.command == "all":
        success = run_all_tests()
    elif args.command == "unit":
        success = run_unit_tests()
    elif args.command == "integration":
        success = run_integration_tests()
    elif args.command == "coverage":
        success = run_with_coverage()
    elif args.command == "performance":
        success = run_performance_tests()
    elif args.command == "quick":
        success = run_quick_tests()
    elif args.command == "check":
        success = check_test_structure()
    elif args.command == "lint":
        success = lint_tests()
    elif args.command in ["extractors", "converters", "filters", "templates", "processor", "config"]:
        success = run_specific_module(args.command)
    else:
        print(f"❌ Unknown command: {args.command}")
        success = False
    
    if success:
        print(f"\n🎉 Test run completed successfully!")
        return 0
    else:
        print(f"\n💥 Test run failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())