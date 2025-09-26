"""
GUI panel for configuring all-in-one processing functions.

Uses the ProcessingStep architecture with base class for consistent functionality.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# PyQt imports
from PyQt6.QtWidgets import QLineEdit, QLabel, QFormLayout, QWidget

# Import base classes and core logic
sys.path.append(str(Path(__file__).parent.parent))
from .base import SingleStepPanel
from ....core.steps.base import StepType


class AllInOnePanel(SingleStepPanel):
    """Panel for configuring all-in-one processing functions."""
    
    def __init__(self):
        super().__init__(StepType.ALLINONE)
    
    def get_panel_description(self) -> Optional[str]:
        """Return panel description."""
        return ("All-in-one functions handle extraction, conversion, and formatting in a single step. "
                "This replaces the need for separate extractor, converter, and template steps.")
    
    def create_builtin_config(self, function_type: str, layout: QFormLayout):
        """Create configuration UI for built-in all-in-one functions."""
        if function_type == 'replace':
            self.add_replace_config(layout)
        elif function_type in ['lowercase', 'uppercase']:
            self.add_simple_config(layout, f"Convert entire filename to {function_type}")
        elif function_type == 'clean_filename':
            self.add_clean_filename_config(layout)
    
    def add_replace_config(self, layout: QFormLayout):
        """Add configuration for replace function."""
        # Find/replace pairs
        find1_input = QLineEdit()
        find1_input.setObjectName("find1")
        find1_input.setPlaceholderText("Text to find")
        layout.addRow("Find 1:", find1_input)
        
        replace1_input = QLineEdit()
        replace1_input.setObjectName("replace1")
        replace1_input.setPlaceholderText("Replacement text")
        layout.addRow("Replace 1:", replace1_input)
        
        find2_input = QLineEdit()
        find2_input.setObjectName("find2")
        find2_input.setPlaceholderText("Optional second find")
        layout.addRow("Find 2:", find2_input)
        
        replace2_input = QLineEdit()
        replace2_input.setObjectName("replace2")
        replace2_input.setPlaceholderText("Optional second replacement")
        layout.addRow("Replace 2:", replace2_input)
        
        help_label = QLabel("Add more find/replace pairs as needed")
        help_label.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        layout.addRow("", help_label)
    
    def add_simple_config(self, layout: QFormLayout, description: str):
        """Add configuration for simple functions that need no parameters."""
        help_label = QLabel(description)
        help_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        layout.addRow("Description:", help_label)
        
        note_label = QLabel("No additional configuration required")
        note_label.setStyleSheet("QLabel { color: #999; font-size: 11px; }")
        layout.addRow("", note_label)
    
    def add_clean_filename_config(self, layout: QFormLayout):
        """Add configuration for clean_filename function."""
        replacement_input = QLineEdit("_")
        replacement_input.setObjectName("replacement_char")
        replacement_input.setPlaceholderText("Character to replace spaces/specials")
        layout.addRow("Replacement Char:", replacement_input)
        
        help_label = QLabel("Replaces spaces and special characters with the specified character")
        help_label.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        layout.addRow("", help_label)
    
    def extract_builtin_config(self, function_type: str, config_area: QWidget) -> Tuple[List[str], Dict[str, Any]]:
        """Extract configuration for built-in all-in-one functions."""
        pos_args = []
        kwargs = {}
        
        if function_type == 'replace':
            # Collect find/replace pairs
            pairs = []
            for i in range(1, 3):  # Support up to 2 pairs for now
                find_widget = config_area.findChild(QLineEdit, f"find{i}")
                replace_widget = config_area.findChild(QLineEdit, f"replace{i}")
                
                if find_widget and replace_widget:
                    find_text = find_widget.text().strip()
                    replace_text = replace_widget.text().strip()
                    if find_text:  # Only add if find text is provided
                        pairs.extend([find_text, replace_text])
            
            if pairs:
                pos_args = pairs
        
        elif function_type in ['lowercase', 'uppercase']:
            # No configuration needed
            pass
        
        elif function_type == 'clean_filename':
            replacement_widget = config_area.findChild(QLineEdit, "replacement_char")
            if replacement_widget:
                replacement_char = replacement_widget.text().strip()
                if replacement_char:
                    pos_args = [replacement_char]
        
        return pos_args, kwargs
    
    def get_allinone_config(self) -> Optional[Dict[str, Any]]:
        """
        Get current all-in-one configuration.
        
        Returns:
            All-in-one config dict or None if not configured
        """
        return self.get_config()
    
    def is_configured(self) -> bool:
        """Check if the all-in-one function is properly configured."""
        config = self.get_allinone_config()
        return config is not None