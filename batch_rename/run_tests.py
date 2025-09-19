#!/usr/bin/env python3
"""
Test runner for batch rename tool.

Provides convenient test execution with different options.
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_tests(test_type="all", coverage=True, parallel=False, verbose=False):
    """Run tests with specified options."""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=batch_rename", "--cov-report=term-missing"])
    
    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Select test type
    if test_type == "unit":
        cmd.extend(["-m", "not slow and not integration and not gui"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "slow":
        cmd.extend(["-m", "slow"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow and not integration"])
    elif test_type == "all":
        cmd.extend(["-m", "not gui"])  # Skip GUI tests by default
    
    # Add test directory
    cmd.append("tests/")
    
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run batch rename tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "slow", "fast"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    parser.add_argument(
        "--parallel",
        action="store_true", 
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies first"
    )
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
        ])
    
    # Run tests
    result = run_tests(
        test_type=args.type,
        coverage=not args.no_coverage,
        parallel=args.parallel,
        verbose=args.verbose
    )
    
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()