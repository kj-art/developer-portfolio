# data_pipeline/ui/cli.py
"""
Command-line interface for the Data Processing Pipeline

Provides a comprehensive CLI for data processing operations with progress tracking,
professional logging, and flexible configuration options.

Features:
- Auto-detection of file formats
- Schema normalization and column mapping
- Streaming and in-memory processing modes
- Progress tracking with tqdm
- Rich logging with StringSmith formatting
- Pandas parameter pass-through
- Configuration validation

Usage:
    python -m data_pipeline.ui.cli --input-folder ./data --output-file merged.csv
    python -m data_pipeline.ui.cli --input-folder ./data --recursive --progress
    python -m data_pipeline.ui.cli --help
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

from data_pipeline.core.processor import DataProcessor
from data_pipeline.core.processing_config import ProcessingConfig, IndexMode
from shared_utils.logger import set_up_logging, get_logger
from shared_utils.progress import create_progress_reporter


def split_arguments(argv: List[str], parser: argparse.ArgumentParser) -> Tuple[List[str], List[str]]:
    """
    Split command line arguments into defined args and pandas args
    
    This function separates arguments that are explicitly defined in our parser
    from those that should be passed through to pandas functions.
    """
    defined_args = []
    pandas_args = []
    
    # Get all defined argument names from parser
    defined_names = set()
    for action in parser._actions:
        for option_string in action.option_strings:
            defined_names.add(option_string)
    
    i = 0
    while i < len(argv):
        arg = argv[i]
        
        if arg.startswith('--'):
            # Check if this is a defined argument
            arg_name = arg.split('=')[0]  # Handle --arg=value format
            
            if arg_name in defined_names:
                defined_args.append(arg)
                # Check if we need to add the next argument as a value
                if '=' not in arg and i + 1 < len(argv) and not argv[i + 1].startswith('-'):
                    i += 1
                    if i < len(argv):
                        defined_args.append(argv[i])
            else:
                # This is a pandas argument
                pandas_args.append(arg)
                # Add value if present
                if '=' not in arg and i + 1 < len(argv) and not argv[i + 1].startswith('-'):
                    i += 1
                    if i < len(argv):
                        pandas_args.append(argv[i])
        elif arg.startswith('-'):
            # Short arguments - assume they're defined
            defined_args.append(arg)
            if i + 1 < len(argv) and not argv[i + 1].startswith('-'):
                i += 1
                if i < len(argv):
                    defined_args.append(argv[i])
        else:
            # Positional arguments go to defined
            defined_args.append(arg)
        
        i += 1
    
    return defined_args, pandas_args


def parse_pandas_args(pandas_args: List[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Parse pandas arguments with type casting and read/write separation
    
    Supports automatic type casting and manual type override with prefixes:
    - --sep "," → {'sep': ','}
    - --int:chunksize 1000 → {'chunksize': 1000}
    - --encoding "utf-8" "latin-1" → read={'encoding': 'utf-8'}, write={'encoding': 'latin-1'}
    """
    read_kwargs = {}
    write_kwargs = {}
    
    i = 0
    while i < len(pandas_args):
        if not pandas_args[i].startswith('--'):
            i += 1
            continue
        
        # Extract argument name and type prefix
        arg_name = pandas_args[i][2:]  # Remove --
        type_prefix = None
        
        if ':' in arg_name:
            type_prefix, arg_name = arg_name.split(':', 1)
        
        # Get values
        values = []
        i += 1
        while i < len(pandas_args) and not pandas_args[i].startswith('-'):
            values.append(pandas_args[i])
            i += 1
        
        if not values:
            continue
        
        # Apply type casting
        casted_values = []
        for value in values:
            if type_prefix == 'str':
                casted_values.append(str(value))
            elif type_prefix == 'int':
                try:
                    casted_values.append(int(value))
                except ValueError:
                    raise ValueError(f"Cannot convert '{value}' to integer for argument --{arg_name}")
            elif type_prefix == 'float':
                try:
                    casted_values.append(float(value))
                except ValueError:
                    raise ValueError(f"Cannot convert '{value}' to float for argument --{arg_name}")
            else:
                # Auto-detect type
                try:
                    if '.' in value or 'e' in value.lower():
                        casted_values.append(float(value))
                    else:
                        casted_values.append(int(value))
                except ValueError:
                    casted_values.append(value)
        
        # Distribute to read/write kwargs
        if len(casted_values) == 1:
            # Single value - applies to both read and write
            read_kwargs[arg_name] = casted_values[0]
            write_kwargs[arg_name] = casted_values[0]
        elif len(casted_values) == 2:
            # Two values - first for read, second for write
            read_kwargs[arg_name] = casted_values[0]
            write_kwargs[arg_name] = casted_values[1]
        else:
            # Multiple values - treat as list for both
            read_kwargs[arg_name] = casted_values
            write_kwargs[arg_name] = casted_values
    
    return read_kwargs, write_kwargs


def add_progress_arguments(parser: argparse.ArgumentParser):
    """Add progress-related CLI arguments"""
    progress_group = parser.add_argument_group('progress options')
    
    progress_group.add_argument(
        '--progress',
        action='store_true',
        help='Show progress bars during processing'
    )
    
    progress_group.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress reporting (overrides --progress)'
    )
    
    progress_group.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output - no progress bars or detailed logging'
    )


def determine_progress_mode(args) -> str:
    """Determine the appropriate progress mode from CLI arguments"""
    if args.quiet:
        return 'null'
    elif args.no_progress:
        return 'null'
    elif args.progress:
        return 'cli'
    else:
        # Auto-detect based on terminal
        return 'auto'


def main():
    """Main CLI entry point with enhanced progress tracking"""
    parser = argparse.ArgumentParser(
        description='Multi-File Data Processing Pipeline - Merge and normalize data from multiple file formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic usage:
    %(prog)s --input-folder ./data --output-file merged.csv
    
  Advanced processing:
    %(prog)s --input-folder ./customer_data --recursive --progress \\
             --filetype csv xlsx --index-mode sequential \\
             --columns first_name,last_name,email
    
  With pandas options:
    %(prog)s --input-folder ./data --sep ";" --encoding utf-8 latin-1
    
  Schema mapping:
    %(prog)s --input-folder ./data --schema ./schema.json
        """
    )

    # Core arguments
    parser.add_argument(
        '--input-folder',
        required=True,
        help='Path to folder containing input files'
    )

    parser.add_argument(
        '--output-file',
        help='Output file path. If not specified, results are printed to console'
    )

    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Process files in subdirectories recursively'
    )

    parser.add_argument(
        '--filetype',
        nargs='+',
        choices=['csv', 'xlsx', 'json'],
        default=['csv', 'xlsx', 'json'],
        help='File types to process (default: csv xlsx json)'
    )

    # Schema and column options
    parser.add_argument(
        '--schema',
        help='JSON file containing column mapping schema'
    )

    parser.add_argument(
        '--columns',
        help='Comma-separated list of expected column names'
    )

    # Column normalization options
    parser.add_argument(
        '--to-lower',
        action=argparse.BooleanOptionalAction,
        default=True,
        help='Convert column names to lowercase (default: true)'
    )

    parser.add_argument(
        '--spaces-to-underscores',
        action=argparse.BooleanOptionalAction,
        default=True,
        help='Convert spaces to underscores in column names (default: true)'
    )

    # Processing options
    parser.add_argument(
        '--force-in-memory',
        action='store_true',
        help='Force in-memory processing instead of streaming (for small datasets)'
    )

    # Index management
    parser.add_argument(
        '--index-mode',
        choices=['none', 'local', 'sequential'],
        type=str.lower,
        help='Index handling mode: none=no index column, local=per-file indices (0,1,2 then 0,1,2), sequential=continuous across files (0,1,2,3,4...)'
    )

    parser.add_argument(
        '--index-start',
        type=int,
        default=0,
        help='Starting number for index values (default: 0)'
    )

    # Add progress arguments
    add_progress_arguments(parser)
    
    # Custom argument parsing to handle pandas arguments reliably
    defined_args, pandas_args = split_arguments(sys.argv, parser)
    
    # Parse defined arguments
    args = parser.parse_args(defined_args[1:])  # Skip script name
    
    # Parse pandas arguments
    try:
        read_kwargs, write_kwargs = parse_pandas_args(pandas_args)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Set up logging after argument parsing is complete
    log_level = 'WARNING' if args.quiet else 'INFO'
    set_up_logging(
        level=log_level,
        log_file='data_pipeline.log',
        enable_colors=True
    )
    logger = get_logger('data_pipeline.cli')
    
    # Create progress reporter
    progress_mode = determine_progress_mode(args)
    progress_reporter = create_progress_reporter(mode=progress_mode)
    
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
    
    # Set progress reporter on processor if it supports it
    if hasattr(processor, 'set_progress_reporter'):
        processor.set_progress_reporter(progress_reporter)
    
    # Create processing configuration from CLI arguments
    config = ProcessingConfig.from_cli_args(args, read_kwargs, write_kwargs)
    
    # Add schema_map if provided
    if schema_map:
        config = config.with_schema_map(schema_map)
    
    try:
        # Run processing with progress tracking
        result = processor.run(config)
        
        # Display results
        if not args.quiet:
            print(f"\n✅ Processing Complete!")
            print(f"Files processed: {result.files_processed}")
            print(f"Total rows: {result.total_rows:,}")
            print(f"Total columns: {result.total_columns}")
            print(f"Processing time: {result.processing_time:.2f}s")
            
            if result.processing_time > 0:
                rate = result.total_rows / result.processing_time
                print(f"Processing rate: {rate:.0f} rows/sec")
            
            if result.output_file:
                print(f"Output written to: {result.output_file}")
            else:
                print("Results displayed above")
        
        logger.info("Processing completed successfully",
                   files_processed=result.files_processed,
                   total_rows=result.total_rows,
                   processing_time=result.processing_time)
        
    except KeyboardInterrupt:
        logger.info("Processing cancelled by user")
        print("\n⚠️ Processing cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error("Processing failed", error=str(e))
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()