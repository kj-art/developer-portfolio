# shared_utils/progress.py
"""
Reusable progress tracking system for data processing operations

Provides both CLI and GUI progress reporting capabilities with consistent
interfaces across different user interaction modes.

Features:
- File-by-file progress tracking
- Row-level progress within files
- Memory usage reporting
- Time estimates and performance metrics
- Thread-safe operation for GUI integration
- CLI progress bars with tqdm
- Callback-based reporting for custom integrations

Usage:
    # CLI usage with tqdm
    from shared_utils.progress import CLIProgressReporter
    
    progress = CLIProgressReporter()
    progress.start_processing(total_files=5)
    
    for file in files:
        progress.start_file(file.name)
        # ... process file ...
        progress.complete_file(rows_processed=1000)
    
    progress.complete_processing(total_rows=5000, processing_time=12.5)
    
    # GUI usage with callbacks
    from shared_utils.progress import CallbackProgressReporter
    
    def update_gui(message_type, content):
        # Update GUI elements
        pass
    
    progress = CallbackProgressReporter(update_gui)
    # Same interface as CLI version
"""

import time
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any
import threading

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class BaseProgressReporter(ABC):
    """Base class for progress reporting with consistent interface"""
    
    def __init__(self):
        self.current_file = None
        self.files_processed = 0
        self.total_files = 0
        self.current_rows = 0
        self.total_rows = 0
        self.start_time = None
        self.lock = threading.Lock()
    
    @abstractmethod
    def start_processing(self, total_files: int):
        """Initialize progress tracking for processing session"""
        pass
    
    @abstractmethod
    def start_file(self, filename: str):
        """Report starting processing of a new file"""
        pass
    
    @abstractmethod
    def update_rows(self, rows_in_chunk: int, estimated_total: Optional[int] = None):
        """Update row processing progress within current file"""
        pass
    
    @abstractmethod
    def complete_file(self, rows_processed: int):
        """Report completion of current file"""
        pass
    
    @abstractmethod
    def complete_processing(self, total_rows: int, processing_time: float):
        """Report completion of all processing"""
        pass
    
    def get_progress_summary(self) -> dict:
        """Get current progress statistics"""
        with self.lock:
            elapsed = time.time() - self.start_time if self.start_time else 0
            return {
                'files_processed': self.files_processed,
                'total_files': self.total_files,
                'current_rows': self.current_rows,
                'total_rows': self.total_rows,
                'elapsed_time': elapsed,
                'current_file': self.current_file
            }


class CLIProgressReporter(BaseProgressReporter):
    """CLI progress reporter using tqdm for terminal progress bars"""
    
    def __init__(self, use_tqdm: bool = None):
        super().__init__()
        self.use_tqdm = use_tqdm if use_tqdm is not None else TQDM_AVAILABLE
        self.file_progress_bar = None
        self.row_progress_bar = None
        
    def start_processing(self, total_files: int):
        """Initialize progress tracking with tqdm progress bars"""
        with self.lock:
            self.total_files = total_files
            self.files_processed = 0
            self.current_rows = 0
            self.total_rows = 0
            self.start_time = time.time()
        
        if self.use_tqdm:
            self.file_progress_bar = tqdm(
                total=total_files,
                desc="Processing files",
                unit="file",
                position=0,
                leave=True
            )
        else:
            print(f"Starting processing of {total_files} files...")
    
    def start_file(self, filename: str):
        """Report starting processing of a new file"""
        with self.lock:
            self.current_file = filename
            self.files_processed += 1
            self.current_rows = 0
        
        if self.use_tqdm:
            # Update file progress bar
            if self.file_progress_bar:
                self.file_progress_bar.set_description(f"Processing: {filename}")
                self.file_progress_bar.update(1)
            
            # Close previous row progress bar if it exists
            if self.row_progress_bar:
                self.row_progress_bar.close()
                self.row_progress_bar = None
        else:
            print(f"Processing file {self.files_processed}/{self.total_files}: {filename}")
    
    def update_rows(self, rows_in_chunk: int, estimated_total: Optional[int] = None):
        """Update row processing progress"""
        with self.lock:
            self.current_rows += rows_in_chunk
            if estimated_total:
                self.total_rows = estimated_total
        
        if self.use_tqdm and estimated_total:
            # Create or update row progress bar
            if not self.row_progress_bar:
                self.row_progress_bar = tqdm(
                    total=estimated_total,
                    desc="  Processing rows",
                    unit="row",
                    position=1,
                    leave=False
                )
            self.row_progress_bar.update(rows_in_chunk)
        elif not self.use_tqdm:
            if estimated_total:
                percentage = (self.current_rows / estimated_total) * 100
                print(f"  └─ Processed {self.current_rows:,} of ~{estimated_total:,} rows ({percentage:.1f}%)")
            else:
                print(f"  └─ Processed {self.current_rows:,} rows")
    
    def complete_file(self, rows_processed: int):
        """Report completion of current file"""
        if self.use_tqdm:
            # Close row progress bar
            if self.row_progress_bar:
                self.row_progress_bar.close()
                self.row_progress_bar = None
        else:
            print(f"  ✓ Completed: {rows_processed:,} rows processed")
    
    def complete_processing(self, total_rows: int, processing_time: float):
        """Report completion of all processing"""
        if self.use_tqdm:
            # Close all progress bars
            if self.file_progress_bar:
                self.file_progress_bar.close()
                self.file_progress_bar = None
            if self.row_progress_bar:
                self.row_progress_bar.close()
                self.row_progress_bar = None
        
        rate = total_rows / processing_time if processing_time > 0 else 0
        print(f"\n✅ Processing complete: {self.files_processed} files, {total_rows:,} rows in {processing_time:.2f}s ({rate:.0f} rows/sec)")


class CallbackProgressReporter(BaseProgressReporter):
    """Progress reporter that uses callbacks for GUI integration"""
    
    def __init__(self, callback: Callable[[str, Any], None]):
        super().__init__()
        self.callback = callback
    
    def start_processing(self, total_files: int):
        """Initialize progress tracking"""
        with self.lock:
            self.total_files = total_files
            self.files_processed = 0
            self.current_rows = 0
            self.total_rows = 0
            self.start_time = time.time()
        
        self.callback('progress', f"Starting processing of {total_files} files...")
    
    def start_file(self, filename: str):
        """Report starting processing of a new file"""
        with self.lock:
            self.current_file = filename
            self.files_processed += 1
        
        progress_msg = f"Processing file {self.files_processed}/{self.total_files}: {filename}"
        self.callback('progress', progress_msg)
    
    def update_rows(self, rows_in_chunk: int, estimated_total: Optional[int] = None):
        """Update row processing progress"""
        with self.lock:
            self.current_rows += rows_in_chunk
            if estimated_total:
                self.total_rows = estimated_total
        
        if estimated_total:
            percentage = (self.current_rows / estimated_total) * 100
            progress_msg = f"  └─ Processed {self.current_rows:,} of ~{estimated_total:,} rows ({percentage:.1f}%)"
        else:
            progress_msg = f"  └─ Processed {self.current_rows:,} rows"
        
        self.callback('progress', progress_msg)
        
        # Also send percentage update for progress bars
        if estimated_total:
            self.callback('percentage', (self.current_rows / estimated_total) * 100)
    
    def complete_file(self, rows_processed: int):
        """Report completion of current file"""
        progress_msg = f"  ✓ Completed: {rows_processed:,} rows processed"
        self.callback('progress', progress_msg)
    
    def complete_processing(self, total_rows: int, processing_time: float):
        """Report completion of all processing"""
        rate = total_rows / processing_time if processing_time > 0 else 0
        progress_msg = f"\n✅ Processing complete: {self.files_processed} files, {total_rows:,} rows in {processing_time:.2f}s ({rate:.0f} rows/sec)"
        self.callback('progress', progress_msg)
        self.callback('complete', {
            'files_processed': self.files_processed,
            'total_rows': total_rows,
            'processing_time': processing_time,
            'rows_per_second': rate
        })


class NullProgressReporter(BaseProgressReporter):
    """Silent progress reporter for batch processing or testing"""
    
    def start_processing(self, total_files: int):
        with self.lock:
            self.total_files = total_files
            self.files_processed = 0
            self.start_time = time.time()
    
    def start_file(self, filename: str):
        with self.lock:
            self.current_file = filename
            self.files_processed += 1
    
    def update_rows(self, rows_in_chunk: int, estimated_total: Optional[int] = None):
        with self.lock:
            self.current_rows += rows_in_chunk
            if estimated_total:
                self.total_rows = estimated_total
    
    def complete_file(self, rows_processed: int):
        pass
    
    def complete_processing(self, total_rows: int, processing_time: float):
        pass


def create_progress_reporter(mode: str = 'auto', **kwargs) -> BaseProgressReporter:
    """
    Factory function to create appropriate progress reporter
    
    Args:
        mode: 'cli', 'gui', 'callback', 'null', or 'auto'
        **kwargs: Additional arguments passed to reporter constructor
    
    Returns:
        Configured progress reporter instance
    """
    if mode == 'auto':
        # Auto-detect based on environment
        try:
            import sys
            if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
                mode = 'cli'
            else:
                mode = 'null'
        except Exception:
            mode = 'null'
    
    if mode == 'cli':
        return CLIProgressReporter(**kwargs)
    elif mode == 'callback' or mode == 'gui':
        if 'callback' not in kwargs:
            raise ValueError("Callback mode requires 'callback' parameter")
        return CallbackProgressReporter(kwargs['callback'])
    elif mode == 'null':
        return NullProgressReporter()
    else:
        raise ValueError(f"Unknown progress reporter mode: {mode}")