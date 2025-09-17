"""
PyQt GUI for Batch Rename Tool

Provides a visual interface for the batch file renaming functionality,
wrapping around the existing CLI core logic.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# PyQt imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QTableWidget,
    QTableWidgetItem, QTabWidget, QComboBox, QCheckBox, QTextEdit,
    QMessageBox, QProgressBar, QStatusBar, QGroupBox, QSpinBox,
    QSplitter, QHeaderView, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

# Import our existing core logic
sys.path.append(str(Path(__file__).parent.parent))
from core.processor import BatchRenameProcessor
from core.config import RenameConfig
from core.extractors import BUILTIN_EXTRACTORS
from core.converters import BUILTIN_CONVERTERS
from core.filters import BUILTIN_FILTERS


class ProcessingThread(QThread):
    """Background thread for processing files to avoid GUI freezing."""
    
    finished = pyqtSignal(object)  # Emits RenameResult
    error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, config: RenameConfig):
        super().__init__()
        self.config = config
    
    def run(self):
        """Execute the batch rename operation in background."""
        try:
            processor = BatchRenameProcessor()
            result = processor.process(self.config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ExtractorPanel(QWidget):
    """Panel for configuring file name extraction."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Extractor type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Extractor Type:"))
        self.extractor_combo = QComboBox()
        self.extractor_combo.addItems(['split', 'regex', 'position', 'metadata'])
        self.extractor_combo.currentTextChanged.connect(self.on_extractor_changed)
        type_layout.addWidget(self.extractor_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # Configuration area that changes based on extractor type
        self.config_area = QWidget()
        self.config_layout = QVBoxLayout(self.config_area)
        layout.addWidget(self.config_area)
        
        # Initialize with split extractor
        self.on_extractor_changed('split')
        
        layout.addStretch()
        self.setLayout(layout)
    
    def on_extractor_changed(self, extractor_type):
        """Update configuration UI based on selected extractor."""
        # Clear existing config widgets
        for i in reversed(range(self.config_layout.count())):
            self.config_layout.itemAt(i).widget().setParent(None)
        
        if extractor_type == 'split':
            self.config_layout.addWidget(QLabel("Split Character:"))
            self.split_char = QLineEdit("_")
            self.config_layout.addWidget(self.split_char)
            
            self.config_layout.addWidget(QLabel("Field Names (comma-separated):"))
            self.field_names = QLineEdit("dept,type,date")
            self.config_layout.addWidget(self.field_names)
            
        elif extractor_type == 'regex':
            self.config_layout.addWidget(QLabel("Regex Pattern (use named groups):"))
            self.regex_pattern = QLineEdit(r"(?P<dept>\w+)_(?P<type>\w+)_(?P<date>\d+)")
            self.config_layout.addWidget(self.regex_pattern)
            
        elif extractor_type == 'position':
            self.config_layout.addWidget(QLabel("Position Mappings:"))
            self.config_layout.addWidget(QLabel("Format: start-end:fieldname,start-end:fieldname"))
            self.position_map = QLineEdit("0-2:dept,3-5:code,6-:type")
            self.config_layout.addWidget(self.position_map)
            
        elif extractor_type == 'metadata':
            self.config_layout.addWidget(QLabel("Metadata Fields:"))
            self.created_date = QCheckBox("Creation Date")
            self.modified_date = QCheckBox("Modified Date")
            self.file_size = QCheckBox("File Size")
            self.config_layout.addWidget(self.created_date)
            self.config_layout.addWidget(self.modified_date)
            self.config_layout.addWidget(self.file_size)
    
    def get_extractor_config(self) -> tuple:
        """Return (extractor_name, positional_args, keyword_args)."""
        extractor_type = self.extractor_combo.currentText()
        
        if extractor_type == 'split':
            pos_args = [self.split_char.text()]
            pos_args.extend(self.field_names.text().split(','))
            return extractor_type, pos_args, {}
            
        elif extractor_type == 'regex':
            return extractor_type, [self.regex_pattern.text()], {}
            
        elif extractor_type == 'position':
            return extractor_type, [self.position_map.text()], {}
            
        elif extractor_type == 'metadata':
            fields = []
            if self.created_date.isChecked():
                fields.append("created")
            if self.modified_date.isChecked():
                fields.append("modified")
            if self.file_size.isChecked():
                fields.append("size")
            return extractor_type, fields, {}


class ConverterPanel(QWidget):
    """Panel for configuring data conversion."""
    
    def __init__(self):
        super().__init__()
        self.converters = []  # List of converter configurations
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Add converter button
        add_button = QPushButton("Add Converter")
        add_button.clicked.connect(self.add_converter)
        layout.addWidget(add_button)
        
        # Scroll area for converters
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        # Add initial template converter
        self.add_converter()
        
        self.setLayout(layout)
    
    def add_converter(self):
        """Add a new converter configuration widget."""
        converter_widget = QGroupBox(f"Converter {len(self.converters) + 1}")
        layout = QHBoxLayout(converter_widget)
        
        # Converter type
        type_combo = QComboBox()
        type_combo.addItems(['template', 'pad_numbers', 'date_format', 'stringsmith'])
        layout.addWidget(type_combo)
        
        # Configuration input
        config_input = QLineEdit()
        type_combo.currentTextChanged.connect(
            lambda text: self.update_converter_placeholder(config_input, text)
        )
        layout.addWidget(config_input)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_converter(converter_widget))
        layout.addWidget(remove_btn)
        
        # Set initial placeholder
        self.update_converter_placeholder(config_input, type_combo.currentText())
        
        self.scroll_layout.addWidget(converter_widget)
        self.converters.append((type_combo, config_input))
    
    def update_converter_placeholder(self, input_widget, converter_type):
        """Update placeholder text based on converter type."""
        placeholders = {
            'template': '"{dept}_{type}_{date}"',
            'pad_numbers': 'field,width (e.g., date,4)',
            'date_format': 'field,input_format,output_format',
            'stringsmith': '"{{;dept;}}{{_;type;}}{{_;date;}}"'
        }
        input_widget.setPlaceholderText(placeholders.get(converter_type, ''))
    
    def remove_converter(self, widget):
        """Remove a converter widget."""
        widget.setParent(None)
        self.converters = [(combo, input) for combo, input in self.converters 
                          if combo.parent() != widget]
    
    def get_converter_configs(self) -> List[Dict]:
        """Return list of converter configurations."""
        configs = []
        for type_combo, config_input in self.converters:
            if config_input.text().strip():
                converter_type = type_combo.currentText()
                args_text = config_input.text().strip()
                
                # Parse arguments (simple comma split for now)
                if args_text:
                    pos_args = [arg.strip().strip('"') for arg in args_text.split(',')]
                else:
                    pos_args = []
                
                configs.append({
                    'name': converter_type,
                    'positional': pos_args,
                    'keyword': {}
                })
        return configs


class FilterPanel(QWidget):
    """Panel for configuring file filters."""
    
    def __init__(self):
        super().__init__()
        self.filters = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Add filter button
        add_button = QPushButton("Add Filter")
        add_button.clicked.connect(self.add_filter)
        layout.addWidget(add_button)
        
        # Scroll area for filters
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
    
    def add_filter(self):
        """Add a new filter configuration widget."""
        filter_widget = QGroupBox(f"Filter {len(self.filters) + 1}")
        layout = QHBoxLayout(filter_widget)
        
        # Invert checkbox
        invert_check = QCheckBox("Exclude")
        layout.addWidget(invert_check)
        
        # Filter type
        type_combo = QComboBox()
        type_combo.addItems(['pattern', 'file-type', 'file-size', 'name-length', 'date-modified'])
        layout.addWidget(type_combo)
        
        # Configuration input
        config_input = QLineEdit()
        type_combo.currentTextChanged.connect(
            lambda text: self.update_filter_placeholder(config_input, text)
        )
        layout.addWidget(config_input)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_filter(filter_widget))
        layout.addWidget(remove_btn)
        
        # Set initial placeholder
        self.update_filter_placeholder(config_input, type_combo.currentText())
        
        self.scroll_layout.addWidget(filter_widget)
        self.filters.append((invert_check, type_combo, config_input))
    
    def update_filter_placeholder(self, input_widget, filter_type):
        """Update placeholder text based on filter type."""
        placeholders = {
            'pattern': '*.pdf (or *.pdf,*_backup_*)',
            'file-type': 'pdf,docx,xlsx',
            'file-size': '1MB,100MB (min,max)',
            'name-length': '5,50 (min,max)',
            'date-modified': '2024-01-01 (or "1 week ago")'
        }
        input_widget.setPlaceholderText(placeholders.get(filter_type, ''))
    
    def remove_filter(self, widget):
        """Remove a filter widget."""
        widget.setParent(None)
        self.filters = [(invert, combo, input) for invert, combo, input in self.filters 
                       if combo.parent() != widget]
    
    def get_filter_configs(self) -> List[Dict]:
        """Return list of filter configurations."""
        configs = []
        for invert_check, type_combo, config_input in self.filters:
            if config_input.text().strip():
                filter_type = type_combo.currentText()
                args_text = config_input.text().strip()
                
                # Parse arguments
                pos_args = [arg.strip() for arg in args_text.split(',') if arg.strip()]
                
                configs.append({
                    'name': filter_type,
                    'positional': pos_args,
                    'keyword': {},
                    'inverted': invert_check.isChecked()
                })
        return configs


class PreviewTable(QTableWidget):
    """Table showing file rename preview."""
    
    def __init__(self):
        super().__init__()
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Current Name", "New Name"])
        
        # Make columns stretch to fill width
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Make read-only
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
    def update_preview(self, preview_data: List[Dict]):
        """Update table with preview data."""
        # Filter to only show files that would change
        changes = [entry for entry in preview_data 
                  if entry['old_name'] != entry['new_name']]
        
        self.setRowCount(len(changes))
        
        for row, entry in enumerate(changes):
            old_item = QTableWidgetItem(entry['old_name'])
            new_item = QTableWidgetItem(entry['new_name'])
            
            self.setItem(row, 0, old_item)
            self.setItem(row, 1, new_item)
        
        if len(changes) == 0:
            self.setRowCount(1)
            no_changes_item = QTableWidgetItem("No files would be renamed")
            no_changes_item.setBackground(Qt.GlobalColor.lightGray)
            self.setItem(0, 0, no_changes_item)
            self.setItem(0, 1, QTableWidgetItem(""))


class BatchRenameGUI(QMainWindow):
    """Main GUI application window."""
    
    def __init__(self):
        super().__init__()
        self.input_folder = None
        self.processing_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Batch File Rename Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Folder selection
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
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Configuration
        config_panel = QTabWidget()
        
        # Extractor tab
        self.extractor_panel = ExtractorPanel()
        config_panel.addTab(self.extractor_panel, "Extractor")
        
        # Converter tab
        self.converter_panel = ConverterPanel()
        config_panel.addTab(self.converter_panel, "Converters")
        
        # Filter tab
        self.filter_panel = FilterPanel()
        config_panel.addTab(self.filter_panel, "Filters")
        
        splitter.addWidget(config_panel)
        
        # Right panel - Preview
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
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")
    
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
        
        # Get extractor configuration
        extractor_name, pos_args, kwargs = self.extractor_panel.get_extractor_config()
        extractor_args = {
            'positional': pos_args,
            'keyword': kwargs
        }
        
        # Get converter configurations
        converters = self.converter_panel.get_converter_configs()
        if not converters:
            raise ValueError("At least one converter is required")
        
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