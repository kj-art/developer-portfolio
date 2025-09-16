# data_pipeline/core/strategies/streaming_processor.py
"""
Streaming data processing strategy with progress reporting.

Processes files one chunk at a time to maintain constant memory usage,
ideal for large datasets. Enhanced with detailed progress tracking
for CLI and GUI integration.
"""

import time
from typing import Optional

from shared_utils.logger import get_logger
from shared_utils.progress import BaseProgressReporter, NullProgressReporter
from ..handlers import FileHandler
from ..processing_config import ProcessingConfig
from ..dataframe_utils import ProcessingResult
from ..indexing import IndexManager
from ..file_utils import get_files_iterator


class StreamingProcessor:
    """
    Strategy for processing files in streaming mode with progress tracking.
    
    Maintains constant memory usage by processing files in chunks and writing
    output incrementally. Provides detailed progress reporting for user feedback.
    """
    
    def __init__(self, schema_detector, file_processor, output_writer):
        """
        Initialize streaming processor with injected services.
        
        Args:
            schema_detector: Service for detecting and normalizing schemas
            file_processor: Service for reading and processing individual files
            output_writer: Service for writing processed data
        """
        self.schema_detector = schema_detector
        self.file_processor = file_processor
        self.output_writer = output_writer
        self._logger = get_logger('data_pipeline.streaming')
        self._progress_reporter = NullProgressReporter()
    
    def set_progress_reporter(self, progress_reporter: BaseProgressReporter):
        """Set progress reporter for tracking processing status"""
        self._progress_reporter = progress_reporter
    
    def process(self, config: ProcessingConfig, writer: Optional[FileHandler] = None) -> ProcessingResult:
        """
        Process files using streaming strategy with detailed progress reporting.
        
        Args:
            config: Processing configuration
            writer: Optional file handler for output (None for console)
            
        Returns:
            ProcessingResult: Processing statistics and metadata
        """
        start_time = time.time()
        
        # Initialize index management
        index_manager = IndexManager(config.index_mode, config.index_start)
        write_options = index_manager.apply_write_options(config.write_options)
        
        # Detect schema upfront for streaming consistency
        self._logger.info("Detecting schema for streaming consistency")
        schema = self.schema_detector.detect_schema(config)
        
        self._logger.info("Starting streaming processing", 
                         schema_columns=len(schema))
        
        # Get files iterator for progress tracking
        files = list(get_files_iterator(
            config.input_folder, 
            config.recursive, 
            config.file_type_filter
        ))
        
        # Process files with enhanced progress tracking
        chunk_iterator = self._process_files_with_progress(
            files, config, schema, index_manager
        )
        
        # Write chunks as they're produced
        total_rows = self.output_writer.write_streaming(
            chunk_iterator, config.output_file, writer, write_options, index_manager
        )
        
        # Calculate final statistics
        processing_time = time.time() - start_time
        files_processed = len(files)
        
        self._logger.info("Streaming processing complete",
                         files_processed=files_processed,
                         total_rows=total_rows,
                         duration=processing_time)
        
        return ProcessingResult(
            files_processed=files_processed,
            total_rows=total_rows,
            total_columns=len(schema),
            processing_time=processing_time,
            output_file=config.output_file,
            schema=schema,
            data=None  # No data retained in streaming mode
        )
    
    def _process_files_with_progress(self, files, config, schema, index_manager):
        """
        Process files with detailed progress reporting.
        
        Yields processed chunks while reporting progress for each file
        and row processing within files.
        """
        for file_path in files:
            # Report file start
            file_name = file_path.name
            self._progress_reporter.start_file(file_name)
            
            try:
                # Process file in chunks
                file_chunks = self.file_processor.process_file_streaming(
                    file_path, config, schema, index_manager
                )
                
                file_row_count = 0
                chunk_count = 0
                
                for chunk in file_chunks:
                    chunk_size = len(chunk)
                    file_row_count += chunk_size
                    chunk_count += 1
                    
                    # Report progress within file
                    if chunk_count % 10 == 0:  # Report every 10 chunks to avoid spam
                        self._progress_reporter.update_rows(chunk_size * 10)
                    
                    yield chunk
                
                # Report any remaining rows
                if chunk_count % 10 != 0:
                    remaining_chunks = chunk_count % 10
                    self._progress_reporter.update_rows(
                        file_row_count - ((chunk_count // 10) * 10 * len(chunk))
                    )
                
                # Report file completion
                self._progress_reporter.complete_file(file_row_count)
                
                self._logger.debug("File processed successfully",
                                 file=file_name,
                                 rows=file_row_count,
                                 chunks=chunk_count)
                
            except Exception as e:
                self._logger.error("Failed to process file",
                                 file=file_name,
                                 error=str(e))
                # Continue with other files instead of failing completely
                continue