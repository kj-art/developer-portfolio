"""
CLI Interface for Batch Rename Tool

Handles command line argument parsing and user interaction.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from ..core.processor import BatchRenameProcessor
from ..core.config import RenameConfig


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
    """Create the command line argument parser."""
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

  # Custom function handles everything
  python batch_rename.py --input-folder ./files \\
    --extract-and-convert my_logic.py --preview
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
    
    return None


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate arguments
    error = validate_args(args)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    
    try:
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
        
        # Create processor and run
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        # Show results
        if config.preview_mode:
            print(f"\nPreview completed: {result.files_analyzed} files analyzed")
            print(f"Would rename {result.files_to_rename} files")
            if result.collisions:
                print(f"Found {result.collisions} naming conflicts")
            
            # Show detailed preview only if --verbose is specified
            if args.verbose and result.preview_data:
                # Filter to only show files that would actually change
                changes = [entry for entry in result.preview_data if entry['old_name'] != entry['new_name']]
                
                if changes:
                    # Check if there are too many changes to display
                    if len(changes) > 10:
                        response = input(f"\nFound {len(changes)} files to rename. Display all changes? (y/N): ")
                        if response.lower() not in ['y', 'yes']:
                            print("Skipping detailed preview.")
                        else:
                            print(f"\nDetailed preview ({len(changes)} changes):")
                            print("-" * 60)
                            for entry in changes:
                                print(f"{entry['old_name']} → {entry['new_name']}")
                            print("-" * 60)
                    else:
                        print(f"\nDetailed preview ({len(changes)} changes):")
                        print("-" * 60)
                        for entry in changes:
                            print(f"{entry['old_name']} → {entry['new_name']}")
                        print("-" * 60)
                else:
                    print("\nNo files would be changed.")
            
            print("\nUse --execute to perform the renames")
        else:
            print(f"\nRename completed: {result.files_renamed} files renamed")
            if result.errors:
                print(f"Errors: {result.errors}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()