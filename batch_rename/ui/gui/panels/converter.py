"""
GUI panel for configuring data conversion/transformation.

Uses the ProcessingStep architecture with base class for consistent functionality.
"""

import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any

# PyQt imports
from PyQt6.QtWidgets import QLineEdit, QSpinBox, QComboBox, QFormLayout, QWidget

# Import base classes and core logic
sys.path.append(str(Path(__file__).parent.parent))
from .base import StackableStepPanel
from ....core.steps.base import StepType


class ConverterPanel(StackableStepPanel):
    """Panel for configuring data conversion steps."""
    
    def __init__(self):
        super().__init__(StepType.CONVERTER)
    
    def create_builtin_config(self, function_type: str, layout: QFormLayout):
        """Create configuration UI for built-in converter functions."""
        if function_type == 'pad_numbers':
            self.add_pad_numbers_config(layout)
        elif function_type == 'date_format':
            self.add_date_format_config(layout)
        elif function_type == 'case':
            self.add_case_config(layout)
    
    def add_pad_numbers_config(self, layout: QFormLayout):
        """Add configuration for pad_numbers converter."""
        field_input = QLineEdit()
        field_input.setObjectName("field")
        field_input.setPlaceholderText("Field name to pad")
        layout.addRow("Field:", field_input)
        
        width_input = QSpinBox()
        width_input.setRange(1, 10)
        width_input.setValue(3)
        width_input.setObjectName("width")
        layout.addRow("Width:", width_input)
    
    def add_date_format_config(self, layout: QFormLayout):
        """Add configuration for date_format converter."""
        field_input = QLineEdit()
        field_input.setObjectName("field")
        field_input.setPlaceholderText("Field name with date")
        layout.addRow("Field:", field_input)
        
        input_format = QLineEdit("%Y%m%d")
        input_format.setObjectName("input_format")
        layout.addRow("Input Format:", input_format)
        
        output_format = QLineEdit("%Y-%m-%d")
        output_format.setObjectName("output_format")
        layout.addRow("Output Format:", output_format)
    
    def add_case_config(self, layout: QFormLayout):
        """Add configuration for case converter."""
        field_input = QLineEdit()
        field_input.setObjectName("field")
        field_input.setPlaceholderText("Field name to change case")
        layout.addRow("Field:", field_input)
        
        case_combo = QComboBox()
        case_combo.addItems(['upper', 'lower', 'title', 'capitalize'])
        case_combo.setObjectName("case_type")
        layout.addRow("Case Type:", case_combo)
    
    def extract_builtin_config(self, function_type: str, config_area: QWidget) -> Tuple[List[str], Dict[str, Any]]:
        """Extract configuration for built-in converter functions."""
        pos_args = []
        kwargs = {}
        
        if function_type == 'pad_numbers':
            field_widget = config_area.findChild(QLineEdit, "field")
            width_widget = config_area.findChild(QSpinBox, "width")
            
            if field_widget and width_widget:
                field = field_widget.text().strip()
                width = width_widget.value()
                if field:
                    pos_args = [field, str(width)]
        
        elif function_type == 'date_format':
            field_widget = config_area.findChild(QLineEdit, "field")
            input_widget = config_area.findChild(QLineEdit, "input_format")
            output_widget = config_area.findChild(QLineEdit, "output_format")
            
            if field_widget and input_widget and output_widget:
                field = field_widget.text().strip()
                input_fmt = input_widget.text().strip()
                output_fmt = output_widget.text().strip()
                if field and input_fmt and output_fmt:
                    pos_args = [field, input_fmt, output_fmt]
        
        elif function_type == 'case':
            field_widget = config_area.findChild(QLineEdit, "field")
            case_widget = config_area.findChild(QComboBox, "case_type")
            
            if field_widget and case_widget:
                field = field_widget.text().strip()
                case_type = case_widget.currentText()
                if field:
                    pos_args = [field, case_type]
        
        return pos_args, kwargs
    
    def get_converter_configs(self) -> List[Dict[str, Any]]:
        """Return list of converter configurations."""
        return self.get_configs()