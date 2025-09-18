import sys
from pathlib import Path
from typing import Dict, Optional

# PyQt imports
from PyQt6.QtWidgets import (
    QVBoxLayout, QWidget, QLabel, QLineEdit,
    QCheckBox, QGroupBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt

# Import our existing core logic
sys.path.append(str(Path(__file__).parent.parent))
class TemplatePanel(QWidget):
    """Panel for configuring output template (optional, mutually exclusive options)."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Enable template checkbox
        self.enable_template = QCheckBox("Enable Template")
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
        self.template_radio.setChecked(True)  # Default to standard template
        
        self.template_group.addButton(self.template_radio)
        self.template_group.addButton(self.stringsmith_radio)
        
        type_layout.addWidget(self.template_radio)
        type_layout.addWidget(self.stringsmith_radio)
        
        self.config_layout.addWidget(type_group)
        
        # Template input area
        input_group = QGroupBox("Template Configuration")
        input_layout = QVBoxLayout(input_group)
        
        self.template_input = QLineEdit()
        self.template_input.setPlaceholderText('"{dept}_{type}_{date}"')
        input_layout.addWidget(QLabel("Template Pattern:"))
        input_layout.addWidget(self.template_input)
        
        # Help text that changes based on selected type
        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        self.help_label.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        input_layout.addWidget(self.help_label)
        
        self.config_layout.addWidget(input_group)
        
        # Connect radio button changes to update help text
        self.template_radio.toggled.connect(self.update_help_text)
        self.stringsmith_radio.toggled.connect(self.update_help_text)
        
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
    
    def update_help_text(self):
        """Update help text based on selected template type."""
        if self.template_radio.isChecked():
            self.help_label.setText(
                "Standard Template: Use {field_name} syntax. "
                "Example: \"{dept}_{type}_{date}\" → \"sales_report_20240315\""
            )
            self.template_input.setPlaceholderText('"{dept}_{type}_{date}"')
        else:
            self.help_label.setText(
                "StringSmith Template: Use {{;field;}} syntax with graceful missing field handling. "
                "Example: \"{{;dept;}}{{_;type;}}{{_;date;}}\" → \"sales_report_20240315\" "
                "(automatically handles missing fields)"
            )
            self.template_input.setPlaceholderText('"{{;dept;}}{{_;type;}}{{_;date;}}"')
    
    def get_template_config(self) -> Optional[Dict]:
        """Return template configuration or None if disabled."""
        if not self.enable_template.isChecked() or not self.template_input.text().strip():
            return None
        
        template_type = "template" if self.template_radio.isChecked() else "stringsmith"
        template_pattern = self.template_input.text().strip().strip('"')
        
        return {
            'name': template_type,
            'positional': [template_pattern],
            'keyword': {}
        }