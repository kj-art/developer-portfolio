import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import time
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_pipeline.core.processor import DataProcessor
from data_pipeline.core.processing_config import ProcessingConfig, IndexMode
from shared_utils.logger import set_up_logging, get_logger

try:
    import psutil
    from shared_utils.memory_sparkline_widget import MemorySparklineWidget
    MEMORY_MONITORING_AVAILABLE = True
except ImportError:
    MEMORY_MONITORING_AVAILABLE = False


class DataPipelineGUI:
    """
    Professional GUI for the data processing pipeline.
    
    Provides an intuitive interface for configuring and running data processing operations
    with real-time progress feedback and comprehensive error handling.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Data Processing Pipeline")
        self.root.geometry("800x750")
        self.root.minsize(600, 550)
        
        # Configure logging for GUI mode
        set_up_logging(level='INFO', enable_colors=False)
        self.logger = get_logger('data_pipeline.gui')
        
        # Processing state
        self.processor = None
        self.processing_thread = None
        self.is_processing = False
        self.progress_queue = queue.Queue()
        
        # Memory monitoring state
        self.memory_monitoring_active = False
        
        # Create GUI variables for form binding
        self._create_variables()
        
        # Build the interface
        self._create_widgets()
        self._setup_bindings()
        
        # Setup memory monitoring if available
        if MEMORY_MONITORING_AVAILABLE:
            self._setup_memory_monitoring()
        
        # Start progress monitoring
        self._check_progress_queue()
    
    def _create_variables(self):
        """Create tkinter variables for two-way data binding with ProcessingConfig"""
        self.input_folder = tk.StringVar()
        self.output_file = tk.StringVar()
        self.recursive = tk.BooleanVar()
        self.to_lower = tk.BooleanVar(value=True)
        self.spaces_to_underscores = tk.BooleanVar(value=True)
        self.force_in_memory = tk.BooleanVar()
        
        # File type selection (multiple checkboxes)
        self.filetype_csv = tk.BooleanVar(value=True)
        self.filetype_xlsx = tk.BooleanVar(value=True)
        self.filetype_json = tk.BooleanVar(value=True)
        
        # Index options
        self.index_mode = tk.StringVar(value="none")
        self.index_start = tk.IntVar(value=0)
        
        # Columns specification
        self.columns = tk.StringVar()
        
        # Schema file
        self.schema_file = tk.StringVar()
    
    def _create_widgets(self):
        """Create all GUI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure root grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        current_row = 0
        
        # Input Section
        input_frame = ttk.LabelFrame(main_frame, text="Input Configuration", padding="10")
        input_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="Input Folder:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(input_frame, textvariable=self.input_folder).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(input_frame, text="Browse...", command=self._browse_input_folder).grid(row=0, column=2)
        
        ttk.Checkbutton(input_frame, text="Search subdirectories recursively", 
                       variable=self.recursive).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
        
        # File Types
        filetype_frame = ttk.Frame(input_frame)
        filetype_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(filetype_frame, text="File Types:").grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(filetype_frame, text="CSV", variable=self.filetype_csv).grid(row=0, column=1, padx=(10, 0))
        ttk.Checkbutton(filetype_frame, text="Excel", variable=self.filetype_xlsx).grid(row=0, column=2, padx=(10, 0))
        ttk.Checkbutton(filetype_frame, text="JSON", variable=self.filetype_json).grid(row=0, column=3, padx=(10, 0))
        
        current_row += 1
        
        # Processing Options Section
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding="10")
        options_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(options_frame, text="Convert column names to lowercase", 
                       variable=self.to_lower).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Checkbutton(options_frame, text="Convert spaces to underscores in column names", 
                       variable=self.spaces_to_underscores).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        ttk.Checkbutton(options_frame, text="Force in-memory processing (override streaming optimizations)", 
                       variable=self.force_in_memory).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Schema Configuration
        schema_frame = ttk.Frame(options_frame)
        schema_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        schema_frame.columnconfigure(1, weight=1)
        
        ttk.Label(schema_frame, text="Schema File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(schema_frame, textvariable=self.schema_file).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(schema_frame, text="Browse...", command=self._browse_schema_file).grid(row=0, column=2)
        
        # Columns Configuration
        columns_frame = ttk.Frame(options_frame)
        columns_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        columns_frame.columnconfigure(1, weight=1)
        
        ttk.Label(columns_frame, text="Expected Columns:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(columns_frame, textvariable=self.columns, 
                 font=("TkDefaultFont", 8)).grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(options_frame, text="(comma-separated, enables streaming optimization)", 
                 font=("TkDefaultFont", 8), foreground="gray").grid(row=5, column=0, columnspan=2, sticky=tk.W)
        
        current_row += 1
        
        # Index Configuration Section
        index_frame = ttk.LabelFrame(main_frame, text="Index Configuration", padding="10")
        index_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(index_frame, text="Index Mode:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        index_combo = ttk.Combobox(index_frame, textvariable=self.index_mode, 
                                  values=["none", "local", "sequential"], state="readonly", width=15)
        index_combo.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(index_frame, text="Start Value:").grid(row=0, column=2, sticky=tk.W, padx=(20, 10))
        index_start_spinbox = ttk.Spinbox(index_frame, textvariable=self.index_start, 
                                         from_=0, to=999999, width=10)
        index_start_spinbox.grid(row=0, column=3, sticky=tk.W)
        
        # Index help text
        index_help = ttk.Label(index_frame, 
                              text="none: no index column, local: per-file indices, sequential: continuous across files",
                              font=("TkDefaultFont", 8), foreground="gray")
        index_help.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        current_row += 1
        
        # Output Section
        output_frame = ttk.LabelFrame(main_frame, text="Output Configuration", padding="10")
        output_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(output_frame, textvariable=self.output_file).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(output_frame, text="Browse...", command=self._browse_output_file).grid(row=0, column=2)
        
        ttk.Label(output_frame, text="(leave empty for console output)", 
                 font=("TkDefaultFont", 8), foreground="gray").grid(row=1, column=0, columnspan=3, sticky=tk.W)
        
        current_row += 1
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=current_row, column=0, columnspan=2, pady=(0, 10))
        
        self.run_button = ttk.Button(button_frame, text="Run Processing", command=self._run_processing)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self._cancel_processing, state="disabled")
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear All", command=self._clear_form).pack(side=tk.LEFT)
        
        current_row += 1
        
        # Memory Monitor Section (if available)
        if MEMORY_MONITORING_AVAILABLE:
            memory_frame = ttk.LabelFrame(main_frame, text="Memory Monitor", padding="10")
            memory_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
            memory_frame.columnconfigure(0, weight=1)
            
            # Memory sparkline widget
            self.memory_sparkline = MemorySparklineWidget(memory_frame, width=400, height=60)
            self.memory_sparkline.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
            
            # Memory status text
            self.memory_status_var = tk.StringVar(value="Initializing memory monitor...")
            self.memory_status_label = ttk.Label(memory_frame, textvariable=self.memory_status_var, 
                                               font=('Consolas', 9))
            self.memory_status_label.grid(row=1, column=0, sticky=tk.W)
            
            current_row += 1
        
        # Progress and Results Section
        results_frame = ttk.LabelFrame(main_frame, text="Progress & Results", padding="10")
        results_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(current_row, weight=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(results_frame, variable=self.progress_var, mode='indeterminate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(results_frame, height=12, wrap=tk.WORD)
        self.results_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        current_row += 1
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def _setup_memory_monitoring(self):
        """Set up memory monitoring"""
        try:
            self.process = psutil.Process()
            self._start_memory_monitoring()
        except Exception as e:
            self.memory_status_var.set(f"⚠️ Memory monitoring error: {str(e)}")
    
    def _start_memory_monitoring(self):
        """Start the memory monitoring loop"""
        if not hasattr(self, 'process'):
            return
        
        self.memory_monitoring_active = True
        self._memory_monitoring_loop()
    
    def _memory_monitoring_loop(self):
        """Memory monitoring loop - runs on main thread with after()"""
        if not self.memory_monitoring_active:
            return
        
        try:
            # Get current memory usage
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            
            # Update sparkline
            self.memory_sparkline.add_data_point(memory_mb)
            
            # Build status text
            status_text = self._build_memory_status_text(memory_mb)
            self.memory_status_var.set(status_text)
            
        except Exception as e:
            self.memory_status_var.set(f"Memory monitoring error: {str(e)}")
        
        # Schedule next update
        self.root.after(1000, self._memory_monitoring_loop)  # Update every second
    
    def _build_memory_status_text(self, memory_mb):
        """Build memory status text without StringSmith"""
        # Get status icon
        if hasattr(self.memory_sparkline, 'red_threshold') and memory_mb > self.memory_sparkline.red_threshold:
            icon = '🚨'
        elif hasattr(self.memory_sparkline, 'yellow_threshold') and memory_mb > self.memory_sparkline.yellow_threshold:
            icon = '⚠️'
        else:
            icon = '📊'
        
        # Get trend indicator
        if len(self.memory_sparkline.data) < 6:
            trend = '→'
        else:
            recent = list(self.memory_sparkline.data)[-3:]
            older = list(self.memory_sparkline.data)[-6:-3]
            
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)
            
            if recent_avg > older_avg * 1.1:
                trend = '↗'
            elif recent_avg < older_avg * 0.9:
                trend = '↘'
            else:
                trend = '→'
        
        # Build status text
        status_text = f"{icon} {memory_mb:.1f}MB {trend}"
        
        # Add baseline if available
        if self.memory_sparkline.yellow_threshold > 0:
            status_text += f" (Baseline: {self.memory_sparkline.baseline:.0f}MB)"
        
        return status_text
    
    def _stop_memory_monitoring(self):
        """Stop memory monitoring"""
        self.memory_monitoring_active = False
    
    def _setup_bindings(self):
        """Set up event bindings and keyboard shortcuts"""
        self.root.bind('<Control-Return>', lambda e: self._run_processing())
        self.root.bind('<Escape>', lambda e: self._cancel_processing())
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _browse_input_folder(self):
        """Open folder browser for input directory"""
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder.set(folder)
    
    def _browse_output_file(self):
        """Open file browser for output file"""
        filetypes = [
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx"),
            ("JSON files", "*.json"),
            ("All files", "*.*")
        ]
        filename = filedialog.asksaveasfilename(title="Select Output File", filetypes=filetypes)
        if filename:
            self.output_file.set(filename)
    
    def _browse_schema_file(self):
        """Open file browser for schema file"""
        filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select Schema File", filetypes=filetypes)
        if filename:
            self.schema_file.set(filename)
    
    def _clear_form(self):
        """Clear all form fields to defaults"""
        self.input_folder.set("")
        self.output_file.set("")
        self.schema_file.set("")
        self.columns.set("")
        self.recursive.set(False)
        self.to_lower.set(True)
        self.spaces_to_underscores.set(True)
        self.force_in_memory.set(False)
        self.filetype_csv.set(True)
        self.filetype_xlsx.set(True)
        self.filetype_json.set(True)
        self.index_mode.set("none")
        self.index_start.set(0)
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Ready")
    
    def _validate_form(self):
        """Validate form inputs and return list of errors"""
        errors = []
        
        if not self.input_folder.get().strip():
            errors.append("Input folder is required")
        elif not Path(self.input_folder.get()).exists():
            errors.append("Input folder does not exist")
        
        # Check that at least one file type is selected
        if not any([self.filetype_csv.get(), self.filetype_xlsx.get(), self.filetype_json.get()]):
            errors.append("At least one file type must be selected")
        
        # Validate schema file if provided
        schema_path = self.schema_file.get().strip()
        if schema_path and not Path(schema_path).exists():
            errors.append("Schema file does not exist")
        
        # Validate output file directory if provided
        output_path = self.output_file.get().strip()
        if output_path:
            output_dir = Path(output_path).parent
            if not output_dir.exists():
                errors.append("Output directory does not exist")
        
        return errors
    
    def _build_config(self):
        """Build ProcessingConfig from GUI form values"""
        # Build file type filter
        file_types = []
        if self.filetype_csv.get():
            file_types.append('csv')
        if self.filetype_xlsx.get():
            file_types.append('xlsx')
        if self.filetype_json.get():
            file_types.append('json')
        
        # Convert index mode string to enum
        index_mode = IndexMode.from_string(self.index_mode.get())
        
        # Parse columns if provided
        columns = None
        columns_text = self.columns.get().strip()
        if columns_text:
            columns = [col.strip() for col in columns_text.split(',') if col.strip()]
        
        # Load schema if provided
        schema_map = None
        schema_path = self.schema_file.get().strip()
        if schema_path:
            import json
            try:
                with open(schema_path, 'r') as f:
                    schema_map = json.load(f)
            except Exception as e:
                raise ValueError(f"Could not load schema file: {e}")
        
        config = ProcessingConfig(
            input_folder=self.input_folder.get().strip(),
            output_file=self.output_file.get().strip() or None,
            recursive=self.recursive.get(),
            file_type_filter=file_types,
            schema_map=schema_map,
            to_lower=self.to_lower.get(),
            spaces_to_underscores=self.spaces_to_underscores.get(),
            index_mode=index_mode,
            index_start=self.index_start.get(),
            columns=columns,
            force_in_memory=self.force_in_memory.get()
        )
        
        return config
    
    def _run_processing(self):
        """Start the data processing operation in a separate thread"""
        if self.is_processing:
            return
        
        # Validate form
        errors = self._validate_form()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
        
        try:
            config = self._build_config()
        except Exception as e:
            messagebox.showerror("Configuration Error", f"Error building configuration: {e}")
            return
        
        # Update UI state
        self.is_processing = True
        self.run_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.progress_bar.start()
        self.status_var.set("Processing...")
        
        # Clear results area
        self.results_text.delete(1.0, tk.END)
        
        # Start processing in separate thread
        self.processor = DataProcessor()
        self.processing_thread = threading.Thread(
            target=self._process_data_thread,
            args=(config,),
            daemon=True
        )
        self.processing_thread.start()
    
    def _process_data_thread(self, config):
        """Run data processing in separate thread to avoid blocking GUI"""
        try:
            start_time = time.time()
            
            # Send initial progress update
            self.progress_queue.put(("status", "Starting data processing..."))
            
            # Run the actual processing
            result = self.processor.run(config)
            
            processing_time = time.time() - start_time
            
            # Send completion message
            success_msg = (
                f"Processing completed successfully!\n\n"
                f"Files processed: {result.files_processed}\n"
                f"Total rows: {result.total_rows}\n"
                f"Total columns: {result.total_columns}\n"
                f"Processing time: {processing_time:.2f} seconds\n"
            )
            
            if result.output_file:
                success_msg += f"Output written to: {result.output_file}\n"
            else:
                success_msg += "Results written to console\n"
            
            self.progress_queue.put(("complete", success_msg))
            
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            self.progress_queue.put(("error", error_msg))
    
    def _cancel_processing(self):
        """Cancel the current processing operation"""
        if not self.is_processing:
            return
        
        self.status_var.set("Cancelling...")
        self._processing_finished()
    
    def _processing_finished(self):
        """Clean up after processing is complete"""
        self.is_processing = False
        self.run_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.progress_bar.stop()
        self.processor = None
        self.processing_thread = None
        import gc
        gc.collect()
    
    def _check_progress_queue(self):
        """Check for progress updates from processing thread"""
        try:
            while True:
                message_type, message = self.progress_queue.get_nowait()
                
                if message_type == "status":
                    self.status_var.set(message)
                    self.results_text.insert(tk.END, f"{message}\n")
                    self.results_text.see(tk.END)
                    
                elif message_type == "complete":
                    self.status_var.set("Processing completed successfully")
                    self.results_text.insert(tk.END, f"\n{message}")
                    self.results_text.see(tk.END)
                    self._processing_finished()
                    messagebox.showinfo("Success", "Processing completed successfully!")
                    
                elif message_type == "error":
                    self.status_var.set("Processing failed")
                    self.results_text.insert(tk.END, f"\nERROR: {message}")
                    self.results_text.see(tk.END)
                    self._processing_finished()
                    messagebox.showerror("Error", message)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._check_progress_queue)
    
    def _on_closing(self):
        """Handle window close event"""
        # Stop memory monitoring if active
        if MEMORY_MONITORING_AVAILABLE and hasattr(self, '_stop_memory_monitoring'):
            self._stop_memory_monitoring()
        
        if self.is_processing:
            if messagebox.askokcancel("Quit", "Processing is still running. Do you want to quit anyway?"):
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


def main():
    """Entry point for GUI application"""
    try:
        app = DataPipelineGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Application Error", f"Failed to start application: {e}")


if __name__ == '__main__':
    main()