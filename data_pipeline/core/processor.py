import os
import gc
from pathlib import Path
import pandas as pd
from . import handlers
from .utils import merge_dataframes, normalize_columns
from .config import SCHEMA_MAP, ALLOWED_EXTENSIONS

# Import the ProcessingConfig class
try:
    from .processing_config import ProcessingConfig
except ImportError:
    # Fallback if not using the config class yet
    ProcessingConfig = None

class DataProcessor:
    def __init__(self, read_kwargs=None, write_kwargs=None):
        """
        Initialize DataProcessor with default file reading and writing options
        
        Args:
            read_kwargs (dict, optional): Default file reading options (e.g. sep=';', encoding='utf-8')
            write_kwargs (dict, optional): Default file writing options (e.g. sep=';', na_rep='NULL')
        
        Example:
            processor = DataProcessor(
                read_kwargs={'sep': ';', 'encoding': 'latin-1'}, 
                write_kwargs={'sep': ';', 'na_rep': 'NULL'}
            )
        """
        self.read_options = read_kwargs or {}
        self.write_options = write_kwargs or {}

    def process_folder(self, input_folder, recursive=False, filetype=None, schema_map=None, to_lower=True, spaces_to_underscores=True, **kwargs):
        """
        Process all files in a folder and return merged DataFrame (legacy method)
        
        This is the original in-memory processing method. For large datasets,
        use process_folder_streaming() instead.
        
        Args:
            input_folder (str): Path to folder containing files to process
            recursive (bool, optional): If True, search subdirectories recursively. 
                                      Defaults to False.
            filetype (str|list, optional): File extensions to process. 
                                                Can be single string or list of strings.
                                                Defaults to all supported types.
            schema_map (dict, optional): Column name mapping for normalization.
                                      Maps standard names to list of alternatives.
                                      If None, uses default SCHEMA_MAP from config.
            **kwargs: Additional options passed to file handlers
        
        Returns:
            pandas.DataFrame: Merged DataFrame from all processed files
        """
        
        schema_map = schema_map or SCHEMA_MAP
        dataframes = []
        path = Path(input_folder)
        
        if recursive:
            files = path.rglob('*')  # Recursive: all files in subdirectories
        else:
            files = path.iterdir()   # Non-recursive: direct children only
        
        for file_path in files:
            if file_path.is_file():  # Skip directories
                data = self.read_file(str(file_path), filetype, **self.read_options)
                if not data:
                    continue
                df = data.dataframe
                if not data.normalized:
                    df = normalize_columns(df, schema_map, to_lower, spaces_to_underscores)
                dataframes.append(df)

        return merge_dataframes(dataframes, schema_map, to_lower, spaces_to_underscores)

    def process_folder_streaming(self, config_or_input_folder, output_file=None, read_kwargs=None, write_kwargs=None, 
                               recursive=False, filetype=None, schema_map=None, to_lower=True, spaces_to_underscores=True, **kwargs):
        """
        Stream processing implementation for large datasets
        
        This method processes files one at a time and writes output incrementally,
        maintaining constant memory usage regardless of dataset size.
        
        Args:
            config_or_input_folder: Either ProcessingConfig object or input folder string (legacy)
            output_file (str): Path to output file (legacy, ignored if config provided)
            read_kwargs (dict): Read-specific kwargs (legacy, ignored if config provided)
            write_kwargs (dict): Write-specific kwargs (legacy, ignored if config provided)
            **kwargs: Additional legacy options (ignored if config provided)
            
        Returns:
            dict: Processing summary with files_processed, total_rows, output_file
            
        Examples:
            # New config-based usage (recommended):
            config = ProcessingConfig(input_folder='data', output_file='output.csv')
            summary = processor.process_folder_streaming(config)
            
            # Legacy usage (still supported):
            summary = processor.process_folder_streaming('data', 'output.csv')
        """
        # Handle both config object and legacy parameter usage
        if ProcessingConfig and isinstance(config_or_input_folder, ProcessingConfig):
            config = config_or_input_folder
        else:
            # Legacy usage - create config from individual parameters
            if ProcessingConfig:
                config = ProcessingConfig(
                    input_folder=config_or_input_folder,
                    output_file=output_file,
                    recursive=recursive,
                    filetype=filetype,
                    schema_map=schema_map,
                    to_lower=to_lower,
                    spaces_to_underscores=spaces_to_underscores,
                    read_options=read_kwargs or {},
                    write_options=write_kwargs or {}
                )
            else:
                # Fallback if ProcessingConfig not available
                return self._process_folder_streaming_legacy(
                    config_or_input_folder, output_file, read_kwargs, write_kwargs,
                    recursive, filetype, schema_map, to_lower, spaces_to_underscores, **kwargs
                )
        
        print("🔄 Starting streaming processing...")
        
        # Merge constructor defaults with config options
        merged_read_kwargs = {**self.read_options, **config.read_options}
        merged_write_kwargs = {**self.write_options, **config.write_options}
        
        # Get CSV handler to filter both read and write kwargs
        csv_handler = self._get_handler_for_extension('csv')
        filtered_read_kwargs = csv_handler.filter_kwargs(merged_read_kwargs, mode='read')
        filtered_write_kwargs = csv_handler.filter_kwargs(merged_write_kwargs, mode='write')
        
        # Step 1: Detect unified schema across all files (using filtered read options)
        schema_info = self._determine_schema(
            config.input_folder, config.recursive, config.filetype, config.schema_map, 
            config.to_lower, config.spaces_to_underscores, **filtered_read_kwargs
        )
        print(f"📋 Target schema: {list(schema_info['dtypes'].keys())}")
        
        # Step 2: Get file iterator (memory efficient)
        file_iterator = self._get_files_iterator(config.input_folder, config.recursive, config.filetype)
        
        try:
            # Step 3: Handle first file (with headers)
            first_file_path = next(file_iterator)
            print(f"📄 Processing first file: {first_file_path.name}")
            
            first_df = self._process_single_file(
                first_file_path, schema_info, config.schema_map, 
                config.to_lower, config.spaces_to_underscores, **filtered_read_kwargs
            )
            
            if first_df is not None:
                # Write first file with headers using filtered write kwargs
                first_df.to_csv(config.output_file, index=False, mode='w', **filtered_write_kwargs)
                print(f"    💾 Wrote {len(first_df)} rows with headers")
                total_rows = len(first_df)
                del first_df  # Clean up immediately
            else:
                print(f"    ❌ Failed to process first file")
                return None
                
            # Step 4: Stream remaining files (append without headers)
            files_processed = 1
            
            for file_path in file_iterator:
                print(f"📄 Processing file {files_processed + 1}: {file_path.name}")
                
                df = self._process_single_file(
                    file_path, schema_info, config.schema_map,
                    config.to_lower, config.spaces_to_underscores, **filtered_read_kwargs
                )
                
                if df is not None:
                    # Append without headers using filtered write kwargs
                    df.to_csv(config.output_file, index=False, mode='a', header=False, **filtered_write_kwargs)
                    total_rows += len(df)
                    print(f"    💾 Appended {len(df)} rows")
                    del df  # Clean up immediately
                    
                files_processed += 1
            
            print(f"✅ Streaming processing complete!")
            print(f"    📊 Processed {files_processed} files")
            print(f"    📈 Total rows written: {total_rows}")
            print(f"    💾 Output: {config.output_file}")
            
            return {
                'files_processed': files_processed,
                'total_rows': total_rows,
                'output_file': config.output_file,
                'schema': schema_info
            }
            
        except StopIteration:
            print("⚠️ No files found to process")
            return None

    def _determine_schema(self, input_folder, recursive=False, filetype=None, 
                         schema_map=None, to_lower=True, spaces_to_underscores=True, 
                         sample_rows=100, **kwargs):
        """
        Determine unified schema across all files by sampling headers and data types
        
        This is the first pass of streaming processing - we read just enough of each
        file to understand the column structure and data types, without loading
        entire files into memory.
        
        Args:
            sample_rows (int): Number of rows to sample for type inference (default: 100)
            **kwargs: File reading options passed to handlers
            
        Returns:
            dict: Schema information containing:
                - 'dtypes': Dict mapping column names to unified data types
                - 'files_processed': Number of files sampled
        """
        print("🔍 Detecting schema across files...")
        
        schema_map = schema_map or SCHEMA_MAP
        all_columns = set()
        column_dtypes = {}
        files_processed = 0
        
        file_iterator = self._get_files_iterator(input_folder, recursive, filetype)
        
        for file_path in file_iterator:
            try:
                print(f"  📄 Sampling: {file_path.name}")
                
                # Read small sample for schema detection
                sample_df = self._read_file_sample(file_path, sample_rows, **kwargs)
                if sample_df is None or sample_df.empty:
                    continue
                
                # Normalize columns using same logic as full processing
                normalized_df = normalize_columns(sample_df, schema_map, to_lower, spaces_to_underscores)
                
                # Collect column information
                file_columns = set(normalized_df.columns)
                all_columns.update(file_columns)
                
                # Update dtype information with most permissive types
                for col in normalized_df.columns:
                    current_dtype = str(normalized_df[col].dtype)
                    existing_dtype = column_dtypes.get(col)
                    
                    # Merge dtypes - choose most permissive
                    unified_dtype = self._merge_dtypes(existing_dtype, current_dtype)
                    column_dtypes[col] = unified_dtype
                
                files_processed += 1
                
                # Explicit memory cleanup
                del sample_df, normalized_df
                
            except Exception as e:
                print(f"  ⚠️ Warning: Could not sample {file_path.name}: {e}")
                continue
        
        # Force garbage collection after processing all samples
        gc.collect()
        
        schema_info = {
            'dtypes': column_dtypes,
            'files_processed': files_processed
        }
        
        unified_columns = list(column_dtypes.keys())
        print(f"  ✅ Schema detection complete:")
        print(f"     📊 {len(unified_columns)} unique columns across {files_processed} files")
        print(f"     📋 Columns: {', '.join(unified_columns[:5])}{'...' if len(unified_columns) > 5 else ''}")
        
        return schema_info

    def _get_files_iterator(self, input_folder, recursive=False, filetype=None):
        """
        Memory-efficient file iterator that yields valid files one at a time
        
        Args:
            input_folder (str): Path to folder containing files
            recursive (bool): Search subdirectories recursively
            filetype (list): File extensions to include
            
        Yields:
            pathlib.Path: Valid file paths that match criteria
        """
        path = Path(input_folder)
        files = path.rglob('*') if recursive else path.iterdir()
        valid_extensions = self._normalize_filetype(filetype)
        
        for file_path in files:
            if file_path.is_file():
                extension = file_path.suffix.lower()[1:]
                if extension in valid_extensions:
                    yield file_path

    def _process_single_file(self, file_path, schema_info, schema_map=None, 
                           to_lower=True, spaces_to_underscores=True, **kwargs):
        """
        Process a single file using the unified schema
        
        Args:
            file_path (Path): Path to file to process
            schema_info (dict): Schema information from _determine_schema()
            **kwargs: File processing options
            
        Returns:
            pd.DataFrame|None: Normalized dataframe or None if processing failed
        """
        try:
            # Read the file
            data = self.read_file(str(file_path), **kwargs)
            if data is None:
                return None
                
            print(f"    📊 Original: {data.dataframe.shape[1]} columns, {data.dataframe.shape[0]} rows")
            
            # Normalize to unified schema
            normalized_df = self._normalize_to_schema(
                data.dataframe, 
                schema_info,
                schema_map,
                to_lower,
                spaces_to_underscores
            )
            
            print(f"    ✅ Normalized: {normalized_df.shape[1]} columns, {normalized_df.shape[0]} rows")
            
            return normalized_df
            
        except Exception as e:
            print(f"    ❌ Error processing {file_path.name}: {e}")
            return None

    def _normalize_to_schema(self, dataframe, schema_info, schema_map=None, 
                           to_lower=True, spaces_to_underscores=True):
        """
        Normalize a dataframe to match the unified schema
        
        This ensures every file has the same columns in the same order with the same types,
        so they can be safely concatenated during streaming processing.
        
        Args:
            dataframe (pd.DataFrame): Individual file's dataframe to normalize
            schema_info (dict): Schema info from _determine_schema()
            schema_map (dict): Column name mappings
            to_lower (bool): Convert column names to lowercase
            spaces_to_underscores (bool): Convert spaces to underscores
            
        Returns:
            pd.DataFrame: Normalized dataframe with unified schema
        """
        # Step 1: Apply same column normalization as current logic
        normalized_df = normalize_columns(dataframe, schema_map, to_lower, spaces_to_underscores)
        
        # Step 2: Get target schema information
        target_dtypes = schema_info['dtypes']
        target_columns = list(target_dtypes.keys())
        
        # Step 3: Add missing columns with appropriate default values
        current_columns = set(normalized_df.columns)
        missing_columns = set(target_columns) - current_columns
        
        for col in missing_columns:
            # Add missing column with appropriate default based on target type
            default_value = self._get_default_value_for_dtype(target_dtypes[col])
            normalized_df[col] = default_value
            print(f"    ➕ Added missing column '{col}' with default {default_value}")
        
        # Step 4: Remove extra columns not in schema (optional - could keep them)
        extra_columns = current_columns - set(target_columns)
        if extra_columns:
            normalized_df = normalized_df.drop(columns=list(extra_columns))
            print(f"    ➖ Removed extra columns: {list(extra_columns)}")
        
        # Step 5: Reorder columns to match schema order
        normalized_df = normalized_df.reindex(columns=target_columns)
        
        # Step 6: Cast data types to match schema
        try:
            # Only cast columns that exist and aren't already the right type
            for col in target_columns:
                if col in normalized_df.columns:
                    current_dtype = str(normalized_df[col].dtype)
                    target_dtype = target_dtypes[col]
                    
                    if current_dtype != target_dtype:
                        normalized_df[col] = normalized_df[col].astype(target_dtype, errors='ignore')
                        
        except Exception as e:
            print(f"    ⚠️ Warning: Type casting failed for some columns: {e}")
            # Continue processing - type mismatches are often not critical
        
        return normalized_df

    def _read_file_sample(self, file_path, sample_rows, **kwargs):
        """
        Read a small sample of a file for schema detection
        
        Args:
            file_path (Path): Path to file to sample
            sample_rows (int): Number of rows to read
            **kwargs: File reading options
            
        Returns:
            pandas.DataFrame|None: Sample dataframe or None if error
        """
        extension = file_path.suffix.lower()[1:]
        handler = self._get_handler_for_extension(extension)
        
        try:
            # Add nrows parameter for sampling (works for CSV and Excel)
            sample_kwargs = {**self.read_options, **kwargs}
            if extension in ['csv']:
                sample_kwargs['nrows'] = sample_rows
            elif extension in ['xlsx']:
                sample_kwargs['nrows'] = sample_rows
            # JSON files are typically loaded entirely (usually smaller)
            
            # Use existing handler logic but with sampling
            result = handler.read(str(file_path), **sample_kwargs)
            return result.dataframe
            
        except Exception as e:
            # If sampling fails, try reading without nrows (for file types that don't support it)
            try:
                result = handler.read(str(file_path), **self.read_options)
                # Manually sample the result
                if len(result.dataframe) > sample_rows:
                    return result.dataframe.head(sample_rows)
                return result.dataframe
            except Exception:
                return None

    def _merge_dtypes(self, existing_dtype, new_dtype):
        """
        Merge two pandas dtypes, choosing the most permissive one
        
        Type hierarchy (most to least permissive):
        object > float64 > int64 > bool
        
        Args:
            existing_dtype (str|None): Current dtype for column
            new_dtype (str): New dtype encountered
            
        Returns:
            str: Most permissive dtype
        """
        if existing_dtype is None:
            return new_dtype
        
        # Define dtype hierarchy (most permissive first)
        dtype_hierarchy = ['object', 'float64', 'int64', 'bool', 'datetime64[ns]']
        
        # Find positions in hierarchy
        try:
            existing_pos = dtype_hierarchy.index(existing_dtype)
        except ValueError:
            existing_pos = 0  # Default to most permissive for unknown types
            
        try:
            new_pos = dtype_hierarchy.index(new_dtype)
        except ValueError:
            new_pos = 0  # Default to most permissive for unknown types
        
        # Return the more permissive type (lower index = more permissive)
        return dtype_hierarchy[min(existing_pos, new_pos)]

    def _get_default_value_for_dtype(self, dtype_str):
        """
        Get appropriate default value for missing columns based on data type
        
        Args:
            dtype_str (str): Pandas dtype string (e.g., 'int64', 'object', 'float64')
            
        Returns:
            Appropriate default value for the data type
        """
        if dtype_str == 'object':
            return None  # Will become NaN for strings
        elif 'int' in dtype_str:
            return None  # Will become NaN, can be filled later if needed
        elif 'float' in dtype_str:
            return None  # Will become NaN
        elif 'bool' in dtype_str:
            return False
        elif 'datetime' in dtype_str:
            return None  # Will become NaT (Not a Time)
        else:
            return None  # Safe default

    def _normalize_filetype(self, filetype=None):
        """
        Normalize and validate filetype filter input
        
        Args:
            filetype (str|list|None, optional): File extensions to allow.
                                                      Can be:
                                                      - None: defaults to all supported types
                                                      - str: single extension (e.g., 'csv')
                                                      - list: multiple extensions (e.g., ['csv', 'xlsx'])
        
        Returns:
            list: Validated list of file extensions
        """
        if filetype is None:
            filetype = ALLOWED_EXTENSIONS
        else:
            if isinstance(filetype, list):
                # Strip leading dots from extensions in list
                filetype = [ext.lstrip('.').lower() for ext in filetype]
            elif isinstance(filetype, str):
                filetype = [filetype.lstrip('.').lower()]
            else:
                raise TypeError(f"filetype must be str, list, or None. Got {type(filetype).__name__}: {filetype}")
            unsupported_filters = set(filetype) - set(ALLOWED_EXTENSIONS)
            if unsupported_filters:
                raise ValueError(f"Unsupported file types in filter: {unsupported_filters}. Supported: {ALLOWED_EXTENSIONS}")
        return filetype
    
    def _get_handler_for_extension(self, extension):
        """Get handler class for a given extension"""
        handler_class_name = f"{extension.capitalize()}Handler"
        try:
            handler_class = getattr(handlers, handler_class_name)
        except AttributeError:
            from .config import ALLOWED_EXTENSIONS
            raise ValueError(f"Unsupported file format: .{extension}. Supported: {[f'.{ext}' for ext in ALLOWED_EXTENSIONS]}")
        
        return handler_class()

    def read_file(self, file_path, filetype=None, **override_options):
        """
        Read a single file if it matches the filetype filter
        
        Args:
            file_path (str): Path to file to read
            filetype (str|list, optional): File extensions to allow. 
                                                Defaults to all supported types.
            **override_options: Options passed to file handlers
        
        Returns:
            FileResult|None: FileResult if file matches filter, None if filtered out
        """
        abs_path = os.path.abspath(file_path)
        print(f"Processing '{abs_path}'...")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{abs_path}' does not exist.")

        extension = Path(file_path).suffix.lower()[1:]

        if extension not in self._normalize_filetype(filetype):
            return None
        
        handler = self._get_handler_for_extension(extension)
        
        # Merge constructor options with override options
        final_read_options = {**self.read_options, **override_options}
        
        data = handler.read(file_path, **final_read_options)
        
        # Get relative path and remove first directory (input folder)
        rel_path = os.path.relpath(abs_path)
        path_parts = Path(rel_path).parts
        if len(path_parts) > 1:
            # Remove first directory (input folder) from path
            data.dataframe['source_file'] = str(Path(*path_parts[1:]))
        else:
            # If only one part, just use the filename
            data.dataframe['source_file'] = path_parts[0]
        
        print(f"Loaded: {data.dataframe.shape[0]} rows, {data.dataframe.shape[1]} columns")
        print(f"Columns: {list(data.dataframe.columns)}")
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
        extension = Path(output_path).suffix.lower()[1:]  # Remove the dot
        
        if not extension:
            raise ValueError(f"Output file must have an extension to determine format: {output_path}")
        
        handler = self._get_handler_for_extension(extension)
        
        # Merge constructor options with override options
        final_write_options = {**self.write_options, **override_options}
        
        # Write the file
        handler.write(dataframe, output_path, **final_write_options)
        print(f"Data saved to '{abs_path}' ({len(dataframe)} rows, {len(dataframe.columns)} columns)")