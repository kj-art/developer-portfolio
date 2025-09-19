"""
Logging wrapper for batch rename operations.

Provides comprehensive logging around the BatchRenameProcessor using the shared
logger utility with StringSmith formatting for rich, conditional log output.
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any

from shared_utils.logger import get_logger, log_performance, log_processing_stats
from .processor import BatchRenameProcessor
from .config import RenameConfig, RenameResult


class LoggingBatchRenameProcessor:
    """
    Professional logging wrapper for BatchRenameProcessor.
    
    Provides comprehensive operation, file-level, and performance logging
    while keeping the core processor focused on business logic.
    """
    
    def __init__(self, processor: Optional[BatchRenameProcessor] = None):
        """
        Initialize logging wrapper.
        
        Args:
            processor: BatchRenameProcessor instance, creates new one if None
        """
        self.processor = processor or BatchRenameProcessor()
        self.logger = get_logger('batch_rename')
        self.perf_logger = get_logger('batch_rename.performance')
        self.file_logger = get_logger('batch_rename.files')
        self.error_logger = get_logger('batch_rename.errors')
    
    def process(self, config: RenameConfig) -> RenameResult:
        """
        Execute batch rename with comprehensive logging.
        
        Args:
            config: Rename configuration
            
        Returns:
            RenameResult with operation statistics
        """
        operation_name = "preview" if config.preview_mode else "execute"
        
        # Log operation start with configuration details
        self._log_operation_start(config, operation_name)
        
        # Execute with performance tracking
        with log_performance(f"batch_rename_{operation_name}", self.perf_logger) as perf_context:
            try:
                result = self._process_with_logging(config)
                self._log_operation_success(config, result, operation_name)
                return result
                
            except Exception as e:
                self._log_operation_failure(config, e, operation_name)
                raise
    
    def _process_with_logging(self, config: RenameConfig) -> RenameResult:
        """Internal processing with detailed file-level logging."""
        
        # Pre-processing validation
        if not config.input_folder.exists():
            raise FileNotFoundError(f"Input folder does not exist: {config.input_folder}")
        
        if not config.input_folder.is_dir():
            raise NotADirectoryError(f"Input path is not a directory: {config.input_folder}")
        
        # Log configuration validation
        self.logger.debug("Configuration validated successfully",
                         extractor=config.extractor,
                         converter_count=len(config.converters),
                         filter_count=len(config.filters),
                         recursive=config.recursive)
        
        # Execute core processing
        result = self.processor.process(config)
        
        # Log detailed results
        self._log_processing_details(config, result)
        
        return result
    
    def _log_operation_start(self, config: RenameConfig, operation_name: str):
        """Log operation startup with configuration summary."""
        self.logger.info(f"Starting batch rename {operation_name}",
                        input_folder=str(config.input_folder),
                        extractor=config.extractor,
                        converter_count=len(config.converters),
                        filter_count=len(config.filters),
                        recursive=config.recursive,
                        preview_mode=config.preview_mode)
        
        # Log extractor configuration
        if config.extractor_args:
            self.logger.debug("Extractor configuration",
                            extractor=config.extractor,
                            positional_args=config.extractor_args.get('positional', []),
                            keyword_args=config.extractor_args.get('keyword', {}))
        
        # Log converter chain
        if config.converters:
            for i, converter in enumerate(config.converters):
                self.logger.debug(f"Converter {i+1} configuration",
                                converter_name=converter['name'],
                                positional_args=converter.get('positional', []),
                                keyword_args=converter.get('keyword', {}))
        
        # Log filter chain
        if config.filters:
            for i, filter_config in enumerate(config.filters):
                self.logger.debug(f"Filter {i+1} configuration",
                                filter_name=filter_config['name'],
                                inverted=filter_config.get('inverted', False),
                                positional_args=filter_config.get('positional', []),
                                keyword_args=filter_config.get('keyword', {}))
    
    def _log_operation_success(self, config: RenameConfig, result: RenameResult, operation_name: str):
        """Log successful operation completion with statistics."""
        
        # Calculate success metrics
        success_rate = 0.0
        if result.files_analyzed > 0:
            processed_files = result.files_analyzed - result.errors
            success_rate = (processed_files / result.files_analyzed) * 100
        
        # Log summary with conditional sections via StringSmith
        self.logger.info(f"Batch rename {operation_name} completed successfully",
                        files_analyzed=result.files_analyzed,
                        files_to_rename=result.files_to_rename,
                        files_renamed=result.files_renamed,
                        success_rate=f"{success_rate:.1f}%",
                        error_count=result.errors,
                        collision_count=result.collisions)
        
        # Log detailed statistics using shared utility
        log_processing_stats(
            operation=f"batch_rename_{operation_name}",
            files_processed=result.files_analyzed,
            duration=0,  # Will be filled by performance context
            errors=result.errors
        )
        
        # Log collision details if any
        if result.collisions > 0:
            self.logger.warning("Naming conflicts detected",
                              collision_count=result.collisions,
                              recommendation="Review naming pattern or add unique identifiers")
    
    def _log_operation_failure(self, config: RenameConfig, error: Exception, operation_name: str):
        """Log operation failure with error context."""
        self.error_logger.error(f"Batch rename {operation_name} failed",
                               input_folder=str(config.input_folder),
                               extractor=config.extractor,
                               exception=error,
                               error_type=type(error).__name__)
    
    def _log_processing_details(self, config: RenameConfig, result: RenameResult):
        """Log detailed processing information for debugging."""
        
        # Log error details
        if result.error_details:
            self.error_logger.warning("Processing errors encountered",
                                    error_count=len(result.error_details))
            
            for error_detail in result.error_details:
                self.error_logger.error("File processing error",
                                      file_path=error_detail['file'],
                                      error_message=error_detail['error'])
        
        # Log preview data summary in debug mode
        if config.preview_mode and result.preview_data:
            unchanged_files = sum(1 for item in result.preview_data 
                                if item['old_name'] == item['new_name'])
            changed_files = len(result.preview_data) - unchanged_files
            
            self.logger.debug("Preview analysis complete",
                            total_files=len(result.preview_data),
                            files_to_change=changed_files,
                            files_unchanged=unchanged_files)
            
            # Log sample of changes for debugging
            changes = [item for item in result.preview_data[:5] 
                      if item['old_name'] != item['new_name']]
            
            for change in changes:
                self.file_logger.debug("Preview change",
                                     old_name=change['old_name'],
                                     new_name=change['new_name'])
        
        # Log execution summary
        if not config.preview_mode and result.files_renamed > 0:
            self.logger.info("File rename execution complete",
                           files_renamed=result.files_renamed,
                           rename_success_rate=f"{(result.files_renamed / result.files_to_rename * 100):.1f}%" 
                           if result.files_to_rename > 0 else "0%")


def create_logging_processor(log_level: str = 'INFO', 
                           log_file: Optional[str] = None,
                           enable_colors: bool = True) -> LoggingBatchRenameProcessor:
    """
    Factory function to create a logging processor with configured logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file to write logs to
        enable_colors: Whether to use colored console output
        
    Returns:
        Configured LoggingBatchRenameProcessor
    """
    from shared_utils.logger import set_up_logging
    
    # Configure logging system
    set_up_logging(
        level=log_level,
        log_file=log_file,
        json_file=f"{log_file}.json" if log_file else None,
        enable_colors=enable_colors
    )
    
    return LoggingBatchRenameProcessor()