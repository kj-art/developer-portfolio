# ui/cli.py - Basic starting point

import argparse
import sys
from pathlib import Path

# Add the parent directory to Python path so we can import from core
sys.path.append(str(Path(__file__).parent.parent))

from core.processor import DataProcessor

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Process and merge data files from multiple formats',
        prog='data-pipeline'
    )
    
    # Add the most basic required argument
    parser.add_argument(
        '--input-folder',
        required=True,
        help='Folder containing files to process'
    )
    
    # Add recursive option
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Search subdirectories recursively for files'
    )
    
    # Add filetype filter
    parser.add_argument(
        '--filetype',
        nargs='*',  # Allow multiple values or none
        help='File types to process (csv, xlsx, json). Use multiple times or space-separated. Default: all supported types'
    )
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Basic validation
    if not Path(args.input_folder).exists():
        print(f"Error: Input folder '{args.input_folder}' does not exist")
        sys.exit(1)
    
    # Create processor and run it
    processor = DataProcessor()
    
    # Handle filetype filter - convert empty list to None for "all types"
    filetype_filter = args.filetype if args.filetype else None
    
    result = processor.process_folder(
        args.input_folder, 
        recursive=args.recursive,
        filetype_filter=filetype_filter
    )
    
    # For now, just print the results
    print(result)

if __name__ == '__main__':
    main()