import sys
from pathlib import Path

# PyQt imports
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QLineEdit,
    QComboBox, QCheckBox
)

# Import our existing core logic
sys.path.append(str(Path(__file__).parent.parent))
from .function_selector import FunctionSelector
from .validators import batch_rename_validator

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
        self.extractor_combo.addItems(['split', 'regex', 'position', 'metadata', 'custom'])
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
            
        elif extractor_type == 'custom':
            # Use the reusable custom function selector
            self.custom_selector = FunctionSelector("extractor function", 1, batch_rename_validator)
            self.config_layout.addWidget(self.custom_selector)
    
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
            
        elif extractor_type == 'custom':
            if not hasattr(self, 'custom_selector') or not self.custom_selector.is_configured():
                raise ValueError("Custom extractor requires a valid function selection")
            
            config = self.custom_selector.get_config()
            if config is None:
                raise ValueError("Custom extractor is not properly configured")
            
            file_path, function_name, pos_args, kwargs = config
            # For custom extractors, we pass the function name as a positional arg
            custom_pos_args = [function_name] + pos_args
            return file_path, custom_pos_args, kwargs