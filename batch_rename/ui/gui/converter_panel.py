import sys
from pathlib import Path
from typing import Dict, List

# PyQt imports
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QLineEdit, QPushButton,
    QComboBox, QGroupBox, QSpinBox,
    QScrollArea, QFormLayout
)
# Import our existing core logic
sys.path.append(str(Path(__file__).parent.parent))
from .function_selector import FunctionSelector
from ...core.validators import validate_converter_function

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
        
        self.setLayout(layout)
    
    def add_converter(self):
        """Add a new converter configuration widget."""
        converter_widget = QGroupBox(f"Converter #{len(self.converters) + 1}")
        converter_layout = QVBoxLayout(converter_widget)
        
        # Converter type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        converter_combo = QComboBox()
        converter_combo.addItems(['pad_numbers', 'date_format', 'custom'])
        type_layout.addWidget(converter_combo)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_converter(converter_widget))
        type_layout.addWidget(remove_btn)
        type_layout.addStretch()
        
        converter_layout.addLayout(type_layout)
        
        # Configuration area
        config_area = QWidget()
        config_layout = QFormLayout(config_area)
        converter_layout.addWidget(config_area)
        
        # Connect type change to update config
        converter_combo.currentTextChanged.connect(
            lambda t: self.update_converter_config(t, config_layout)
        )
        
        # Initialize with pad_numbers
        self.update_converter_config('pad_numbers', config_layout)
        
        # Track this converter
        self.converters.append((converter_combo, config_area))
        
        # Add to scroll layout
        self.scroll_layout.addWidget(converter_widget)
    
    def update_converter_config(self, converter_type, config_layout):
        """Update converter configuration UI based on type."""
        # Clear existing config widgets
        for i in reversed(range(config_layout.count())):
            item = config_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                # Handle nested layouts
                nested_layout = item.layout()
                for j in reversed(range(nested_layout.count())):
                    nested_item = nested_layout.itemAt(j)
                    if nested_item.widget():
                        nested_item.widget().setParent(None)
        
        if converter_type == 'pad_numbers':
            # Field name input
            field_input = QLineEdit()
            field_input.setPlaceholderText("e.g., sequence, date, number")
            field_input.setObjectName("field")
            config_layout.addRow("Field:", field_input)
            
            # Width input with spinner
            width_input = QSpinBox()
            width_input.setRange(1, 10)
            width_input.setValue(3)
            width_input.setObjectName("width")
            config_layout.addRow("Width:", width_input)
            
        elif converter_type == 'date_format':
            # Field name input
            field_input = QLineEdit()
            field_input.setPlaceholderText("e.g., date, created_date")
            field_input.setObjectName("field")
            config_layout.addRow("Field:", field_input)
            
            # Input format
            input_format = QLineEdit("%Y%m%d")
            input_format.setObjectName("input_format")
            config_layout.addRow("Input Format:", input_format)
            
            # Output format
            output_format = QLineEdit("%Y-%m-%d")
            output_format.setObjectName("output_format")
            config_layout.addRow("Output Format:", output_format)
            
        elif converter_type == 'custom':
            # Use the reusable custom function selector with CONVERTER validator
            custom_selector = FunctionSelector("converter function", 1, validate_converter_function)
            custom_selector.setObjectName("custom_selector")
            config_layout.addRow("Custom Function:", custom_selector)
    
    def remove_converter(self, widget):
        """Remove a converter widget."""
        widget.setParent(None)
        self.converters = [(combo, config_area) for combo, config_area in self.converters 
                          if combo.parent() != widget]
    
    def get_converter_configs(self) -> List[Dict]:
        """Return list of converter configurations."""
        configs = []
        
        for combo, config_area in self.converters:
            if combo.parent() is None:  # Widget was removed
                continue
                
            converter_type = combo.currentText()
            config_layout = config_area.layout()
            
            pos_args = []
            kwargs = {}
            
            if converter_type == 'pad_numbers':
                field_widget = config_area.findChild(QLineEdit, "field")
                width_widget = config_area.findChild(QSpinBox, "width")
                
                if field_widget and field_widget.text().strip():
                    pos_args = [field_widget.text().strip(), str(width_widget.value())]
                    
            elif converter_type == 'date_format':
                field_widget = config_area.findChild(QLineEdit, "field")
                input_format_widget = config_area.findChild(QLineEdit, "input_format")
                output_format_widget = config_area.findChild(QLineEdit, "output_format")
                
                if field_widget and field_widget.text().strip():
                    pos_args = [
                        field_widget.text().strip(),
                        input_format_widget.text() if input_format_widget else "%Y%m%d",
                        output_format_widget.text() if output_format_widget else "%Y-%m-%d"
                    ]
                    
            elif converter_type == 'custom':
                custom_selector = config_area.findChild(FunctionSelector, "custom_selector")
                
                if custom_selector and custom_selector.is_configured():
                    config = custom_selector.get_config()
                    if config:
                        file_path, function_name, pos_args, kwargs = config
                        
                        configs.append({
                            'name': file_path,  # Use file path as name for custom
                            'positional': [function_name] + pos_args,  # Function name as first arg
                            'keyword': kwargs
                        })
                        continue  # Skip the standard config addition below
            
            # Only add converter if we have valid configuration
            if pos_args:
                configs.append({
                    'name': converter_type,
                    'positional': pos_args,
                    'keyword': kwargs
                })
        
        return configs