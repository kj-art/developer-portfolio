from ...handlers import CsvHandler
from typing import Dict, Any

class StreamingReader:
    def __init__(self, read_options:Dict[str, Any] = None):
       self._read_options:Dict[str, Any] = read_options or {}
       self._handler:CsvHandler = CsvHandler()

    def run(self, file_path:str, read_options:Dict[str, Any] = None):
        pass

'''import gc, os
from pathlib import Path
from shared_utils.logger import get_logger, log_performance
from ..processing_config import ProcessingConfig
from ..config import SCHEMA_MAP, ALLOWED_EXTENSIONS
from ..dataframe_utils import normalize_columns, merge_dataframes, ProcessingResult
from ..handlers import get_handler_for_extension
from .file_utils import get_files_iterator, get_source_file_path

class StreamingProcessor:
    def __init__(self, read_options:dict=None, write_options:dict=None):
        self._read_options = read_options or {}
        self._write_options = write_options or {}
        self._logger = get_logger('data_pipeline.streaming')

    def run(self, config: ProcessingConfig) -> ProcessingResult:
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
            csv_handler = get_handler_for_extension('csv')
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
            file_iterator = get_files_iterator(config.input_folder, config.recursive, config.filetype)

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
        
        handler = get_handler_for_extension(extension)
        
        # Merge constructor options with override options
        final_read_options = {**self._read_options, **override_options}
        
        data = handler.read(file_path, **final_read_options)
        
        # Get relative path and remove first directory (input folder)
        data.dataframe['source_file'] = get_source_file_path(abs_path)
        
        return data

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
        
        file_iterator = get_files_iterator(input_folder, recursive, filetype)
        
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
        
        return schema_info'''