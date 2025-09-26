#!/usr/bin/env python3
"""
Generate test data for bulk processing demonstration.
"""

import os
import random
import string
from pathlib import Path
from datetime import datetime, timedelta


def generate_test_data(count=1000, output_dir="test_data"):
    """Generate test files for performance testing."""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    departments = ["HR", "Finance", "IT", "Legal", "Marketing", "Operations"]
    doc_types = ["report", "policy", "contract", "analysis", "proposal", "manual"]
    statuses = ["draft", "review", "final", "approved", "archived"]
    
    print(f"Generating {count} test files in {output_path}...")
    
    for i in range(count):
        # Random filename components
        dept = random.choice(departments)
        doc_type = random.choice(doc_types)
        status = random.choice(statuses)
        
        # Random date in last year
        days_ago = random.randint(1, 365)
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y%m%d")
        
        # Generate filename
        filename = f"{dept}_{doc_type}_{status}_{date}_{i:04d}.txt"
        file_path = output_path / filename
        
        # Create file with minimal content
        content = f"Test file {i+1}/{count}\nGenerated: {datetime.now()}\n"
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{count} files...")
    
    print(f"✅ Generated {count} test files in {output_path}")


def clean_test_data(output_dir="test_data"):
    """Remove generated test files."""
    import shutil
    
    output_path = Path(output_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
        print(f"✅ Cleaned test data from {output_path}")
    else:
        print(f"❌ Test data directory {output_path} not found")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test data for batch rename tool")
    parser.add_argument("--count", type=int, default=1000, 
                       help="Number of files to generate (default: 1000)")
    parser.add_argument("--output-dir", default="test_data",
                       help="Output directory (default: test_data)")
    parser.add_argument("--clean", action="store_true",
                       help="Clean existing test data")
    
    args = parser.parse_args()
    
    if args.clean:
        clean_test_data(args.output_dir)
    else:
        generate_test_data(args.count, args.output_dir)
