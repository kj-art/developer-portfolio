"""
Logging wrapper for batch rename operations.

Provides comprehensive logging around the BatchRenameProcessor.
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any

from .processor import BatchRenameProcessor
from .config import RenameConfig, RenameResult


class LoggingBatchRenameProcessor:
    """
    Logging wrapper for BatchRenameProcessor.
    
    Provides operation logging while keeping the core processor focused on business logic.
    """
    
    def __init__(self, processor: Optional[BatchRenameProcessor] = None):
        """
        Initialize logging wrapper.
        
        Args:
            processor: BatchRenameProcessor instance, creates new one if None
        """
        self.processor = processor or BatchRenameProcessor()
    
    def process(self, config: RenameConfig) -> RenameResult:
        """
        Execute batch rename with logging.
        
        Args:
            config: Rename configuration
            
        Returns:
            RenameResult with operation statistics
        """
        try:
            result = self.processor.process(config)
            return result
        except Exception as e:
            # Re-raise the exception after any logging
            raise


def create_logging_processor(log_level: str = 'INFO', log_file: Optional[str] = None, 
                           enable_colors: bool = True) -> LoggingBatchRenameProcessor:
    """
    Factory function to create a logging processor.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file to write logs to
        enable_colors: Whether to use colored console output
        
    Returns:
        Configured LoggingBatchRenameProcessor
    """
    # Try to set up logging if the shared logger is available
    try:
        from shared_utils.logger import set_up_logging
        
        # Configure logging system
        set_up_logging(
            level=log_level,
            log_file=log_file,
            json_file=f"{log_file}.json" if log_file else None,
            enable_colors=enable_colors
        )
    except ImportError:
        # If shared logger isn't available, use basic logging
        import logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    return LoggingBatchRenameProcessor()