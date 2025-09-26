#!/usr/bin/env python3
"""
Command Line Interface for Batch Rename Tool.

Supports both traditional CLI argument configuration and YAML/JSON config files.
Config files are optional - all functionality available via CLI arguments.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from ..core.processor import BatchRenameProcessor
from ..core.config import RenameConfig


def parse_function_call(call_string: str) -> Tuple[str, List[str], Dict[str, Any], bool]:
    """
    Parse function call string into components.
    
    Examples:
        'split,_,dept,type' → ('split', ['_', 'dept', 'type'], {}, False)
        'case,field,upper' → ('case', ['field', 'upper'], {}, False)
        '!pattern,*backup*' → ('pattern', ['*backup*'], {}, True)
    """
    # Check for inversion prefix
    inverted = call_string.startswith('!')
    if inverted:
        call_string = call_string[1:]
    
    parts = [part.strip() for part in call_string.split(',')]
    function_name = parts[0]
    
    # For now, treat everything as positional args
    # Future enhancement: support key=value syntax for keyword args
    positional_args = parts[1:] if len(parts) > 1 else []
    keyword_args = {}
    
    return function_name, positional_args, keyword_args, inverted


def highlight_collisions(preview_data: List[Dict], use_colors: bool = True) -> List[Dict]:
    """Add collision highlighting to preview data."""
    if not use_colors:
        return preview_data
    
    # Find duplicate new names
    new_names = [item['new_name'] for item in preview_data]
    duplicates = set([name for name in new_names if new_names.count(name) > 1])
    
    # Add color highlighting for duplicates
    for item in preview_data:
        if item['new_name'] in duplicates:
            item['new_name'] = f"\033[91m{item['new_name']}\033[0m"  # Red color
    
    return preview_data


def create_config_from_cli_args(args) -> RenameConfig:
    """Create RenameConfig from CLI arguments (traditional mode)."""
    
    # Parse extractor configuration
    if not args.extractor:
        raise ValueError("--extractor is required when not using --config")
    
    extractor_name, pos_args, kwargs, inverted = parse_function_call(args.extractor)
    if inverted:
        raise ValueError("Extractor cannot be inverted with !")
    
    extractor_args = {
        'positional': pos_args,
        'keyword': kwargs
    }
    
    # Parse converter configurations
    converters = []
    if args.converter:
        for conv_call in args.converter:
            conv_name, pos_args, kwargs, inverted = parse_function_call(conv_call)
            if inverted:
                raise ValueError("Converters cannot be inverted with !")
            
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
            raise ValueError("Templates cannot be inverted with !")
        
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
    
    # Create configuration from CLI arguments
    return RenameConfig(
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


def create_config_from_file(args) -> RenameConfig:
    """Create RenameConfig from config file with CLI overrides."""
    from ..config.config_loader import ConfigLoader
    
    # Prepare CLI overrides
    cli_overrides = {}
    if hasattr(args, 'input_folder') and args.input_folder:
        cli_overrides['input_folder'] = args.input_folder
    if hasattr(args, 'recursive'):
        cli_overrides['recursive'] = args.recursive
    if hasattr(args, 'execute') and args.execute:
        cli_overrides['execute'] = args.execute
    if hasattr(args, 'preview') and args.preview:
        cli_overrides['preview_mode'] = True
    
    # Load configuration from file
    config = ConfigLoader.load_rename_config(args.config, cli_overrides)
    
    # Validate that required fields are present
    if not config.input_folder:
        raise ValueError("input_folder must be specified in config file or via --input-folder")
    
    return config


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description='Batch rename files using extractors, converters, and templates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Traditional CLI usage
  python -m batch_rename.ui.cli --input-folder ./docs \\
    --extractor split,_,dept,type,date \\
    --converter case,dept,upper \\
    --template join,dept,type,date,separator=-

  # Using configuration file
  python -m batch_rename.ui.cli --config corporate_docs.yaml

  # Config file with CLI overrides
  python -m batch_rename.ui.cli --config media_files.yaml \\
    --input-folder ./photos --execute

  # Preview mode (safe - no actual renaming)
  python -m batch_rename.ui.cli --config corporate_docs.yaml --preview
        """
    )
    
    # Configuration source (mutually exclusive with traditional args)
    config_group = parser.add_argument_group('Configuration')
    config_group.add_argument('--config', 
                             help='Load configuration from YAML/JSON file')
    
    # Input/output options
    io_group = parser.add_argument_group('Input/Output')
    io_group.add_argument('--input-folder', required=False,
                         help='Folder containing files to rename')
    io_group.add_argument('--recursive', action='store_true',
                         help='Process subdirectories recursively')
    
    # Processing pipeline (traditional CLI mode)
    pipeline_group = parser.add_argument_group('Processing Pipeline (CLI mode)')
    pipeline_group.add_argument('--extractor', 
                               help='Extractor function: name,arg1,arg2,...')
    pipeline_group.add_argument('--converter', action='append',
                               help='Converter function: name,arg1,arg2,... (can specify multiple)')
    pipeline_group.add_argument('--template',
                               help='Template function: name,arg1,arg2,...')
    pipeline_group.add_argument('--filter', action='append',
                               help='Filter function: name,arg1,arg2,... (can specify multiple)')
    pipeline_group.add_argument('--extract-and-convert',
                               help='All-in-one function: filename.py,function_name')
    
    # Execution control
    execution_group = parser.add_argument_group('Execution Control')
    execution_group.add_argument('--preview', action='store_true', default=True,
                                help='Show preview of changes (default)')
    execution_group.add_argument('--execute', action='store_true',
                                help='Execute the rename operations (overrides --preview)')
    
    # Collision handling
    collision_group = parser.add_argument_group('Collision Handling')
    collision_group.add_argument('--on-existing-collision', 
                                choices=['skip', 'error', 'append_number'], default='skip',
                                help='How to handle files that would overwrite existing files')
    collision_group.add_argument('--on-internal-collision',
                                choices=['skip', 'error', 'append_number'], default='skip', 
                                help='How to handle multiple files getting the same new name')
    
    # Display options
    display_group = parser.add_argument_group('Display Options')
    display_group.add_argument('--no-colors', action='store_true',
                              help='Disable colored output')
    display_group.add_argument('--quiet', action='store_true',
                              help='Minimal output')
    display_group.add_argument('--verbose', action='store_true',
                              help='Detailed output')
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate argument combinations
    if not args.config and not args.input_folder:
        print("Error: Either --config or --input-folder must be specified", file=sys.stderr)
        return 1
    
    if not args.config and not args.extractor:
        print("Error: --extractor is required when not using --config", file=sys.stderr)
        return 1
    
    # Color support detection
    use_colors = not args.no_colors and sys.stdout.isatty()
    
    try:
        # Create processor
        processor = BatchRenameProcessor()
        
        # Create configuration from appropriate source
        if args.config:
            config = create_config_from_file(args)
        else:
            config = create_config_from_cli_args(args)
        
        # Validate input folder exists
        if not Path(config.input_folder).exists():
            print(f"Error: Input folder does not exist: {config.input_folder}", file=sys.stderr)
            return 1
        
        # Execute processing
        result = processor.process(config)
        
        # Display results
        if not args.quiet:
            operation_type = "PREVIEW" if config.preview_mode else "EXECUTE"
            print(f"\n=== BATCH RENAME {operation_type} RESULTS ===")
            print(f"Files analyzed: {result.files_found}")
            
            if config.preview_mode:
                print(f"Files to rename: {result.files_to_rename}")
                if result.files_to_rename > 0:
                    print("\nPreview of changes:")
                    
                    # Highlight collisions if colors are enabled
                    preview_data = highlight_collisions(result.preview_data, use_colors)
                    
                    # Display changes in pages of 10
                    page_size = 10
                    total_changes = len(preview_data)
                    
                    for page_start in range(0, total_changes, page_size):
                        page_end = min(page_start + page_size, total_changes)
                        
                        # Show current page
                        for item in preview_data[page_start:page_end]:
                            print(f"  {item['old_name']} → {item['new_name']}")
                        
                        # Check if there are more pages
                        remaining = total_changes - page_end
                        if remaining > 0:
                            print(f"\nShowing {page_end}/{total_changes} changes.", end=" ")
                            try:
                                input("Press Enter to see more, Ctrl+C to stop...")
                                print()
                            except KeyboardInterrupt:
                                print(f"\n\n({remaining} more changes not shown)")
                                break
                
                if result.collisions > 0:
                    print(f"\n⚠️  Warning: {result.collisions} naming collisions detected")
                    print("Use --execute to proceed, or modify configuration to resolve conflicts")
                
                print(f"\nTo execute these changes, run with --execute")
                
            else:  # Execute mode
                print(f"Files renamed: {result.files_renamed}")
                if result.errors > 0:
                    print(f"Errors: {result.errors}")
                    if args.verbose and result.error_details:
                        print("\nError details:")
                        for error in result.error_details:
                            print(f"  {error['file']}: {error['error']}")
                
                if result.files_renamed > 0:
                    print("✅ Rename operation completed successfully")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())