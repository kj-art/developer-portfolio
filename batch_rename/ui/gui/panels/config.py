"""
Configuration management panel for the batch rename GUI.

Handles loading, saving, and managing configuration presets using PyQt6.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from pathlib import Path
from typing import Optional, Callable

from ....config.config_loader import ConfigLoader
from ....core.config import RenameConfig


class ConfigPanel(QWidget):
    """Configuration file management panel for the GUI."""
    
    def __init__(self, on_config_loaded: Optional[Callable[[RenameConfig], None]] = None,
                 on_config_cleared: Optional[Callable[[], None]] = None):
        """
        Initialize configuration panel.
        
        Args:
            on_config_loaded: Callback when configuration is loaded
            on_config_cleared: Callback when configuration is cleared
        """
        super().__init__()
        self.on_config_loaded = on_config_loaded
        self.on_config_cleared = on_config_cleared
        self.current_config_path: Optional[Path] = None
        
        self._create_widgets()
        self._load_preset_list()
    
    def _create_widgets(self):
        """Create configuration panel widgets."""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Main group box
        group = QGroupBox("Configuration Source")
        group_layout = QVBoxLayout(group)
        
        # Radio button selection
        self.radio_group = QButtonGroup(self)
        
        # Built-in presets option
        self.builtin_radio = QRadioButton("Use built-in preset:")
        self.builtin_radio.setChecked(True)
        self.builtin_radio.toggled.connect(self._on_mode_changed)
        self.radio_group.addButton(self.builtin_radio)
        group_layout.addWidget(self.builtin_radio)
        
        # Built-in preset selection (indented)
        builtin_layout = QHBoxLayout()
        builtin_layout.addSpacing(20)  # Indent to show it belongs to radio button
        
        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        builtin_layout.addWidget(self.preset_combo)
        
        self.load_builtin_btn = QPushButton("Load Preset")
        self.load_builtin_btn.clicked.connect(self._load_selected_preset)
        builtin_layout.addWidget(self.load_builtin_btn)
        
        builtin_layout.addStretch()
        group_layout.addLayout(builtin_layout)
        
        # Custom file option
        self.custom_radio = QRadioButton("Browse for custom config file:")
        self.custom_radio.toggled.connect(self._on_mode_changed)
        self.radio_group.addButton(self.custom_radio)
        group_layout.addWidget(self.custom_radio)
        
        # Custom file selection (indented)
        custom_layout = QHBoxLayout()
        custom_layout.addSpacing(20)  # Indent to show it belongs to radio button
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_and_load_config)
        self.browse_btn.setEnabled(False)  # Initially disabled
        custom_layout.addWidget(self.browse_btn)
        
        custom_layout.addStretch()
        group_layout.addLayout(custom_layout)
        
        # Separator
        group_layout.addSpacing(10)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear Config")
        self.clear_btn.clicked.connect(self._clear_config)
        self.clear_btn.setEnabled(False)  # Initially disabled
        control_layout.addWidget(self.clear_btn)
        
        control_layout.addStretch()
        group_layout.addLayout(control_layout)
        
        # Status label
        self.status_label = QLabel("No configuration loaded")
        self.status_label.setStyleSheet("color: gray; font-size: 10px; font-style: italic;")
        group_layout.addWidget(self.status_label)
        
        layout.addWidget(group)
    
    def _get_built_ins_dir(self) -> Path:
        """Get the built-in configs directory path."""
        try:
            # Look for batch_rename/core/built_ins/configs directory
            current_dir = Path(__file__).parent
            while current_dir.name != "batch_rename":
                current_dir = current_dir.parent
                if current_dir.parent == current_dir:  # Hit root
                    break
            
            built_ins_dir = current_dir / "core" / "built_ins" / "configs"
            return built_ins_dir
            
        except Exception:
            return Path.cwd() / "configs"  # Fallback
    
    def _load_preset_list(self):
        """Load available presets from built-ins directory."""
        try:
            built_ins_dir = self._get_built_ins_dir()
            
            preset_files = []
            if built_ins_dir.exists():
                for pattern in ["*.yaml", "*.yml", "*.json"]:
                    preset_files.extend(built_ins_dir.glob(pattern))
            
            preset_names = [f.stem.replace('_', ' ').title() for f in sorted(preset_files)]
            
            self.preset_combo.clear()
            if preset_names:
                self.preset_combo.addItems(preset_names)
            else:
                self.preset_combo.addItem("(no built-in presets found)")
            
        except Exception as e:
            self.preset_combo.clear()
            self.preset_combo.addItem(f"(error: {e})")
    
    def _on_mode_changed(self):
        """Handle radio button mode change."""
        builtin_mode = self.builtin_radio.isChecked()
        
        # Enable/disable controls based on mode
        self.preset_combo.setEnabled(builtin_mode)
        self.load_builtin_btn.setEnabled(builtin_mode)
        self.browse_btn.setEnabled(not builtin_mode)
        
        # Clear selection when switching modes
        if not builtin_mode:
            self.preset_combo.setCurrentIndex(0)
        
        self._update_selection()
    
    def _update_selection(self):
        """Update the current config path based on current selection."""
        if self.builtin_radio.isChecked():
            self._on_preset_selected(self.preset_combo.currentText())
        else:
            self.current_config_path = None
    
    def _on_preset_selected(self, preset_name: str):
        """Handle preset selection from combobox."""
        if not preset_name or preset_name.startswith("(") or not self.builtin_radio.isChecked():
            self.current_config_path = None
            return
        
        # Convert display name back to filename
        filename = preset_name.lower().replace(' ', '_')
        built_ins_dir = self._get_built_ins_dir()
        
        for ext in ['.yaml', '.yml', '.json']:
            preset_path = built_ins_dir / f"{filename}{ext}"
            if preset_path.exists():
                self.current_config_path = preset_path
                break
        else:
            self.current_config_path = None
    
    def _load_selected_preset(self):
        """Load the currently selected preset."""
        if not self.current_config_path:
            QMessageBox.critical(self, "Error", "Please select a preset first")
            return
        
        self._load_config_file(self.current_config_path)
    
    def _browse_and_load_config(self):
        """Browse for config file and load it."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Configuration File",
            str(Path.cwd()),
            "YAML files (*.yaml *.yml);;JSON files (*.json);;All files (*.*)"
        )
        
        if filename:
            config_path = Path(filename)
            self.current_config_path = config_path
            self._load_config_file(config_path)
    
    def _load_config_file(self, config_path: Path):
        """Load configuration from file."""
        try:
            config = ConfigLoader.load_rename_config(config_path)
            
            self.current_config_path = config_path
            self.status_label.setText(f"Loaded: {config_path.name}")
            self.status_label.setStyleSheet("color: blue; font-weight: bold; font-size: 10px;")
            
            # Enable clear button
            self.clear_btn.setEnabled(True)
            
            if self.on_config_loaded:
                self.on_config_loaded(config)
            
            # Update UI to reflect the loaded config source
            if self.builtin_radio.isChecked():
                # Update preset selection if it matches
                preset_display_name = config_path.stem.replace('_', ' ').title()
                index = self.preset_combo.findText(preset_display_name)
                if index >= 0:
                    self.preset_combo.setCurrentIndex(index)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load configuration:\n{str(e)}")
            self.status_label.setText("Error loading configuration")
            self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 10px;")
    
    def _clear_config(self):
        """Clear current configuration."""
        # Reset UI state
        self.builtin_radio.setChecked(True)  # Default back to built-in mode
        self.preset_combo.setCurrentIndex(0)
        self.current_config_path = None
        
        # Update status
        self.status_label.setText("No configuration loaded")
        self.status_label.setStyleSheet("color: gray; font-size: 10px; font-style: italic;")
        
        # Disable clear button
        self.clear_btn.setEnabled(False)
        
        # Update control states
        self._on_mode_changed()
        
        if self.on_config_cleared:
            self.on_config_cleared()