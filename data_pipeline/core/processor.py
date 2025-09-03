import os
import gc
from pathlib import Path
import pandas as pd
from . import handlers
from .dataframe_utils import merge_dataframes, normalize_columns, ProcessingResult
from .config import SCHEMA_MAP, ALLOWED_EXTENSIONS
from .processing_config import ProcessingConfig
from .file_utils import get_files_iterator, merge_kwargs
from shared_utils.logger import get_logger, log_performance
import processors.readers as readers
import processors.writers as writers

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

    def run(self, config: ProcessingConfig) -> ProcessingResult:
        output_is_csv = config.output_file and config.output_file.lower().endswith('.csv')
        writer_class = writers.StreamingWriter if output_is_csv else writers.InMemoryWriter 
        read_options = merge_kwargs(self._read_options, config.read_options)
        write_options = merge_kwargs(self._write_options, config.write_options)
        
        file_iterator = get_files_iterator(config.input_folder, config.recursive, config.filetype)
        #return processor_class().run(config)

    def process_folder(self, config):
        """
        Process all files in a folder and return merged DataFrame (in-memory processing)
        
        Args:
            config (ProcessingConfig): Processing configuration object
            
        Returns:
            pandas.DataFrame: Merged DataFrame from all processed files
        """
        with log_performance("in_memory_processing", 
                           input_folder=config.input_folder, 
                           recursive=config.recursive):
            
            self._logger.info("Starting in-memory processing", 
                           input_folder=config.input_folder,
                           recursive=config.recursive,
                           file_types=config.filetype)
            
            schema_map = config.schema_map or SCHEMA_MAP
            dataframes = []
            path = Path(config.input_folder)
            
            files = path.rglob('*') if config.recursive else path.iterdir()
            files_processed = 0
            
            # Merge constructor options with config options
            merged_read_kwargs = {**self._read_options, **config.read_options}
            
            for file_path in files:
                if file_path.is_file():
                    data = self.read_file(str(file_path), config.filetype, **merged_read_kwargs)
                    if not data:
                        continue
                    df = data.dataframe
                    if not data.normalized:
                        df = normalize_columns(df, schema_map, config.to_lower, config.spaces_to_underscores)
                    dataframes.append(df)
                    files_processed += 1

            result = merge_dataframes(dataframes, schema_map, config.to_lower, config.spaces_to_underscores)
            self._logger.info("In-memory processing complete", 
                           files_processed=files_processed, 
                           total_rows=len(result), 
                           columns=len(result.columns))
            return result

    def process_folder_streaming(self, config):
        """
        Stream processing implementation for large datasets
        
        This method processes files one at a time and writes output incrementally,
        maintaining constant memory usage regardless of dataset size.
        
        Args:
            config (ProcessingConfig): Processing configuration object
            
        Returns:
            dict: Processing summary with files_processed, total_rows, output_file
        """
        with log_performance("streaming_processing", 
                           input_folder=config.input_folder,
                           output_file=config.output_file,
                           file_types=config.filetype):
            
            self._logger.info("Starting streaming processing", 
                           input_folder=config.input_folder,
                           output_file=config.output_file)
            
            # Merge constructor defaults with config options
            merged_read_kwargs = {**self._read_options, **config.read_options}
            merged_write_kwargs = {**self._write_options, **config.write_options}
            
            # Get CSV handler to filter both read and write kwargs
            csv_handler = self._get_handler_for_extension('csv')
            filtered_read_kwargs = csv_handler.filter_kwargs(merged_read_kwargs, mode='read')
            filtered_write_kwargs = csv_handler.filter_kwargs(merged_write_kwargs, mode='write')
            
            # Step 1: Detect unified schema across all files
            schema_info = self._determine_schema(
                config.input_folder, config.recursive, config.filetype, config.schema_map, 
                config.to_lower, config.spaces_to_underscores, **filtered_read_kwargs
            )
            
            self._logger.info("Schema detection complete", 
                           columns=len(schema_info['dtypes']),
                           files_sampled=schema_info['files_processed'])
            
            # Step 2: Get file iterator (memory efficient)
            file_iterator = self._get_files_iterator(config.input_folder, config.recursive, config.filetype)
            
            try:
                # Step 3: Handle first file (with headers)
                first_file_path = next(file_iterator)
                self._logger.info("Processing first file", file_name=first_file_path.name)
                
                first_df = self._process_single_file(
                    first_file_path, schema_info, config.schema_map, 
                    config.to_lower, config.spaces_to_underscores, **filtered_read_kwargs
                )
                
                if first_df is not None:
                    first_df.to_csv(config.output_file, index=False, mode='w', **filtered_write_kwargs)
                    total_rows = len(first_df)
                    self._logger.info("First file written", rows=total_rows)
                    del first_df
                else:
                    self._logger.error("Failed to process first file", file_name=first_file_path.name)
                    return None
                    
                # Step 4: Stream remaining files
                files_processed = 1
                
                for file_path in file_iterator:
                    self._logger.info("Processing file", 
                                   file_name=file_path.name, 
                                   file_number=files_processed + 1)
                    
                    df = self._process_single_file(
                        file_path, schema_info, config.schema_map,
                        config.to_lower, config.spaces_to_underscores, **filtered_read_kwargs
                    )
                    
                    if df is not None:
                        df.to_csv(config.output_file, index=False, mode='a', header=False, **filtered_write_kwargs)
                        total_rows += len(df)
                        del df
                        
                    files_processed += 1
                
                self._logger.info("Streaming processing complete", 
                               files_processed=files_processed,
                               total_rows=total_rows,
                               output_file=config.output_file)
                
                return {
                    'files_processed': files_processed,
                    'total_rows': total_rows,
                    'output_file': config.output_file,
                    'schema': schema_info
                }
                
            except StopIteration:
                self._logger.warning("No files found to process", input_folder=config.input_folder)
                return None

    def _get_source_file_path(self, file_path):
        """Extract source file path relative to input folder"""
        rel_path = os.path.relpath(str(file_path))
        path_parts = Path(rel_path).parts
        if len(path_parts) > 1:
            return str(Path(*path_parts[1:]))
        else:
            return path_parts[0]

    def _determine_schema(self, input_folder, recursive=False, filetype=None, 
                         schema_map=None, to_lower=True, spaces_to_underscores=True, 
                         sample_rows=100, **kwargs):
        """
        Determine unified schema across all files by sampling headers and data types
        """
        self._logger.info("Starting schema detection", 
                        input_folder=input_folder, 
                        sample_rows=sample_rows)
        
        schema_map = schema_map or SCHEMA_MAP
        all_columns = set()
        column_dtypes = {}
        files_processed = 0
        
        file_iterator = self._get_files_iterator(input_folder, recursive, filetype)
        
        for file_path in file_iterator:
            try:
                sample_df = self._read_file_sample(file_path, sample_rows, **kwargs)

                # Add source_file column during schema detection
                sample_df['source_file'] = self._get_source_file_path(file_path)

                if sample_df is None or sample_df.empty:
                    continue
                
                normalized_df = normalize_columns(sample_df, schema_map, to_lower, spaces_to_underscores)
                
                file_columns = set(normalized_df.columns)
                all_columns.update(file_columns)
                
                for col in normalized_df.columns:
                    current_dtype = str(normalized_df[col].dtype)
                    existing_dtype = column_dtypes.get(col)
                    unified_dtype = self._merge_dtypes(existing_dtype, current_dtype)
                    column_dtypes[col] = unified_dtype
                
                files_processed += 1
                del sample_df, normalized_df
                
            except Exception as e:
                self._logger.warning("Could not sample file", 
                                  file_name=file_path.name, 
                                  error=str(e))
                continue
        
        gc.collect()
        
        schema_info = {
            'dtypes': column_dtypes,
            'files_processed': files_processed
        }
        
        return schema_info

    '''def _get_files_iterator(self, input_folder, recursive=False, filetype=None):
        """Memory-efficient file iterator that yields valid files one at a time"""
        path = Path(input_folder)
        files = path.rglob('*') if recursive else path.iterdir()
        valid_extensions = self._normalize_filetype(filetype)
        
        for file_path in files:
            if file_path.is_file():
                extension = file_path.suffix.lower()[1:]
                if extension in valid_extensions:
                    yield file_path'''

    def _process_single_file(self, file_path, schema_info, schema_map=None, 
                           to_lower=True, spaces_to_underscores=True, **kwargs):
        """Process a single file using the unified schema"""
        try:
            data = self.read_file(str(file_path), **kwargs)
            if data is None:
                return None
                
            normalized_df = self._normalize_to_schema(
                data.dataframe, 
                schema_info,
                schema_map,
                to_lower,
                spaces_to_underscores
            )
            
            return normalized_df
            
        except Exception as e:
            self._logger.error("Error processing file", 
                            file_name=file_path.name, 
                            error=str(e))
            return None

    def _normalize_to_schema(self, dataframe, schema_info, schema_map=None, 
                           to_lower=True, spaces_to_underscores=True):
        """Normalize a dataframe to match the unified schema"""
        normalized_df = normalize_columns(dataframe, schema_map, to_lower, spaces_to_underscores)
        
        target_dtypes = schema_info['dtypes']
        target_columns = list(target_dtypes.keys())
        
        # Add missing columns
        current_columns = set(normalized_df.columns)
        missing_columns = set(target_columns) - current_columns
        
        for col in missing_columns:
            default_value = self._get_default_value_for_dtype(target_dtypes[col])
            normalized_df[col] = default_value
        
        # Remove extra columns
        extra_columns = current_columns - set(target_columns)
        if extra_columns:
            normalized_df = normalized_df.drop(columns=list(extra_columns))
        
        # Reorder columns to match schema order
        normalized_df = normalized_df.reindex(columns=target_columns)
        
        # Cast data types to match schema
        try:
            for col in target_columns:
                if col in normalized_df.columns:
                    current_dtype = str(normalized_df[col].dtype)
                    target_dtype = target_dtypes[col]
                    
                    if current_dtype != target_dtype:
                        normalized_df[col] = normalized_df[col].astype(target_dtype, errors='ignore')
                        
        except Exception as e:
            self._logger.warning("Type casting failed for some columns", error=str(e))
        
        return normalized_df

    def _read_file_sample(self, file_path, sample_rows, **kwargs):
        """Read a small sample of a file for schema detection"""
        extension = file_path.suffix.lower()[1:]
        handler = self._get_handler_for_extension(extension)
        
        try:
            sample_kwargs = {**self._read_options, **kwargs}
            if extension in ['csv', 'xlsx']:
                sample_kwargs['nrows'] = sample_rows
            
            result = handler.read(str(file_path), **sample_kwargs)
            return result.dataframe
            
        except Exception:
            # Fallback: try reading without nrows
            try:
                result = handler.read(str(file_path), **self._read_options)
                if len(result.dataframe) > sample_rows:
                    return result.dataframe.head(sample_rows)
                return result.dataframe
            except Exception:
                return None

    def _merge_dtypes(self, existing_dtype, new_dtype):
        """Merge two pandas dtypes, choosing the most permissive one"""
        if existing_dtype is None:
            return new_dtype
        
        dtype_hierarchy = ['object', 'float64', 'int64', 'bool', 'datetime64[ns]']
        
        try:
            existing_pos = dtype_hierarchy.index(existing_dtype)
        except ValueError:
            existing_pos = 0
            
        try:
            new_pos = dtype_hierarchy.index(new_dtype)
        except ValueError:
            new_pos = 0
        
        return dtype_hierarchy[min(existing_pos, new_pos)]

    def _get_default_value_for_dtype(self, dtype_str):
        """Get appropriate default value for missing columns based on data type"""
        if 'bool' in dtype_str:
            return False
        return None

    '''def _normalize_filetype(self, filetype=None):
        """Normalize and validate filetype filter input"""
        if filetype is None:
            filetype = ALLOWED_EXTENSIONS
        else:
            if isinstance(filetype, list):
                filetype = [ext.lstrip('.').lower() for ext in filetype]
            elif isinstance(filetype, str):
                filetype = [filetype.lstrip('.').lower()]
            else:
                raise TypeError(f"filetype must be str, list, or None. Got {type(filetype).__name__}: {filetype}")
            unsupported_filters = set(filetype) - set(ALLOWED_EXTENSIONS)
            if unsupported_filters:
                raise ValueError(f"Unsupported file types in filter: {unsupported_filters}. Supported: {ALLOWED_EXTENSIONS}")
        return filetype'''
    
    def _get_handler_for_extension(self, extension):
        """Get handler class for a given extension"""
        handler_class_name = f"{extension.capitalize()}Handler"
        try:
            handler_class = getattr(handlers, handler_class_name)
        except AttributeError:
            raise ValueError(f"Unsupported file format: .{extension}. Supported: {[f'.{ext}' for ext in ALLOWED_EXTENSIONS]}")
        
        return handler_class()

    def read_file(self, file_path, filetype=None, **override_options):
        """
        Read a single file if it matches the filetype filter
        
        Args:
            file_path (str): Path to file to read
            filetype (str|list, optional): File extensions to allow
            **override_options: Options passed to file handlers
        
        Returns:
            FileResult|None: FileResult if file matches filter, None if filtered out
        """
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{abs_path}' does not exist.")

        extension = Path(file_path).suffix.lower()[1:]

        if extension not in self._normalize_filetype(filetype):
            return None
        
        handler = self._get_handler_for_extension(extension)
        
        # Merge constructor options with override options
        final_read_options = {**self._read_options, **override_options}
        
        data = handler.read(file_path, **final_read_options)
        
        # Get relative path and remove first directory (input folder)
        data.dataframe['source_file'] = self._get_source_file_path(abs_path)
        
        return data
    
    def write_file(self, dataframe, output_path, **override_options):
        """
        Save DataFrame to file, determining format from file extension
        
        Args:
            dataframe (pandas.DataFrame): DataFrame to save
            output_path (str): Path to output file
            **override_options: Options passed to file handlers
        """
        abs_path = os.path.abspath(output_path)
        extension = Path(output_path).suffix.lower()[1:]
        
        if not extension:
            raise ValueError(f"Output file must have an extension to determine format: {output_path}")
        
        handler = self._get_handler_for_extension(extension)
        
        # Merge constructor options with override options
        final_write_options = {**self._write_options, **override_options}
        
        # Write the file
        handler.write(dataframe, output_path, **final_write_options)
        self._logger.info("Data saved to file", 
                        output_file=abs_path, 
                        rows=len(dataframe), 
                        columns=len(dataframe.columns))