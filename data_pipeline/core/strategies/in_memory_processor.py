"""
In-memory processing strategy for data pipeline operations.

Implements full-dataset processing by loading all data into memory, enabling
complex operations and transformations that require access to the complete dataset.
"""

from typing import Optional
import time
import pandas as pd

from shared_utils.logger import get_logger
from ..services.schema_detector import SchemaDetector
from ..services.file_processor import FileProcessor
from ..services.output_writer import OutputWriter
from ..dataframe_utils import ProcessingResult
from ..processing_config import ProcessingConfig
from ..indexing import IndexManager
from ..handlers import FileHandler


class InMemoryProcessor:
    """
    Strategy for in-memory data processing with full dataset access.
    
    Loads all data into memory, applies transformations, then outputs complete dataset.
    Suitable for smaller datasets or when complex operations require full dataset access.
    """
    
    def __init__(self, schema_detector: SchemaDetector, file_processor: FileProcessor, 
                 output_writer: OutputWriter):
        """
        Initialize in-memory processor with required services.
        
        Args:
            schema_detector: Service for detecting unified schema across files
            file_processor: Service for processing file chunks
            output_writer: Service for writing output data
        """
        self.schema_detector = schema_detector
        self.file_processor = file_processor
        self.output_writer = output_writer
        self._logger = get_logger('data_pipeline.in_memory_processor')
    
    def process(self, config: ProcessingConfig, writer: Optional[FileHandler]) -> ProcessingResult:
        """
        Execute in-memory processing strategy.
        
        Args:
            config: Processing configuration
            writer: Optional file handler for output (None for console)
            
        Returns:
            ProcessingResult: Processing statistics and complete dataset
        """
        start_time = time.time()
        
        # Initialize index management
        index_manager = IndexManager(config.index_mode, config.index_start)
        write_options = index_manager.apply_write_options(config.write_options)
        
        # For in-memory processing, schema detection is optional
        # (we can infer schema as we go since we have full dataset)
        schema = None
        if config.columns:
            self._logger.info("Using predefined schema for in-memory processing")
            schema = self.schema_detector.detect_schema(config)
        
        self._logger.info("Starting in-memory processing")
        
        # Load all chunks into memory
        all_chunks = self.file_processor.process_files_in_memory(
            config, schema, index_manager
        )
        
        if not all_chunks:
            self._logger.warning("No data chunks processed")
            return self._create_empty_result(start_time, config)
        
        # Merge all chunks into single dataset
        self._logger.info("Merging chunks into complete dataset", 
                         chunk_count=len(all_chunks))
        merged_dataset = pd.concat(all_chunks, ignore_index=True)
        
        # Write complete dataset
        total_rows = self.output_writer.write_complete_dataset(
            merged_dataset, config.output_file, writer, write_options, index_manager
        )
        
        # Calculate final statistics
        processing_time = time.time() - start_time
        files_processed = self._count_unique_source_files(merged_dataset)
        
        self._logger.info("In-memory processing complete",
                         files_processed=files_processed,
                         total_rows=total_rows,
                         total_columns=len(merged_dataset.columns),
                         duration=processing_time)
        
        return ProcessingResult(
            files_processed=files_processed,
            total_rows=total_rows,
            total_columns=len(merged_dataset.columns),
            processing_time=processing_time,
            output_file=config.output_file,
            schema=schema,
            data=merged_dataset  # Full dataset available in in-memory mode
        )
    
    def _count_unique_source_files(self, dataset: pd.DataFrame) -> int:
        """Count number of unique source files in the merged dataset."""
        if 'source_file' in dataset.columns:
            return dataset['source_file'].nunique()
        return 0  # Fallback if no source tracking
    
    def _create_empty_result(self, start_time: float, config: ProcessingConfig) -> ProcessingResult:
        """Create result object for empty processing run."""
        processing_time = time.time() - start_time
        
        return ProcessingResult(
            files_processed=0,
            total_rows=0,
            total_columns=0,
            processing_time=processing_time,
            output_file=config.output_file,
            schema=None,
            data=pd.DataFrame()  # Empty DataFrame
        )