"""
Output writing service for data pipeline operations.

Handles writing processed data to files or console with proper formatting,
streaming support, and write option management.
"""

from typing import Optional, Iterator
import pandas as pd

from shared_utils.logger import get_logger
from ..handlers import FileHandler
from ..indexing import IndexManager


class OutputWriter:
    """
    Service for writing processed data to various output destinations.
    
    Supports both streaming (chunk-by-chunk) and batch (complete dataset) writing
    with proper file handling and console output formatting.
    """
    
    def __init__(self):
        self._logger = get_logger('data_pipeline.output_writer')
        self._is_first_write = True
    
    def write_streaming(self, chunks: Iterator[pd.DataFrame], output_file: Optional[str], 
                       writer: Optional[FileHandler], write_options: dict,
                       index_manager: IndexManager) -> int:
        """
        Write chunks in streaming mode as they're produced.
        
        Args:
            chunks: Iterator of DataFrame chunks to write
            output_file: Path to output file (None for console output)
            writer: File handler for writing (None for console output)
            write_options: Write options for pandas output functions
            index_manager: Index manager for finalizing chunks
            
        Returns:
            int: Total number of rows written
        """
        total_rows = 0
        current_write_options = write_options.copy()
        
        # Set up initial write mode for streaming
        current_write_options['mode'] = 'w'
        current_write_options['header'] = True
        
        for chunk in chunks:
            # Finalize chunk index for output
            chunk = index_manager.finalize_streaming_chunk(chunk)
            
            if writer and output_file:
                self._write_chunk_to_file(chunk, output_file, writer, current_write_options)
                
                # Switch to append mode after first write
                current_write_options['mode'] = 'a'
                current_write_options['header'] = False
            else:
                self._write_chunk_to_console(chunk, current_write_options)
            
            total_rows += len(chunk)
        
        if writer and output_file:
            self._logger.info("Streaming output complete", 
                             output_file=output_file, 
                             total_rows=total_rows)
        
        return total_rows
    
    def write_complete_dataset(self, dataset: pd.DataFrame, output_file: Optional[str],
                              writer: Optional[FileHandler], write_options: dict,
                              index_manager: IndexManager) -> int:
        """
        Write complete dataset in batch mode.
        
        Args:
            dataset: Complete DataFrame to write
            output_file: Path to output file (None for console output)
            writer: File handler for writing (None for console output)
            write_options: Write options for pandas output functions
            index_manager: Index manager for finalizing dataset
            
        Returns:
            int: Number of rows written
        """
        if dataset.empty:
            self._logger.warning("No data to write - empty dataset")
            return 0
        
        # Finalize dataset index
        final_dataset = index_manager.finalize_in_memory_index(dataset)
        
        if writer and output_file:
            self._write_dataset_to_file(final_dataset, output_file, writer, write_options)
            self._logger.info("Batch output complete",
                             output_file=output_file,
                             rows=len(final_dataset),
                             columns=len(final_dataset.columns))
        else:
            self._write_dataset_to_console(final_dataset, write_options)
        
        return len(final_dataset)
    
    def _write_chunk_to_file(self, chunk: pd.DataFrame, output_file: str, 
                            writer: FileHandler, write_options: dict) -> None:
        """Write a single chunk to file."""
        try:
            writer.write(chunk, output_file, **write_options)
        except Exception as e:
            self._logger.error("Failed to write chunk to file",
                             output_file=output_file,
                             chunk_rows=len(chunk),
                             error=str(e),
                             exception=e)
            raise
    
    def _write_dataset_to_file(self, dataset: pd.DataFrame, output_file: str,
                              writer: FileHandler, write_options: dict) -> None:
        """Write complete dataset to file."""
        try:
            writer.write(dataset, output_file, **write_options)
        except Exception as e:
            self._logger.error("Failed to write dataset to file",
                             output_file=output_file,
                             dataset_rows=len(dataset),
                             error=str(e),
                             exception=e)
            raise
    
    def _write_chunk_to_console(self, chunk: pd.DataFrame, write_options: dict) -> None:
        """Write chunk to console with proper formatting."""
        include_index = write_options.get('index', False)
        print(chunk.to_string(index=include_index))
    
    def _write_dataset_to_console(self, dataset: pd.DataFrame, write_options: dict) -> None:
        """Write complete dataset to console with proper formatting."""
        include_index = write_options.get('index', False)
        print(dataset.to_string(index=include_index))
    
    def reset_write_state(self) -> None:
        """Reset write state for processing a new batch of files."""
        self._is_first_write = True