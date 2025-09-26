"""
GUI panel for configuring data extraction from filenames.

Uses the ProcessingStep architecture with base class for consistent functionality.
"""

import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

# PyQt imports
from PyQt6.QtWidgets import QLineEdit, QLabel, QFormLayout, QWidget

# Import base classes and core logic
sys.path.append(str(Path(__file__).parent.parent))
from .base import SingleStepPanel
from ....core.steps.base import StepType


class ExtractorPanel(SingleStepPanel):
    """Panel for configuring data extraction step."""
    
    def __init__(self):
        super().__init__(StepType.EXTRACTOR)
    
    def get_panel_description(self) -> Optional[str]:
        """Return panel description."""
        return "Extract data fields from filenames and file metadata for use in conversion and formatting."
    
    def create_builtin_config(self, function_type: str, layout: QFormLayout):
        """Create configuration UI for built-in extractor functions."""
        if function_type == 'split':
            self.add_split_config(layout)
        elif function_type == 'regex':
            self.add_regex_config(layout)
        elif function_type == 'position':
            self.add_position_config(layout)
        elif function_type == 'metadata':
            self.add_metadata_config(layout)
    
    def add_split_config(self, layout: QFormLayout):
        """Add configuration for split extractor."""
        delimiter_input = QLineEdit("_")
        delimiter_input.setObjectName("delimiter")
        delimiter_input.setPlaceholderText("Character to split on")
        layout.addRow("Delimiter:", delimiter_input)
        
        fields_input = QLineEdit("dept,type,date")
        fields_input.setObjectName("fields")
        fields_input.setPlaceholderText("Field names separated by commas")
        layout.addRow("Field Names:", fields_input)
    
    def add_regex_config(self, layout: QFormLayout):
        """Add configuration for regex extractor."""
        pattern_input = QLineEdit()
        pattern_input.setObjectName("pattern")
        pattern_input.setPlaceholderText("(?P<dept>\\w+)_(?P<num>\\d+)")
        layout.addRow("Regex Pattern:", pattern_input)
        
        help_label = QLabel("Use named groups: (?P<fieldname>pattern)")
        help_label.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        layout.addRow("", help_label)
    
    def add_position_config(self, layout: QFormLayout):
        """Add configuration for position extractor."""
        positions_input = QLineEdit()
        positions_input.setObjectName("positions")
        positions_input.setPlaceholderText("0-2:dept,3-5:code,6:type")
        layout.addRow("Position Specs:", positions_input)
        
        help_label = QLabel("Format: start-end:fieldname or start:fieldname")
        help_label.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        layout.addRow("", help_label)
    
    def add_metadata_config(self, layout: QFormLayout):
        """Add configuration for metadata extractor."""
        fields_input = QLineEdit("created,modified,size")
        fields_input.setObjectName("metadata_fields")
        fields_input.setPlaceholderText("created,modified,size")
        layout.addRow("Metadata Fields:", fields_input)
        
        help_label = QLabel("Available: created, modified, size")
        help_label.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        layout.addRow("", help_label)
    
    def extract_builtin_config(self, function_type: str, config_area: QWidget) -> Tuple[List[str], Dict[str, Any]]:
        """Extract configuration for built-in extractor functions."""
        pos_args = []
        kwargs = {}
        
        if function_type == 'split':
            delimiter_widget = config_area.findChild(QLineEdit, "delimiter")
            fields_widget = config_area.findChild(QLineEdit, "fields")
            
            if delimiter_widget and fields_widget:
                delimiter = delimiter_widget.text().strip()
                fields_text = fields_widget.text().strip()
                
                if delimiter and fields_text:
                    field_names = [f.strip() for f in fields_text.split(',')]
                    pos_args = [delimiter] + field_names
        
        elif function_type == 'regex':
            pattern_widget = config_area.findChild(QLineEdit, "pattern")
            if pattern_widget:
                pattern = pattern_widget.text().strip()
                if pattern:
                    pos_args = [pattern]
        
        elif function_type == 'position':
            positions_widget = config_area.findChild(QLineEdit, "positions")
            if positions_widget:
                positions_text = positions_widget.text().strip()
                if positions_text:
                    pos_args = [positions_text]
        
        elif function_type == 'metadata':
            fields_widget = config_area.findChild(QLineEdit, "metadata_fields")
            if fields_widget:
                fields_text = fields_widget.text().strip()
                if fields_text:
                    field_names = [f.strip() for f in fields_text.split(',')]
                    pos_args = field_names
        
        return pos_args, kwargs
    
    def get_extractor_config(self) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        Get current extractor configuration.
        
        Returns:
            Tuple of (extractor_name, positional_args, keyword_args)
        """
        config = self.get_config()
        if not config:
            raise ValueError("Extractor must be configured")
        
        return config['name'], config['positional'], config['keyword']