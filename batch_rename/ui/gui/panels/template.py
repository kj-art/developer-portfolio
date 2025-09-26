"""
GUI panel for configuring final filename formatting templates.

Uses the ProcessingStep architecture with base class for consistent functionality.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# PyQt imports
from PyQt6.QtWidgets import (
    QVBoxLayout, QLineEdit, QLabel, QCheckBox,
    QFormLayout, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt

# Import base classes and core logic
sys.path.append(str(Path(__file__).parent.parent))
from .base import SingleStepPanel
from ....core.steps.base import StepType


class TemplatePanel(SingleStepPanel):
    """Panel for configuring filename formatting templates."""
    
    def __init__(self):
        super().__init__(StepType.TEMPLATE)
        self.enable_template = None
        self.template_group = None
    
    def create_config_area(self) -> QWidget:
        """Create configuration area with enable/disable functionality."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title_label = QLabel("Filename Template Configuration")
        title_label.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        layout.addWidget(title_label)
        
        # Enable template checkbox
        self.enable_template = QCheckBox("Use template for filename formatting")
        self.enable_template.stateChanged.connect(self.on_template_enabled)
        layout.addWidget(self.enable_template)
        
        # Template configuration group
        self.template_group = QGroupBox("Template Configuration")
        self.template_group.setEnabled(False)
        template_layout = QVBoxLayout(self.template_group)
        
        # Add description
        description = self.get_panel_description()
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("QLabel { color: #666; margin-bottom: 10px; }")
            template_layout.addWidget(desc_label)
        
        # Create function selector within the group
        self.function_combo, self.config_area, self.custom_selector = self.create_function_selector_layout(template_layout)
        
        # Setup connections
        self.setup_function_type_connection(self.function_combo, self.config_area, self.custom_selector)
        
        layout.addWidget(self.template_group)
        layout.addStretch()
        return widget
    
    def get_panel_description(self) -> Optional[str]:
        """Return panel description."""
        return "Format final filename from extracted and converted data fields."
    
    def on_template_enabled(self, state: int):
        """Handle template enable/disable."""
        enabled = state == Qt.CheckState.Checked.value
        self.template_group.setEnabled(enabled)
    
    def create_builtin_config(self, function_type: str, layout: QFormLayout):
        """Create configuration UI for built-in template functions."""
        if function_type == 'template':
            self.add_template_config(layout)
        elif function_type == 'stringsmith':
            self.add_stringsmith_config(layout)
        elif function_type == 'join':
            self.add_join_config(layout)
    
    def add_template_config(self, layout: QFormLayout):
        """Add configuration for Python template formatter."""
        template_input = QLineEdit()
        template_input.setObjectName("template_string")
        template_input.setPlaceholderText("{dept}_{type}_{date}")
        layout.addRow("Template:", template_input)
        
        help_label = QLabel("Use {fieldname} for extracted field values")
        help_label.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        layout.addRow("", help_label)
    
    def add_stringsmith_config(self, layout: QFormLayout):
        """Add configuration for StringSmith template formatter."""
        template_input = QLineEdit()
        template_input.setObjectName("stringsmith_template")
        template_input.setPlaceholderText("{dept|upper}_{sequence:03d}_{date}")
        layout.addRow("StringSmith Template:", template_input)
        
        help_label = QLabel("Use {field|transform} and {field:format} syntax")
        help_label.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        layout.addRow("", help_label)
    
    def add_join_config(self, layout: QFormLayout):
        """Add configuration for simple join formatter."""
        separator_input = QLineEdit("_")
        separator_input.setObjectName("separator")
        separator_input.setPlaceholderText("Character to join fields")
        layout.addRow("Separator:", separator_input)
        
        fields_input = QLineEdit("dept,type,date")
        fields_input.setObjectName("field_order")
        fields_input.setPlaceholderText("Field names in order, comma-separated")
        layout.addRow("Field Order:", fields_input)
    
    def extract_builtin_config(self, function_type: str, config_area: QWidget) -> Tuple[List[str], Dict[str, Any]]:
        """Extract configuration for built-in template functions."""
        pos_args = []
        kwargs = {}
        
        if function_type == 'template':
            template_widget = config_area.findChild(QLineEdit, "template_string")
            if template_widget:
                template_str = template_widget.text().strip()
                if template_str:
                    pos_args = [template_str]
        
        elif function_type == 'stringsmith':
            template_widget = config_area.findChild(QLineEdit, "stringsmith_template")
            if template_widget:
                template_str = template_widget.text().strip()
                if template_str:
                    pos_args = [template_str]
        
        elif function_type == 'join':
            separator_widget = config_area.findChild(QLineEdit, "separator")
            fields_widget = config_area.findChild(QLineEdit, "field_order")
            
            if separator_widget and fields_widget:
                separator = separator_widget.text().strip()
                fields_text = fields_widget.text().strip()
                
                if separator and fields_text:
                    field_names = [f.strip() for f in fields_text.split(',')]
                    pos_args = [separator] + field_names
        
        return pos_args, kwargs
    
    def get_template_config(self) -> Optional[Dict[str, Any]]:
        """
        Get current template configuration.
        
        Returns:
            Template config dict or None if template is disabled
        """
        if not self.enable_template.isChecked():
            return None
        
        return self.get_config()