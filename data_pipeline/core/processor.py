import os
import gc
import time
from pathlib import Path
import pandas as pd
from .dataframe_utils import merge_dataframes, normalize_columns, normalize_chunk, ProcessingResult
from .processing_config import ProcessingConfig, IndexMode
from .file_utils import *
from shared_utils.logger import get_logger, log_performance
from .handlers import FileHandler, get_handler_for_extension
from collections import defaultdict

class DataProcessor:
    def __init__(self, read_kwargs: dict = None, write_kwargs: dict = None):
        """
        Initialize DataProcessor with default file reading and writing options
        
        Args:
            read_kwargs (dict, optional): Default file reading options (e.g. sep=';', encoding='utf-8')
            write_kwargs (dict, optional): Default file writing options (e.g. sep=';', na_rep='NULL')
        """
        self._read_options = read_kwargs or {}
        self._write_options = write_kwargs or {}
        self._logger = get_logger('data_pipeline.processor')
        self._handlers = defaultdict(lambda: None)
    
    def _get_handler_for_extension(self, extension: str) -> FileHandler:
        self._handlers[extension] = self._handlers[extension] or get_handler_for_extension(extension)
        return self._handlers[extension]

    def run(self, config: ProcessingConfig) -> ProcessingResult:
        """
        Process files using appropriate reader/writer strategy based on configuration.
        
        Args:
            config: Processing configuration object
            
        Returns:
            ProcessingResult: Standardized result with processing statistics and data/output info
        """
        with log_performance("data_processing", 
                           input_folder=config.input_folder,
                           output_file=config.output_file):
            
            start_time = time.time()

            read_options = merge_kwargs(self._read_options, config.read_options)
            write_options = merge_kwargs(self._write_options, config.write_options)
            write_options['mode'] = 'w'
            write_options['header'] = True

            if config.output_file:
                output_ext = get_extension(config.output_file)
                writer = self._get_handler_for_extension(output_ext)
                can_stream_output = is_streamable_extension(output_ext)
            else:
                # output to console only
                writer = None
                can_stream_output = True
            
            use_streaming = can_stream_output and not config.force_in_memory

            files_processed, total_rows, total_columns, data = (
                self._run_streaming(config, writer, read_options, write_options)
                if use_streaming
                else self._run_in_memory(config)
            )

            # Finalize and get results
            processing_time = time.time() - start_time
            
            self._logger.info("Processing complete", 
                            files_processed=files_processed,
                            total_rows=total_rows,
                            duration=processing_time)
            
            return ProcessingResult(files_processed,
                                    total_rows,
                                    total_columns,
                                    processing_time,
                                    config.output_file,
                                    config.schema_map,
                                    data)

    def _run_in_memory(self,
                       config: ProcessingConfig,
                       writer: FileHandler = None,
                       read_options: dict = None,
                       write_options: dict = None) -> tuple[int, int, int, pd.DataFrame]:
        files_processed = 0
        total_rows = 0
        
        read_options = read_options or {}
        write_options = write_options or {}

        write_options['index'] = False
        
        all_chunks = []
        current_global_index = config.index_start

        # if config.columns is provided, limit (and expand) columns to those columns only.
        # otherwise, add columns as you find them 
        
        for file_path in get_files_iterator(config.input_folder, config.recursive, config.file_type_filter):
            self._logger.info("Processing file", file_name=file_path.name)
            reader = self._get_handler_for_extension(get_extension(file_path))
            
            try:
                for chunk in reader.read(file_path, **read_options):
                    chunk['source_file'] = get_source_file_path(file_path)
                    chunk = normalize_chunk(chunk, config)

                    # If config.columns is provided, filter columns. Otherwise, add all columns found.
                    if config.columns:
                        chunk = chunk.reindex(columns=config.columns, fill_value=None)
                    
                    # Add manual index column based on mode
                    if config.index_mode == IndexMode.LOCAL:
                        # Each file starts from index_start
                        chunk['__index__'] = range(config.index_start, 
                                                config.index_start + len(chunk))
                    elif config.index_mode == IndexMode.SEQUENTIAL:
                        # Continuous across all files
                        chunk['__index__'] = range(current_global_index, 
                                                current_global_index + len(chunk))
                        current_global_index += len(chunk)
                    
                    all_chunks.append(chunk)
                    total_rows += len(chunk)
                files_processed += 1
            except Exception as e:
                self._logger.error("Failed to process file", 
                                    file_name=file_path.name, 
                                    error=str(e),
                                    exception=e)
                
        # Merge and finalize
        merged_data = pd.concat(all_chunks, ignore_index=True)
        
        # Move manual index to actual index if needed
        if config.index_mode in [IndexMode.LOCAL, IndexMode.SEQUENTIAL]:
            merged_data = merged_data.set_index('__index__')
            merged_data.index.name = None  # Remove the index name
            write_options['index'] = True

        # Output the result
        if writer:
            writer.write(merged_data, config.output_file, **write_options)
            self._logger.info("Data saved to file", 
                            output_file=config.output_file,
                            rows=len(merged_data),
                            columns=len(merged_data.columns))
        else:
            print(merged_data.to_string(index=write_options['index']))

        return files_processed, total_rows, len(merged_data.columns), merged_data

    def _run_streaming(self,
                       config: ProcessingConfig,
                       writer: FileHandler = None,
                       read_options: dict = None,
                       write_options: dict = None) -> tuple[int, int, int, pd.DataFrame]:
        files_processed = 0
        total_rows = 0
        
        read_options = read_options or {}
        write_options = write_options or {}

        needs_reindex = False
        match config.index_mode:
            case IndexMode.NONE:
                write_options['index'] = False
            case IndexMode.LOCAL:
                write_options['index'] = True
                if config.index_start != 0:
                    needs_reindex = True
            case IndexMode.SEQUENTIAL:
                write_options['index'] = True
                needs_reindex = True

        has_unmapped = False
            
        if config.columns:
            column_dtypes = {}
            for col in config.columns:
                mapped_value = (config.schema_map or {}).get(col, None)
                column_dtypes[col] = mapped_value
                if mapped_value is None:
                    has_unmapped = True
        else:
            # if streaming, determine columns now
            column_dtypes, _ = self._determine_columns(config.input_folder,
                                                       config.recursive,
                                                       config.file_type_filter,
                                                       config.schema_map,
                                                       config.to_lower,
                                                       config.spaces_to_underscores,
                                                       **read_options)
            
            column_dtypes['source_file'] = 'object'

        for file_path in get_files_iterator(config.input_folder, config.recursive, config.file_type_filter):
            self._logger.info("Processing file", file_name=file_path.name)
            reader = self._get_handler_for_extension(get_extension(file_path))
            
            try:
                for chunk in reader.read(file_path, **read_options):
                    '''if hasattr(column_dtypes, 'source_file'):
                        column_dtypes['source_file'] = get_source_file_path(file_path)'''
                    if has_unmapped:                        
                        file_columns = self._get_dtypes_from_sample(chunk, config.schema_map, config.to_lower,
                                                                    config.spaces_to_underscores, column_dtypes)
                        if not file_columns:
                            continue
                        has_unmapped = False
                    
                    chunk['source_file'] = get_source_file_path(file_path)
                    
                    chunk:pd.DataFrame = normalize_chunk(chunk, config)
                    chunk = chunk.reindex(columns=column_dtypes.keys(), fill_value=None)

                    if needs_reindex:
                        chunk.reset_index(drop=True, inplace=True)
                        offset = total_rows if config.index_mode == IndexMode.SEQUENTIAL else 0
                        chunk.index = range(offset + config.index_start,
                                            offset + config.index_start + len(chunk))
                    
                    # Send chunk to writer
                    if writer:
                        writer.write(chunk, config.output_file, **write_options)
                        write_options['mode'] = 'a'
                        write_options['header'] = False
                    else:
                        print(chunk.to_string(index=write_options['index']))
                    total_rows += len(chunk)
                    
                files_processed += 1

            except Exception as e:
                self._logger.error("Failed to process file", 
                                    file_name=file_path.name, 
                                    error=str(e),
                                    exception=e)

        return files_processed, total_rows, len(column_dtypes.keys()), None

    def _get_dtypes_from_sample(self, sample_df: pd.DataFrame, schema_map:dict,
                                to_lower:bool, spaces_to_underscores:bool, column_dtypes:dict):        
        normalized_df = normalize_columns(sample_df,
                                          schema_map,
                                          to_lower,
                                          spaces_to_underscores)
        
        file_columns = set(normalized_df.columns)
        
        for col in normalized_df.columns:
            current_dtype = str(normalized_df[col].dtype)
            existing_dtype = column_dtypes.get(col)
            unified_dtype = merge_dtypes(existing_dtype, current_dtype)
            column_dtypes[col] = unified_dtype
        
        del sample_df, normalized_df

        return file_columns

    def _determine_columns(self, input_folder, recursive=False, filetype=None,
                           schema_map:dict=None, to_lower=True, spaces_to_underscores=True,
                           sample_rows=100, **kwargs) -> tuple[dict, int]:
        """
        Determine unified schema across all files by sampling headers and data types
        """
        self._logger.info("Starting schema detection", 
                        input_folder=input_folder, 
                        sample_rows=sample_rows)
        
        all_columns = set()
        column_dtypes = {}
        files_processed = 0
        
        file_iterator = get_files_iterator(input_folder, recursive, filetype)
        
        for file_path in file_iterator:
            try:
                sample_df = self._read_file_sample(file_path, sample_rows, **kwargs)
                
                if sample_df is None or sample_df.empty:
                    return None
                
                file_columns = self._get_dtypes_from_sample(sample_df, schema_map, to_lower,
                                                            spaces_to_underscores, column_dtypes)
                if file_columns:
                    files_processed += 1
            except Exception as e:
                self._logger.warning("Could not sample file", 
                                  file_name=file_path.name, 
                                  error=str(e))
                continue
        
        gc.collect()
        
        return column_dtypes, files_processed

    def _read_file_sample(self, file_path: str, default_sample_rows:int = 100, **kwargs):
        """Read a small sample of a file for schema detection"""
        extension = get_extension(file_path)
        handler = get_handler_for_extension(extension)
        handler_sample_rows = handler.schema_sample_rows
        sample_rows = handler_sample_rows if handler_sample_rows is not None else default_sample_rows
        
        try:
            if handler_sample_rows is not None:  # Handler supports sampling
                kwargs['nrows'] = sample_rows
            return next(handler.read(str(file_path), **kwargs))
        except Exception:
            # Fallback logic can safely reference actual_sample_rows (never None)
            if sample_rows and 'nrows' in kwargs:
                del kwargs['nrows']  # Remove nrows and try again
                return next(handler.read(str(file_path), **kwargs))