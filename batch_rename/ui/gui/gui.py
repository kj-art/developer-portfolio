"""
PyQt GUI for Batch Rename Tool

Provides a visual interface for the batch file renaming functionality,
wrapping around the existing CLI core logic.
"""

import sys
from pathlib import Path

# PyQt imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QPushButton, QFileDialog,
    QTabWidget, QComboBox, QCheckBox,
    QMessageBox, QStatusBar, QGroupBox,
    QSplitter, QRadioButton,
    QButtonGroup, QFormLayout, QStackedWidget
)
from PyQt6.QtCore import Qt

# Import our existing core logic
sys.path.append(str(Path(__file__).parent.parent))
from ...core.config import RenameConfig
from .converter_panel import ConverterPanel
from .custom_function_selector import CustomFunctionSelector
from .extractor_panel import ExtractorPanel
from .filter_panel import FilterPanel
from .preview_table import PreviewTable
from .processing_thread import ProcessingThread
from .template_panel import TemplatePanel


class BatchRenameGUI(QMainWindow):
    """Main GUI application window."""
    
    def __init__(self):
        super().__init__()
        print("BatchRenameGUI.__init__ called - Version 3.0")  # Debug version check
        self.input_folder = None
        self.processing_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        print("=== STARTING INIT_UI - VERSION 3.0 ===")
        self.setWindowTitle("Batch File Rename Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Folder selection
        print("Creating folder selection")
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Input Folder:"))
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; }")
        folder_layout.addWidget(self.folder_label, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        
        self.recursive_check = QCheckBox("Include Subdirectories")
        folder_layout.addWidget(self.recursive_check)
        
        main_layout.addLayout(folder_layout)
        
        # Mode selection at the top
        print("Creating mode selection")
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Processing Mode:"))
        
        self.mode_group = QButtonGroup()
        self.modular_radio = QRadioButton("Modular Components")
        self.allinone_radio = QRadioButton("All-in-One Script")
        
        # Block signals during initialization to prevent early firing
        self.modular_radio.blockSignals(True)
        self.allinone_radio.blockSignals(True)
        
        print("Setting modular radio checked")
        self.modular_radio.setChecked(True)  # Default to modular
        print("Modular radio checked")
        
        self.mode_group.addButton(self.modular_radio)
        self.mode_group.addButton(self.allinone_radio)
        
        mode_layout.addWidget(self.modular_radio)
        mode_layout.addWidget(self.allinone_radio)
        mode_layout.addStretch()
        
        main_layout.addLayout(mode_layout)

        # Debug: Test if radio button changes are detected
        self.modular_radio.clicked.connect(lambda: print("Modular radio clicked"))
        self.allinone_radio.clicked.connect(lambda: print("All-in-one radio clicked"))

        # Main content area with splitter
        print("Creating main content area")
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Use QStackedWidget for clean mode switching
        self.config_stack = QStackedWidget()
        
        # Create and add both config panels
        print("About to create config panels")
        self.modular_config = self.create_modular_config()
        self.allinone_config = self.create_allinone_config()
        print("Config panels created")
        
        self.config_stack.addWidget(self.modular_config)  # Index 0
        self.config_stack.addWidget(self.allinone_config)  # Index 1
        self.config_stack.setCurrentIndex(0)  # Default to modular
        
        splitter.addWidget(self.config_stack)
        
        # Right panel - Preview
        print("Creating preview panel")
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        preview_layout.addWidget(QLabel("Preview:"))
        self.preview_table = PreviewTable()
        preview_layout.addWidget(self.preview_table)
        
        # Preview and Execute buttons
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Update Preview")
        self.preview_btn.clicked.connect(self.update_preview)
        button_layout.addWidget(self.preview_btn)
        
        self.execute_btn = QPushButton("Execute Rename")
        self.execute_btn.clicked.connect(self.execute_rename)
        self.execute_btn.setEnabled(False)
        button_layout.addWidget(self.execute_btn)
        
        button_layout.addStretch()
        preview_layout.addLayout(button_layout)
        
        splitter.addWidget(preview_widget)
        
        # Set splitter proportions (30% config, 70% preview)
        splitter.setSizes([360, 840])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        print("Creating status bar")
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")
        
        # Connect mode change signals AFTER everything is initialized
        # Unblock signals and connect them
        print("Connecting mode change signals")
        self.modular_radio.blockSignals(False)
        self.allinone_radio.blockSignals(False)
        
        self.modular_radio.toggled.connect(self.on_mode_changed)
        self.allinone_radio.toggled.connect(self.on_mode_changed)
        
        print("GUI initialization complete - signals connected")
    
    def create_modular_config(self):
        """Create the modular configuration tab widget."""
        print("Creating modular config")
        config_panel = QTabWidget()
        
        # Extractor tab
        self.extractor_panel = ExtractorPanel()
        config_panel.addTab(self.extractor_panel, "Extractor")
        
        # Converter tab
        self.converter_panel = ConverterPanel()
        config_panel.addTab(self.converter_panel, "Converters")
        
        # Template tab
        self.template_panel = TemplatePanel()
        config_panel.addTab(self.template_panel, "Template")
        
        # Filter tab
        self.filter_panel = FilterPanel()
        config_panel.addTab(self.filter_panel, "Filters")
        
        print("Modular config created")
        return config_panel
    
    def create_allinone_config(self):
        """Create the all-in-one script configuration panel."""
        print("Creating all-in-one config")
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title_label = QLabel("All-in-One Script Configuration")
        title_label.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Select a Python file and function that handles extraction, conversion, and formatting in one step.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("QLabel { color: #666; }")
        layout.addWidget(desc_label)
        
        # Custom function selector
        self.allinone_selector = CustomFunctionSelector("all-in-one processing function")
        layout.addWidget(self.allinone_selector)
        
        layout.addStretch()
        print("All-in-one config created")
        return panel
        
        file_layout.addLayout(file_select_layout)
        layout.addWidget(file_group)
        
        # Function selection
        func_group = QGroupBox("Function Selection")
        func_layout = QVBoxLayout(func_group)
        
        func_select_layout = QHBoxLayout()
        func_select_layout.addWidget(QLabel("Function:"))
        self.allinone_function_combo = QComboBox()
        self.allinone_function_combo.setEnabled(False)
        self.allinone_function_combo.currentTextChanged.connect(self.on_function_selected)
        func_select_layout.addWidget(self.allinone_function_combo)
        func_select_layout.addStretch()
        func_layout.addLayout(func_select_layout)
        
        # Validation status
        self.validation_label = QLabel("")
        self.validation_label.setWordWrap(True)
        func_layout.addWidget(self.validation_label)
        
        layout.addWidget(func_group)
        
        # Function arguments
        self.args_group = QGroupBox("Function Arguments")
        self.args_layout = QFormLayout(self.args_group)
        self.args_group.setVisible(False)
        layout.addWidget(self.args_group)
        
        layout.addStretch()
        print("All-in-one config created")
        return panel
    
    def on_mode_changed(self, checked):
        """Handle switching between modular and all-in-one modes."""
        print(f"on_mode_changed called: checked={checked}, modular_checked={self.modular_radio.isChecked()}")
        
        # Use QStackedWidget for clean switching
        if hasattr(self, 'config_stack'):
            if self.modular_radio.isChecked():
                self.config_stack.setCurrentIndex(0)  # Modular config
                print("Switched to modular config")
            else:
                self.config_stack.setCurrentIndex(1)  # All-in-one config
                print("Switched to all-in-one config")
        else:
            print("config_stack not ready yet")
    
    def browse_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Input Folder", str(Path.home())
        )
        if folder:
            self.input_folder = Path(folder)
            self.folder_label.setText(str(self.input_folder))
            self.preview_btn.setEnabled(True)
            self.statusbar.showMessage(f"Selected folder: {folder}")
    
    def browse_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Input Folder", str(Path.home())
        )
        if folder:
            self.input_folder = Path(folder)
            self.folder_label.setText(str(self.input_folder))
            self.preview_btn.setEnabled(True)
            self.statusbar.showMessage(f"Selected folder: {folder}")
    
    def update_preview(self):
        """Update the preview table with potential renames."""
        if not self.input_folder:
            QMessageBox.warning(self, "Error", "Please select an input folder first.")
            return
        
        try:
            config = self.build_config(preview_mode=True)
            self.statusbar.showMessage("Updating preview...")
            
            # Run processing in background thread
            self.processing_thread = ProcessingThread(config)
            self.processing_thread.finished.connect(self.on_preview_finished)
            self.processing_thread.error.connect(self.on_processing_error)
            self.processing_thread.start()
            
            self.preview_btn.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", str(e))
    
    def on_preview_finished(self, result):
        """Handle preview processing completion."""
        self.preview_table.update_preview(result.preview_data)
        
        message = f"Preview: {result.files_analyzed} files analyzed, {result.files_to_rename} would be renamed"
        if result.collisions > 0:
            message += f", {result.collisions} conflicts detected"
        
        self.statusbar.showMessage(message)
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(result.files_to_rename > 0)
        
        if result.collisions > 0:
            QMessageBox.warning(self, "Conflicts Detected", 
                              f"Found {result.collisions} naming conflicts. "
                              "Please review the configuration.")
    
    def execute_rename(self):
        """Execute the actual file renames."""
        # Confirm with user
        reply = QMessageBox.question(
            self, "Confirm Rename",
            "Are you sure you want to rename the files?\n"
            "This operation cannot be easily undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                config = self.build_config(preview_mode=False)
                self.statusbar.showMessage("Executing renames...")
                
                # Run processing in background thread
                self.processing_thread = ProcessingThread(config)
                self.processing_thread.finished.connect(self.on_execute_finished)
                self.processing_thread.error.connect(self.on_processing_error)
                self.processing_thread.start()
                
                self.execute_btn.setEnabled(False)
                self.preview_btn.setEnabled(False)
                
            except Exception as e:
                QMessageBox.critical(self, "Configuration Error", str(e))
    
    def on_execute_finished(self, result):
        """Handle execution completion."""
        message = f"Execution complete: {result.files_renamed} files renamed"
        if result.errors > 0:
            message += f", {result.errors} errors"
        
        self.statusbar.showMessage(message)
        
        if result.errors > 0:
            QMessageBox.warning(self, "Execution Complete", 
                              f"Renamed {result.files_renamed} files with {result.errors} errors.")
        else:
            QMessageBox.information(self, "Success", 
                                  f"Successfully renamed {result.files_renamed} files.")
        
        # Re-enable buttons and clear preview
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(False)
        self.preview_table.setRowCount(0)
    
    def on_processing_error(self, error_msg):
        """Handle processing errors."""
        self.statusbar.showMessage("Error occurred")
        QMessageBox.critical(self, "Processing Error", error_msg)
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(False)
    
    def build_config(self, preview_mode=True) -> RenameConfig:
        """Build RenameConfig from GUI settings."""
        if not self.input_folder:
            raise ValueError("No input folder selected")
        
        if self.modular_radio.isChecked():
            # Modular mode - use existing logic
            return self.build_modular_config(preview_mode)
        else:
            # All-in-one mode
            return self.build_allinone_config(preview_mode)
    
    def build_modular_config(self, preview_mode=True) -> RenameConfig:
        """Build config for modular mode."""
        # Get extractor configuration
        extractor_name, pos_args, kwargs = self.extractor_panel.get_extractor_config()
        extractor_args = {
            'positional': pos_args,
            'keyword': kwargs
        }
        
        # Get converter configurations
        converters = self.converter_panel.get_converter_configs()
        
        # Get template configuration and add to converters if enabled
        template_config = self.template_panel.get_template_config()
        if template_config:
            converters.append(template_config)
        
        # Require at least one converter (including template)
        if not converters:
            raise ValueError("At least one converter or template is required")
        
        # Get filter configurations
        filters = self.filter_panel.get_filter_configs()
        
        return RenameConfig(
            input_folder=self.input_folder,
            extractor=extractor_name,
            extractor_args=extractor_args,
            converters=converters,
            filters=filters,
            recursive=self.recursive_check.isChecked(),
            preview_mode=preview_mode
        )
        """Build config for all-in-one mode."""
        if not self.allinone_selector.is_configured():
            raise ValueError("All-in-one script function must be selected")
        
        config = self.allinone_selector.get_config()
        if config is None:
            raise ValueError("All-in-one script is not properly configured")
        
        file_path, function_name, pos_args, kwargs = config
        
        # For all-in-one mode, we use a special extractor that calls the custom function
        # The custom function will handle extraction, conversion, and formatting
        return RenameConfig(
            input_folder=self.input_folder,
            extractor=file_path,  # Use file path as extractor
            extractor_args={
                'positional': [function_name] + pos_args,  # Function name as first arg
                'keyword': kwargs  # Additional function arguments
            },
            converters=[],  # No separate converters needed
            filters=[],  # No filters in all-in-one mode for now
            recursive=self.recursive_check.isChecked(),
            preview_mode=preview_mode
        )


def main():
    """Main entry point for GUI application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Batch File Rename Tool")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = BatchRenameGUI()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())