# data_pipeline/core/processor.py
"""
Main data processor with strategy-based architecture and progress reporting.

Orchestrates data processing operations using pluggable strategies and services,
providing a clean separation between processing logic and orchestration concerns.
Enhanced with progress reporting capabilities for CLI and GUI integration.
"""

import time
from typing import Optional

from shared_utils.logger import get_logger, log_performance
from shared_utils.progress import BaseProgressReporter, NullProgressReporter
from .processing_config import ProcessingConfig
from .dataframe_utils import ProcessingResult
from .file_utils import get_extension, is_streamable_extension, merge_kwargs, get_files_iterator
from .indexing import IndexManager
from .handlers import get_handler_for_extension, FileHandler

# Import services
from .services.schema_detector import SchemaDetector
from .services.file_processor import FileProcessor
from .services.output_writer import OutputWriter

# Import strategies
from .strategies.streaming_processor import StreamingProcessor
from .strategies.in_memory_processor import InMemoryProcessor


class DataProcessor:
    """
    Main orchestrator for data processing operations with progress tracking.
    
    Uses strategy pattern to select appropriate processing approach (streaming vs in-memory)
    and dependency injection to coordinate services for modular, testable architecture.
    Supports progress reporting for CLI and GUI interfaces.
    """
    
    def __init__(self, read_kwargs: dict = None, write_kwargs: dict = None):
        """
        Initialize DataProcessor with default file operation options.
        
        Args:
            read_kwargs: Default file reading options (e.g. sep=';', encoding='utf-8')
            write_kwargs: Default file writing options (e.g. sep=';', na_rep='NULL')
        """
        self._read_options = read_kwargs or {}
        self._write_options = write_kwargs or {}
        self._logger = get_logger('data_pipeline.processor')
        self._progress_reporter = NullProgressReporter()
        
        # Initialize services (dependency injection)
        self._schema_detector = SchemaDetector()
        self._file_processor = FileProcessor()
        self._output_writer = OutputWriter()
    
    def set_progress_reporter(self, progress_reporter: BaseProgressReporter):
        """Set progress reporter for tracking processing status"""
        self._progress_reporter = progress_reporter
    
    def run(self, config: ProcessingConfig) -> ProcessingResult:
        """
        Process files using appropriate strategy based on configuration.
        
        Automatically selects streaming vs in-memory processing based on:
        - Output file format (CSV enables streaming)
        - Configuration flags (force_in_memory overrides)
        - Dataset size considerations
        
        Args:
            config: Processing configuration object
            
        Returns:
            ProcessingResult: Standardized result with processing statistics
        """
        with log_performance("data_processing", 
                           input_folder=config.input_folder,
                           output_file=config.output_file):
            
            # Count files for progress tracking
            files = list(get_files_iterator(
                config.input_folder, 
                config.recursive, 
                config.file_type_filter
            ))
            self._progress_reporter.start_processing(len(files))
            
            # Determine output handler and capabilities
            writer, can_stream_output = self._set_up_output_handler(config)
            
            # Select processing strategy
            use_streaming = self._should_use_streaming(config, can_stream_output)
            
            strategy = (StreamingProcessor
                        if use_streaming
                        else InMemoryProcessor)(
                            self._schema_detector,
                            self._file_processor,
                            self._output_writer
                            )
            
            # Inject progress reporter into strategy
            if hasattr(strategy, 'set_progress_reporter'):
                strategy.set_progress_reporter(self._progress_reporter)
            
            # Update config with merged options
            config.read_options = merge_kwargs(self._read_options, config.read_options)
            config.write_options = merge_kwargs(self._write_options, config.write_options)
            
            # Execute processing strategy
            result = strategy.process(config, writer)
            
            # Complete progress tracking
            self._progress_reporter.complete_processing(
                result.total_rows, 
                result.processing_time
            )
            
            return result
    
    def _set_up_output_handler(self, config: ProcessingConfig) -> tuple[Optional[FileHandler], bool]:
        """
        Set up output handler and determine streaming capabilities.
        
        Returns:
            Tuple of (output_handler, can_stream_output)
            - output_handler: File handler for writing (None for console output)
            - can_stream_output: Boolean indicating if streaming output is supported
        """
        if not config.output_file:
            return None, False
        
        extension = get_extension(config.output_file)
        can_stream = is_streamable_extension(extension)
        
        handler = get_handler_for_extension(extension)
        if not handler:
            self._logger.warning("Unknown output format, defaulting to CSV", 
                               extension=extension)
            handler = get_handler_for_extension('.csv')
        
        return handler, can_stream
    
    def _should_use_streaming(self, config: ProcessingConfig, can_stream_output: bool) -> bool:
        """
        Determine whether to use streaming or in-memory processing.
        
        Streaming is preferred for:
        - Large datasets (to maintain constant memory usage)
        - CSV output (which supports incremental writing)
        - Production environments (better resource utilization)
        
        In-memory is preferred for:
        - Small datasets (faster processing)
        - Complex output formats that require full dataset (Excel, JSON)
        - Explicit user configuration (force_in_memory=True)
        """
        if config.force_in_memory:
            self._logger.info("Using in-memory processing (forced by configuration)")
            return False
        
        if not can_stream_output:
            self._logger.info("Using in-memory processing (output format requires full dataset)")
            return False
        
        # Default to streaming for better memory efficiency
        self._logger.info("Using streaming processing (efficient for large datasets)")
        return True
    
    def get_available_strategies(self) -> list[str]:
        """Get list of available processing strategies for debugging/testing"""
        return ['streaming', 'in_memory']
    
    def get_service_status(self) -> dict:
        """Get status information about internal services for debugging"""
        return {
            'schema_detector': type(self._schema_detector).__name__,
            'file_processor': type(self._file_processor).__name__,
            'output_writer': type(self._output_writer).__name__,
            'read_options': list(self._read_options.keys()),
            'write_options': list(self._write_options.keys()),
            'progress_reporter': type(self._progress_reporter).__name__
        }