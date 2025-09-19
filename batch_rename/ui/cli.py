"""
CLI Interface for Batch Rename Tool with Logging Integration

Handles command line argument parsing and user interaction with comprehensive logging.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from ..core.processor import BatchRenameProcessor
from ..core.config import RenameConfig
from ..core.logging_processor import LoggingBatchRenameProcessor, create_logging_processor
from shared_utils.logger import get_logger


def parse_function_call(call_string: str) -> tuple:
    """
    Parse function call syntax: "function,arg1,arg2,key=value"
    
    Args:
        call_string: String like "split,_,dept,type,date" or "pad_numbers,field=seq,width=3"
        
    Returns:
        Tuple of (function_name, positional_args, keyword_args, inverted)
    """
    if not call_string:
        return None, [], {}, False
    
    # Handle inversion with ! prefix
    inverted = call_string.startswith('!')
    if inverted:
        call_string = call_string[1:]
    
    # Split on comma
    parts = [part.strip() for part in call_string.split(',')]
    
    if not parts:
        return None, [], {}, inverted
    
    function_name = parts[0]
    positional_args = []
    keyword_args = {}
    
    # Parse remaining arguments
    for part in parts[1:]:
        if '=' in part:
            # Keyword argument
            key, value = part.split('=', 1)
            keyword_args[key.strip()] = value.strip()
        else:
            # Positional argument
            positional_args.append(part)
    
    return function_name, positional_args, keyword_args, inverted


def create_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser with logging options."""
    parser = argparse.ArgumentParser(
        description="Professional batch file renaming with extractors and converters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic split extraction with template conversion
  python batch_rename.py --input-folder ./docs \\
    --extractor split,_,dept,type,date \\
    --converter template,"{dept}_{type}_{date}" \\
    --preview

  # With detailed logging to file
  python batch_rename.py --input-folder ./docs \\
    --extractor split,_,dept,type,date \\
    --converter template,"{dept}_{type}_{date}" \\
    --execute --log-level DEBUG --log-file operations.log

  # Quiet execution for scripts
  python batch_rename.py --input-folder ./files \\
    --extract-and-convert my_logic.py \\
    --execute --quiet --log-file batch.log
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--input-folder',
        required=True,
        type=Path,
        help='Folder containing files to rename'
    )
    
    # Extraction options (mutually exclusive)
    extraction_group = parser.add_mutually_exclusive_group(required=True)
    extraction_group.add_argument(
        '--extractor',
        help='Extractor function call: "function,arg1,arg2,key=value"'
    )
    extraction_group.add_argument(
        '--extract-and-convert',
        help='Path to function that handles both extraction and conversion'
    )
    
    # Conversion options (can have multiple)
    parser.add_argument(
        '--converter',
        action='append',
        help='Converter function call: "function,arg1,arg2,key=value" (can be repeated)'
    )
    
    # Filtering options (can have multiple)
    parser.add_argument(
        '--filter',
        action='append',
        help='Filter function call: "function,arg1,arg2,key=value" (use ! prefix to exclude)'
    )
    
    # Processing options
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Process subdirectories recursively'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        default=True,
        help='Show changes without executing (default: true)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed preview of all file changes'
    )
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually perform the renames (overrides --preview)'
    )
    
    # Collision handling
    parser.add_argument(
        '--on-existing-collision',
        choices=['skip', 'overwrite', 'backup', 'rename'],
        default='skip',
        help='How to handle collisions with existing files'
    )
    
    parser.add_argument(
        '--on-internal-collision',
        choices=['error', 'auto-number', 'skip-duplicates'],
        default='error',
        help='How to handle multiple files mapping to same name'
    )
    
    # Logging options
    logging_group = parser.add_argument_group('logging options')
    
    logging_group.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging verbosity level (default: INFO)'
    )
    
    logging_group.add_argument(
        '--log-file',
        type=str,
        metavar='PATH',
        help='Write detailed logs to file (creates .json file for structured logs)'
    )
    
    logging_group.add_argument(
        '--no-colors',
        action='store_true',
        help='Disable colored console output'
    )
    
    logging_group.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress non-essential output (errors only)'
    )
    
    return parser


def validate_args(args) -> Optional[str]:
    """
    Validate parsed arguments for consistency and completeness.
    
    Returns:
        Error message if validation fails, None if valid
    """
    # Check input folder exists
    if not args.input_folder.exists():
        return f"Input folder does not exist: {args.input_folder}"
    
    if not args.input_folder.is_dir():
        return f"Input path is not a directory: {args.input_folder}"
    
    # If using separate extractor, need converters
    if args.extractor and not args.converter:
        return "When using --extractor, must provide at least one --converter"
    
    # Check custom function files exist
    if args.extractor:
        try:
            func_name, _, _, _ = parse_function_call(args.extractor)
            if func_name and Path(func_name).suffix == '.py':
                if not Path(func_name).exists():
                    return f"Extractor file not found: {func_name}"
        except:
            pass  # Skip validation if parsing fails
    
    if args.extract_and_convert:
        if not Path(args.extract_and_convert).exists():
            return f"Extract-and-convert file not found: {args.extract_and_convert}"
    
    if args.converter:
        for converter_call in args.converter:
            try:
                func_name, _, _, _ = parse_function_call(converter_call)
                if func_name and Path(func_name).suffix == '.py':
                    if not Path(func_name).exists():
                        return f"Converter file not found: {func_name}"
            except:
                pass  # Skip validation if parsing fails
    
    # Validate log file path
    if args.log_file:
        log_path = Path(args.log_file)
        if not log_path.parent.exists():
            return f"Log file directory does not exist: {log_path.parent}"
    
    return None


def setup_logging_and_processor(args):
    """Setup logging configuration and create logging processor."""
    
    # Handle legacy verbose flag
    log_level = args.log_level
    if args.verbose and log_level == 'INFO':
        log_level = 'DEBUG'
    
    # Create logging processor with configuration
    processor = create_logging_processor(
        log_level=log_level,
        log_file=args.log_file,
        enable_colors=not args.no_colors,
    )
    
    return processor


def print_operation_header(args):
    """Print operation header information if not in quiet mode."""
    if args.quiet:
        return
        
    operation_type = "PREVIEW" if (args.preview and not args.execute) else "EXECUTE"
    
    print(f"\n=== BATCH RENAME {operation_type} ===")
    print(f"Input folder: {args.input_folder}")
    
    if args.extractor:
        print(f"Extractor: {args.extractor}")
    elif args.extract_and_convert:
        print(f"Extract & Convert: {args.extract_and_convert}")
    
    if args.converter:
        converter_summary = " -> ".join(args.converter)
        print(f"Converters: {converter_summary}")
    
    if args.filter:
        filter_summary = []
        for filt in args.filter:
            if filt.startswith('!'):
                filter_summary.append(f"!{filt[1:]}")
            else:
                filter_summary.append(filt)
        print(f"Filters: {', '.join(filter_summary)}")
    
    print(f"Recursive: {'Yes' if args.recursive else 'No'}")
    print()


def print_operation_results(args, result):
    """Print operation results in CLI-friendly format if not in quiet mode."""
    if args.quiet:
        return
        
    print(f"\n=== RESULTS ===")
    print(f"Files analyzed: {result.files_analyzed}")
    
    if args.preview and not args.execute:
        print(f"Files to rename: {result.files_to_rename}")
        
        if result.files_to_rename > 0:
            print(f"\nTo execute these changes, add --execute to your command.")
    else:
        print(f"Files renamed: {result.files_renamed}")
        
        if result.files_renamed > 0:
            success_rate = (result.files_renamed / result.files_to_rename * 100) if result.files_to_rename > 0 else 0
            print(f"Success rate: {success_rate:.1f}%")
    
    # Print warnings/errors
    if result.collisions > 0:
        print(f"\n⚠️  Warning: {result.collisions} naming conflicts detected!")
        print("   Some files would have the same new name.")
    
    if result.errors > 0:
        print(f"\n❌ Errors: {result.errors} files failed to process")
        
        # Show first few errors if not using file logging
        if not args.log_file and result.error_details:
            print("\nError details:")
            for error in result.error_details[:3]:
                print(f"  • {error['file']}: {error['error']}")
            
            if len(result.error_details) > 3:
                print(f"  ... and {len(result.error_details) - 3} more errors")
                print("  Use --log-file or --log-level DEBUG for full error details")
    
    # Print preview sample if requested
    if args.verbose and result.preview_data and (args.preview and not args.execute):
        print_preview_sample(result.preview_data, enable_colors=not args.no_colors)


def print_preview_sample(preview_data, enable_colors=None):
    """Print sample of preview changes with collision highlighting."""
    
    # Auto-detect if we should use colors
    if enable_colors is None:
        enable_colors = sys.stdout.isatty()  # True if terminal, False if piped
    
    # Filter to only show actual changes
    changes = [item for item in preview_data if item['old_name'] != item['new_name']]
    
    if not changes:
        print("\nNo filename changes would be made.")
        return
    
    # Find collisions - new names that appear multiple times
    new_names = [change['new_name'] for change in changes]
    collision_names = {name for name in new_names if new_names.count(name) > 1}
    
    # ANSI color codes (only if colors enabled)
    if enable_colors:
        RED = '\033[91m'
        RESET = '\033[0m'
    else:
        RED = ''
        RESET = ''
    
    def format_change(change):
        """Format a change with red highlighting for collisions."""
        old_name = change['old_name']
        new_name = change['new_name']
        
        if new_name in collision_names:
            if enable_colors:
                return f"  {old_name} → {RED}{new_name}{RESET}"
            else:
                return f"  {old_name} → {new_name} [COLLISION]"
        else:
            return f"  {old_name} → {new_name}"
    
    print(f"\nSample changes (showing first {min(5, len(changes))} of {len(changes)}):")
    
    for change in changes[:5]:
        print(format_change(change))
    
    if len(changes) > 5:
        print(f"  ... and {len(changes) - 5} more changes")
        
        if len(changes) > 10:
            response = input(f"\nFound {len(changes)} files to rename. Display all changes? (y/N): ")
            if response.lower() in ['y', 'yes']:
                print(f"\nDetailed preview ({len(changes)} changes):")
                print("-" * 60)
                for entry in changes:
                    print(format_change(entry))
                print("-" * 60)
                
                if collision_names:
                    if enable_colors:
                        print(f"\n{RED}Files in red have naming conflicts{RESET}")
                    else:
                        print("\nFiles marked [COLLISION] have naming conflicts")


def main():
    """Main CLI entry point with integrated logging."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate arguments
    error = validate_args(args)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Setup logging and create processor
        processor = setup_logging_and_processor(args)
        
        # Get CLI logger
        cli_logger = get_logger('batch_rename.cli')
        
        # Print operation header
        print_operation_header(args)
        
        # Parse extractor
        extractor_name = None
        extractor_args = {}
        if args.extractor:
            extractor_name, pos_args, kwargs, inverted = parse_function_call(args.extractor)
            if inverted:
                print("Error: Extractors cannot be inverted with !", file=sys.stderr)
                sys.exit(1)
            extractor_args = {'positional': pos_args, 'keyword': kwargs}
        
        # Parse converters
        converters = []
        if args.converter:
            for converter_call in args.converter:
                conv_name, pos_args, kwargs, inverted = parse_function_call(converter_call)
                if inverted:
                    print("Error: Converters cannot be inverted with !", file=sys.stderr)
                    sys.exit(1)
                converters.append({
                    'name': conv_name,
                    'positional': pos_args,
                    'keyword': kwargs
                })
        
        # Parse filters
        filters = []
        if args.filter:
            for filter_call in args.filter:
                filter_name, pos_args, kwargs, inverted = parse_function_call(filter_call)
                filters.append({
                    'name': filter_name,
                    'positional': pos_args,
                    'keyword': kwargs,
                    'inverted': inverted
                })
        
        # Create configuration
        config = RenameConfig(
            input_folder=args.input_folder,
            extractor=extractor_name,
            extractor_args=extractor_args,
            converters=converters,
            extract_and_convert=args.extract_and_convert,
            filters=filters,
            recursive=args.recursive,
            preview_mode=args.preview and not args.execute,
            on_existing_collision=args.on_existing_collision,
            on_internal_collision=args.on_internal_collision
        )
        
        # Execute with logging
        cli_logger.info("CLI operation started", 
                       operation_type="preview" if config.preview_mode else "execute",
                       input_folder=str(args.input_folder))
        
        result = processor.process(config)
        
        # Print results
        print_operation_results(args, result)
        
        # Log completion
        cli_logger.info("CLI operation completed",
                       files_analyzed=result.files_analyzed,
                       files_renamed=result.files_renamed,
                       errors=result.errors)
        
        # Determine exit code
        if result.errors > 0:
            cli_logger.warning("Operation completed with errors", error_count=result.errors)
            sys.exit(1)
        
        if not args.quiet and config.preview_mode and result.files_to_rename > 0:
            print("\nUse --execute to perform the renames")
    
    except KeyboardInterrupt:
        cli_logger.warning("Operation cancelled by user")
        if not args.quiet:
            print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)  # Standard exit code for SIGINT
        
    except Exception as e:
        cli_logger.error("CLI execution failed", exception=e)
        if not args.quiet:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()