class InMemoryReader:
  pass

'''from pathlib import Path
from shared_utils.logger import get_logger, log_performance
from ..processing_config import ProcessingConfig
from ..config import SCHEMA_MAP, ALLOWED_EXTENSIONS
from ..dataframe_utils import normalize_columns, merge_dataframes, ProcessingResult

class InMemoryProcessor:
  def __init__(self, read_options:dict=None, write_options:dict=None):
     self._read_options = read_options
     self._write_options = write_options
     self._logger = get_logger('data_pipeline.in_memory')

  def run(self, config: ProcessingConfig) -> ProcessingResult:
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
        



        return
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
        return result'''