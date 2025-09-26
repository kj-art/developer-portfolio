"""
Schema detection service for data processing pipelines.

Handles schema discovery across multiple files with different formats,
providing unified column detection and type inference for consistent processing.
"""

import gc
from typing import Dict, Optional
from pathlib import Path

from shared_utils.logger import get_logger
from ..file_utils import get_files_iterator, get_extension
from ..handlers import get_handler_for_extension
from ..dataframe_utils import normalize_columns, merge_dtypes
from ..processing_config import ProcessingConfig


class SchemaDetector:
    """
    Service for detecting and managing unified schemas across multiple data files.
    
    Handles the complexity of schema detection by sampling files, normalizing column names,
    and merging data types to create a consistent schema for processing operations.
    """
    
    def __init__(self):
        self._logger = get_logger('data_pipeline.schema_detector')
    
    def detect_schema(self, config: ProcessingConfig, sample_rows: int = 100) -> Dict[str, str]:
        """
        Detect unified schema across all files in the input folder.
        
        Args:
            config: Processing configuration with file paths and normalization settings
            sample_rows: Number of rows to sample from each file for type detection
            
        Returns:
            Dictionary mapping column names to unified data types
            
        Raises:
            ValueError: If no valid files found or schema detection fails
        """
        if config.columns:
            return self._build_schema_from_columns(config.columns, config.schema_map)
        
        return self._detect_schema_from_files(config, sample_rows)
    
    def _build_schema_from_columns(self, columns: list, schema_map: Optional[Dict]) -> Dict[str, str]:
        """Build schema dictionary from predefined columns list."""
        schema = {}
        for col in columns:
            mapped_type = (schema_map or {}).get(col)
            schema[col] = mapped_type or 'object'  # Default to object type
        
        # Always include source_file tracking
        schema['source_file'] = 'object'
        return schema
    
    def _detect_schema_from_files(self, config: ProcessingConfig, sample_rows: int) -> Dict[str, str]:
        """Detect schema by sampling actual files."""
        self._logger.info("Starting schema detection", 
                         input_folder=config.input_folder, 
                         sample_rows=sample_rows)
        
        column_dtypes = {}
        files_processed = 0
        
        file_iterator = get_files_iterator(
            config.input_folder, 
            config.recursive, 
            config.file_type_filter
        )
        
        for file_path in file_iterator:
            try:
                sample_df = self._read_file_sample(file_path, sample_rows, config.read_options)
                
                if sample_df is None or sample_df.empty:
                    continue
                
                file_schema = self._extract_file_schema(sample_df, config)
                self._merge_schema(column_dtypes, file_schema)
                files_processed += 1
                
            except Exception as e:
                self._logger.warning("Could not sample file", 
                                   file_name=file_path.name, 
                                   error=str(e))
                continue
        
        if not column_dtypes:
            raise ValueError(f"No valid files found for schema detection in {config.input_folder}")
        
        # Add source file tracking
        column_dtypes['source_file'] = 'object'
        
        # Clean up memory after schema detection
        gc.collect()
        
        self._logger.info("Schema detection complete", 
                         columns_detected=len(column_dtypes),
                         files_sampled=files_processed)
        
        return column_dtypes
    
    def _read_file_sample(self, file_path: Path, sample_rows: int, read_options: dict):
        """Read a small sample of a file for schema detection."""
        extension = get_extension(file_path)
        handler = get_handler_for_extension(extension)
        handler_sample_rows = handler.schema_sample_rows
        actual_sample_rows = handler_sample_rows if handler_sample_rows is not None else sample_rows
        
        # Create read options for sampling
        sampling_options = read_options.copy()
        if handler_sample_rows is not None:
            sampling_options['nrows'] = actual_sample_rows
        
        try:
            return next(handler.read(str(file_path), **sampling_options))
        except Exception:
            # Fallback: try without nrows parameter
            if 'nrows' in sampling_options:
                del sampling_options['nrows']
                return next(handler.read(str(file_path), **sampling_options))
            raise
    
    def _extract_file_schema(self, sample_df, config: ProcessingConfig) -> Dict[str, str]:
        """Extract schema information from a sample DataFrame."""
        normalized_df = normalize_columns(
            sample_df,
            config.schema_map,
            config.to_lower,
            config.spaces_to_underscores
        )
        
        # Extract column types
        file_schema = {}
        for col in normalized_df.columns:
            file_schema[col] = str(normalized_df[col].dtype)
        
        return file_schema
    
    def _merge_schema(self, main_schema: Dict[str, str], file_schema: Dict[str, str]) -> None:
        """Merge file schema into main schema with type unification."""
        for col, dtype in file_schema.items():
            existing_dtype = main_schema.get(col)
            unified_dtype = merge_dtypes(existing_dtype, dtype)
            main_schema[col] = unified_dtype