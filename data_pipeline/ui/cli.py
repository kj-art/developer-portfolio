# ui/cli.py - Updated with custom argument parser

import argparse
import sys
from pathlib import Path
from shared_utils.logger import set_up_logging, get_logger
from data_pipeline.core.processor import DataProcessor
from data_pipeline.core.processing_config import ProcessingConfig, IndexMode
from ..core.dataframe_utils import ProcessingResult

def cast_string_to_appropriate_type(value):
    """
    Cast string values to appropriate Python types (int, float, or keep as string)
    
    Supports optional type prefixes to force specific types:
    - "str:5" -> "5" (force string)
    - "int:3.14" -> 3 (force int, truncates float)
    - "float:42" -> 42.0 (force float)
    - "5" -> 5 (auto-detect as int)
    
    Args:
        value (str): String value to cast, optionally with type prefix
        
    Returns:
        int|float|str: Appropriately cast value
        
    Examples:
        "42" -> 42
        "3.14" -> 3.14
        "1e-5" -> 1e-05
        "utf-8" -> "utf-8"
        "str:5" -> "5"
        "int:3.14" -> 3
        "float:42" -> 42.0
        "" -> ""
    """
    if not isinstance(value, str):
        return value
    
    # Handle empty strings
    if value == "":
        return value
    
    if value.lower() in ('true'):
        return True
    elif value.lower() in ('false'):
        return False
    
    # Check for type prefixes
    if ':' in value:
        prefix, actual_value = value.split(':', 1)
        
        if prefix == 'str':
            return actual_value
        elif prefix == 'int':
            try:
                return int(float(actual_value))  # Handle "int:3.14" -> 3
            except ValueError:
                raise ValueError(f"Cannot convert '{actual_value}' to int with int: prefix")
        elif prefix == 'float':
            try:
                return float(actual_value)
            except ValueError:
                raise ValueError(f"Cannot convert '{actual_value}' to float with float: prefix")
        # If prefix is not recognized, fall through to auto-detection
    
    # Auto-detection for values without prefixes
    # Try integer first
    try:
        # Check if it looks like an integer (no decimal point, no scientific notation)
        if '.' not in value and 'e' not in value.lower():
            return int(value)
    except ValueError:
        pass
    
    # Try float (handles scientific notation too)
    try:
        return float(value)
    except ValueError:
        pass
    
    # Keep as string if not numeric
    return value

def get_known_args_from_parser(parser):
    """Extract all defined argument names from the parser"""
    known_args = set()
    for action in parser._actions:
        if action.option_strings:  # Skip positional arguments
            known_args.update(action.option_strings)
    return known_args

def split_arguments(argv, parser):
    """Split command line into defined args and pandas args"""
    known_args = get_known_args_from_parser(parser)
    defined_args = []
    pandas_args = []

    current_list = None

    for item in argv[1:]:
        if item.startswith("--"):
            current_list = defined_args if item in known_args else pandas_args
            current_list.append(item)
        else:
            if current_list is None:
                raise ValueError(f"Value '{item}' found before any key")
            current_list.append(item)

    return defined_args, pandas_args

def parse_pandas_args(pandas_args):
    """
    Parse pandas arguments into read/write kwargs
    
    Args:
        pandas_args: List like ['--index', 'False', 'false', '--sep', ';']
        
    Returns:
        tuple: (read_kwargs, write_kwargs)
    """
    kwargs = {}
    i = 0
    while i < len(pandas_args):
        if pandas_args[i].startswith('--'):
            key = pandas_args[i][2:].replace('-', '_')  # --sheet-name -> sheet_name
            values = []
            
            # Collect all values for this key (until next -- or end)
            i += 1
            while i < len(pandas_args) and not pandas_args[i].startswith('--'):
                # Cast string values to appropriate types
                cast_value = cast_string_to_appropriate_type(pandas_args[i])
                values.append(cast_value)
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
  
  Type casting:
    Values are automatically converted to int/float when possible.
    To force a specific type, use prefixes:
      str:VALUE    Force string type (e.g., str:5 -> "5")
      int:VALUE    Force integer type (e.g., int:3.14 -> 3)
      float:VALUE  Force float type (e.g., float:42 -> 42.0)
  
  For available parameters, see pandas documentation:
    Read functions: https://pandas.pydata.org/docs/reference/io.html
    Write functions: DataFrame.to_csv(), .to_excel(), .to_json() methods
  
  Common examples:
    --encoding utf-8                    # Same encoding for read and write
    --encoding latin-1 utf-8           # Read latin-1, write utf-8
    --sep ";"                          # Use semicolon separator for CSV
    --sheet-name str:5                 # Access sheet named "5" (not 6th sheet)
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
        description='Process and merge data files from multiple formats. CSV outputs automatically use memory-efficient streaming for large datasets.',
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
        help='Path to output file. CSV files automatically use memory-efficient streaming processing for large datasets. Other formats use in-memory processing with full feature support.'
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
        action=argparse.BooleanOptionalAction,
        default=True,
        help='Convert column names to lowercase. Use --no-to-lower to disable. Default: enabled'
    )

    parser.add_argument(
        '--spaces-to-underscores',
        action=argparse.BooleanOptionalAction,
        default=True,
        help='Convert spaces to underscores in column names. Use --no-spaces-to-underscores to disable. Default: enabled'
    )
    
    parser.add_argument(
        '--columns',
        help='Comma-separated list of column names to expect in output (enables streaming for mixed file types by skipping schema detection). Example: --columns first_name,last_name,age,city'
    )

    parser.add_argument(
        '--force-in-memory',
        action='store_true',
        help='Force in-memory processing even for large datasets or CSV output. Overrides streaming optimizations. Use when you need the full dataset in memory for complex operations.'
    )

    parser.add_argument(
        '--index-mode',
        choices=['none', 'local', 'sequential'],
        type=str.lower,
        help='Index handling mode: none=no index column, local=per-file indices (0,1,2 then 0,1,2), sequential=continuous across files (0,1,2,3,4...). Overrides --index parameter if specified.'
    )

    parser.add_argument(
        '--index-start',
        type=int,
        default=0,
        help='Starting number for index values. Examples: 0 (0,1,2...), 1 (1,2,3...), 100 (100,101,102...). Only applies when index-mode shows indices. Default: 0'
    )
    
    # Custom argument parsing to handle pandas arguments reliably
    defined_args, pandas_args = split_arguments(sys.argv, parser)
    
    # Parse defined arguments
    args = parser.parse_args(defined_args)  # Skip script name
    
    # Parse pandas arguments
    try:
        read_kwargs, write_kwargs = parse_pandas_args(pandas_args)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Set up logging after argument parsing is complete with StringSmith templates
    set_up_logging(
        level='INFO', 
        log_file='data_pipeline.log',
        enable_colors=True,
        console_template=(
            "{{#level_color;[;levelname;]}} {{message}}"
            "{{?has_file_name; - ;file_name;}}"
            "{{?has_file_count; (;file_count; files)}}"
            "{{ in ;duration;{$format_duration}}}"
            "{{?has_error_count; - ;error_count; errors}}"
            "{{?has_error; - ;error;}}"
        )
    )
    logger = get_logger('data_pipeline.cli')
    
    logger.info("Data pipeline started", input_folder=args.input_folder)
    
    # Basic validation
    if not Path(args.input_folder).exists():
        logger.error("Input folder does not exist", folder=args.input_folder)
        sys.exit(1)

    # Load custom schema if provided
    schema_map = None
    if args.schema:
        if not Path(args.schema).exists():
            logger.error("Schema file does not exist", schema_file=args.schema)
            sys.exit(1)
        try:
            import json
            with open(args.schema, 'r') as f:
                schema_map = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in schema file", schema_file=args.schema, error=str(e))
            sys.exit(1)
        except Exception as e:
            logger.error("Could not read schema file", schema_file=args.schema, error=str(e))
            sys.exit(1)

    # Create processor with both read and write defaults
    processor = DataProcessor(read_kwargs=read_kwargs, write_kwargs=write_kwargs)
    
    # Create processing configuration from CLI arguments
    config = ProcessingConfig.from_cli_args(args, read_kwargs, write_kwargs)
    
    # Add schema_map if provided
    if schema_map:
        config = config.with_schema_map(schema_map)
    
    summary = processor.run(config)

if __name__ == '__main__':
    main()