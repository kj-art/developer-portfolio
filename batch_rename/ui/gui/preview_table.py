import sys
from pathlib import Path
from typing import Dict, List

# PyQt imports
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt

# Import our existing core logic
sys.path.append(str(Path(__file__).parent.parent))
class PreviewTable(QTableWidget):
    """Table showing file rename preview."""
    
    def __init__(self):
        super().__init__()
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Current Name", "New Name"])
        
        # Make columns stretch to fill width
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Make read-only
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
    def update_preview(self, preview_data: List[Dict]):
        """Update table with preview data."""
        # Filter to only show files that would change
        changes = [entry for entry in preview_data 
                  if entry['old_name'] != entry['new_name']]
        
        self.setRowCount(len(changes))
        
        for row, entry in enumerate(changes):
            old_item = QTableWidgetItem(entry['old_name'])
            new_item = QTableWidgetItem(entry['new_name'])
            
            self.setItem(row, 0, old_item)
            self.setItem(row, 1, new_item)
        
        if len(changes) == 0:
            self.setRowCount(1)
            no_changes_item = QTableWidgetItem("No files would be renamed")
            no_changes_item.setBackground(Qt.GlobalColor.lightGray)
            self.setItem(0, 0, no_changes_item)
            self.setItem(0, 1, QTableWidgetItem(""))