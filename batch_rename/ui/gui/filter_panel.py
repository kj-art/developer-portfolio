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
from .custom_function_selector import CustomFunctionSelector

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
        main_layout = QVBoxLayout(filter_widget)
        
        # Header with invert checkbox, type selection, and remove button
        header_layout = QHBoxLayout()
        
        # Invert checkbox
        invert_check = QCheckBox("Exclude")
        header_layout.addWidget(invert_check)
        
        # Filter type
        type_combo = QComboBox()
        type_combo.addItems(['pattern', 'file-type', 'file-size', 'name-length', 'date-modified', 'custom'])
        header_layout.addWidget(QLabel("Type:"))
        header_layout.addWidget(type_combo)
        
        header_layout.addStretch()
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_filter(filter_widget))
        header_layout.addWidget(remove_btn)
        
        main_layout.addLayout(header_layout)
        
        # Configuration area that changes based on filter type
        config_area = QWidget()
        config_layout = QFormLayout(config_area)
        main_layout.addWidget(config_area)
        
        # Connect type change to update config area
        type_combo.currentTextChanged.connect(
            lambda filter_type: self.update_filter_config(config_area, config_layout, filter_type)
        )
        
        # Initialize with first filter type
        self.update_filter_config(config_area, config_layout, type_combo.currentText())
        
        self.scroll_layout.addWidget(filter_widget)
        self.filters.append((invert_check, type_combo, config_area))
    
    def update_filter_config(self, config_area, config_layout, filter_type):
        """Update configuration UI based on selected filter type."""
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
        
        if filter_type == 'pattern':
            # Include pattern
            include_input = QLineEdit()
            include_input.setPlaceholderText("e.g., *.pdf, *_report_*")
            include_input.setObjectName("include")
            config_layout.addRow("Include Pattern:", include_input)
            
            # Exclude pattern (optional)
            exclude_input = QLineEdit()
            exclude_input.setPlaceholderText("e.g., *_backup_*, *_temp_*")
            exclude_input.setObjectName("exclude")
            config_layout.addRow("Exclude Pattern:", exclude_input)
            
        elif filter_type == 'file-type':
            # File types
            types_input = QLineEdit()
            types_input.setPlaceholderText("e.g., pdf,docx,xlsx")
            types_input.setObjectName("types")
            config_layout.addRow("File Types:", types_input)
            
        elif filter_type == 'file-size':
            # Min and max size
            min_size_input = QLineEdit()
            min_size_input.setPlaceholderText("e.g., 1MB, 500KB")
            min_size_input.setObjectName("min_size")
            config_layout.addRow("Min Size:", min_size_input)
            
            max_size_input = QLineEdit()
            max_size_input.setPlaceholderText("e.g., 100MB, 1GB")
            max_size_input.setObjectName("max_size")
            config_layout.addRow("Max Size:", max_size_input)
            
        elif filter_type == 'name-length':
            # Min and max length
            min_length_input = QSpinBox()
            min_length_input.setRange(0, 1000)
            min_length_input.setValue(0)
            min_length_input.setObjectName("min_length")
            config_layout.addRow("Min Length:", min_length_input)
            
            max_length_input = QSpinBox()
            max_length_input.setRange(0, 1000)
            max_length_input.setValue(255)
            max_length_input.setObjectName("max_length")
            config_layout.addRow("Max Length:", max_length_input)
            
        elif filter_type == 'date-modified':
            # Date threshold
            date_input = QLineEdit()
            date_input.setPlaceholderText("e.g., 2024-01-01, '1 week ago'")
            date_input.setObjectName("date_threshold")
            config_layout.addRow("Date Threshold:", date_input)
            
        elif filter_type == 'custom':
            # Use the reusable custom function selector
            custom_selector = CustomFunctionSelector("filter function")
            custom_selector.setObjectName("custom_selector")
            config_layout.addRow("Custom Function:", custom_selector)
    
    def remove_filter(self, widget):
        """Remove a filter widget."""
        widget.setParent(None)
        self.filters = [(invert, combo, config_area) for invert, combo, config_area in self.filters 
                       if combo.parent() != widget]
    
    def get_filter_configs(self) -> List[Dict]:
        """Return list of filter configurations."""
        configs = []
        for invert_check, type_combo, config_area in self.filters:
            filter_type = type_combo.currentText()
            pos_args = []
            
            if filter_type == 'pattern':
                include_widget = config_area.findChild(QLineEdit, "include")
                exclude_widget = config_area.findChild(QLineEdit, "exclude")
                
                if include_widget and include_widget.text().strip():
                    pos_args.append(include_widget.text().strip())
                    
                if exclude_widget and exclude_widget.text().strip():
                    pos_args.append(exclude_widget.text().strip())
                    
            elif filter_type == 'file-type':
                types_widget = config_area.findChild(QLineEdit, "types")
                
                if types_widget and types_widget.text().strip():
                    # Split comma-separated types into individual args
                    types = [t.strip() for t in types_widget.text().split(',') if t.strip()]
                    pos_args.extend(types)
                    
            elif filter_type == 'file-size':
                min_size_widget = config_area.findChild(QLineEdit, "min_size")
                max_size_widget = config_area.findChild(QLineEdit, "max_size")
                
                size_args = []
                if min_size_widget and min_size_widget.text().strip():
                    size_args.append(min_size_widget.text().strip())
                if max_size_widget and max_size_widget.text().strip():
                    size_args.append(max_size_widget.text().strip())
                
                if size_args:
                    pos_args = [','.join(size_args)]  # Pass as single comma-separated string
                    
            elif filter_type == 'name-length':
                min_length_widget = config_area.findChild(QSpinBox, "min_length")
                max_length_widget = config_area.findChild(QSpinBox, "max_length")
                
                if min_length_widget and max_length_widget:
                    pos_args = [f"{min_length_widget.value()},{max_length_widget.value()}"]
                    
            elif filter_type == 'date-modified':
                date_widget = config_area.findChild(QLineEdit, "date_threshold")
                
                if date_widget and date_widget.text().strip():
                    pos_args = [date_widget.text().strip()]
                    
            elif filter_type == 'custom':
                custom_selector = config_area.findChild(CustomFunctionSelector, "custom_selector")
                
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
                    'keyword': {},
                    'inverted': invert_check.isChecked()
                })
        
        return configs