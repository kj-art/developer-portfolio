"""
CLI integration with logging support for batch rename operations.

Provides enhanced CLI functionality with comprehensive logging options
and professional output formatting.
"""

import sys
from pathlib import Path
from typing import Optional

from .logging_processor import LoggingBatchRenameProcessor, create_logging_processor
from .config import RenameConfig
from shared_utils.logger import get_logger


class CLIProcessor:
    """
    Enhanced CLI processor with integrated logging capabilities.
    
    Handles command-line execution with proper logging configuration,
    error handling, and user-friendly output formatting.
    """
    
    def __init__(self, log_level: str = 'INFO', 
                 log_file: Optional[str] = None,
                 enable_colors: bool = True,
                 quiet: bool = False):
        """
        Initialize CLI processor with logging configuration.
        
        Args:
            log_level: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
            log_file: Optional log file path
            enable_colors: Enable colored console output
            quiet: Suppress non-essential output
        """
        self.quiet = quiet
        self.log_level = log_level
        
        # Create logging processor
        self.processor = create_logging_processor(
            log_level=log_level,
            log_file=log_file,
            enable_colors=enable_colors and not quiet
        )
        
        # Get CLI-specific logger
        self.cli_logger = get_logger('batch_rename.cli')
    
    def execute(self, config: RenameConfig) -> int:
        """
        Execute batch rename operation with CLI-appropriate logging and output.
        
        Args:
            config: Rename configuration
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            # Log CLI execution start
            if not self.quiet:
                self._print_operation_header(config)
            
            # Execute with logging
            result = self.processor.process(config)
            
            # Print CLI-friendly results
            if not self.quiet:
                self._print_operation_results(config, result)
            
            # Determine exit code
            if result.errors > 0:
                self.cli_logger.warning("Operation completed with errors",
                                      error_count=result.errors)
                return 1
            
            return 0
            
        except KeyboardInterrupt:
            self.cli_logger.warning("Operation cancelled by user")
            if not self.quiet:
                print("\nOperation cancelled by user.", file=sys.stderr)
            return 130  # Standard exit code for SIGINT
            
        except Exception as e:
            self.cli_logger.error("CLI execution failed", exception=e)
            if not self.quiet:
                print(f"Error: {str(e)}", file=sys.stderr)
            return 1
    
    def _print_operation_header(self, config: RenameConfig):
        """Print operation header information."""
        operation_type = "PREVIEW" if config.preview_mode else "EXECUTE"
        
        print(f"\n=== BATCH RENAME {operation_type} ===")
        print(f"Input folder: {config.input_folder}")
        print(f"Extractor: {config.extractor}")
        
        if config.converters:
            converter_names = [conv['name'] for conv in config.converters]
            print(f"Converters: {' -> '.join(converter_names)}")
        
        if config.filters:
            filter_summary = []
            for filt in config.filters:
                name = filt['name']
                if filt.get('inverted'):
                    name = f"!{name}"
                filter_summary.append(name)
            print(f"Filters: {', '.join(filter_summary)}")
        
        print(f"Recursive: {'Yes' if config.recursive else 'No'}")
        print()
    
    def _print_operation_results(self, config: RenameConfig, result):
        """Print operation results in CLI-friendly format."""
        
        # Print summary
        print(f"\n=== RESULTS ===")
        print(f"Files analyzed: {result.files_analyzed}")
        
        if config.preview_mode:
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
            
            # Show first few errors in quiet mode
            if self.log_level in ['DEBUG', 'INFO'] and result.error_details:
                print("\nError details:")
                for error in result.error_details[:3]:
                    print(f"  • {error['file']}: {error['error']}")
                
                if len(result.error_details) > 3:
                    print(f"  ... and {len(result.error_details) - 3} more errors")
                    print("  Use --log-level DEBUG for full error details")
        
        # Print preview sample
        if config.preview_mode and result.preview_data:
            self._print_preview_sample(result.preview_data)
    
    def _print_preview_sample(self, preview_data):
        """Print sample of preview changes."""
        
        # Filter to only show actual changes
        changes = [item for item in preview_data if item['old_name'] != item['new_name']]
        
        if not changes:
            print("\nNo filename changes would be made.")
            return
        
        print(f"\nSample changes (showing first {min(5, len(changes))} of {len(changes)}):")
        
        for change in changes[:5]:
            print(f"  {change['old_name']} → {change['new_name']}")
        
        if len(changes) > 5:
            print(f"  ... and {len(changes) - 5} more changes")


def add_logging_arguments(parser):
    """
    Add logging-related arguments to argument parser.
    
    Args:
        parser: argparse.ArgumentParser instance
    """
    
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


def create_cli_processor_from_args(args) -> CLIProcessor:
    """
    Create CLI processor from parsed command line arguments.
    
    Args:
        args: Parsed arguments from argparse
        
    Returns:
        Configured CLIProcessor
    """
    return CLIProcessor(
        log_level=args.log_level,
        log_file=args.log_file,
        enable_colors=not args.no_colors,
        quiet=args.quiet
    )


def execute_with_logging(config: RenameConfig, 
                        log_level: str = 'INFO',
                        log_file: Optional[str] = None,
                        enable_colors: bool = True,
                        quiet: bool = False) -> int:
    """
    Convenience function to execute batch rename with logging from Python code.
    
    Args:
        config: Rename configuration
        log_level: Logging verbosity level
        log_file: Optional log file path
        enable_colors: Enable colored console output
        quiet: Suppress non-essential output
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    cli_processor = CLIProcessor(
        log_level=log_level,
        log_file=log_file,
        enable_colors=enable_colors,
        quiet=quiet
    )
    
    return cli_processor.execute(config)