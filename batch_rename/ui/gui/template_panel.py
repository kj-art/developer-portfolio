"""
Template Panel for GUI

Enhanced panel supporting built-in templates (template, stringsmith) and custom template functions.
Ensures only one template can be active at a time.
"""

import sys
from pathlib import Path
from typing import Dict, Optional

# PyQt imports
from PyQt6.QtWidgets import (
    QVBoxLayout, QWidget, QLabel, QLineEdit,
    QCheckBox, QGroupBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt

# Import our existing core logic and GUI components
sys.path.append(str(Path(__file__).parent.parent))
from .function_selector import FunctionSelector
from ...core.validators import validate_template_function


class TemplatePanel(QWidget):
    """Panel for configuring output template (optional, mutually exclusive options)."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Enable template checkbox
        self.enable_template = QCheckBox("Enable Template Formatting")
        self.enable_template.stateChanged.connect(self.on_template_enabled)
        layout.addWidget(self.enable_template)
        
        # Template configuration area
        self.config_area = QWidget()
        self.config_layout = QVBoxLayout(self.config_area)
        
        # Template type selection (radio buttons for mutual exclusion)
        type_group = QGroupBox("Template Type")
        type_layout = QVBoxLayout(type_group)
        
        self.template_group = QButtonGroup()
        self.template_radio = QRadioButton("Standard Template")
        self.stringsmith_radio = QRadioButton("StringSmith Template")
        self.custom_radio = QRadioButton("Custom Template Function")
        self.template_radio.setChecked(True)  # Default to standard template
        
        self.template_group.addButton(self.template_radio)
        self.template_group.addButton(self.stringsmith_radio)
        self.template_group.addButton(self.custom_radio)
        
        type_layout.addWidget(self.template_radio)
        type_layout.addWidget(self.stringsmith_radio)
        type_layout.addWidget(self.custom_radio)
        
        self.config_layout.addWidget(type_group)
        
        # Built-in template configuration
        self.builtin_config = QGroupBox("Template Configuration")
        builtin_layout = QVBoxLayout(self.builtin_config)
        
        self.template_input = QLineEdit()
        self.template_input.setPlaceholderText('"{dept}_{type}_{date}"')
        builtin_layout.addWidget(QLabel("Template Pattern:"))
        builtin_layout.addWidget(self.template_input)
        
        # Help text that changes based on selected type
        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        self.help_label.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        builtin_layout.addWidget(self.help_label)
        
        self.config_layout.addWidget(self.builtin_config)
        
        # Custom template configuration
        self.custom_config = QGroupBox("Custom Template Function")
        custom_layout = QVBoxLayout(self.custom_config)
        
        # Description for custom templates
        custom_desc = QLabel(
            "Custom template functions take a ProcessingContext and return "
            "{'formatted_name': 'new_filename'} for final formatting."
        )
        custom_desc.setWordWrap(True)
        custom_desc.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        custom_layout.addWidget(custom_desc)
        
        self.custom_selector = FunctionSelector("template function", 1, validate_template_function)
        custom_layout.addWidget(self.custom_selector)
        
        self.config_layout.addWidget(self.custom_config)
        self.custom_config.setVisible(False)  # Initially hidden
        
        # Connect radio button changes to update UI and help text
        self.template_radio.toggled.connect(self.on_template_type_changed)
        self.stringsmith_radio.toggled.connect(self.on_template_type_changed)
        self.custom_radio.toggled.connect(self.on_template_type_changed)
        
        # Set initial help text
        self.update_help_text()
        
        layout.addWidget(self.config_area)
        layout.addStretch()
        
        # Initially disable the config area
        self.config_area.setEnabled(False)
        
        self.setLayout(layout)
    
    def on_template_enabled(self, state):
        """Enable/disable template configuration based on checkbox."""
        self.config_area.setEnabled(state == Qt.CheckState.Checked.value)
    
    def on_template_type_changed(self):
        """Handle template type change - show appropriate configuration area."""
        if self.custom_radio.isChecked():
            self.builtin_config.setVisible(False)
            self.custom_config.setVisible(True)
        else:
            self.builtin_config.setVisible(True)
            self.custom_config.setVisible(False)
            self.update_help_text()
    
    def update_help_text(self):
        """Update help text based on selected template type."""
        if self.template_radio.isChecked():
            self.help_label.setText(
                "Standard Template: Use {field_name} syntax. "
                "Example: \"{dept}_{type}_{date}\" → \"sales_report_20240315\""
            )
            self.template_input.setPlaceholderText('"{dept}_{type}_{date}"')
        elif self.stringsmith_radio.isChecked():
            self.help_label.setText(
                "StringSmith Template: Use {{;field;}} syntax with graceful missing field handling. "
                "Example: \"{{;dept;}}{{_;type;}}{{_;date;}}\" → \"sales_report_20240315\" "
                "(automatically handles missing fields)"
            )
            self.template_input.setPlaceholderText('"{{;dept;}}{{_;type;}}{{_;date;}}"')
    
    def get_template_config(self) -> Optional[Dict]:
        """Return template configuration or None if disabled."""
        if not self.enable_template.isChecked():
            return None
        
        if self.custom_radio.isChecked():
            # Custom template function
            if not self.custom_selector.is_configured():
                return None
            
            config = self.custom_selector.get_config()
            if config is None:
                return None
            
            file_path, function_name, pos_args, kwargs = config
            
            return {
                'name': file_path,  # Use file path as template name for custom
                'positional': [function_name] + pos_args,  # Function name as first arg
                'keyword': kwargs
            }
        else:
            # Built-in template (template or stringsmith)
            if not self.template_input.text().strip():
                return None
            
            template_type = "template" if self.template_radio.isChecked() else "stringsmith"
            template_pattern = self.template_input.text().strip().strip('"')
            
            return {
                'name': template_type,
                'positional': [template_pattern],
                'keyword': {}
            }
    
    def reset_configuration(self):
        """Reset all template configuration to defaults."""
        self.enable_template.setChecked(False)
        self.template_radio.setChecked(True)
        self.template_input.clear()
        self.custom_selector.reset()
        self.config_area.setEnabled(False)