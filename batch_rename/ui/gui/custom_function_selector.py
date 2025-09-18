"""
Custom Function Selector Widget

Reusable PyQt widget for selecting and configuring custom Python functions
from files, with signature validation and parameter input generation.
"""

import importlib.util
import inspect
from pathlib import Path
from typing import Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QComboBox, QGroupBox, QFormLayout, QCheckBox, QSpinBox
)
from PyQt6.QtCore import QTimer


class CustomFunctionSelector(QWidget):
    """
    Reusable widget for selecting custom Python functions from files.
    
    Provides file selection, function discovery, signature validation,
    and parameter input widgets for custom extractors, converters, and filters.
    """
    
    def __init__(self, function_description="custom function"):
        super().__init__()
        self.function_description = function_description
        self.current_function = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Python File:"))
        self.file_path = QLineEdit()
        self.file_path.textChanged.connect(self.on_file_changed)
        file_layout.addWidget(self.file_path)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)
        
        # Function selection
        func_layout = QHBoxLayout()
        func_layout.addWidget(QLabel("Function:"))
        self.function_combo = QComboBox()
        self.function_combo.setEnabled(False)
        self.function_combo.currentIndexChanged.connect(self.on_function_index_changed)
        func_layout.addWidget(self.function_combo)
        layout.addLayout(func_layout)
        
        # Validation status
        self.validation_label = QLabel("")
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("QLabel { margin: 5px; padding: 5px; color: #666; font-size: 11px; }")
        layout.addWidget(self.validation_label)
        
        # Arguments group (shown when function has parameters)
        self.args_group = QGroupBox("Function Arguments")
        self.args_layout = QFormLayout()
        self.args_group.setLayout(self.args_layout)
        self.args_group.setVisible(False)
        layout.addWidget(self.args_group)
        
        self.setLayout(layout)
    
    def browse_file(self):
        """Open file dialog to select Python script."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select {self.function_description.title()} Script", 
            str(Path.home()), "Python Files (*.py)"
        )
        if file_path:
            self.file_path.setText(file_path)
    
    def on_file_changed(self):
        """Handle file path changes."""
        file_path = self.file_path.text().strip()
        
        if not file_path:
            self.function_combo.clear()
            self.function_combo.setEnabled(False)
            self.validation_label.setText("")
            self.args_group.setVisible(False)
            self.current_function = None
            return
        
        if not Path(file_path).exists():
            self.validation_label.setText("❌ File does not exist")
            self.function_combo.clear()
            self.function_combo.setEnabled(False)
            self.args_group.setVisible(False)
            self.current_function = None
            return
        
        # Load functions from the file
        try:
            functions = self.load_functions_from_file(file_path)
            self.function_combo.clear()
            self.function_combo.addItems(functions)
            self.function_combo.setEnabled(len(functions) > 0)
            
            if len(functions) == 0:
                self.validation_label.setText("❌ No functions found in file")
                self.current_function = None
            else:
                self.validation_label.setText(f"✓ Found {len(functions)} function(s)")
                # Use QTimer to ensure the UI is fully updated before triggering function selection
                QTimer.singleShot(100, self.on_function_selected)
                
        except Exception as e:
            self.validation_label.setText(f"❌ Error loading file: {str(e)}")
            self.function_combo.clear()
            self.function_combo.setEnabled(False)
            self.current_function = None
        
        self.args_group.setVisible(False)
    
    def load_functions_from_file(self, file_path):
        """Load and return list of function names from a Python file."""
        spec = importlib.util.spec_from_file_location("custom_module", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get all functions defined in the module (not imported)
        functions = []
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            # Only include functions defined in this module
            if obj.__module__ == module.__name__:
                functions.append(name)
        
        return functions
    
    def on_function_index_changed(self, index):
        """Handle function combo box index changes - this fires even for initial selection."""
        if index >= 0:  # Valid index selected
            self.on_function_selected()
    
    def on_function_selected(self):
        """Handle function selection and validate signature."""
        function_name = self.function_combo.currentText()
        file_path = self.file_path.text().strip()
        
        if not function_name or not file_path:
            self.args_group.setVisible(False)
            self.current_function = None
            return
        
        try:
            # Load the function and validate
            function = self.load_function_from_file(file_path, function_name)
            validation_result = self.validate_function(function)
            
            if validation_result['valid']:
                self.validation_label.setText(f"✓ {validation_result['message']}")
                self.create_argument_inputs(validation_result['parameters'])
                self.current_function = function
            else:
                self.validation_label.setText(f"❌ {validation_result['message']}")
                self.args_group.setVisible(False)
                self.current_function = None
                
        except Exception as e:
            self.validation_label.setText(f"❌ Error validating function: {str(e)}")
            self.args_group.setVisible(False)
            self.current_function = None
    
    def load_function_from_file(self, file_path, function_name):
        """Load a specific function from a Python file."""
        spec = importlib.util.spec_from_file_location("custom_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if not hasattr(module, function_name):
            raise ValueError(f"Function '{function_name}' not found in {file_path}")
        
        return getattr(module, function_name)
    
    def validate_function(self, function):
        """Validate function signature. Override in subclasses for specific validation."""
        try:
            sig = inspect.signature(function)
            params = list(sig.parameters.values())
            
            validation_points = []
            
            # Check: at least one parameter (should be ProcessingContext)
            if len(params) == 0:
                return {
                    'valid': False,
                    'message': 'Function must accept at least one parameter (ProcessingContext)'
                }
            
            validation_points.append(f"✓ Function has {len(params)} parameter(s)")
            
            # Check first parameter name/type hint for ProcessingContext
            first_param = params[0]
            context_hints = ['ProcessingContext', 'context']
            if (first_param.annotation != first_param.empty and 
                'ProcessingContext' in str(first_param.annotation)) or \
               any(hint in first_param.name.lower() for hint in context_hints):
                validation_points.append(f"✓ First parameter '{first_param.name}' appears to be ProcessingContext")
            else:
                validation_points.append(f"⚠ First parameter '{first_param.name}' should be ProcessingContext")
            
            # Get additional parameters for return value
            additional_params = params[1:]
            
            # Build multi-line message (removed the additional parameters line)
            message = f"Valid signature: {function.__name__}()\n" + "\n".join(validation_points)
            
            return {
                'valid': True,
                'message': message,
                'parameters': additional_params  # Skip first parameter (ProcessingContext)
            }
            
            return {
                'valid': True,
                'message': message,
                'parameters': additional_params  # Skip first parameter (ProcessingContext)
            }
                    
        except Exception as e:
            return {
                'valid': False,
                'message': f'Error inspecting function: {str(e)}'
            }
    
    def create_argument_inputs(self, parameters):
        """Create input widgets for function parameters with descriptions from docstring."""
        # Clear existing argument inputs
        for i in reversed(range(self.args_layout.count())):
            item = self.args_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        if len(parameters) == 0:
            self.args_group.setVisible(False)
            return
        
        # Parse docstring to get parameter descriptions
        param_descriptions = self.parse_docstring_params()
        
        # Create inputs for each parameter
        for param in parameters:
            input_widget = self.create_parameter_input(param)
            
            # Create label with description if available
            description = param_descriptions.get(param.name, "")
            if description:
                label_text = f"{param.name}:"
                help_text = f"{description}"
                
                # Create a label with tooltip
                label = QLabel(label_text)
                label.setToolTip(help_text)
                
                # Also set tooltip on the input widget
                input_widget.setToolTip(help_text)
                
                # Add a small help indicator
                label.setStyleSheet("QLabel:hover { color: #0066cc; }")
                
                self.args_layout.addRow(label, input_widget)
            else:
                self.args_layout.addRow(f"{param.name}:", input_widget)
        
        self.args_group.setVisible(True)
    
    def parse_docstring_params(self) -> Dict[str, str]:
        """Parse docstring to extract parameter descriptions."""
        if not self.current_function:
            return {}
        
        # Add debug print to see what we're working with
        docstring = inspect.getdoc(self.current_function)
        print(f"DEBUG: Parsing docstring for {self.current_function.__name__}")
        print(f"DEBUG: Docstring content:\n{docstring}")
        
        try:
            # Try using docstring_parser if available
            try:
                from docstring_parser import parse
                parsed = parse(docstring)
                descriptions = {}
                for param in parsed.params:
                    descriptions[param.arg_name] = param.description
                print(f"DEBUG: docstring_parser found: {descriptions}")
                return descriptions
            except ImportError:
                print("DEBUG: docstring_parser not available, using manual parsing")
                # Fallback to manual parsing
                return self.manual_parse_docstring()
                
        except Exception as e:
            print(f"DEBUG: Error in parse_docstring_params: {e}")
            return {}
    
    def manual_parse_docstring(self) -> Dict[str, str]:
        """Manually parse docstring for Args: section."""
        docstring = inspect.getdoc(self.current_function)
        if not docstring:
            print("DEBUG: No docstring found")
            return {}
        
        descriptions = {}
        lines = docstring.split('\n')
        
        # Look for Args: section
        in_args_section = False
        current_param = None
        current_desc = []
        
        print(f"DEBUG: Processing {len(lines)} lines")
        
        for i, line in enumerate(lines):
            line = line.strip()
            print(f"DEBUG: Line {i}: '{line}' (in_args: {in_args_section})")
            
            # Check if we're entering Args section
            if line.lower() in ['args:', 'arguments:', 'parameters:']:
                print(f"DEBUG: Found Args section at line {i}")
                in_args_section = True
                continue
            
            # Check if we're leaving Args section
            if in_args_section and line.lower() in ['returns:', 'yields:', 'raises:', 'examples:', 'note:', 'notes:']:
                print(f"DEBUG: Leaving Args section at line {i}")
                # Save any pending parameter
                if current_param and current_desc:
                    descriptions[current_param] = ' '.join(current_desc).strip()
                break
            
            if in_args_section and line:
                # Check if this is a new parameter (starts with identifier:)
                if ':' in line and not line.startswith(' '):
                    print(f"DEBUG: Found parameter line: '{line}'")
                    # Save previous parameter if exists
                    if current_param and current_desc:
                        descriptions[current_param] = ' '.join(current_desc).strip()
                        print(f"DEBUG: Saved param '{current_param}': '{descriptions[current_param]}'")
                    
                    # Start new parameter
                    parts = line.split(':', 1)
                    current_param = parts[0].strip()
                    current_desc = [parts[1].strip()] if len(parts) > 1 else []
                    print(f"DEBUG: Starting new param '{current_param}' with desc: {current_desc}")
                elif current_param and line.startswith(' '):
                    # Continuation of current parameter description
                    current_desc.append(line.strip())
                    print(f"DEBUG: Added continuation to '{current_param}': '{line.strip()}'")
        
        # Save final parameter
        if current_param and current_desc:
            descriptions[current_param] = ' '.join(current_desc).strip()
            print(f"DEBUG: Saved final param '{current_param}': '{descriptions[current_param]}'")
        
        print(f"DEBUG: Final descriptions: {descriptions}")
        return descriptions
    
    def create_parameter_input(self, param):
        """Create appropriate input widget for a function parameter."""
        # Determine widget type based on parameter info
        if param.annotation == bool or (hasattr(param, 'default') and isinstance(param.default, bool)):
            # Boolean parameter
            widget = QCheckBox()
            if hasattr(param, 'default'):
                widget.setChecked(param.default)
            return widget
        elif param.annotation == int or (hasattr(param, 'default') and isinstance(param.default, int)):
            # Integer parameter
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            if hasattr(param, 'default'):
                widget.setValue(param.default)
            return widget
        else:
            # String parameter (default)
            widget = QLineEdit()
            if hasattr(param, 'default') and param.default != inspect.Parameter.empty:
                widget.setText(str(param.default))
            return widget
    
    def get_argument_values(self):
        """Get current values from argument input widgets."""
        values = {}
        for i in range(self.args_layout.rowCount()):
            label_item = self.args_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
            field_item = self.args_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
            
            if label_item and field_item:
                label = label_item.widget()
                widget = field_item.widget()
                
                if isinstance(label, QLabel):
                    param_name = label.text().rstrip(':')
                    
                    if isinstance(widget, QCheckBox):
                        values[param_name] = widget.isChecked()
                    elif isinstance(widget, QSpinBox):
                        values[param_name] = widget.value()
                    elif isinstance(widget, QLineEdit):
                        text = widget.text().strip()
                        values[param_name] = text if text else None
        
        return values
    
    def get_config(self):
        """Get complete configuration including file path, function name, and arguments."""
        if not self.is_configured():
            return None
        
        file_path = self.file_path.text().strip()
        function_name = self.function_combo.currentText()
        
        # Get argument values
        arg_values = self.get_argument_values()
        
        # Separate positional and keyword arguments
        # For now, treat all as keyword arguments
        pos_args = []
        kwargs = arg_values
        
        return file_path, function_name, pos_args, kwargs
    
    def is_configured(self):
        """Check if selector has a valid configuration."""
        return self.current_function is not None