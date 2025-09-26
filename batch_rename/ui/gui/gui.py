"""
Main GUI application for batch rename tool with configuration support.

Provides both traditional step-by-step configuration and config file loading.
"""

import sys
from pathlib import Path
from typing import Optional

# PyQt imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QPushButton, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QProgressBar,
    QStatusBar, QTabWidget, QRadioButton, QCheckBox,
    QStackedWidget, QSplitter, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

# Add the project root to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import our GUI panels
from .panels.extractor import ExtractorPanel
from .panels.converter import ConverterPanel
from .panels.template import TemplatePanel
from .panels.filter import FilterPanel
from .panels.all_in_one import AllInOnePanel
from .panels.config import ConfigPanel

# Import core functionality
from ...core.processor import BatchRenameProcessor
from ...core.config import RenameConfig, RenameResult


class ProcessingThread(QThread):
    """Background thread for file processing."""
    
    finished = pyqtSignal(object)  # RenameResult
    error = pyqtSignal(str)
    
    def __init__(self, processor: BatchRenameProcessor, config: RenameConfig):
        super().__init__()
        self.processor = processor
        self.config = config
    
    def run(self):
        """Run the processing in background thread."""
        try:
            result = self.processor.process(self.config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class BatchRenameGUI(QMainWindow):
    """Main GUI window for batch rename application."""
    
    def __init__(self):
        super().__init__()
        self.input_folder = None
        self.processor = BatchRenameProcessor()
        self.processing_thread = None
        self.current_config = None  # Store loaded config
        self.config_mode = False    # Track if we're in config mode vs manual mode
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Professional Batch Rename Tool")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout with splitter
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - configuration
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - preview
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set initial sizes (40% left, 60% right for preview)
        splitter.setSizes([560, 840])
        main_layout.addWidget(splitter)
        
        # Create status bar
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready - Load a config or select folder to begin")
    
    def create_left_panel(self) -> QWidget:
        """Create the left configuration panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Configuration file management
        self.config_panel = ConfigPanel(
            on_config_loaded=self.on_config_loaded,
            on_config_cleared=self.on_config_cleared
        )
        layout.addWidget(self.config_panel)
        
        # Folder selection
        layout.addWidget(self.create_folder_selection())
        
        # Processing mode selection
        layout.addWidget(self.create_mode_selection())
        
        # Step configuration area
        layout.addWidget(self.create_configuration_area())
        
        # Control buttons
        layout.addWidget(self.create_control_buttons())
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right preview panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Preview area takes full right panel
        layout.addWidget(self.create_preview_area())
        
        return panel
    
    def create_folder_selection(self) -> QWidget:
        """Create folder selection section."""
        group = QGroupBox("Input Folder")
        layout = QVBoxLayout(group)
        
        # Folder path display and browse
        folder_layout = QHBoxLayout()
        
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("QLabel { background-color: white; color: black; padding: 8px; border: 1px solid #cccccc; }")
        self.folder_label.setMinimumHeight(32)
        folder_layout.addWidget(self.folder_label, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        
        layout.addLayout(folder_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self.recursive_checkbox = QCheckBox("Include subdirectories")
        options_layout.addWidget(self.recursive_checkbox)
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        return group
    
    def create_mode_selection(self) -> QWidget:
        """Create processing mode selection."""
        group = QGroupBox("Processing Mode")
        layout = QVBoxLayout(group)
        
        self.modular_radio = QRadioButton("Step-by-step (Extractor + Converters + Template)")
        self.modular_radio.setChecked(True)
        self.modular_radio.toggled.connect(self.on_mode_changed)
        layout.addWidget(self.modular_radio)
        
        self.allinone_radio = QRadioButton("All-in-one function")
        self.allinone_radio.toggled.connect(self.on_mode_changed)
        layout.addWidget(self.allinone_radio)
        
        return group
    
    def create_configuration_area(self) -> QWidget:
        """Create the configuration area with step panels."""
        self.config_stack = QStackedWidget()
        
        # Add both configuration modes
        self.config_stack.addWidget(self.create_modular_config())
        self.config_stack.addWidget(self.create_allinone_config())
        
        return self.config_stack
    
    def create_modular_config(self) -> QWidget:
        """Create modular step-by-step configuration."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create tabs for different step types
        tab_widget = QTabWidget()
        
        # Create panels for each step type
        self.extractor_panel = ExtractorPanel()
        self.converter_panel = ConverterPanel()
        self.template_panel = TemplatePanel()
        self.filter_panel = FilterPanel()
        
        # Add panels as tabs
        tab_widget.addTab(self.extractor_panel, "1. Extract Data")
        tab_widget.addTab(self.converter_panel, "2. Transform Data")
        tab_widget.addTab(self.template_panel, "3. Build Names")
        tab_widget.addTab(self.filter_panel, "4. File Filters")
        
        layout.addWidget(tab_widget)
        return widget
    
    def create_allinone_config(self) -> QWidget:
        """Create all-in-one function configuration."""
        self.allinone_panel = AllInOnePanel()
        return self.allinone_panel
    
    def create_preview_area(self) -> QWidget:
        """Create the preview results area."""
        group = QGroupBox("Preview & Results")
        layout = QVBoxLayout(group)
        
        # Results summary
        self.results_label = QLabel("")
        self.results_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.results_label)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(["Current Name", "New Name"])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setMinimumHeight(400)
        layout.addWidget(self.preview_table)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return group
    
    def create_control_buttons(self) -> QWidget:
        """Create control buttons."""
        group = QGroupBox("Actions")
        layout = QHBoxLayout(group)
        
        self.preview_btn = QPushButton("Preview Changes")
        self.preview_btn.clicked.connect(self.preview_changes)
        self.preview_btn.setEnabled(False)
        self.preview_btn.setMinimumHeight(35)
        layout.addWidget(self.preview_btn)
        
        self.execute_btn = QPushButton("Execute Rename")
        self.execute_btn.clicked.connect(self.execute_rename)
        self.execute_btn.setEnabled(False)
        self.execute_btn.setMinimumHeight(35)
        self.execute_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        layout.addWidget(self.execute_btn)
        
        clear_btn = QPushButton("Clear Preview")
        clear_btn.clicked.connect(self.clear_preview)
        clear_btn.setMinimumHeight(35)
        layout.addWidget(clear_btn)
        
        return group
    
    def on_config_loaded(self, config: RenameConfig):
        """Handle configuration loaded from file."""
        self.current_config = config
        self.config_mode = True
        
        # Only update input folder if user hasn't selected one yet
        if config.input_folder and not self.input_folder:
            self.input_folder = Path(config.input_folder)
            self.folder_label.setText(str(self.input_folder))
        
        self.recursive_checkbox.setChecked(config.recursive)
        
        # Disable manual configuration panels when config is loaded
        self.config_stack.setEnabled(False)
        self.modular_radio.setEnabled(False)
        self.allinone_radio.setEnabled(False)
        
        self.preview_btn.setEnabled(True)
        
        # AUTO-PREVIEW: If we have an input folder, automatically run preview
        if self.input_folder and self.input_folder.exists():
            self.preview_changes()
        
        self.statusbar.showMessage("Configuration loaded - ready to preview")
        
        # Update results info
        self.results_label.setText("✓ Configuration loaded from file. Manual settings disabled.")
        self.results_label.setStyleSheet("color: blue; font-weight: bold; padding: 5px;")
    
    def on_config_cleared(self):
        """Handle configuration cleared."""
        self.current_config = None
        self.config_mode = False
        
        # Re-enable manual configuration
        self.config_stack.setEnabled(True)
        self.modular_radio.setEnabled(True)
        self.allinone_radio.setEnabled(True)
        
        # Clear results
        self.clear_preview()
        self.results_label.setText("")
        self.results_label.setStyleSheet("")
        
        self.statusbar.showMessage("Configuration cleared - configure manually or load config")
    
    def on_mode_changed(self):
        """Handle switching between modular and all-in-one modes."""
        if self.config_mode:
            return  # Don't change modes when config is loaded
            
        if self.modular_radio.isChecked():
            self.config_stack.setCurrentIndex(0)  # Modular config
        else:
            self.config_stack.setCurrentIndex(1)  # All-in-one config
        
        # Clear preview when mode changes
        self.clear_preview()
    
    def browse_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Input Folder", str(Path.home())
        )
        if folder:
            self.input_folder = Path(folder)
            self.folder_label.setText(str(self.input_folder))
            
            # Enable preview if we have either config or manual setup
            if self.config_mode or self.validate_manual_config():
                self.preview_btn.setEnabled(True)
                
            self.statusbar.showMessage(f"Selected folder: {folder}")
    
    def validate_manual_config(self) -> bool:
        """Validate that manual configuration is complete."""
        if self.modular_radio.isChecked():
            # Check if extractor is configured (basic validation)
            try:
                return hasattr(self.extractor_panel, 'get_config')
            except:
                return False
        else:
            # Check if all-in-one is configured
            try:
                return hasattr(self.allinone_panel, 'get_config')
            except:
                return False
    
    def build_config(self, preview_mode: bool = True) -> RenameConfig:
        """Build configuration from current GUI state."""
        if not self.input_folder:
            raise ValueError("Please select an input folder")
        
        if self.config_mode:
            # Use loaded config with GUI overrides
            config = RenameConfig(
                input_folder=self.input_folder,
                extractor=self.current_config.extractor,
                extractor_args=self.current_config.extractor_args,
                converters=self.current_config.converters,
                template=self.current_config.template,
                filters=self.current_config.filters,
                recursive=self.recursive_checkbox.isChecked(),
                preview_mode=preview_mode,
                on_existing_collision=self.current_config.on_existing_collision,
                on_internal_collision=self.current_config.on_internal_collision
            )
        else:
            # Build config from manual GUI settings
            if self.modular_radio.isChecked():
                # For now, create a basic config - panels need to be implemented
                config = RenameConfig(
                    input_folder=self.input_folder,
                    extractor="split",  # Default
                    extractor_args={'positional': ['_', 'name'], 'keyword': {}},
                    converters=[],
                    template=None,
                    filters=[],
                    recursive=self.recursive_checkbox.isChecked(),
                    preview_mode=preview_mode,
                    on_existing_collision='skip',
                    on_internal_collision='skip'
                )
            else:
                # All-in-one mode - also basic for now
                config = RenameConfig(
                    input_folder=self.input_folder,
                    extract_and_convert="basic_rename",
                    recursive=self.recursive_checkbox.isChecked(),
                    preview_mode=preview_mode,
                    on_existing_collision='skip',
                    on_internal_collision='skip'
                )
        
        return config
    
    def preview_changes(self):
        """Preview the rename changes."""
        try:
            config = self.build_config(preview_mode=True)
            self.start_processing(config)
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", str(e))
    
    def execute_rename(self):
        """Execute the actual rename operation."""
        try:
            config = self.build_config(preview_mode=False)
            
            # Confirm execution
            reply = QMessageBox.question(
                self, "Confirm Execution",
                "Are you sure you want to execute the rename operation?\n"
                "This will actually rename files and cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.start_processing(config)
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", str(e))
    
    def start_processing(self, config: RenameConfig):
        """Start background processing."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.preview_btn.setEnabled(False)
        self.execute_btn.setEnabled(False)
        
        # Start processing thread
        self.processing_thread = ProcessingThread(self.processor, config)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.error.connect(self.on_processing_error)
        self.processing_thread.start()
        
        operation = "Previewing" if config.preview_mode else "Executing"
        self.statusbar.showMessage(f"{operation} rename operation...")
    
    def on_processing_finished(self, result: RenameResult):
        """Handle processing completion."""
        self.progress_bar.setVisible(False)
        self.preview_btn.setEnabled(True)
        
        # Always clear table first
        self.preview_table.setRowCount(0)
        
        if result.preview_data:
            self.update_preview_table(result)
            
            # Update results info
            collision_text = f" ({result.collisions} collisions)" if result.collisions > 0 else ""
            status_text = f"Found {result.files_found} files, {len(result.preview_data)} to rename{collision_text}"
            
            self.results_label.setText(status_text)
            
            if result.collisions > 0:
                self.results_label.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
                self.execute_btn.setEnabled(False)
            else:
                self.results_label.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
                self.execute_btn.setEnabled(True)
            
            self.statusbar.showMessage("Preview complete")
        else:
            self.results_label.setText("No files to rename with current configuration")
            self.results_label.setStyleSheet("color: gray; padding: 5px;")
            self.statusbar.showMessage("No changes needed")
            # Clear everything when no results
            self.results_label.setText("No files to rename with current configuration")
            self.results_label.setStyleSheet("color: gray; padding: 5px;")
            self.execute_btn.setEnabled(False)
            self.statusbar.showMessage("No changes needed")
        
        # If this was an execution, show success
        if not self.processing_thread.config.preview_mode:
            QMessageBox.information(
                self, "Success", 
                f"Rename operation completed successfully!\n"
                f"Files renamed: {result.files_renamed}\n"
                f"Errors: {result.errors}"
            )
    
    def on_processing_error(self, error_msg: str):
        """Handle processing error."""
        self.progress_bar.setVisible(False)
        self.preview_btn.setEnabled(True)
        QMessageBox.critical(self, "Processing Error", error_msg)
        self.statusbar.showMessage("Error occurred during processing")
    
    def update_preview_table(self, result: RenameResult):
        """Update the preview table with results."""
        self.preview_table.setRowCount(len(result.preview_data))
        
        for row, item in enumerate(result.preview_data):
            old_name_item = QTableWidgetItem(item['old_name'])
            new_name_item = QTableWidgetItem(item['new_name'])
            
            # Highlight conflicts in red
            if result.collisions > 0:
                new_names = [item['new_name'] for item in result.preview_data]
                if new_names.count(item['new_name']) > 1:
                    new_name_item.setBackground(Qt.GlobalColor.red)
                    new_name_item.setForeground(Qt.GlobalColor.white)
            
            self.preview_table.setItem(row, 0, old_name_item)
            self.preview_table.setItem(row, 1, new_name_item)
        
        # Resize columns to content
        self.preview_table.resizeColumnsToContents()
    
    def clear_preview(self):
        """Clear the preview table."""
        self.preview_table.setRowCount(0)
        self.execute_btn.setEnabled(False)
        self.results_label.setText("")
        self.results_label.setStyleSheet("")
        self.statusbar.showMessage("Preview cleared")


def main():
    """Main entry point for GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Batch Rename Tool")
    
    # Set application font
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)
    
    # Create and show main window
    window = BatchRenameGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()