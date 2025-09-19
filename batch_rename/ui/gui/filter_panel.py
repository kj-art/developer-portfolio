import sys
from pathlib import Path
from typing import Dict, List

# PyQt imports
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox,
    QGroupBox, QSpinBox,
    QScrollArea, QFormLayout
)

# Import our existing core logic
sys.path.append(str(Path(__file__).parent.parent))
from .function_selector import FunctionSelector
from ...core.validators import validate_filter_function

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
        filter_widget = QGroupBox(f"Filter #{len(self.filters) + 1}")
        filter_layout = QVBoxLayout(filter_widget)
        
        # Filter type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        filter_combo = QComboBox()
        filter_combo.addItems(['pattern', 'file-type', 'file-size', 'name-length', 'custom'])
        type_layout.addWidget(filter_combo)
        
        # Invert checkbox
        invert_check = QCheckBox("Invert (exclude matches)")
        type_layout.addWidget(invert_check)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_filter(filter_widget))
        type_layout.addWidget(remove_btn)
        type_layout.addStretch()
        
        filter_layout.addLayout(type_layout)
        
        # Configuration area
        config_area = QWidget()
        config_layout = QFormLayout(config_area)
        filter_layout.addWidget(config_area)
        
        # Connect type change to update config
        filter_combo.currentTextChanged.connect(
            lambda t: self.update_filter_config(t, config_layout)
        )
        
        # Initialize with pattern filter
        self.update_filter_config('pattern', config_layout)
        
        # Track this filter
        self.filters.append((filter_combo, config_area, invert_check))
        
        # Add to scroll layout
        self.scroll_layout.addWidget(filter_widget)
    
    def update_filter_config(self, filter_type, config_layout):
        """Update filter configuration UI based on type."""
        # Clear existing config widgets
        for i in reversed(range(config_layout.count())):
            item = config_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        if filter_type == 'pattern':
            pattern_input = QLineEdit()
            pattern_input.setPlaceholderText("*.pdf, report_*, IMG_????.jpg")
            pattern_input.setObjectName("pattern")
            config_layout.addRow("Pattern:", pattern_input)
            
        elif filter_type == 'file-type':
            extension_input = QLineEdit()
            extension_input.setPlaceholderText(".pdf, .docx, .txt")
            extension_input.setObjectName("extension")
            config_layout.addRow("Extensions:", extension_input)
            
        elif filter_type == 'file-size':
            min_size = QSpinBox()
            min_size.setRange(0, 999999)
            min_size.setSuffix(" KB")
            min_size.setObjectName("min_size")
            config_layout.addRow("Min Size:", min_size)
            
            max_size = QSpinBox()
            max_size.setRange(0, 999999)
            max_size.setValue(10000)
            max_size.setSuffix(" KB") 
            max_size.setObjectName("max_size")
            config_layout.addRow("Max Size:", max_size)
            
        elif filter_type == 'name-length':
            min_length = QSpinBox()
            min_length.setRange(1, 255)
            min_length.setValue(3)
            min_length.setObjectName("min_length")
            config_layout.addRow("Min Length:", min_length)
            
            max_length = QSpinBox()
            max_length.setRange(1, 255)
            max_length.setValue(50)
            max_length.setObjectName("max_length")
            config_layout.addRow("Max Length:", max_length)
            
        elif filter_type == 'custom':
            # Use the reusable custom function selector with FILTER validator
            custom_selector = FunctionSelector("filter function", 1, validate_filter_function)
            custom_selector.setObjectName("custom_selector")
            config_layout.addRow("Custom Function:", custom_selector)
    
    def remove_filter(self, widget):
        """Remove a filter widget."""
        widget.setParent(None)
        self.filters = [(combo, config_area, invert_check) for combo, config_area, invert_check in self.filters 
                       if combo.parent() != widget]
    
    def get_filter_configs(self) -> List[Dict]:
        """Return list of filter configurations."""
        configs = []
        
        for combo, config_area, invert_check in self.filters:
            if combo.parent() is None:  # Widget was removed
                continue
                
            filter_type = combo.currentText()
            config_layout = config_area.layout()
            
            pos_args = []
            kwargs = {}
            
            if filter_type == 'pattern':
                pattern_widget = config_area.findChild(QLineEdit, "pattern")
                if pattern_widget and pattern_widget.text().strip():
                    pos_args = [pattern_widget.text().strip()]
                    
            elif filter_type == 'file-type':
                extension_widget = config_area.findChild(QLineEdit, "extension")
                if extension_widget and extension_widget.text().strip():
                    # Split extensions by comma and clean them
                    extensions = [ext.strip() for ext in extension_widget.text().split(',')]
                    pos_args = extensions
                    
            elif filter_type == 'file-size':
                min_widget = config_area.findChild(QSpinBox, "min_size")
                max_widget = config_area.findChild(QSpinBox, "max_size")
                if min_widget and max_widget:
                    pos_args = [str(min_widget.value() * 1024), str(max_widget.value() * 1024)]  # Convert KB to bytes
                    
            elif filter_type == 'name-length':
                min_widget = config_area.findChild(QSpinBox, "min_length")
                max_widget = config_area.findChild(QSpinBox, "max_length")
                if min_widget and max_widget:
                    pos_args = [str(min_widget.value()), str(max_widget.value())]
                    
            elif filter_type == 'custom':
                custom_selector = config_area.findChild(FunctionSelector, "custom_selector")
                
                if custom_selector and custom_selector.is_configured():
                    config = custom_selector.get_config()
                    if config:
                        file_path, function_name, pos_args, kwargs = config
                        
                        configs.append({
                            'name': file_path,  # Use file path as name for custom
                            'positional': [function_name] + pos_args,  # Function name as first arg
                            'keyword': kwargs,
                            'inverted': invert_check.isChecked()
                        })
                        continue  # Skip the standard config addition below
            
            # Only add filter if we have valid configuration
            if pos_args:
                configs.append({
                    'name': filter_type,
                    'positional': pos_args,
                    'keyword': kwargs,
                    'inverted': invert_check.isChecked()
                })
        
        return configs