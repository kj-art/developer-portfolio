"""
File processing service for data pipeline operations.

Handles the core file reading, chunk processing, and data transformation logic
with proper error handling and logging for production environments.
"""

from typing import Iterator, Dict, List, Optional
from pathlib import Path
import pandas as pd

from shared_utils.logger import get_logger
from ..file_utils import get_files_iterator, get_extension, get_source_file_path
from ..handlers import get_handler_for_extension
from ..dataframe_utils import normalize_chunk
from ..processing_config import ProcessingConfig
from ..indexing import IndexManager


class FileProcessor:
    """
    Service for processing data files with chunk-based operations.
    
    Handles file iteration, chunk reading, normalization, and index management
    in a unified way that works for both streaming and in-memory processing modes.
    """
    
    def __init__(self):
        self._logger = get_logger('data_pipeline.file_processor')
        self._handlers = {}  # Cache handlers for reuse
    
    def process_files_streaming(self, config: ProcessingConfig, schema: Dict[str, str], 
                               index_manager: IndexManager) -> Iterator[pd.DataFrame]:
        """
        Process files in streaming mode, yielding chunks as they're processed.
        
        Args:
            config: Processing configuration
            schema: Expected schema for consistent column structure
            index_manager: Index management for chunk processing
            
        Yields:
            pd.DataFrame: Processed chunks ready for immediate output
        """
        files_processed = 0
        
        for file_path in get_files_iterator(config.input_folder, config.recursive, config.file_type_filter):
            self._logger.info("Processing file", file_name=file_path.name)
            
            try:
                chunks = self._process_single_file(file_path, config, schema, index_manager, 
                                                 is_first_file=(files_processed == 0))
                
                for chunk in chunks:
                    yield chunk
                
                files_processed += 1
                
            except Exception as e:
                self._logger.error("Failed to process file", 
                                 file_name=file_path.name, 
                                 error=str(e),
                                 exception=e)
                continue
    
    def process_files_in_memory(self, config: ProcessingConfig, schema: Optional[Dict[str, str]], 
                               index_manager: IndexManager) -> List[pd.DataFrame]:
        """
        Process all files and return list of chunks for in-memory operations.
        
        Args:
            config: Processing configuration
            schema: Optional schema for column consistency (can be None for in-memory)
            index_manager: Index management for chunk processing
            
        Returns:
            List[pd.DataFrame]: All processed chunks ready for concatenation
        """
        all_chunks = []
        files_processed = 0
        
        for file_path in get_files_iterator(config.input_folder, config.recursive, config.file_type_filter):
            self._logger.info("Processing file", file_name=file_path.name)
            
            try:
                chunks = self._process_single_file(file_path, config, schema, index_manager,
                                                 is_first_file=(files_processed == 0))
                
                all_chunks.extend(chunks)
                files_processed += 1
                
            except Exception as e:
                self._logger.error("Failed to process file", 
                                 file_name=file_path.name, 
                                 error=str(e),
                                 exception=e)
                continue
        
        return all_chunks
    
    def _process_single_file(self, file_path: Path, config: ProcessingConfig, 
                           schema: Optional[Dict[str, str]], index_manager: IndexManager,
                           is_first_file: bool = False) -> List[pd.DataFrame]:
        """
        Process a single file and return its chunks.
        
        Args:
            file_path: Path to file to process
            config: Processing configuration
            schema: Optional schema for column consistency
            index_manager: Index management for chunk processing
            is_first_file: Whether this is the first file being processed
            
        Returns:
            List[pd.DataFrame]: Processed chunks from this file
        """
        extension = get_extension(file_path)
        handler = self._get_handler(extension)
        chunks = []
        is_first_chunk_of_file = True
        
        for chunk in handler.read(str(file_path), **config.read_options):
            # Add source file tracking
            chunk['source_file'] = get_source_file_path(file_path)
            
            # Apply column normalization
            chunk = normalize_chunk(chunk, config)
            
            # Apply schema consistency if provided
            if schema:
                chunk = chunk.reindex(columns=schema.keys(), fill_value=None)
            elif config.columns:
                chunk = chunk.reindex(columns=config.columns, fill_value=None)
            
            # Apply index management
            chunk = index_manager.process_chunk(chunk, is_new_file=is_first_chunk_of_file)
            is_first_chunk_of_file = False
            
            chunks.append(chunk)
        
        return chunks
    
    def _get_handler(self, extension: str):
        """Get cached handler for file extension."""
        if extension not in self._handlers:
            self._handlers[extension] = get_handler_for_extension(extension)
        return self._handlers[extension]
    
    def get_processing_stats(self) -> Dict[str, int]:
        """
        Get statistics about files processed (for monitoring/logging).
        
        Returns:
            Dictionary with processing statistics
        """
        # This could be enhanced to track more detailed stats
        return {
            'handlers_cached': len(self._handlers),
        }