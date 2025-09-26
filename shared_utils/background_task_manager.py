"""
Background task management for GUI applications.

Provides thread-safe communication between GUI and background worker threads
with standardized progress reporting and status updates.
"""

import threading
import queue
import time
from typing import Callable, Optional, Any, Dict
from enum import Enum


class TaskStatus(Enum):
    """Status values for background tasks"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskMessage:
    """Message passed between background thread and GUI"""
    
    def __init__(self, message_type: str, content: str, data: Optional[Dict[str, Any]] = None):
        self.message_type = message_type
        self.content = content
        self.data = data or {}
        self.timestamp = time.time()


class BackgroundTaskManager:
    """
    Manages background task execution with thread-safe GUI communication.
    
    Handles the complexity of running tasks in separate threads while providing
    safe communication channels for progress updates, status changes, and results.
    Integrates with GUI frameworks through callback-based architecture.
    """
    
    def __init__(self,
                 status_callback: Optional[Callable[[str], None]] = None,
                 progress_callback: Optional[Callable[[str], None]] = None,
                 completion_callback: Optional[Callable[[str], None]] = None,
                 error_callback: Optional[Callable[[str], None]] = None,
                 scheduler_callback: Optional[Callable[[int, Callable], None]] = None):
        """
        Initialize task manager with GUI integration callbacks.
        
        Args:
            status_callback: Called when task status changes
            progress_callback: Called with progress updates during task execution
            completion_callback: Called when task completes successfully
            error_callback: Called when task fails with error
            scheduler_callback: Function to schedule GUI updates (e.g., tkinter's after())
        """
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback
        self.scheduler_callback = scheduler_callback
        
        # Task state
        self.current_task = None
        self.current_thread = None
        self.task_status = TaskStatus.IDLE
        self.message_queue = queue.Queue()
    
    def run_task(self, task_function: Callable, *args, **kwargs) -> bool:
        """
        Execute a function in a background thread with progress monitoring.
        
        Args:
            task_function: Function to execute in background thread
            *args: Positional arguments for task function
            **kwargs: Keyword arguments for task function
            
        Returns:
            bool: True if task was started, False if another task is already running
        """
        if self.is_running():
            return False
        
        # Update status
        self.task_status = TaskStatus.RUNNING
        self._update_status("Starting task...")
        
        # Start message processing loop now that task is running
        if self.scheduler_callback:
            self._process_message_queue()
        
        # Create and start background thread
        self.current_thread = threading.Thread(
            target=self._task_wrapper,
            args=(task_function, args, kwargs),
            daemon=True
        )
        self.current_thread.start()
        
        return True
    
    def cancel_task(self) -> None:
        """Cancel the currently running task"""
        if not self.is_running():
            return
        
        self.task_status = TaskStatus.CANCELLED
        self._update_status("Cancelling task...")
        self._clean_up_task()
    
    def is_running(self) -> bool:
        """Check if a task is currently running"""
        return self.task_status == TaskStatus.RUNNING
    
    def get_status(self) -> TaskStatus:
        """Get current task status"""
        return self.task_status
    
    def send_progress_update(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Send progress update from background task to GUI"""
        self.message_queue.put(TaskMessage("progress", message, data))
    
    def _task_wrapper(self, task_function: Callable, args: tuple, kwargs: dict) -> None:
        """Wrapper that executes the actual task with error handling"""
        start_time = time.time()
        
        try:
            # Create progress reporter
            progress_reporter = ProgressReporter(self.send_progress_update)
            
            # Execute the task with progress reporting capability
            if 'progress_reporter' not in kwargs:
                kwargs['progress_reporter'] = progress_reporter
            
            result = task_function(*args, **kwargs)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Send completion message with the actual result
            completion_data = {
                'result': result,
                'execution_time': execution_time
            }
            
            # Use the result as the completion message if it's a string, otherwise use default
            if isinstance(result, str):
                completion_message = result
            else:
                completion_message = "Task completed successfully"
            
            self.message_queue.put(TaskMessage("complete", completion_message, completion_data))
            
        except Exception as e:
            # Send error message
            error_data = {
                'exception': e,
                'execution_time': time.time() - start_time
            }
            
            self.message_queue.put(TaskMessage("error", f"Task failed: {str(e)}", error_data))
    
    def _start_message_processing(self) -> None:
        """Start the message processing loop"""
        if self.scheduler_callback:
            self._process_message_queue()
        
    def _process_message_queue(self) -> None:
        """Process messages from background thread (runs on GUI thread)"""
        try:
            message_count = 0
            while True:
                message = self.message_queue.get_nowait()
                message_count += 1
                self._handle_message(message)
        except queue.Empty:
            pass
        
        # Schedule next check if scheduler is available and task is still active
        should_continue = self.task_status in [TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED]
        
        if self.scheduler_callback and should_continue:
            self.scheduler_callback(100, self._process_message_queue)
    
    def _handle_message(self, message: TaskMessage) -> None:
        """Handle a message from the background thread"""
        
        if message.message_type == "progress":
            if self.progress_callback:
                self.progress_callback(message.content)
        
        elif message.message_type == "complete":
            self.task_status = TaskStatus.COMPLETED
            if self.completion_callback:
                self.completion_callback(message.content)
            self._clean_up_task()
        
        elif message.message_type == "error":
            self.task_status = TaskStatus.FAILED
            if self.error_callback:
                self.error_callback(message.content)
            self._clean_up_task()
    
    def _update_status(self, status_text: str) -> None:
        """Send status update via callback"""
        if self.status_callback:
            self.status_callback(status_text)
    
    def _clean_up_task(self) -> None:
        """Clean up after task completion or cancellation"""
        self.current_task = None
        self.current_thread = None
        
        # Don't change status to idle immediately - let the final messages process first
        # The status will be checked in the GUI callbacks
        
        # Force garbage collection
        import gc
        gc.collect()


class ProgressReporter:
    """
    Helper class for sending progress updates from background tasks.
    
    Provides a convenient interface for task functions to report progress
    without needing direct access to the task manager.
    """
    
    def __init__(self, send_function: Callable[[str, Optional[Dict]], None]):
        self.send_function = send_function
    
    def update(self, message: str, **data) -> None:
        """Send a progress update with optional data"""
        self.send_function(message, data)
    
    def update_with_stats(self, message: str, 
                         files_processed: int = 0,
                         total_files: int = 0,
                         current_file: str = None,
                         **extra_data) -> None:
        """Send progress update with standardized processing statistics"""
        data = {
            'files_processed': files_processed,
            'total_files': total_files,
            'current_file': current_file,
            **extra_data
        }
        self.send_function(message, data)