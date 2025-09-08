"""
Index management for data processing pipelines.

Provides unified index handling for both streaming and in-memory processing modes,
eliminating code duplication and ensuring consistent behavior across processing strategies.
"""

import pandas as pd
from typing import Tuple, Optional
from .processing_config import IndexMode


class IndexManager:
    """
    Unified index management for data processing operations.
    
    Handles index assignment and tracking across different processing modes
    (streaming vs in-memory) and index strategies (none, local, sequential).
    
    Design Philosophy:
    - Single responsibility: index logic only
    - Mode-agnostic: works with both streaming and in-memory processing
    - Stateful tracking: maintains global index position across chunks
    - Performance-aware: minimal overhead for common operations
    """
    
    def __init__(self, mode: Optional[IndexMode], start_value: int = 0):
        """
        Initialize index manager with specified mode and starting value.
        
        Args:
            mode: Index handling strategy (NONE, LOCAL, SEQUENTIAL, or None)
            start_value: Starting number for index values (default: 0)
        """
        self.mode = mode
        self.start_value = start_value
        self.global_index_position = start_value
        self.current_file_position = start_value
        self.file_count = 0
    
    def process_chunk(self, chunk: pd.DataFrame, is_new_file: bool = False) -> pd.DataFrame:
        """
        Apply index strategy to a data chunk.
        
        Args:
            chunk: DataFrame chunk to process
            is_new_file: Whether this chunk starts a new file (affects LOCAL mode)
            
        Returns:
            DataFrame with appropriate index applied (may have __index__ column for temp tracking)
        """
        if self.mode is None or self.mode == IndexMode.NONE:
            return chunk
        
        chunk = chunk.copy()  # Avoid modifying original
        
        if is_new_file:
            self.file_count += 1
            if self.mode == IndexMode.LOCAL:
                self.current_file_position = self.start_value
        
        if self.mode == IndexMode.LOCAL:
            chunk_start = self.current_file_position
            self.current_file_position += len(chunk)
                
        elif self.mode == IndexMode.SEQUENTIAL:
            chunk_start = self.global_index_position
            self.global_index_position += len(chunk)
        else:
            # Shouldn't reach here, but safe fallback
            chunk_start = 0
        
        # Add temporary index column for tracking
        chunk['__index__'] = range(chunk_start, chunk_start + len(chunk))
        
        return chunk
    
    def finalize_in_memory_index(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Convert temporary index column to actual DataFrame index for in-memory processing.
        
        Args:
            dataframe: Complete DataFrame with __index__ column
            
        Returns:
            DataFrame with proper index set
        """
        if self.mode is None or self.mode == IndexMode.NONE:
            return dataframe
            
        if '__index__' not in dataframe.columns:
            raise ValueError("DataFrame missing __index__ column. Call process_chunk() first.")
        
        # Convert temporary column to actual index
        result = dataframe.set_index('__index__')
        result.index.name = None  # Remove the index name for cleaner output
        
        return result
    
    def finalize_streaming_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare chunk for streaming output by converting temp index to real index.
        
        Args:
            chunk: DataFrame chunk with __index__ column
            
        Returns:
            DataFrame ready for streaming output
        """
        if self.mode is None or self.mode == IndexMode.NONE:
            return chunk
            
        if '__index__' not in chunk.columns:
            raise ValueError("Chunk missing __index__ column. Call process_chunk() first.")
        
        # For streaming, we set the index directly on each chunk
        chunk = chunk.set_index('__index__')
        chunk.index.name = None
        
        return chunk
    
    def apply_write_options(self, write_options: dict) -> dict:
        """
        Apply index settings to write options with IndexMode taking precedence.
        
        When both --index-mode and --index are specified, IndexMode wins.
        This provides a clear hierarchy: high-level config > low-level pandas args.
        
        Args:
            write_options: Current write options dictionary
            
        Returns:
            Updated write options with IndexMode applied
        """
        updated_options = write_options.copy()
        
        if self.mode is not None:
            # IndexMode overrides any existing index setting
            updated_options['index'] = self.mode != IndexMode.NONE
        
        return updated_options
    
    def should_include_index(self) -> bool:
        """
        Determine if index should be included in output.
        
        Returns:
            True if index should be written to output files
        """
        return self.mode is not None and self.mode != IndexMode.NONE
    
    def reset_file_tracking(self):
        """Reset file-level tracking (useful for processing multiple batches)"""
        self.file_count = 0
        self.global_index_position = self.start_value
        self.current_file_position = self.start_value