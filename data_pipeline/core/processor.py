"""
Main data processor with strategy-based architecture.

Orchestrates data processing operations using pluggable strategies and services,
providing a clean separation between processing logic and orchestration concerns.
"""

import time
from typing import Optional

from shared_utils.logger import get_logger, log_performance
from .processing_config import ProcessingConfig
from .dataframe_utils import ProcessingResult
from .file_utils import get_extension, is_streamable_extension, merge_kwargs
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
    Main orchestrator for data processing operations.
    
    Uses strategy pattern to select appropriate processing approach (streaming vs in-memory)
    and dependency injection to coordinate services for modular, testable architecture.
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
        
        # Initialize services (dependency injection)
        self._schema_detector = SchemaDetector()
        self._file_processor = FileProcessor()
        self._output_writer = OutputWriter()
    
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
            
            # Update config with merged options
            config.read_options = merge_kwargs(self._read_options, config.read_options)
            config.write_options = merge_kwargs(self._write_options, config.write_options)
            
            # Execute processing strategy
            return strategy.process(config, writer)
    
    def _set_up_output_handler(self, config: ProcessingConfig) -> tuple[Optional[FileHandler], bool]:
        """
        Set up output handler and determine streaming capabilities.
        
        Args:
            config: Processing configuration
            
        Returns:
            Tuple of (handler, can_stream) where:
            - handler: FileHandler for output (None for console)
            - can_stream: Whether output format supports streaming
        """
        if config.output_file:
            output_ext = get_extension(config.output_file)
            writer = get_handler_for_extension(output_ext)
            can_stream_output = is_streamable_extension(output_ext)
            return writer, can_stream_output
        else:
            # Console output always supports "streaming"
            return None, True
    
    def _should_use_streaming(self, config: ProcessingConfig, can_stream_output: bool) -> bool:
        """
        Determine whether to use streaming processing strategy.
        
        Decision matrix:
        1. If force_in_memory=True → In-memory
        2. If output can't stream → In-memory  
        3. Otherwise → Streaming (default for efficiency)
        
        Args:
            config: Processing configuration
            can_stream_output: Whether output format supports streaming
            
        Returns:
            True if streaming should be used, False for in-memory
        """
        if config.force_in_memory:
            self._logger.info("In-memory processing forced by configuration")
            return False
        
        if not can_stream_output:
            self._logger.info("In-memory processing required for output format", 
                             output_file=config.output_file)
            return False
        
        # Default to streaming for efficiency
        return True
    
    def get_available_strategies(self) -> list[str]:
        """
        Get list of available processing strategies.
        
        Returns:
            List of strategy names for documentation/debugging
        """
        return ["streaming", "in_memory"]
    
    def get_service_status(self) -> dict:
        """
        Get status information about internal services.
        
        Returns:
            Dictionary with service status information for monitoring
        """
        return {
            "schema_detector": "ready",
            "file_processor": "ready", 
            "output_writer": "ready",
            "file_processor_stats": self._file_processor.get_processing_stats()
        }