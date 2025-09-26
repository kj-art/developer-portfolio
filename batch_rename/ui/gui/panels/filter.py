"""
GUI panel for configuring file filtering.

Uses the ProcessingStep architecture with base class for consistent functionality.
"""

import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any

# PyQt imports
from PyQt6.QtWidgets import (
    QLineEdit, QSpinBox, QComboBox, QCheckBox,
    QFormLayout, QWidget, QHBoxLayout
)

# Import base classes and core logic
sys.path.append(str(Path(__file__).parent.parent))
from .base import StackableStepPanel
from ....core.steps.base import StepType


class FilterPanel(StackableStepPanel):
    """Panel for configuring file filters."""
    
    def __init__(self):
        super().__init__(StepType.FILTER)
    
    def create_extra_controls(self, layout: QHBoxLayout) -> Tuple[QCheckBox]:
        """Create invert checkbox for filters."""
        invert_check = QCheckBox("Invert (exclude matches)")
        layout.addWidget(invert_check)
        return (invert_check,)
    
    def create_builtin_config(self, function_type: str, layout: QFormLayout):
        """Create configuration UI for built-in filter functions."""
        if function_type == 'pattern':
            self.add_pattern_config(layout)
        elif function_type == 'file-type':
            self.add_file_type_config(layout)
        elif function_type == 'file-size':
            self.add_file_size_config(layout)
        elif function_type == 'name-length':
            self.add_name_length_config(layout)
        elif function_type == 'date-modified':
            self.add_date_modified_config(layout)
    
    def add_pattern_config(self, layout: QFormLayout):
        """Add configuration for pattern filter."""
        pattern_input = QLineEdit()
        pattern_input.setObjectName("pattern")
        pattern_input.setPlaceholderText("*.pdf, report_*, IMG_????.jpg")
        layout.addRow("Pattern:", pattern_input)
    
    def add_file_type_config(self, layout: QFormLayout):
        """Add configuration for file-type filter."""
        extensions_input = QLineEdit()
        extensions_input.setObjectName("extensions")
        extensions_input.setPlaceholderText("pdf,docx,txt")
        layout.addRow("Extensions:", extensions_input)
    
    def add_file_size_config(self, layout: QFormLayout):
        """Add configuration for file-size filter."""
        min_size = QSpinBox()
        min_size.setRange(0, 999999)
        min_size.setSuffix(" KB")
        min_size.setObjectName("min_size")
        layout.addRow("Min Size:", min_size)
        
        max_size = QSpinBox()
        max_size.setRange(0, 999999)
        max_size.setValue(10000)
        max_size.setSuffix(" KB")
        max_size.setObjectName("max_size")
        layout.addRow("Max Size:", max_size)
    
    def add_name_length_config(self, layout: QFormLayout):
        """Add configuration for name-length filter."""
        min_length = QSpinBox()
        min_length.setRange(1, 255)
        min_length.setValue(1)
        min_length.setObjectName("min_length")
        layout.addRow("Min Length:", min_length)
        
        max_length = QSpinBox()
        max_length.setRange(1, 255)
        max_length.setValue(50)
        max_length.setObjectName("max_length")
        layout.addRow("Max Length:", max_length)
    
    def add_date_modified_config(self, layout: QFormLayout):
        """Add configuration for date-modified filter."""
        operator_combo = QComboBox()
        operator_combo.addItems(['>', '<', '>=', '<=', '=='])
        operator_combo.setObjectName("operator")
        layout.addRow("Operator:", operator_combo)
        
        date_input = QLineEdit()
        date_input.setObjectName("date")
        date_input.setPlaceholderText("YYYY-MM-DD")
        layout.addRow("Date:", date_input)
    
    def extract_builtin_config(self, function_type: str, config_area: QWidget) -> Tuple[List[str], Dict[str, Any]]:
        """Extract configuration for built-in filter functions."""
        pos_args = []
        kwargs = {}
        
        if function_type == 'pattern':
            pattern_widget = config_area.findChild(QLineEdit, "pattern")
            if pattern_widget:
                pattern = pattern_widget.text().strip()
                if pattern:
                    pos_args = [pattern]
        
        elif function_type == 'file-type':
            extensions_widget = config_area.findChild(QLineEdit, "extensions")
            if extensions_widget:
                extensions_text = extensions_widget.text().strip()
                if extensions_text:
                    extensions = [ext.strip() for ext in extensions_text.split(',')]
                    pos_args = extensions
        
        elif function_type == 'file-size':
            min_widget = config_area.findChild(QSpinBox, "min_size")
            max_widget = config_area.findChild(QSpinBox, "max_size")
            if min_widget and max_widget:
                min_size_bytes = min_widget.value() * 1024
                max_size_bytes = max_widget.value() * 1024
                pos_args = [str(min_size_bytes), str(max_size_bytes)]
        
        elif function_type == 'name-length':
            min_widget = config_area.findChild(QSpinBox, "min_length")
            max_widget = config_area.findChild(QSpinBox, "max_length")
            if min_widget and max_widget:
                pos_args = [str(min_widget.value()), str(max_widget.value())]
        
        elif function_type == 'date-modified':
            operator_widget = config_area.findChild(QComboBox, "operator")
            date_widget = config_area.findChild(QLineEdit, "date")
            if operator_widget and date_widget:
                operator = operator_widget.currentText()
                date_str = date_widget.text().strip()
                if date_str:
                    pos_args = [operator, date_str]
        
        return pos_args, kwargs
    
    def extract_extra_config(self, instance: Tuple) -> Dict[str, Any]:
        """Extract invert setting from filter instance."""
        if len(instance) > 3:  # Has invert checkbox
            invert_check = instance[3]
            return {'inverted': invert_check.isChecked()}
        return {}
    
    def get_filter_configs(self) -> List[Dict[str, Any]]:
        """Return list of filter configurations."""
        return self.get_configs()