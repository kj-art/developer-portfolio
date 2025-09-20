"""
CLI Interface for Batch Rename Tool

Handles command line argument parsing and user interaction with graceful dependency handling.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Try to import core modules with graceful fallbacks
try:
    from ..core.processor import BatchRenameProcessor
    from ..core.config import RenameConfig
    CORE_AVAILABLE = True
except ImportError:
    BatchRenameProcessor = None
    RenameConfig = None
    CORE_AVAILABLE = False

# Try to import logging with fallback
try:
    from ..core.logging_processor import create_logging_processor
    LOGGING_AVAILABLE = True
except ImportError:
    create_logging_processor = None
    LOGGING_AVAILABLE = False

# Try to import validators with fallback
try:
    from ..core.validators import get_validator
    from ..core.function_loader import load_custom_function
    from ..core.templates import is_template_function
    VALIDATION_AVAILABLE = True
except ImportError:
    get_validator = None
    load_custom_function = None
    is_template_function = None
    VALIDATION_AVAILABLE = False


def parse_function_call(call_string: str) -> Tuple[Optional[str], List[str], Dict[str, str], bool]:
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
  # Basic split extraction with template
  python batch_rename.py --input-folder ./docs \\
    --extractor split,_,dept,type,date \\
    --template template,"{dept}_{type}_{date}" \\
    --preview

  # Multiple converters with template formatting
  python batch_rename.py --input-folder ./docs \\
    --extractor split,_,dept,type,date \\
    --converter pad_numbers,date,4 \\
    --converter date_format,date,%Y%m%d,%Y-%m-%d \\
    --template stringsmith,"{{;dept;}}{{_;type;}}{{_;date;}}" \\
    --preview

  # All-in-one function (no converters or templates needed)
  python batch_rename.py --input-folder ./files \\
    --extract-and-convert my_logic.py \\
    --execute
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
    
    # Template formatting (separate from converters, optional, max one)
    parser.add_argument(
        '--template',
        help='Template formatter: "template,{pattern}" or "stringsmith,{{;pattern;}}" (applied after all converters)'
    )
    
    # Filtering options (can have multiple)
    parser.add_argument(
        '--filter',
        action='append',
        help='Filter function call: "function,arg1,arg2,key=value" (use !function to invert, can be repeated)'
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
    
    # Template constraints validation (only if validation is available)
    if args.template and VALIDATION_AVAILABLE:
        template_name, _, _, _ = parse_function_call(args.template)
        if not is_template_function(template_name) and not Path(template_name).suffix == '.py':
            return f"Invalid template type '{template_name}'. Only 'template', 'stringsmith', or custom .py files are allowed."
    
    # Extractor + converter/template requirement
    if args.extractor and not args.converter and not args.template:
        return "When using --extractor, must provide at least one --converter or --template"
    
    # Extract-and-convert should be standalone
    if args.extract_and_convert and (args.converter or args.template):
        return "Cannot use --converter or --template with --extract-and-convert"
    
    # Custom function validation (only if validation is available)
    if VALIDATION_AVAILABLE:
        # Validate custom extractor functions
        if args.extractor and Path(args.extractor.split(',')[0]).suffix == '.py':
            try:
                extractor_path = args.extractor.split(',')[0]
                function_name = args.extractor.split(',')[1] if ',' in args.extractor else None
                if not function_name:
                    return f"Custom extractor requires function name: {extractor_path},function_name"
                
                # Load and validate function
                func = load_custom_function(extractor_path, function_name)
                validator = get_validator('extractor')
                result = validator(func)
                if not result.valid:
                    return f"Extractor function validation failed: {result.message}"
                    
            except Exception as e:
                return f"Extractor validation error: {e}"
        
        # Validate custom converter functions
        if args.converter:
            for converter_call in args.converter:
                parts = converter_call.split(',')
                if len(parts) > 0 and Path(parts[0]).suffix == '.py':
                    try:
                        converter_path = parts[0]
                        function_name = parts[1] if len(parts) > 1 else None
                        if not function_name:
                            return f"Custom converter requires function name: {converter_path},function_name"
                        
                        # Load and validate function
                        func = load_custom_function(converter_path, function_name)
                        validator = get_validator('converter')
                        result = validator(func)
                        if not result.valid:
                            return f"Converter function validation failed: {result.message}"
                            
                    except Exception as e:
                        return f"Converter validation error: {e}"
    
    return None


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate arguments
    error = validate_args(args)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    
    # Check if core functionality is available
    if not CORE_AVAILABLE:
        print("Error: Core batch rename functionality not available", file=sys.stderr)
        return 1
    
    try:
        # Set up logging if available
        if LOGGING_AVAILABLE:
            processor = create_logging_processor(
                log_level=args.log_level,
                log_file=args.log_file,
                enable_colors=not args.no_colors
            )
        else:
            processor = BatchRenameProcessor()
        
        # Parse extractor configuration
        if args.extractor:
            extractor_name, pos_args, kwargs, _ = parse_function_call(args.extractor)
            extractor_args = {'positional': pos_args, 'keyword': kwargs}
        else:
            extractor_name = None
            extractor_args = {}
        
        # Parse converter configurations
        converters = []
        if args.converter:
            for converter_call in args.converter:
                conv_name, pos_args, kwargs, inverted = parse_function_call(converter_call)
                if inverted:
                    print("Error: Converters cannot be inverted with !", file=sys.stderr)
                    return 1
                
                converters.append({
                    'name': conv_name,
                    'positional': pos_args,
                    'keyword': kwargs
                })
        
        # Parse template configuration
        template = None
        if args.template:
            template_name, pos_args, kwargs, inverted = parse_function_call(args.template)
            if inverted:
                print("Error: Templates cannot be inverted with !", file=sys.stderr)
                return 1
            
            template = {
                'name': template_name,
                'positional': pos_args,
                'keyword': kwargs
            }
        
        # Parse filter configurations
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
            template=template,
            extract_and_convert=args.extract_and_convert,
            filters=filters,
            recursive=args.recursive,
            preview_mode=args.preview and not args.execute,
            on_existing_collision=args.on_existing_collision,
            on_internal_collision=args.on_internal_collision
        )
        
        # Execute processing
        result = processor.process(config)
        
        # Print results
        operation_type = "PREVIEW" if config.preview_mode else "EXECUTE"
        print(f"\n=== BATCH RENAME {operation_type} RESULTS ===")
        print(f"Files analyzed: {result.files_analyzed}")
        
        if config.preview_mode:
            print(f"Files to rename: {result.files_to_rename}")
            if result.files_to_rename > 0:
                print("\nPreview of changes:")
                for item in result.preview_data[:10]:  # Show first 10
                    print(f"  {item['old_name']} → {item['new_name']}")
                if len(result.preview_data) > 10:
                    print(f"  ... and {len(result.preview_data) - 10} more")
                print(f"\nTo execute these changes, add --execute to your command.")
        else:
            print(f"Files renamed: {result.files_renamed}")
        
        if result.errors > 0:
            print(f"\nErrors: {result.errors}")
            for error in result.error_details[:5]:  # Show first 5 errors
                print(f"  {error['file']}: {error['error']}")
            if len(result.error_details) > 5:
                print(f"  ... and {len(result.error_details) - 5} more errors")
        
        if result.collisions > 0:
            print(f"\nWarning: {result.collisions} naming conflicts detected!")
        
        return 0 if result.errors == 0 else 1
        
    except KeyboardInterrupt:
        if not args.quiet:
            print("\nOperation cancelled by user.")
        return 130
            
    except Exception as e:
        if not args.quiet:
            print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())