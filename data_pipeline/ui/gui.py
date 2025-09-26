import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_pipeline.core.processor import DataProcessor
from data_pipeline.core.processing_config import ProcessingConfig, IndexMode
from data_pipeline.core.file_utils import get_files_iterator, normalize_filetype
from shared_utils.logger import set_up_logging, get_logger
from shared_utils.progress import CallbackProgressReporter

try:
    from shared_utils.memory_sparkline_widget import MemorySparklineWidget
    from shared_utils.memory_monitor import MemoryMonitor
    MEMORY_MONITORING_AVAILABLE = True
except ImportError:
    MEMORY_MONITORING_AVAILABLE = False


class ValidationHelper:
    """Enhanced validation with detailed error and warning reporting"""
    
    @staticmethod
    def validate_config_form(form_data: dict) -> tuple[list, list]:
        """
        Validate form configuration and return errors and warnings
        
        Returns:
            Tuple of (errors, warnings) where errors must be fixed before processing
        """
        errors = []
        warnings = []
        
        # Input folder validation
        input_folder = form_data.get('input_folder', '').strip()
        if not input_folder:
            errors.append("Input folder is required")
        elif not Path(input_folder).exists():
            errors.append(f"Input folder does not exist: {input_folder}")
        elif not Path(input_folder).is_dir():
            errors.append(f"Input path is not a directory: {input_folder}")
        else:
            # Check if folder has any processable files
            try:
                files = list(get_files_iterator(input_folder, 
                                              form_data.get('recursive', False),
                                              form_data.get('file_type_filter', [])))
                if not files:
                    warnings.append("No processable files found in input folder")
                elif len(files) > 1000:
                    warnings.append(f"Large number of files detected ({len(files)}). Consider using streaming mode.")
            except Exception as e:
                warnings.append(f"Could not scan input folder: {e}")
        
        # File type validation
        file_types = form_data.get('file_type_filter', [])
        if not file_types:
            errors.append("At least one file type must be selected")
        else:
            try:
                normalize_filetype(file_types)
            except ValueError as e:
                errors.append(str(e))
        
        # Output file validation
        output_file = form_data.get('output_file', '').strip()
        if output_file:
            output_path = Path(output_file)
            if not output_path.parent.exists():
                errors.append(f"Output directory does not exist: {output_path.parent}")
            elif output_path.exists():
                warnings.append(f"Output file exists and will be overwritten: {output_file}")
            
            # Check for reasonable output format
            if output_path.suffix.lower() not in ['.csv', '.xlsx', '.json']:
                warnings.append(f"Unusual output format: {output_path.suffix}")
        
        # Schema file validation
        schema_file = form_data.get('schema_file', '').strip()
        if schema_file:
            schema_path = Path(schema_file)
            if not schema_path.exists():
                errors.append(f"Schema file does not exist: {schema_file}")
            elif schema_path.suffix.lower() != '.json':
                warnings.append("Schema file should typically be a JSON file")
        
        # Columns validation
        columns = form_data.get('columns', '').strip()
        if columns:
            try:
                col_list = [col.strip() for col in columns.split(',') if col.strip()]
                if len(col_list) != len(set(col_list)):
                    warnings.append("Duplicate column names detected")
                if any(' ' in col for col in col_list):
                    warnings.append("Column names contain spaces - they will be converted to underscores")
            except Exception:
                errors.append("Invalid column specification format")
        
        return errors, warnings


class DataPipelineGUI:
    """Enhanced GUI with better progress tracking, validation, and error handling"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Data Processing Pipeline")
        self.root.geometry("800x700")  # Smaller height
        self.root.minsize(600, 500)    # Smaller minimum
        self.root.maxsize(1200, 900)   # Limit maximum horizontal resize
        
        # Configure logging for GUI mode
        set_up_logging(level='INFO', enable_colors=False)
        self.logger = get_logger('data_pipeline.gui')
        
        # Processing state
        self.processing_thread = None
        self.is_processing = False
        self.cancel_requested = False
        self.message_queue = queue.Queue()
        
        # Memory monitoring
        self.memory_monitor = None
        
        # Progress tracking
        self.progress_reporter = None
        
        # Create GUI variables
        self._create_variables()
        
        # Build interface
        self._create_widgets()
        self._setup_bindings()
        
        # Setup memory monitoring if available
        if MEMORY_MONITORING_AVAILABLE:
            self._setup_memory_monitoring()
        
        # Start message processing
        self._process_message_queue()
    
    def _create_variables(self):
        """Create tkinter variables for form binding"""
        self.input_folder = tk.StringVar()
        self.output_file = tk.StringVar()
        self.recursive = tk.BooleanVar()
        self.to_lower = tk.BooleanVar(value=True)
        self.spaces_to_underscores = tk.BooleanVar(value=True)
        self.force_in_memory = tk.BooleanVar()
        
        # File type selection
        self.filetype_csv = tk.BooleanVar(value=True)
        self.filetype_xlsx = tk.BooleanVar(value=True)
        self.filetype_json = tk.BooleanVar(value=True)
        
        # Index options
        self.index_mode = tk.StringVar(value="none")
        self.index_start = tk.IntVar(value=0)
        
        # Columns and schema
        self.columns = tk.StringVar()
        self.schema_file = tk.StringVar()
        
        # Status and progress
        self.progress_var = tk.DoubleVar()
        self.current_operation = tk.StringVar()
    
    def _create_widgets(self):
        """Create GUI widgets with better validation feedback"""
        # Create scrollable main container - with horizontal scaling
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure for horizontal expansion
        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Make the scrollable frame match the canvas width
            canvas_width = event.width
            canvas.itemconfig(canvas_frame_id, width=canvas_width)
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        canvas_frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack with proper expansion
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main container - back to working approach
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        current_row = 0
        
        # Input Section with validation feedback
        input_frame = ttk.LabelFrame(main_frame, text="Input Configuration", padding="8")
        input_frame.pack(fill="x", pady=(0, 8))
        input_frame.columnconfigure(1, weight=1)
        
        # Input folder
        ttk.Label(input_frame, text="Input Folder:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        input_folder_frame = ttk.Frame(input_frame)
        input_folder_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        input_folder_frame.columnconfigure(0, weight=1)
        
        self.input_entry = ttk.Entry(input_folder_frame, textvariable=self.input_folder, width=50)
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(input_folder_frame, text="Browse", command=self._browse_input_folder).grid(row=0, column=1)
        
        # Input validation indicator
        self.input_validation_label = ttk.Label(input_frame, text="", foreground="gray")
        self.input_validation_label.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # File type selection with validation feedback
        ttk.Label(input_frame, text="File Types:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        filetype_frame = ttk.Frame(input_frame)
        filetype_frame.grid(row=2, column=1, sticky=tk.W, pady=(0, 5))
        
        ttk.Checkbutton(filetype_frame, text="CSV", variable=self.filetype_csv, 
                       command=self._validate_file_types).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(filetype_frame, text="Excel", variable=self.filetype_xlsx,
                       command=self._validate_file_types).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Checkbutton(filetype_frame, text="JSON", variable=self.filetype_json,
                       command=self._validate_file_types).grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
        # File type validation indicator
        self.filetype_validation_label = ttk.Label(input_frame, text="", foreground="gray")
        self.filetype_validation_label.grid(row=3, column=1, sticky=tk.W, pady=(0, 5))
        
        # Recursive option with feedback
        recursive_frame = ttk.Frame(input_frame)
        recursive_frame.grid(row=4, column=1, sticky=tk.W, pady=(0, 5))
        
        ttk.Checkbutton(recursive_frame, text="Include subdirectories", 
                       variable=self.recursive, command=self._validate_input_folder).grid(row=0, column=0, sticky=tk.W)
        
        # Output Section
        output_frame = ttk.LabelFrame(main_frame, text="Output Configuration", padding="8")
        output_frame.pack(fill="x", pady=(0, 8))
        output_frame.columnconfigure(1, weight=1)
        
        # Output file
        ttk.Label(output_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        output_file_frame = ttk.Frame(output_frame)
        output_file_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        output_file_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(output_file_frame, textvariable=self.output_file, width=50).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(output_file_frame, text="Browse", command=self._browse_output_file).grid(row=0, column=1)
        
        ttk.Label(output_frame, text="(Leave blank for console output)", 
                 foreground="gray").grid(row=1, column=1, sticky=tk.W, pady=(0, 5))
        
        # Processing and Advanced Options side by side to save vertical space
        options_container = ttk.Frame(main_frame)
        options_container.pack(fill="x", pady=(0, 8))
        options_container.columnconfigure(0, weight=0)  # Processing Options - fixed width
        options_container.columnconfigure(1, weight=1)  # Advanced Options - expands
        
        # Processing Options - left side
        options_frame = ttk.LabelFrame(options_container, text="Processing Options", padding="8")
        options_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 4))
        
        # Column normalization
        ttk.Checkbutton(options_frame, text="Convert column names to lowercase", 
                       variable=self.to_lower).pack(anchor=tk.W, pady=(0, 3))
        
        ttk.Checkbutton(options_frame, text="Convert spaces to underscores in column names", 
                       variable=self.spaces_to_underscores).pack(anchor=tk.W, pady=(0, 3))
        
        # Force in-memory
        ttk.Checkbutton(options_frame, text="Force in-memory processing (disable streaming)", 
                       variable=self.force_in_memory).pack(anchor=tk.W, pady=(0, 8))
        
        # Index mode
        index_frame = ttk.Frame(options_frame)
        index_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(index_frame, text="Index Mode:").pack(anchor=tk.W)
        index_radio_frame = ttk.Frame(index_frame)
        index_radio_frame.pack(anchor=tk.W, pady=(2, 0))
        
        index_modes = [("None", "none"), ("Sequential", "sequential"), ("Reset per file", "reset")]
        for i, (text, value) in enumerate(index_modes):
            ttk.Radiobutton(index_radio_frame, text=text, variable=self.index_mode, 
                           value=value).pack(side=tk.LEFT, padx=(0, 10))
        
        # Index start
        start_frame = ttk.Frame(options_frame)
        start_frame.pack(fill="x")
        ttk.Label(start_frame, text="Index Start:").pack(side=tk.LEFT)
        ttk.Spinbox(start_frame, from_=0, to=999999, textvariable=self.index_start, 
                   width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # Advanced Options - right side
        advanced_frame = ttk.LabelFrame(options_container, text="Advanced Options", padding="8")
        advanced_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(4, 0))
        
        # Expected columns
        ttk.Label(advanced_frame, text="Expected Columns:").pack(anchor=tk.W, pady=(0, 2))
        ttk.Entry(advanced_frame, textvariable=self.columns).pack(fill="x", pady=(0, 2))
        ttk.Label(advanced_frame, text="(Comma-separated list, optional)", 
                 foreground="gray").pack(anchor=tk.W, pady=(0, 8))
        
        # Schema file
        ttk.Label(advanced_frame, text="Schema File:").pack(anchor=tk.W, pady=(0, 2))
        schema_file_frame = ttk.Frame(advanced_frame)
        schema_file_frame.pack(fill="x", pady=(0, 2))
        schema_file_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(schema_file_frame, textvariable=self.schema_file).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(schema_file_frame, text="Browse", command=self._browse_schema_file).grid(row=0, column=1)
        
        # Control buttons - just buttons, no memory monitoring here
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(0, 8))
        
        self.run_button = ttk.Button(button_frame, text="Start Processing", command=self._run_processing)
        self.run_button.grid(row=0, column=0, padx=(0, 5))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self._cancel_processing, state="disabled")
        self.cancel_button.grid(row=0, column=1, padx=(0, 5))
        
        ttk.Button(button_frame, text="Validate Configuration", command=self._validate_configuration).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(button_frame, text="Clear Form", command=self._clear_form).grid(row=0, column=3, padx=(0, 5))
        
        # Progress and results section
        results_frame = ttk.LabelFrame(main_frame, text="Progress & Results", padding="8")
        results_frame.pack(fill="both", expand=True, pady=(0, 8))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(3, weight=1)
        
        # Current operation
        self.current_op_label = ttk.Label(results_frame, textvariable=self.current_operation, foreground="blue")
        self.current_op_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Progress bar with percentage
        progress_frame = ttk.Frame(results_frame)
        progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.progress_percentage = ttk.Label(progress_frame, text="0%", width=6)
        self.progress_percentage.grid(row=0, column=1)
        
        # Memory monitoring - make the text expand instead of the graph
        if MEMORY_MONITORING_AVAILABLE:
            memory_frame = ttk.Frame(results_frame)
            memory_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
            memory_frame.columnconfigure(1, weight=1)  # Memory text expands instead
            
            ttk.Label(memory_frame, text="Memory Usage:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
            
            # Memory status text - now expands to fill available space
            self.memory_status_var = tk.StringVar(value="0 MB - Monitoring system memory usage")
            memory_status_label = ttk.Label(memory_frame, textvariable=self.memory_status_var, anchor="w")
            memory_status_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
            
            # Memory sparkline widget - fixed size on the right
            self.memory_sparkline = MemorySparklineWidget(memory_frame, height=60)
            self.memory_sparkline.grid(row=0, column=2, sticky=tk.E)
        
        # Progress text area
        self.progress_text = scrolledtext.ScrolledText(results_frame, height=8, wrap=tk.WORD)
        self.progress_text.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Remove redundant status bar - current operation label is sufficient
    
    def _setup_memory_monitoring(self):
        """Set up memory monitoring with integrated callbacks"""
        if MEMORY_MONITORING_AVAILABLE:
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
    
    def _setup_bindings(self):
        """Set up event bindings and keyboard shortcuts"""
        self.root.bind('<Control-Return>', lambda e: self._run_processing())
        self.root.bind('<Escape>', lambda e: self._cancel_processing())
        
        # Bind input validation
        self.input_folder.trace('w', lambda *args: self._validate_input_folder())
        self.recursive.trace('w', lambda *args: self._validate_input_folder())
        
        # Initialize validations
        self._validate_file_types()
        self._validate_input_folder()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _validate_file_types(self):
        """Validate file type selection and update UI feedback"""
        if not any([self.filetype_csv.get(), self.filetype_xlsx.get(), self.filetype_json.get()]):
            self.filetype_validation_label.config(text="❌ Select at least one file type", foreground="red")
        else:
            types = []
            if self.filetype_csv.get(): types.append("CSV")
            if self.filetype_xlsx.get(): types.append("Excel") 
            if self.filetype_json.get(): types.append("JSON")
            self.filetype_validation_label.config(text=f"✓ Will process: {', '.join(types)}", foreground="green")
    
    def _validate_input_folder(self):
        """Validate input folder and update UI feedback"""
        folder = self.input_folder.get().strip()
        if not folder:
            self.input_validation_label.config(text="", foreground="gray")
            return
            
        if not Path(folder).exists():
            self.input_validation_label.config(text="❌ Folder does not exist", foreground="red")
        elif not Path(folder).is_dir():
            self.input_validation_label.config(text="❌ Not a directory", foreground="red")
        else:
            try:
                # Get selected file types for accurate count
                file_types = []
                if self.filetype_csv.get(): file_types.append('csv')
                if self.filetype_xlsx.get(): file_types.append('xlsx')
                if self.filetype_json.get(): file_types.append('json')
                
                files = list(get_files_iterator(folder, self.recursive.get(), file_types))
                if files:
                    recursive_text = " (including subdirectories)" if self.recursive.get() else ""
                    self.input_validation_label.config(text=f"✓ {len(files)} files found{recursive_text}", foreground="green")
                else:
                    self.input_validation_label.config(text="⚠️ No processable files found", foreground="orange")
            except Exception:
                self.input_validation_label.config(text="❓ Unable to scan folder", foreground="gray")
    
    def _process_message_queue(self):
        """Process messages from background processing thread"""
        try:
            while True:
                msg_type, content = self.message_queue.get_nowait()
                self._handle_progress_message(msg_type, content)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._process_message_queue)
    
    def _handle_progress_message(self, msg_type: str, content):
        """Handle progress messages from the processing thread"""
        if msg_type == 'progress':
            self.progress_text.insert(tk.END, f"{content}\n")
            self.progress_text.see(tk.END)
        elif msg_type == 'percentage':
            self.progress_var.set(content)
            self.progress_percentage.config(text=f"{content:.1f}%")
        elif msg_type == 'complete':
            self.progress_text.insert(tk.END, f"\n✅ Processing Complete!\n")
            self.progress_text.insert(tk.END, f"Files: {content['files_processed']}\n")
            self.progress_text.insert(tk.END, f"Rows: {content['total_rows']:,}\n")
            self.progress_text.insert(tk.END, f"Time: {content['processing_time']:.2f}s\n")
            self.progress_text.insert(tk.END, f"Rate: {content['rows_per_second']:.0f} rows/sec\n")
            self.progress_text.see(tk.END)
            self._reset_ui_state()
            messagebox.showinfo("Success", "Processing completed successfully!")
        elif msg_type == 'error':
            self.progress_text.insert(tk.END, f"\n❌ ERROR: {content}")
            self.progress_text.see(tk.END)
            self._reset_ui_state()
            messagebox.showerror("Error", content)
    
    def _reset_ui_state(self):
        """Reset UI to ready state"""
        self.is_processing = False
        self.run_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.current_operation.set("")  # Clear current operation instead of setting status
        self.progress_var.set(0)
        self.progress_percentage.config(text="0%")
    
    def _build_config(self):
        """Build ProcessingConfig from form data"""
        file_types = []
        if self.filetype_csv.get(): file_types.append('csv')
        if self.filetype_xlsx.get(): file_types.append('xlsx')
        if self.filetype_json.get(): file_types.append('json')
        
        index_mode = IndexMode.from_string(self.index_mode.get())
        
        columns = None
        columns_text = self.columns.get().strip()
        if columns_text:
            columns = [col.strip() for col in columns_text.split(',') if col.strip()]
        
        schema_map = None
        schema_path = self.schema_file.get().strip()
        if schema_path:
            import json
            with open(schema_path, 'r') as f:
                schema_map = json.load(f)
        
        return ProcessingConfig(
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
    
    def _validate_configuration(self):
        """Show validation results in a dialog"""
        form_data = self._get_form_data()
        errors, warnings = ValidationHelper.validate_config_form(form_data)
        
        # Create validation dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Configuration Validation")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Results text
        result_frame = ttk.Frame(dialog, padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=15)
        result_text.pack(fill=tk.BOTH, expand=True)
        
        # Populate results
        if not errors and not warnings:
            result_text.insert(tk.END, "✅ VALIDATION PASSED\n\n")
            result_text.insert(tk.END, "Configuration looks good! Ready to process data.")
        else:
            if errors:
                result_text.insert(tk.END, "❌ ERRORS (must fix before processing):\n")
                for error in errors:
                    result_text.insert(tk.END, f"  • {error}\n")
                result_text.insert(tk.END, "\n")
            
            if warnings:
                result_text.insert(tk.END, "⚠️ WARNINGS (review recommended):\n")
                for warning in warnings:
                    result_text.insert(tk.END, f"  • {warning}\n")
        
        result_text.config(state=tk.DISABLED)
        
        # OK button
        ttk.Button(dialog, text="OK", command=dialog.destroy).pack(pady=10)
    
    def _get_form_data(self):
        """Extract form data for validation"""
        file_types = []
        if self.filetype_csv.get(): file_types.append('csv')
        if self.filetype_xlsx.get(): file_types.append('xlsx')
        if self.filetype_json.get(): file_types.append('json')
        
        return {
            'input_folder': self.input_folder.get(),
            'output_file': self.output_file.get(),
            'file_type_filter': file_types,
            'recursive': self.recursive.get(),
            'schema_file': self.schema_file.get(),
            'columns': self.columns.get()
        }
    
    def _browse_input_folder(self):
        """Browse for input folder"""
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder.set(folder)
            self._validate_input_folder()
    
    def _browse_output_file(self):
        """Browse for output file"""
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
        """Browse for schema file"""
        filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select Schema File", filetypes=filetypes)
        if filename:
            self.schema_file.set(filename)
    
    def _clear_form(self):
        """Clear all form fields"""
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
        self.progress_text.delete(1.0, tk.END)
        self.current_operation.set("")  # Clear operation status
        self.progress_var.set(0)
        self._validate_input_folder()
        self._validate_file_types()
    
    def _run_processing(self):
        """Start processing with progress tracking"""
        if self.is_processing:
            return
        
        # Validate configuration
        form_data = self._get_form_data()
        errors, warnings = ValidationHelper.validate_config_form(form_data)
        
        if errors:
            error_msg = "Cannot start processing due to errors:\n\n" + "\n".join(f"• {e}" for e in errors)
            messagebox.showerror("Configuration Error", error_msg)
            return
        
        if warnings:
            warning_msg = "Warnings detected:\n\n" + "\n".join(f"• {w}" for w in warnings)
            warning_msg += "\n\nContinue anyway?"
            if not messagebox.askyesno("Warnings Detected", warning_msg):
                return
        
        # Update UI state
        self.is_processing = True
        self.cancel_requested = False
        self.run_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.progress_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        # Create progress reporter with GUI callback
        def progress_callback(msg_type, content):
            self.message_queue.put((msg_type, content))
        
        self.progress_reporter = CallbackProgressReporter(progress_callback)
        
        # Start processing in background thread
        config = self._build_config()
        self.processing_thread = threading.Thread(
            target=self._process_data_background,
            args=(config,),
            daemon=True
        )
        self.processing_thread.start()
    
    def _process_data_background(self, config: ProcessingConfig):
        """Background processing with progress reporting"""
        try:
            self.current_operation.set("Initializing processor...")
            
            # Create processor with progress integration
            processor = DataProcessor()
            
            # Inject progress reporter into processor
            # Note: This requires the processor to support progress reporting
            if hasattr(processor, 'set_progress_reporter'):
                processor.set_progress_reporter(self.progress_reporter)
            
            # Run processing
            result = processor.run(config)
            
            # Report completion
            self.progress_reporter.complete_processing(
                result.total_rows, 
                result.processing_time
            )
            
        except Exception as e:
            self.logger.exception("Processing failed")
            self.message_queue.put(('error', str(e)))
    
    def _cancel_processing(self):
        """Cancel the current processing operation"""
        if self.is_processing:
            self.cancel_requested = True
            self.status_var.set("Cancelling...")
            self.current_operation.set("Cancellation requested...")
            # Note: Actual cancellation requires thread-safe cancellation support in processor
    
    def _on_closing(self):
        """Handle window close"""
        if self.memory_monitor:
            self.memory_monitor.stop_monitoring()
        
        if self.is_processing:
            if messagebox.askokcancel("Quit", "Processing is running. Quit anyway?"):
                self.cancel_requested = True
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


def main():
    """Entry point for GUI"""
    try:
        app = DataPipelineGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Application Error", f"Failed to start application: {e}")


if __name__ == '__main__':
    main()