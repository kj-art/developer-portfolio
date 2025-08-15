# ui/cli.py - Option A: parse_known_args() with pandas docs reference

import argparse
import sys
from pathlib import Path

# Add the parent directory to Python path so we can import from core
sys.path.append(str(Path(__file__).parent.parent))

from core.processor import DataProcessor

def parse_unknown_args(unknown_args):
    """
    Parse unknown arguments from argparse into kwargs dict
    
    Handles the read/write split logic:
    - 0 values: use defaults
    - 1 value: same for read and write  
    - 2 values: first=read, second=write
    - 3+ values: error
    
    Args:
        unknown_args: List from parse_known_args() like ['--encoding', 'utf-8', '--sep', ';', ';']
        
    Returns:
        tuple: (read_kwargs, write_kwargs)
    """
    # Parse flat list into key-value pairs
    kwargs = {}
    i = 0
    while i < len(unknown_args):
        if unknown_args[i].startswith('--'):
            key = unknown_args[i][2:].replace('-', '_')  # --sheet-name -> sheet_name
            values = []
            
            # Collect all values for this key (until next -- or end)
            i += 1
            while i < len(unknown_args) and not unknown_args[i].startswith('--'):
                values.append(unknown_args[i])
                i += 1
            
            kwargs[key] = values
        else:
            i += 1
    
    # Apply read/write split logic
    read_kwargs = {}
    write_kwargs = {}
    
    for key, values in kwargs.items():
        if len(values) == 0:
            # No values - use defaults
            pass
        elif len(values) == 1:
            # One value - same for both
            read_kwargs[key] = values[0]
            write_kwargs[key] = values[0]
        elif len(values) == 2:
            # Two values - read, write
            read_kwargs[key] = values[0]
            write_kwargs[key] = values[1]
        else:
            raise ValueError(f"--{key.replace('_', '-')} accepts 0, 1, or 2 values. Got {len(values)}: {values}")
    
    return read_kwargs, write_kwargs

def print_pandas_help():
    """Print help for pandas options"""
    print("""
Pandas options:
  Any pandas read/write parameter can be used with the pattern:
  --parameter-name VALUE [VALUE]
  
  Pattern rules:
    0 values: use pandas defaults for both read and write
    1 value: same value for both read and write  
    2 values: first value for read, second value for write
  
  For available parameters, see pandas documentation:
    Read functions: https://pandas.pydata.org/docs/reference/io.html
    Write functions: DataFrame.to_csv(), .to_excel(), .to_json() methods
  
  Common examples:
    --encoding utf-8                    # Same encoding for read and write
    --encoding latin-1 utf-8           # Read latin-1, write utf-8
    --sep ";"                          # Use semicolon separator for CSV
    --sheet-name 0 Summary             # Read sheet 0, write to sheet "Summary"
    --na-values "NULL" "N/A"           # Treat NULL as NaN when reading, N/A when writing
    --schema custom_mappings.json      # Use custom column name mappings
    
  Parameter names:
    Use dashes in CLI (--sheet-name) which become underscores in pandas (sheet_name)
""")

class CustomHelpAction(argparse.Action):
    """Custom help action that shows both argparse help and pandas help"""
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=None):
        super().__init__(option_strings, dest, nargs=0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        print_pandas_help()
        parser.exit()

def main():
    # Create argument parser - only define the core CLI arguments
    parser = argparse.ArgumentParser(
        description='Process and merge data files from multiple formats',
        prog='data-pipeline',
        add_help=False  # We'll add custom help
    )
    
    # Add custom help action
    parser.add_argument(
        '-h', '--help',
        action=CustomHelpAction,
        help='Show this help message and exit'
    )
    
    # Only define our custom CLI arguments
    parser.add_argument(
        '--input-folder',
        required=True,
        help='Folder containing files to process'
    )
    
    parser.add_argument(
        '--output-file',
        help='Path to output file (if not specified, prints to console)'
    )
    
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Search subdirectories recursively for files'
    )
    
    parser.add_argument(
        '--filetype',
        nargs='*',
        help='File types to process (csv, xlsx, json). Default: all supported types'
    )
    
    parser.add_argument(
        '--schema',
        help='JSON file with custom column name mappings (overrides default schema)'
    )

    parser.add_argument(
        '--to-lower',
        type=str,
        choices=['true', 'false'],
        help='Convert column names to lowercase (true/false). Default: true'
    )

    parser.add_argument(
        '--spaces-to-underscores',
        type=str, 
        choices=['true', 'false'],
        help='Convert spaces to underscores in column names (true/false). Default: true'
    )
    
    # Parse known args, let everything else go to unknown
    args, unknown_args = parser.parse_known_args()
    
    # Basic validation
    if not Path(args.input_folder).exists():
        print(f"Error: Input folder '{args.input_folder}' does not exist")
        sys.exit(1)
    
    # Load custom schema if provided
    schema_map = None
    if args.schema:
        if not Path(args.schema).exists():
            print(f"Error: Schema file '{args.schema}' does not exist")
            sys.exit(1)
        try:
            import json
            with open(args.schema, 'r') as f:
                schema_map = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in schema file '{args.schema}': {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: Could not read schema file '{args.schema}': {e}")
            sys.exit(1)
    
    # Parse unknown arguments into read/write kwargs
    try:
        read_kwargs, write_kwargs = parse_unknown_args(unknown_args)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Create processor and run it
    processor = DataProcessor(**read_kwargs)
    
    # Handle filetype filter
    filetype_filter = args.filetype if args.filetype else None
    
    to_lower = True if args.to_lower is None else args.to_lower == 'true'
    spaces_to_underscores = True if args.spaces_to_underscores is None else args.spaces_to_underscores == 'true'

    result = processor.process_folder(
        args.input_folder, 
        recursive=args.recursive,
        filetype_filter=filetype_filter,
        schema_map=schema_map,
        to_lower=to_lower,
        spaces_to_underscores=spaces_to_underscores
    )
    print(f'output file: {args.output_file}')
    # Output results
    if args.output_file:
        processor.write_file(result, args.output_file, **write_kwargs)
    else:
        print(result)

if __name__ == '__main__':
    main()