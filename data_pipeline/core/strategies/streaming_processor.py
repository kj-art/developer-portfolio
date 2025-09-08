"""
Streaming processing strategy for data pipeline operations.

Implements memory-efficient streaming processing by detecting schema upfront,
then processing and writing files chunk-by-chunk without loading entire dataset.
"""

from typing import Optional
import time

from shared_utils.logger import get_logger
from ..services.schema_detector import SchemaDetector
from ..services.file_processor import FileProcessor
from ..services.output_writer import OutputWriter
from ..dataframe_utils import ProcessingResult
from ..processing_config import ProcessingConfig
from ..indexing import IndexManager
from ..handlers import FileHandler


class StreamingProcessor:
    """
    Strategy for memory-efficient streaming data processing.
    
    Optimized for large datasets and CSV output. Detects schema upfront for consistency,
    then processes files chunk-by-chunk, writing output immediately to minimize memory usage.
    """
    
    def __init__(self, schema_detector: SchemaDetector, file_processor: FileProcessor, 
                 output_writer: OutputWriter):
        """
        Initialize streaming processor with required services.
        
        Args:
            schema_detector: Service for detecting unified schema across files
            file_processor: Service for processing file chunks
            output_writer: Service for writing output data
        """
        self.schema_detector = schema_detector
        self.file_processor = file_processor
        self.output_writer = output_writer
        self._logger = get_logger('data_pipeline.streaming_processor')
    
    def process(self, config: ProcessingConfig, writer: Optional[FileHandler]) -> ProcessingResult:
        """
        Execute streaming processing strategy.
        
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
        
        # Process files in streaming mode
        chunk_iterator = self.file_processor.process_files_streaming(
            config, schema, index_manager
        )
        
        # Write chunks as they're produced
        total_rows = self.output_writer.write_streaming(
            chunk_iterator, config.output_file, writer, write_options, index_manager
        )
        
        # Calculate final statistics
        processing_time = time.time() - start_time
        files_processed = self._estimate_files_processed(config)
        
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
    
    def _estimate_files_processed(self, config: ProcessingConfig) -> int:
        """
        Estimate number of files processed (since streaming doesn't track this directly).
        
        This is a limitation of streaming mode - we don't know exactly how many
        files were successfully processed without additional tracking.
        """
        # For now, return a simple count of valid files found
        # In production, you might want to add more sophisticated tracking
        from ..file_utils import get_files_iterator
        
        try:
            return len(list(get_files_iterator(
                config.input_folder, 
                config.recursive, 
                config.file_type_filter
            )))
        except Exception:
            return 0  # Fallback if file counting fails