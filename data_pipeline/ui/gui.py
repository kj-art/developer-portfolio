import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_pipeline.core.processor import DataProcessor
from data_pipeline.core.processing_config import ProcessingConfig, IndexMode
from shared_utils.logger import set_up_logging, get_logger

try:
    from shared_utils.memory_sparkline_widget import MemorySparklineWidget
    from shared_utils.memory_monitor import MemoryMonitor
    from shared_utils.background_task_manager import BackgroundTaskManager
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
        
        # Initialize task manager
        self.task_manager = BackgroundTaskManager(
            status_callback=self._update_status,
            progress_callback=self._update_progress,
            completion_callback=self._handle_completion,
            error_callback=self._handle_error,
            scheduler_callback=self.root.after
        )
        
        # Memory monitoring
        self.memory_monitor = None
        
        # Create GUI variables for form binding
        self._create_variables()
        
        # Build the interface
        self._create_widgets()
        self._set_up_bindings()
        
        # Setup memory monitoring if available
        if MEMORY_MONITORING_AVAILABLE:
            self._set_up_memory_monitoring()
    
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
        self.results_text = scrolledtext.ScrolledText(results_frame, height=8, wrap=tk.WORD)
        self.results_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        current_row += 1
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def _set_up_memory_monitoring(self):
        """Set up memory monitoring with integrated callbacks"""
        # Create memory monitor with GUI integration
        self.memory_monitor = MemoryMonitor(
            update_interval_ms=1000,
            status_callback=self.memory_status_var.set,
            scheduler_callback=self.root.after
        )
        
        # Connect to sparkline widget
        if hasattr(self, 'memory_sparkline'):
            self.memory_monitor.set_sparkline_widget(self.memory_sparkline)
        
        # Start monitoring
        self.memory_monitor.start_monitoring()
    
    def _set_up_bindings(self):
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
        
        # Create a variable to track selected file type
        file_type_var = tk.StringVar()
        
        filename = filedialog.asksaveasfilename(
            title="Select Output File", 
            filetypes=filetypes,
            typevariable=file_type_var
        )
        
        if filename:
            # Check if extension is missing and add based on selected type
            if not Path(filename).suffix:
                selected_type = file_type_var.get()
                if "CSV" in selected_type:
                    filename += ".csv"
                elif "Excel" in selected_type:
                    filename += ".xlsx"
                elif "JSON" in selected_type:
                    filename += ".json"
            
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
        """Start the data processing operation using task manager"""
        if self.task_manager.is_running():
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
        self.run_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.progress_bar.start()
        
        # Clear results area
        self.results_text.delete(1.0, tk.END)
        
        # Start processing using task manager
        success = self.task_manager.run_task(self._process_data_task, config)
        if not success:
            messagebox.showerror("Task Error", "Could not start processing task")
            self._reset_ui_state()
    
    def _process_data_task(self, config, progress_reporter=None):
        """Data processing task function for BackgroundTaskManager"""
        processor = DataProcessor()
        result = processor.run(config)
        
        # Build completion message
        completion_msg = (
            f"Processing completed successfully!\n\n"
            f"Files processed: {result.files_processed}\n"
            f"Total rows: {result.total_rows}\n"
            f"Total columns: {result.total_columns}\n"
            f"Processing time: {result.processing_time:.2f} seconds\n"
        )
        
        if result.output_file:
            completion_msg += f"Output written to: {result.output_file}\n"
        else:
            completion_msg += "Results written to console\n"
        
        return completion_msg
    
    def _cancel_processing(self):
        """Cancel the current processing operation"""
        if not self.task_manager.is_running():
            return
        
        self.task_manager.cancel_task()
        self._reset_ui_state()
    
    def _reset_ui_state(self):
        """Reset UI to ready state"""
        self.run_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.progress_bar.stop()
        self.status_var.set("Ready")
    
    def _update_status(self, status_text):
        """Callback for task manager status updates"""
        self.status_var.set(status_text)
    
    def _update_progress(self, progress_text):
        """Callback for task manager progress updates"""
        self.results_text.insert(tk.END, f"{progress_text}\n")
        self.results_text.see(tk.END)
    
    def _handle_completion(self, completion_text):
        """Callback for task completion"""
        self.results_text.insert(tk.END, f"\n{completion_text}")
        self.results_text.see(tk.END)
        self._reset_ui_state()
        messagebox.showinfo("Success", "Processing completed successfully!")
    
    def _handle_error(self, error_text):
        """Callback for task errors"""
        self.results_text.insert(tk.END, f"\nERROR: {error_text}")
        self.results_text.see(tk.END)
        self._reset_ui_state()
        messagebox.showerror("Error", error_text)
    
    def _on_closing(self):
        """Handle window close event"""
        # Stop memory monitoring if active
        if self.memory_monitor:
            self.memory_monitor.stop_monitoring()
        
        if self.task_manager.is_running():
            if messagebox.askokcancel("Quit", "Processing is still running. Do you want to quit anyway?"):
                self.task_manager.cancel_task()
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

#   python -m data_pipeline.ui.gui