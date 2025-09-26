"""
Base classes for processing step panels.

Provides common functionality for all step configuration panels.
"""

import sys
from abc import abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# PyQt imports
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QWidget, QLabel, QPushButton,
    QComboBox, QTextEdit,
    QGroupBox, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt

# Import our core logic
sys.path.append(str(Path(__file__).parent.parent))
from ..function_selector import FunctionSelector
from ....core.step_factory import StepFactory
from ....core.steps.base import StepType, ProcessingStep


class ProcessingStepPanel(QWidget):
    """Base class for all processing step configuration panels."""
    
    def __init__(self, step_type: StepType):
        super().__init__()
        self.step_type = step_type
        self.step = StepFactory.get_step(step_type)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface with common structure."""
        layout = QVBoxLayout()
        
        # Create splitter for main content and help
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Main configuration area
        config_widget = self.create_config_area()
        splitter.addWidget(config_widget)
        
        # Help area
        help_widget = self.create_help_area()
        splitter.addWidget(help_widget)
        
        # Set splitter proportions (70% config, 30% help)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    @abstractmethod
    def create_config_area(self) -> QWidget:
        """Create the main configuration area. Must be implemented by subclasses."""
        pass
    
    def create_help_area(self) -> QWidget:
        """Create the help documentation area."""
        widget = QGroupBox("Help & Documentation")
        layout = QVBoxLayout(widget)
        
        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setPlainText(self.step.get_help_text())
        
        layout.addWidget(self.help_text)
        return widget
    
    def create_function_selector_layout(self, parent_layout: QVBoxLayout) -> Tuple[QComboBox, QWidget, FunctionSelector]:
        """
        Create standard function selector layout.
        
        Returns:
            Tuple of (function_combo, config_area, custom_selector)
        """
        # Function type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Function Type:"))
        
        function_combo = QComboBox()
        builtin_functions = list(self.step.builtin_functions.keys())
        function_combo.addItems(builtin_functions + ['custom'])
        type_layout.addWidget(function_combo)
        type_layout.addStretch()
        
        parent_layout.addLayout(type_layout)
        
        # Configuration area for built-in functions
        config_area = QWidget()
        config_layout = QFormLayout(config_area)
        parent_layout.addWidget(config_area)
        
        # Custom function selector (initially hidden)
        custom_selector = FunctionSelector(
            f"{self.step_type.value} function",
            1,
            self.step.validate_custom_function
        )
        custom_selector.setVisible(False)
        parent_layout.addWidget(custom_selector)
        
        return function_combo, config_area, custom_selector
    
    def setup_function_type_connection(self, function_combo: QComboBox, config_area: QWidget, custom_selector: FunctionSelector):
        """Setup the connection for function type changes."""
        function_combo.currentTextChanged.connect(
            lambda t: self.update_function_config(t, config_area, custom_selector)
        )
        
        # Initialize with first function type
        builtin_functions = list(self.step.builtin_functions.keys())
        if builtin_functions:
            self.update_function_config(builtin_functions[0], config_area, custom_selector)
    
    def update_function_config(self, function_type: str, config_area: QWidget, custom_selector: FunctionSelector):
        """Update function configuration UI based on selected type."""
        # Clear existing config widgets
        self.clear_config_layout(config_area.layout())
        
        if function_type == 'custom':
            # Show custom function selector
            custom_selector.setVisible(True)
            config_area.setVisible(False)
        else:
            # Hide custom selector and show built-in config
            custom_selector.setVisible(False)
            config_area.setVisible(True)
            
            # Create built-in specific configuration
            self.create_builtin_config(function_type, config_area.layout())
    
    def clear_config_layout(self, layout: QFormLayout):
        """Clear all widgets from a form layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
    
    @abstractmethod
    def create_builtin_config(self, function_type: str, layout: QFormLayout):
        """Create configuration UI for a specific built-in function type."""
        pass
    
    @abstractmethod
    def extract_builtin_config(self, function_type: str, config_area: QWidget) -> Tuple[List[str], Dict[str, Any]]:
        """
        Extract configuration for a built-in function.
        
        Returns:
            Tuple of (positional_args, keyword_args)
        """
        pass
    
    def extract_custom_config(self, custom_selector: FunctionSelector) -> Optional[Tuple[str, List[str], Dict[str, Any]]]:
        """
        Extract configuration for a custom function.
        
        Returns:
            Tuple of (file_path, positional_args, keyword_args) or None
        """
        if custom_selector.is_configured():
            config = custom_selector.get_config()
            if config:
                file_path, function_name, pos_args, kwargs = config
                return file_path, [function_name] + pos_args, kwargs
        return None


class SingleStepPanel(ProcessingStepPanel):
    """Base class for non-stackable step panels (Extractor, Template, AllInOne)."""
    
    def __init__(self, step_type: StepType):
        super().__init__(step_type)
        self.function_combo = None
        self.config_area = None
        self.custom_selector = None
    
    def create_config_area(self) -> QWidget:
        """Create configuration area for single step."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title_label = QLabel(f"{self.step_type.value.title()} Configuration")
        title_label.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        layout.addWidget(title_label)
        
        # Add description if provided by subclass
        description = self.get_panel_description()
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("QLabel { color: #666; margin-bottom: 10px; }")
            layout.addWidget(desc_label)
        
        # Create function selector
        self.function_combo, self.config_area, self.custom_selector = self.create_function_selector_layout(layout)
        
        # Setup connections
        self.setup_function_type_connection(self.function_combo, self.config_area, self.custom_selector)
        
        layout.addStretch()
        return widget
    
    def get_panel_description(self) -> Optional[str]:
        """Return optional panel description. Override in subclasses."""
        return None
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """
        Get current configuration.
        
        Returns:
            Configuration dict or None if not configured
        """
        function_type = self.function_combo.currentText()
        
        if function_type == 'custom':
            config = self.extract_custom_config(self.custom_selector)
            if config:
                file_path, pos_args, kwargs = config
                return {
                    'name': file_path,
                    'positional': pos_args,
                    'keyword': kwargs
                }
            return None
        else:
            # Built-in function
            pos_args, kwargs = self.extract_builtin_config(function_type, self.config_area)
            if pos_args or kwargs:
                return {
                    'name': function_type,
                    'positional': pos_args,
                    'keyword': kwargs
                }
            return None


class StackableStepPanel(ProcessingStepPanel):
    """Base class for stackable step panels (Converter, Filter)."""
    
    def __init__(self, step_type: StepType):
        super().__init__(step_type)
        self.step_instances = []  # List of (combo, config_area, custom_selector, *extra_widgets)
    
    def create_config_area(self) -> QWidget:
        """Create configuration area for stackable steps."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title_label = QLabel(f"{self.step_type.value.title()} Configuration")
        title_label.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        layout.addWidget(title_label)
        
        # Add button
        add_button = QPushButton(f"Add {self.step_type.value.title()}")
        add_button.clicked.connect(self.add_step_instance)
        layout.addWidget(add_button)
        
        # Scroll area for step instances
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        return widget
    
    def add_step_instance(self):
        """Add a new step instance widget."""
        instance_widget = QGroupBox(f"{self.step_type.value.title()} #{len(self.step_instances) + 1}")
        instance_layout = QVBoxLayout(instance_widget)
        
        # Create controls layout
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Type:"))
        
        # Function selector
        function_combo = QComboBox()
        builtin_functions = list(self.step.builtin_functions.keys())
        function_combo.addItems(builtin_functions + ['custom'])
        controls_layout.addWidget(function_combo)
        
        # Add extra controls (like invert checkbox for filters)
        extra_widgets = self.create_extra_controls(controls_layout)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_step_instance(instance_widget))
        controls_layout.addWidget(remove_btn)
        controls_layout.addStretch()
        
        instance_layout.addLayout(controls_layout)
        
        # Configuration area
        config_area = QWidget()
        config_layout = QFormLayout(config_area)
        instance_layout.addWidget(config_area)
        
        # Custom function selector
        custom_selector = FunctionSelector(
            f"{self.step_type.value} function",
            1,
            self.step.validate_custom_function
        )
        custom_selector.setVisible(False)
        instance_layout.addWidget(custom_selector)
        
        # Setup connections
        function_combo.currentTextChanged.connect(
            lambda t: self.update_function_config(t, config_area, custom_selector)
        )
        
        # Initialize with first function
        if builtin_functions:
            self.update_function_config(builtin_functions[0], config_area, custom_selector)
        
        # Track this instance
        instance_data = (function_combo, config_area, custom_selector) + extra_widgets
        self.step_instances.append(instance_data)
        
        # Add to scroll layout
        self.scroll_layout.addWidget(instance_widget)
    
    def create_extra_controls(self, layout: QHBoxLayout) -> Tuple:
        """Create extra control widgets. Override in subclasses. Return tuple of widgets."""
        return ()
    
    def remove_step_instance(self, widget: QGroupBox):
        """Remove a step instance widget."""
        widget.setParent(None)
        # Update the instances list to remove the deleted widget
        self.step_instances = [
            instance for instance in self.step_instances
            if instance[0].parent() and instance[0].parent().parent() != widget
        ]
        
        # Update numbering
        self.update_instance_numbering()
    
    def update_instance_numbering(self):
        """Update instance widget titles with correct numbering."""
        for i, instance in enumerate(self.step_instances):
            combo = instance[0]  # First element is always the combo
            if combo.parent() and combo.parent().parent():
                widget = combo.parent().parent()
                if isinstance(widget, QGroupBox):
                    widget.setTitle(f"{self.step_type.value.title()} #{i + 1}")
    
    def get_configs(self) -> List[Dict[str, Any]]:
        """Return list of all step configurations."""
        configs = []
        
        for instance in self.step_instances:
            combo = instance[0]
            config_area = instance[1]
            custom_selector = instance[2]
            
            if not combo.parent():  # Widget was removed
                continue
            
            function_type = combo.currentText()
            
            if function_type == 'custom':
                config = self.extract_custom_config(custom_selector)
                if config:
                    file_path, pos_args, kwargs = config
                    config_dict = {
                        'name': file_path,
                        'positional': pos_args,
                        'keyword': kwargs
                    }
                    # Add extra config from subclass
                    extra_config = self.extract_extra_config(instance)
                    config_dict.update(extra_config)
                    configs.append(config_dict)
            else:
                # Built-in function
                pos_args, kwargs = self.extract_builtin_config(function_type, config_area)
                if pos_args or kwargs:
                    config_dict = {
                        'name': function_type,
                        'positional': pos_args,
                        'keyword': kwargs
                    }
                    # Add extra config from subclass
                    extra_config = self.extract_extra_config(instance)
                    config_dict.update(extra_config)
                    configs.append(config_dict)
        
        return configs
    
    def extract_extra_config(self, instance: Tuple) -> Dict[str, Any]:
        """Extract extra configuration from instance. Override in subclasses."""
        return {}