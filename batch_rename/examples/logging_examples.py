#!/usr/bin/env python3
"""
Example usage of batch rename logging system.

Demonstrates various logging configurations and usage patterns
for different scenarios and environments.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import RenameConfig
from core.logging_processor import LoggingBatchRenameProcessor, create_logging_processor
from core.cli_integration import execute_with_logging
from config.logging_config import LoggingConfig, auto_setup_logging


def example_basic_logging():
    """Basic logging example with default settings."""
    print("=== Basic Logging Example ===")
    
    # Create configuration
    config = RenameConfig(
        input_folder=Path("./test_files"),
        extractor="filename_parts",
        extractor_args={'positional': [], 'keyword': {}},
        converters=[{
            'name': 'format',
            'positional': ['{prefix}_{date}'],
            'keyword': {}
        }],
        preview_mode=True
    )
    
    # Create processor with basic logging
    processor = create_logging_processor(
        log_level='INFO',
        enable_colors=True
    )
    
    # Execute (would fail if test_files doesn't exist, but shows logging setup)
    try:
        result = processor.process(config)
        print(f"Processed {result.files_analyzed} files")
    except Exception as e:
        print(f"Expected error (demo): {e}")


def example_detailed_file_logging():
    """Example with detailed file logging for audit trails."""
    print("\n=== Detailed File Logging Example ===")
    
    # Setup structured logging with separate files
    base_log_file = "./logs/batch_rename_detailed"
    log_files = LoggingConfig.setup_structured_logging(base_log_file)
    
    print("Created separate log files:")
    for log_type, file_path in log_files.items():
        print(f"  {log_type}: {file_path}")
    
    config = RenameConfig(
        input_folder=Path("./documents"),
        extractor="business_metadata",
        extractor_args={'positional': [], 'keyword': {}},
        converters=[{
            'name': 'format',
            'positional': ['{department}_{doc_type}_{date}'],
            'keyword': {}
        }],
        filters=[{
            'name': 'file-type',
            'positional': ['pdf', 'docx'],
            'keyword': {},
            'inverted': False
        }],
        recursive=True,
        preview_mode=False  # Execute mode
    )
    
    # Execute with detailed logging
    exit_code = execute_with_logging(
        config,
        log_level='DEBUG',
        log_file=f"{base_log_file}.log",
        enable_colors=True
    )
    
    print(f"Operation completed with exit code: {exit_code}")


def example_production_logging():
    """Example production logging setup with minimal console output."""
    print("\n=== Production Logging Example ===")
    
    # Setup production environment logging
    log_file = LoggingConfig.get_log_file_path('batch_rename_prod', './prod_logs')
    
    LoggingConfig.setup_for_environment(
        'production',
        log_file=str(log_file)
    )
    
    print(f"Production logging configured to: {log_file}")
    
    # Create processor
    processor = LoggingBatchRenameProcessor()
    
    # Configuration for production batch job
    config = RenameConfig(
        input_folder=Path("./batch_input"),
        extractor="standardize_naming",
        extractor_args={'positional': [], 'keyword': {}},
        converters=[{
            'name': 'format',
            'positional': ['{company_code}_{doc_id}_{version}'],
            'keyword': {}
        }],
        filters=[{
            'name': 'pattern',
            'positional': ['*.pdf'],
            'keyword': {},
            'inverted': False
        }],
        recursive=True,
        preview_mode=False,
        on_existing_collision='skip',
        on_internal_collision='number'
    )
    
    try:
        result = processor.process(config)
        print(f"Production batch: {result.files_renamed} files processed")
    except Exception as e:
        print(f"Production error: {e}")


def example_performance_monitoring():
    """Example with performance monitoring and metrics."""
    print("\n=== Performance Monitoring Example ===")
    
    from shared_utils.logger import log_performance, get_logger
    
    # Setup performance-focused logging
    LoggingConfig.setup_for_environment(
        'development',
        log_file='./logs/performance_test.log'
    )
    
    perf_logger = get_logger('performance_test')
    
    # Simulate performance monitoring
    with log_performance("file_processing_benchmark", perf_logger) as perf:
        print("Simulating file processing...")
        
        # Log processing stats
        import time
        time.sleep(0.1)  # Simulate work
        
        perf_logger.info("Batch processing milestone",
                        files_processed=1000,
                        files_per_second=500,
                        memory_usage_mb=45.2,
                        success_rate=98.5)


def example_error_handling_logging():
    """Example demonstrating error handling and logging."""
    print("\n=== Error Handling Logging Example ===")
    
    # Setup logging with error focus
    LoggingConfig.setup_for_batch_rename(
        log_level='DEBUG',
        log_file='./logs/error_handling_test.log',
        enable_colors=True
    )
    
    # Create configuration that will cause errors
    config = RenameConfig(
        input_folder=Path("./nonexistent_folder"),  # This will cause an error
        extractor="invalid_extractor",  # This will also cause an error
        extractor_args={'positional': [], 'keyword': {}},
        converters=[],
        preview_mode=True
    )
    
    processor = LoggingBatchRenameProcessor()
    
    try:
        result = processor.process(config)
    except Exception as e:
        print(f"Caught expected error: {e}")
        print("Check ./logs/error_handling_test.log for detailed error logging")


def example_cli_integration():
    """Example showing CLI integration with various logging options."""
    print("\n=== CLI Integration Example ===")
    
    # Simulate different CLI scenarios
    cli_scenarios = [
        {
            'name': 'Quick Preview',
            'args': {
                'log_level': 'INFO',
                'log_file': None,
                'enable_colors': True,
                'quiet': False
            }
        },
        {
            'name': 'Detailed Debug',
            'args': {
                'log_level': 'DEBUG', 
                'log_file': './logs/cli_debug.log',
                'enable_colors': True,
                'quiet': False
            }
        },
        {
            'name': 'Silent Batch',
            'args': {
                'log_level': 'ERROR',
                'log_file': './logs/cli_batch.log',
                'enable_colors': False,
                'quiet': True
            }
        }
    ]
    
    for scenario in cli_scenarios:
        print(f"\nCLI Scenario: {scenario['name']}")
        print(f"  Log level: {scenario['args']['log_level']}")
        print(f"  Log file: {scenario['args']['log_file']}")
        print(f"  Colors: {scenario['args']['enable_colors']}")
        print(f"  Quiet: {scenario['args']['quiet']}")


def example_custom_logging_templates():
    """Example showing custom StringSmith logging templates."""
    print("\n=== Custom Logging Templates Example ===")
    
    from shared_utils.logger import set_up_logging
    
    # Custom templates for specific use cases
    custom_console_template = (
        "{{#cyan;[BATCH]}} {{#level_color;[;levelname;]}} "
        "{{message}}{{ - ;operation;}}{{ (;file_count; files)}}"
        "{{ in ;duration;$format_duration}}{{ - ;success_rate;% success}}"
    )
    
    custom_file_template = (
        "{{asctime}} | {{levelname:>8}} | {{name:>20}} | "
        "OP: {{operation}} | FILES: {{file_count}} | "
        "DURATION: {{duration}}s | SUCCESS: {{success_rate}}% | "
        "MSG: {{message}}"
    )
    
    # Setup with custom templates
    set_up_logging(
        level='INFO',
        log_file='./logs/custom_template.log',
        enable_colors=True,
        console_template=custom_console_template,
        file_template=custom_file_template
    )
    
    # Test custom logging
    logger = get_logger('custom_test')
    logger.info("Custom template test",
               operation="batch_rename",
               file_count=150,
               duration=5.2,
               success_rate=96.7)
    
    print("Custom template logging configured")
    print("Check console output and ./logs/custom_template.log")


def main():
    """Run all logging examples."""
    print("Batch Rename Logging System Examples")
    print("=" * 50)
    
    # Create logs directory
    Path('./logs').mkdir(exist_ok=True)
    
    # Run examples
    example_basic_logging()
    example_detailed_file_logging()
    example_production_logging()
    example_performance_monitoring()
    example_error_handling_logging()
    example_cli_integration()
    example_custom_logging_templates()
    
    print("\n" + "=" * 50)
    print("All examples completed!")
    print("Check the ./logs directory for generated log files")


if __name__ == "__main__":
    main()