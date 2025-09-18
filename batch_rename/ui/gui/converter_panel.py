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
        converter_widget = QGroupBox(f"Converter {len(self.converters) + 1}")
        main_layout = QVBoxLayout(converter_widget)
        
        # Header with type selection and remove button
        header_layout = QHBoxLayout()
        
        # Converter type (removed template and stringsmith)
        type_combo = QComboBox()
        type_combo.addItems(['pad_numbers', 'date_format', 'custom'])
        header_layout.addWidget(QLabel("Type:"))
        header_layout.addWidget(type_combo)
        
        header_layout.addStretch()
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_converter(converter_widget))
        header_layout.addWidget(remove_btn)
        
        main_layout.addLayout(header_layout)
        
        # Configuration area that changes based on converter type
        config_area = QWidget()
        config_layout = QFormLayout(config_area)
        main_layout.addWidget(config_area)
        
        # Connect type change to update config area
        type_combo.currentTextChanged.connect(
            lambda converter_type: self.update_converter_config(config_area, config_layout, converter_type)
        )
        
        # Initialize with first converter type
        self.update_converter_config(config_area, config_layout, type_combo.currentText())
        
        self.scroll_layout.addWidget(converter_widget)
        self.converters.append((type_combo, config_area))
    
    def update_converter_config(self, config_area, config_layout, converter_type):
        """Update configuration UI based on selected converter type."""
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
            # Use the reusable custom function selector
            custom_selector = FunctionSelector("converter function", 1)
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
        for type_combo, config_area in self.converters:
            converter_type = type_combo.currentText()
            
            # Extract values from input widgets in config area
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
                        input_format_widget.text().strip() or "%Y%m%d",
                        output_format_widget.text().strip() or "%Y-%m-%d"
                    ]
                    
            elif converter_type == 'custom':
                custom_selector = config_area.findChild(FunctionSelector, "custom_selector", 1)
                
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