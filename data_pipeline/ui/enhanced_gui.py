# data_pipeline/ui/enhanced_gui.py

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
from data_pipeline.core.file_utils import get_files_iterator, normalize_filetype
from shared_utils.logger import set_up_logging, get_logger

try:
    from shared_utils.memory_sparkline_widget import MemorySparklineWidget
    from shared_utils.memory_monitor import MemoryMonitor
    MEMORY_MONITORING_AVAILABLE = True
except ImportError:
    MEMORY_MONITORING_AVAILABLE = False


class ProgressReporter:
    """Enhanced progress reporter for detailed file processing updates"""
    
    def __init__(self, gui_callback):
        self.gui_callback = gui_callback
        self.current_file = None
        self.files_processed = 0
        self.total_files = 0
        self.current_rows = 0
        self.total_rows = 0
        
    def start_processing(self, total_files):
        """Initialize progress tracking"""
        self.total_files = total_files
        self.files_processed = 0
        self.current_rows = 0
        self.total_rows = 0
        self.gui_callback('progress', f"Starting processing of {total_files} files...")
        
    def start_file(self, filename):
        """Report starting processing of a new file"""
        self.current_file = filename
        self.files_processed += 1
        progress_msg = f"Processing file {self.files_processed}/{self.total_files}: {filename}"
        self.gui_callback('progress', progress_msg)
        
    def update_rows(self, rows_in_chunk, estimated_total=None):
        """Update row processing progress"""
        self.current_rows += rows_in_chunk
        if estimated_total:
            self.total_rows = estimated_total
            percentage = (self.current_rows / self.total_rows) * 100
            progress_msg = f"  └─ Processed {self.current_rows:,} of ~{self.total_rows:,} rows ({percentage:.1f}%)"
        else:
            progress_msg = f"  └─ Processed {self.current_rows:,} rows"
        self.gui_callback('progress', progress_msg)
        
    def complete_file(self, rows_processed):
        """Report completion of current file"""
        progress_msg = f"  ✓ Completed: {rows_processed:,} rows processed"
        self.gui_callback('progress', progress_msg)
        
    def complete_processing(self, total_rows, processing_time):
        """Report completion of all processing"""
        progress_msg = f"\n✅ Processing complete: {self.files_processed} files, {total_rows:,} total rows in {processing_time:.2f}s"
        self.gui_callback('progress', progress_msg)


class ValidationHelper:
    """Helper class for form validation with detailed error reporting"""
    
    @staticmethod
    def validate_config_form(form_data):
        """Validate form data and return detailed error information"""
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
            # Check for valid files
            try:
                file_types = form_data.get('file_type_filter', ['csv', 'xlsx', 'json'])
                files = list(get_files_iterator(input_folder, 
                                              form_data.get('recursive', False), 
                                              file_types))
                if not files:
                    warnings.append(f"No {', '.join(file_types)} files found in input folder")
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


class EnhancedDataPipelineGUI:
    """Enhanced GUI with better progress tracking, validation, and error handling"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Data Processing Pipeline - Enhanced")
        self.root.geometry("900x800")
        self.root.minsize(700, 600)
        
        # Configure logging for GUI mode
        set_up_logging(level='INFO', enable_colors=False)
        self.logger = get_logger('data_pipeline.enhanced_gui')
        
        # Processing state
        self.processing_thread = None
        self.is_processing = False
        self.cancel_requested = False
        self.message_queue = queue.Queue()
        
        # Memory monitoring
        self.memory_monitor = None
        
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
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar()
        self.current_operation = tk.StringVar()
    
    def _create_widgets(self):
        """Create enhanced GUI widgets with better validation feedback"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        current_row = 0
        
        # Input Section with validation feedback
        input_frame = ttk.LabelFrame(main_frame, text="Input Configuration", padding="10")
        input_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="Input Folder:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.input_folder_entry = ttk.Entry(input_frame, textvariable=self.input_folder)
        self.input_folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.input_folder_entry.bind('<FocusOut>', self._validate_input_folder)
        ttk.Button(input_frame, text="Browse...", command=self._browse_input_folder).grid(row=0, column=2)
        
        # Validation feedback for input folder
        self.input_validation_label = ttk.Label(input_frame, text="", foreground="red", font=("TkDefaultFont", 8))
        self.input_validation_label.grid(row=1, column=0, columnspan=3, sticky=tk.W)
        
        ttk.Checkbutton(input_frame, text="Search subdirectories recursively", 
                       variable=self.recursive, command=self._validate_input_folder).grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # File type selection with file count display
        filetype_frame = ttk.Frame(input_frame)
        filetype_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(filetype_frame, text="File Types:").grid(row=0, column=0, sticky=tk.W)
        self.csv_check = ttk.Checkbutton(filetype_frame, text="CSV", variable=self.filetype_csv, command=self._validate_input_folder)
        self.csv_check.grid(row=0, column=1, padx=(10, 0))
        self.xlsx_check = ttk.Checkbutton(filetype_frame, text="Excel", variable=self.filetype_xlsx, command=self._validate_input_folder)
        self.xlsx_check.grid(row=0, column=2, padx=(10, 0))
        self.json_check = ttk.Checkbutton(filetype_frame, text="JSON", variable=self.filetype_json, command=self._validate_input_folder)
        self.json_check.grid(row=0, column=3, padx=(10, 0))
        
        # File count display
        self.file_count_label = ttk.Label(filetype_frame, text="", foreground="blue", font=("TkDefaultFont", 8))
        self.file_count_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        current_row += 1
        
        # Processing Options
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding="10")
        options_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(options_frame, text="Convert column names to lowercase", 
                       variable=self.to_lower).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Checkbutton(options_frame, text="Convert spaces to underscores in column names", 
                       variable=self.spaces_to_underscores).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        ttk.Checkbutton(options_frame, text="Force in-memory processing", 
                       variable=self.force_in_memory).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Schema and columns configuration
        schema_frame = ttk.Frame(options_frame)
        schema_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        schema_frame.columnconfigure(1, weight=1)
        
        ttk.Label(schema_frame, text="Schema File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(schema_frame, textvariable=self.schema_file).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(schema_frame, text="Browse...", command=self._browse_schema_file).grid(row=0, column=2)
        
        ttk.Label(schema_frame, text="Expected Columns:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        ttk.Entry(schema_frame, textvariable=self.columns).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(10, 0))
        
        current_row += 1
        
        # Index Configuration
        index_frame = ttk.LabelFrame(main_frame, text="Index Configuration", padding="10")
        index_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(index_frame, text="Index Mode:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        index_combo = ttk.Combobox(index_frame, textvariable=self.index_mode, 
                                  values=["none", "local", "sequential"], state="readonly", width=15)
        index_combo.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(index_frame, text="Start Value:").grid(row=0, column=2, sticky=tk.W, padx=(20, 10))
        ttk.Spinbox(index_frame, textvariable=self.index_start, from_=0, to=999999, width=10).grid(row=0, column=3, sticky=tk.W)
        
        current_row += 1
        
        # Output Section
        output_frame = ttk.LabelFrame(main_frame, text="Output Configuration", padding="10")
        output_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(output_frame, textvariable=self.output_file).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(output_frame, text="Browse...", command=self._browse_output_file).grid(row=0, column=2)
        
        current_row += 1
        
        # Control Buttons with enhanced state management
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=current_row, column=0, columnspan=2, pady=(0, 10))
        
        self.run_button = ttk.Button(button_frame, text="Run Processing", command=self._run_processing)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self._cancel_processing, state="disabled")
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.validate_button = ttk.Button(button_frame, text="Validate Config", command=self._validate_full_config)
        self.validate_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear All", command=self._clear_form).pack(side=tk.LEFT)
        
        current_row += 1
        
        # Memory Monitor Section
        if MEMORY_MONITORING_AVAILABLE:
            memory_frame = ttk.LabelFrame(main_frame, text="Memory Monitor", padding="10")
            memory_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
            memory_frame.columnconfigure(0, weight=1)
            
            self.memory_sparkline = MemorySparklineWidget(memory_frame, width=450, height=60)
            self.memory_sparkline.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
            
            self.memory_status_var = tk.StringVar(value="Initializing memory monitor...")
            ttk.Label(memory_frame, textvariable=self.memory_status_var, font=('Consolas', 9)).grid(row=1, column=0, sticky=tk.W)
            
            current_row += 1
        
        # Enhanced Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Processing Progress", padding="10")
        progress_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(current_row, weight=1)
        
        # Current operation display
        ttk.Label(progress_frame, text="Current Operation:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.operation_label = ttk.Label(progress_frame, textvariable=self.current_operation, font=('TkDefaultFont', 9, 'bold'))
        self.operation_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=(0, 5))
        
        # Progress bar with percentage
        progress_container = ttk.Frame(progress_frame)
        progress_container.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_container.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(progress_container, variable=self.progress_var, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.progress_percentage = ttk.Label(progress_container, text="0%")
        self.progress_percentage.grid(row=0, column=1)
        
        # Detailed progress log
        self.progress_text = scrolledtext.ScrolledText(progress_frame, height=10, wrap=tk.WORD)
        self.progress_text.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        current_row += 1
        
        # Status bar
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def _setup_bindings(self):
        """Setup event bindings"""
        self.root.bind('<Control-Return>', lambda e: self._run_processing())
        self.root.bind('<Escape>', lambda e: self._cancel_processing())
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_memory_monitoring(self):
        """Setup memory monitoring"""
        self.memory_monitor = MemoryMonitor(
            update_interval_ms=1000,
            status_callback=self.memory_status_var.set,
            scheduler_callback=self.root.after
        )
        self.memory_monitor.set_sparkline_widget(self.memory_sparkline)
        self.memory_monitor.start_monitoring()
    
    def _validate_input_folder(self, event=None):
        """Real-time validation of input folder"""
        input_path = self.input_folder.get().strip()
        
        if not input_path:
            self.input_validation_label.config(text="")
            self.file_count_label.config(text="")
            return
        
        if not Path(input_path).exists():
            self.input_validation_label.config(text="⚠️ Folder does not exist", foreground="red")
            self.file_count_label.config(text="")
            return
        
        if not Path(input_path).is_dir():
            self.input_validation_label.config(text="⚠️ Path is not a directory", foreground="red")
            self.file_count_label.config(text="")
            return
        
        # Count files
        try:
            file_types = []
            if self.filetype_csv.get(): file_types.append('csv')
            if self.filetype_xlsx.get(): file_types.append('xlsx')
            if self.filetype_json.get(): file_types.append('json')
            
            if not file_types:
                self.file_count_label.config(text="No file types selected")
                return
            
            files = list(get_files_iterator(input_path, self.recursive.get(), file_types))
            
            if files:
                self.input_validation_label.config(text="✓ Valid folder", foreground="green")
                count_text = f"Found {len(files)} {', '.join(file_types)} file(s)"
                if len(files) > 100:
                    count_text += " (large dataset - streaming recommended)"
                self.file_count_label.config(text=count_text, foreground="blue")
            else:
                self.input_validation_label.config(text="⚠️ No matching files found", foreground="orange")
                self.file_count_label.config(text="")
                
        except Exception as e:
            self.input_validation_label.config(text=f"⚠️ Error scanning folder: {e}", foreground="red")
            self.file_count_label.config(text="")
    
    def _validate_full_config(self):
        """Full configuration validation with detailed feedback"""
        form_data = self._get_form_data()
        errors, warnings = ValidationHelper.validate_config_form(form_data)
        
        # Create validation dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Configuration Validation")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create text widget for results
        text_frame = ttk.Frame(dialog, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        result_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
        result_text.pack(fill=tk.BOTH, expand=True)
        
        # Display results
        if not errors and not warnings:
            result_text.insert(tk.END, "✅ Configuration is valid!\n\n")
            result_text.insert(tk.END, "All settings look good. Ready to process data.")
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
        self.status_var.set("Ready")
        self.current_operation.set("")
        self.progress_var.set(0)
        self._validate_input_folder()
    
    def _run_processing(self):
        """Start processing with enhanced progress tracking"""
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
            if not messagebox.askyesno("Configuration Warnings", warning_msg):
                return
        
        try:
            config = self._build_config()
        except Exception as e:
            messagebox.showerror("Configuration Error", f"Error building configuration: {e}")
            return
        
        # Update UI state
        self.is_processing = True
        self.cancel_requested = False
        self.run_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.progress_text.delete(1.0, tk.END)
        self.current_operation.set("Initializing...")
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._processing_worker,
            args=(config,),
            daemon=True
        )
        self.processing_thread.start()
    
    def _processing_worker(self, config):
        """Worker thread for data processing with enhanced progress reporting"""
        try:
            # Create progress reporter
            progress_reporter = ProgressReporter(self._queue_message)
            
            # Count total files first
            files = list(get_files_iterator(config.input_folder, config.recursive, config.file_type_filter))
            progress_reporter.start_processing(len(files))
            
            # Start processing
            self._queue_message('status', 'Processing files...')
            self._queue_message('operation', 'Schema Detection')
            
            processor = DataProcessor()
            
            # Create a custom processor that reports progress
            result = processor.run(config)
            
            progress_reporter.complete_processing(result.total_rows, result.processing_time)
            
            # Final status
            completion_msg = (
                f"✅ Processing completed successfully!\n\n"
                f"Files processed: {result.files_processed}\n"
                f"Total rows: {result.total_rows:,}\n"
                f"Total columns: {result.total_columns}\n"
                f"Processing time: {result.processing_time:.2f} seconds\n"
            )
            
            if result.output_file:
                completion_msg += f"Output saved to: {result.output_file}"
            
            self._queue_message('complete', completion_msg)
            
        except Exception as e:
            self._queue_message('error', f"Processing failed: {str(e)}")
    
    def _cancel_processing(self):
        """Cancel processing operation"""
        if not self.is_processing:
            return
        
        self.cancel_requested = True
        self._queue_message('status', 'Cancelling...')
        self._queue_message('operation', 'Cancelling')
        
        # Note: This is a basic cancellation - in a full implementation,
        # you'd need to interrupt the pandas operations more gracefully
        self._reset_ui_state()
    
    def _queue_message(self, msg_type, content):
        """Queue message for GUI thread"""
        self.message_queue.put({'type': msg_type, 'content': content})
    
    def _process_message_queue(self):
        """Process messages from worker thread"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                self._handle_message(message)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._process_message_queue)
    
    def _handle_message(self, message):
        """Handle message from worker thread"""
        msg_type = message['type']
        content = message['content']
        
        if msg_type == 'status':
            self.status_var.set(content)
        elif msg_type == 'operation':
            self.current_operation.set(content)
        elif msg_type == 'progress':
            self.progress_text.insert(tk.END, f"{content}\n")
            self.progress_text.see(tk.END)
        elif msg_type == 'complete':
            self.progress_text.insert(tk.END, f"\n{content}")
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
        self.current_operation.set("")
        self.progress_var.set(0)
        self.progress_percentage.config(text="0%")
        self.status_var.set("Ready")
    
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
    """Entry point for enhanced GUI"""
    try:
        app = EnhancedDataPipelineGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Application Error", f"Failed to start application: {e}")


if __name__ == '__main__':
    main()