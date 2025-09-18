"""
PyQt GUI for Batch Rename Tool

Provides a visual interface for the batch file renaming functionality,
wrapping around the existing CLI core logic.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util
import inspect

# PyQt imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QTableWidget,
    QTableWidgetItem, QTabWidget, QComboBox, QCheckBox, QTextEdit,
    QMessageBox, QProgressBar, QStatusBar, QGroupBox, QSpinBox,
    QSplitter, QHeaderView, QScrollArea, QFrame, QRadioButton,
    QButtonGroup, QFormLayout, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

# Import our existing core logic
sys.path.append(str(Path(__file__).parent.parent))
from core.processor import BatchRenameProcessor
from core.config import RenameConfig
from core.extractors import BUILTIN_EXTRACTORS
from core.converters import BUILTIN_CONVERTERS
from core.filters import BUILTIN_FILTERS


class CustomFunctionSelector(QWidget):
    """
    Reusable widget for selecting custom Python functions from files.
    
    Handles the flow: File selection → Function dropdown → Argument inputs
    """
    
    def __init__(self, function_description: str = "processing function"):
        super().__init__()
        self.function_description = function_description
        self.current_function = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText(f"Select a .py file containing your {self.function_description}")
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
        self.function_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.function_combo.setMinimumWidth(200)
        self.function_combo.currentTextChanged.connect(self.on_function_selected)
        self.function_combo.currentIndexChanged.connect(self.on_function_index_changed)
        func_layout.addWidget(self.function_combo)
        layout.addLayout(func_layout)
        
        # Validation status
        self.validation_label = QLabel("")
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        layout.addWidget(self.validation_label)
        
        # Function arguments
        self.args_group = QGroupBox("Function Arguments")
        self.args_layout = QFormLayout(self.args_group)
        self.args_group.setVisible(False)
        layout.addWidget(self.args_group)
        
        self.setLayout(layout)
    
    def browse_file(self):
        """Open file dialog to select custom function file."""
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
                from PyQt6.QtCore import QTimer
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
            
            # Check: at least one parameter (should be ProcessingContext)
            if len(params) == 0:
                return {
                    'valid': False,
                    'message': 'Function must accept at least one parameter (ProcessingContext)'
                }
            
            # Check first parameter name/type hint for ProcessingContext
            first_param = params[0]
            context_hints = ['ProcessingContext', 'context']
            if (first_param.annotation != first_param.empty and 
                'ProcessingContext' in str(first_param.annotation)) or \
               any(hint in first_param.name.lower() for hint in context_hints):
                param_info = f"✓ First parameter '{first_param.name}' appears to be ProcessingContext"
            else:
                param_info = f"⚠ First parameter '{first_param.name}' should be ProcessingContext"
            
            # Success - return all parameters except the first one (ProcessingContext)
            param_names = [p.name for p in params]
            message = f"Valid signature: {function.__name__}({', '.join(param_names)}). {param_info}"
            
            return {
                'valid': True,
                'message': message,
                'parameters': params[1:]  # Skip first parameter (ProcessingContext)
            }
            
                    
        except Exception as e:
            return {
                'valid': False,
                'message': f'Error inspecting function: {str(e)}'
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
        
        try:
            # Try using docstring_parser if available
            try:
                from docstring_parser import parse
                docstring = parse(inspect.getdoc(self.current_function))
                descriptions = {}
                for param in docstring.params:
                    descriptions[param.arg_name] = param.description
                return descriptions
            except ImportError:
                # Fallback to manual parsing
                return self.manual_parse_docstring()
                
        except Exception:
            return {}
    
    def manual_parse_docstring(self) -> Dict[str, str]:
        """Manually parse docstring for Args: section."""
        docstring = inspect.getdoc(self.current_function)
        if not docstring:
            return {}
        
        descriptions = {}
        lines = docstring.split('\n')
        
        # Look for Args: section
        in_args_section = False
        current_param = None
        current_desc = []
        
        for line in lines:
            line = line.strip()
            
            # Check if we're entering Args section
            if line.lower() in ['args:', 'arguments:', 'parameters:']:
                in_args_section = True
                continue
            
            # Check if we're leaving Args section
            if in_args_section and line.lower() in ['returns:', 'yields:', 'raises:', 'examples:', 'note:', 'notes:']:
                # Save any pending parameter
                if current_param and current_desc:
                    descriptions[current_param] = ' '.join(current_desc).strip()
                break
            
            if in_args_section and line:
                # Check if this is a new parameter (starts with identifier:)
                if ':' in line and not line.startswith(' '):
                    # Save previous parameter if exists
                    if current_param and current_desc:
                        descriptions[current_param] = ' '.join(current_desc).strip()
                    
                    # Start new parameter
                    parts = line.split(':', 1)
                    current_param = parts[0].strip()
                    current_desc = [parts[1].strip()] if len(parts) > 1 else []
                elif current_param and line.startswith(' '):
                    # Continuation of current parameter description
                    current_desc.append(line.strip())
        
        # Save final parameter
        if current_param and current_desc:
            descriptions[current_param] = ' '.join(current_desc).strip()
        
        return descriptions
    
    def create_parameter_input(self, param):
        """Create appropriate input widget for a function parameter."""
        # Create input based on parameter annotation and default
        if param.annotation == int:
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            if param.default != param.empty:
                widget.setValue(param.default)
        elif param.annotation == float:
            widget = QLineEdit()
            widget.setPlaceholderText("Enter number (e.g., 1.5)")
            if param.default != param.empty:
                widget.setText(str(param.default))
        elif param.annotation == bool:
            widget = QCheckBox()
            if param.default != param.empty:
                widget.setChecked(param.default)
        else:
            # Default to string input
            widget = QLineEdit()
            if param.default != param.empty:
                widget.setText(str(param.default))
            else:
                widget.setPlaceholderText(f"Enter {param.name}")
        
        widget.setObjectName(param.name)
        return widget
    
    def get_config(self) -> tuple:
        """Return (file_path, function_name, positional_args, keyword_args) or None if not configured."""
        file_path = self.file_path.text().strip()
        function_name = self.function_combo.currentText()
        
        if not file_path or not function_name or not self.current_function:
            return None
        
        # Collect function arguments
        pos_args = []
        kwargs = {}
        
        if self.args_group.isVisible():
            for i in range(self.args_layout.count()):
                item = self.args_layout.itemAt(i)
                if item.labelItem() and item.fieldItem():
                    label_text = item.labelItem().widget().text().rstrip(':')
                    field_widget = item.fieldItem().widget()
                    
                    # Get value based on widget type
                    if isinstance(field_widget, QSpinBox):
                        kwargs[label_text] = field_widget.value()
                    elif isinstance(field_widget, QCheckBox):
                        kwargs[label_text] = field_widget.isChecked()
                    elif isinstance(field_widget, QLineEdit):
                        if field_widget.text().strip():
                            kwargs[label_text] = field_widget.text().strip()
        
        return file_path, function_name, pos_args, kwargs
    
    def is_configured(self) -> bool:
        """Return True if a valid function is selected."""
        return self.current_function is not None


class ProcessingThread(QThread):
    """Background thread for processing files to avoid GUI freezing."""
    
    finished = pyqtSignal(object)  # Emits RenameResult
    error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, config: RenameConfig):
        super().__init__()
        self.config = config
    
    def run(self):
        """Execute the batch rename operation in background."""
        try:
            processor = BatchRenameProcessor()
            result = processor.process(self.config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ExtractorPanel(QWidget):
    """Panel for configuring file name extraction."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Extractor type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Extractor Type:"))
        self.extractor_combo = QComboBox()
        self.extractor_combo.addItems(['split', 'regex', 'position', 'metadata', 'custom'])
        self.extractor_combo.currentTextChanged.connect(self.on_extractor_changed)
        type_layout.addWidget(self.extractor_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # Configuration area that changes based on extractor type
        self.config_area = QWidget()
        self.config_layout = QVBoxLayout(self.config_area)
        layout.addWidget(self.config_area)
        
        # Initialize with split extractor
        self.on_extractor_changed('split')
        
        layout.addStretch()
        self.setLayout(layout)
    
    def on_extractor_changed(self, extractor_type):
        """Update configuration UI based on selected extractor."""
        # Clear existing config widgets
        for i in reversed(range(self.config_layout.count())):
            self.config_layout.itemAt(i).widget().setParent(None)
        
        if extractor_type == 'split':
            self.config_layout.addWidget(QLabel("Split Character:"))
            self.split_char = QLineEdit("_")
            self.config_layout.addWidget(self.split_char)
            
            self.config_layout.addWidget(QLabel("Field Names (comma-separated):"))
            self.field_names = QLineEdit("dept,type,date")
            self.config_layout.addWidget(self.field_names)
            
        elif extractor_type == 'regex':
            self.config_layout.addWidget(QLabel("Regex Pattern (use named groups):"))
            self.regex_pattern = QLineEdit(r"(?P<dept>\w+)_(?P<type>\w+)_(?P<date>\d+)")
            self.config_layout.addWidget(self.regex_pattern)
            
        elif extractor_type == 'position':
            self.config_layout.addWidget(QLabel("Position Mappings:"))
            self.config_layout.addWidget(QLabel("Format: start-end:fieldname,start-end:fieldname"))
            self.position_map = QLineEdit("0-2:dept,3-5:code,6-:type")
            self.config_layout.addWidget(self.position_map)
            
        elif extractor_type == 'metadata':
            self.config_layout.addWidget(QLabel("Metadata Fields:"))
            self.created_date = QCheckBox("Creation Date")
            self.modified_date = QCheckBox("Modified Date")
            self.file_size = QCheckBox("File Size")
            self.config_layout.addWidget(self.created_date)
            self.config_layout.addWidget(self.modified_date)
            self.config_layout.addWidget(self.file_size)
            
        elif extractor_type == 'custom':
            # Use the reusable custom function selector
            self.custom_selector = CustomFunctionSelector("extractor function")
            self.config_layout.addWidget(self.custom_selector)
    
    def get_extractor_config(self) -> tuple:
        """Return (extractor_name, positional_args, keyword_args)."""
        extractor_type = self.extractor_combo.currentText()
        
        if extractor_type == 'split':
            pos_args = [self.split_char.text()]
            pos_args.extend(self.field_names.text().split(','))
            return extractor_type, pos_args, {}
            
        elif extractor_type == 'regex':
            return extractor_type, [self.regex_pattern.text()], {}
            
        elif extractor_type == 'position':
            return extractor_type, [self.position_map.text()], {}
            
        elif extractor_type == 'metadata':
            fields = []
            if self.created_date.isChecked():
                fields.append("created")
            if self.modified_date.isChecked():
                fields.append("modified")
            if self.file_size.isChecked():
                fields.append("size")
            return extractor_type, fields, {}
            
        elif extractor_type == 'custom':
            if not hasattr(self, 'custom_selector') or not self.custom_selector.is_configured():
                raise ValueError("Custom extractor requires a valid function selection")
            
            config = self.custom_selector.get_config()
            if config is None:
                raise ValueError("Custom extractor is not properly configured")
            
            file_path, function_name, pos_args, kwargs = config
            # For custom extractors, we pass the function name as a positional arg
            custom_pos_args = [function_name] + pos_args
            return file_path, custom_pos_args, kwargs


class ConverterPanel(QWidget):
    """Panel for configuring data conversion."""
    
    def __init__(self):
        super().__init__()
        self.converters = []  # List of converter configurations
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Add converter button
        add_button = QPushButton("Add Converter")
        add_button.clicked.connect(self.add_converter)
        layout.addWidget(add_button)
        
        # Scroll area for converters
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
    
    def add_converter(self):
        """Add a new converter configuration widget."""
        converter_widget = QGroupBox(f"Converter {len(self.converters) + 1}")
        main_layout = QVBoxLayout(converter_widget)
        
        # Header with type selection and remove button
        header_layout = QHBoxLayout()
        
        # Converter type (removed template and stringsmith)
        type_combo = QComboBox()
        type_combo.addItems(['pad_numbers', 'date_format', 'custom'])
        header_layout.addWidget(QLabel("Type:"))
        header_layout.addWidget(type_combo)
        
        header_layout.addStretch()
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_converter(converter_widget))
        header_layout.addWidget(remove_btn)
        
        main_layout.addLayout(header_layout)
        
        # Configuration area that changes based on converter type
        config_area = QWidget()
        config_layout = QFormLayout(config_area)
        main_layout.addWidget(config_area)
        
        # Connect type change to update config area
        type_combo.currentTextChanged.connect(
            lambda converter_type: self.update_converter_config(config_area, config_layout, converter_type)
        )
        
        # Initialize with first converter type
        self.update_converter_config(config_area, config_layout, type_combo.currentText())
        
        self.scroll_layout.addWidget(converter_widget)
        self.converters.append((type_combo, config_area))
    
    def update_converter_config(self, config_area, config_layout, converter_type):
        """Update configuration UI based on selected converter type."""
        # Clear existing config widgets
        for i in reversed(range(config_layout.count())):
            item = config_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                # Handle nested layouts
                nested_layout = item.layout()
                for j in reversed(range(nested_layout.count())):
                    nested_item = nested_layout.itemAt(j)
                    if nested_item.widget():
                        nested_item.widget().setParent(None)
        
        if converter_type == 'pad_numbers':
            # Field name input
            field_input = QLineEdit()
            field_input.setPlaceholderText("e.g., sequence, date, number")
            field_input.setObjectName("field")
            config_layout.addRow("Field:", field_input)
            
            # Width input with spinner
            width_input = QSpinBox()
            width_input.setRange(1, 10)
            width_input.setValue(3)
            width_input.setObjectName("width")
            config_layout.addRow("Width:", width_input)
            
        elif converter_type == 'date_format':
            # Field name input
            field_input = QLineEdit()
            field_input.setPlaceholderText("e.g., date, created_date")
            field_input.setObjectName("field")
            config_layout.addRow("Field:", field_input)
            
            # Input format
            input_format = QLineEdit("%Y%m%d")
            input_format.setObjectName("input_format")
            config_layout.addRow("Input Format:", input_format)
            
            # Output format
            output_format = QLineEdit("%Y-%m-%d")
            output_format.setObjectName("output_format")
            config_layout.addRow("Output Format:", output_format)
            
        elif converter_type == 'custom':
            # Use the reusable custom function selector
            custom_selector = CustomFunctionSelector("converter function")
            custom_selector.setObjectName("custom_selector")
            config_layout.addRow("Custom Function:", custom_selector)
    
    def remove_converter(self, widget):
        """Remove a converter widget."""
        widget.setParent(None)
        self.converters = [(combo, config_area) for combo, config_area in self.converters 
                          if combo.parent() != widget]
    
    def get_converter_configs(self) -> List[Dict]:
        """Return list of converter configurations."""
        configs = []
        for type_combo, config_area in self.converters:
            converter_type = type_combo.currentText()
            
            # Extract values from input widgets in config area
            pos_args = []
            kwargs = {}
            
            if converter_type == 'pad_numbers':
                field_widget = config_area.findChild(QLineEdit, "field")
                width_widget = config_area.findChild(QSpinBox, "width")
                
                if field_widget and field_widget.text().strip():
                    pos_args = [field_widget.text().strip(), str(width_widget.value())]
                    
            elif converter_type == 'date_format':
                field_widget = config_area.findChild(QLineEdit, "field")
                input_format_widget = config_area.findChild(QLineEdit, "input_format")
                output_format_widget = config_area.findChild(QLineEdit, "output_format")
                
                if field_widget and field_widget.text().strip():
                    pos_args = [
                        field_widget.text().strip(),
                        input_format_widget.text().strip() or "%Y%m%d",
                        output_format_widget.text().strip() or "%Y-%m-%d"
                    ]
                    
            elif converter_type == 'custom':
                custom_selector = config_area.findChild(CustomFunctionSelector, "custom_selector")
                
                if custom_selector and custom_selector.is_configured():
                    config = custom_selector.get_config()
                    if config:
                        file_path, function_name, pos_args, kwargs = config
                        
                        configs.append({
                            'name': file_path,  # Use file path as name for custom
                            'positional': [function_name] + pos_args,  # Function name as first arg
                            'keyword': kwargs
                        })
                        continue  # Skip the standard config addition below
            
            # Only add converter if we have valid configuration
            if pos_args:
                configs.append({
                    'name': converter_type,
                    'positional': pos_args,
                    'keyword': kwargs
                })
        
        return configs


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


class FilterPanel(QWidget):
    """Panel for configuring file filters."""
    
    def __init__(self):
        super().__init__()
        self.filters = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Add filter button
        add_button = QPushButton("Add Filter")
        add_button.clicked.connect(self.add_filter)
        layout.addWidget(add_button)
        
        # Scroll area for filters
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
    
    def add_filter(self):
        """Add a new filter configuration widget."""
        filter_widget = QGroupBox(f"Filter {len(self.filters) + 1}")
        main_layout = QVBoxLayout(filter_widget)
        
        # Header with invert checkbox, type selection, and remove button
        header_layout = QHBoxLayout()
        
        # Invert checkbox
        invert_check = QCheckBox("Exclude")
        header_layout.addWidget(invert_check)
        
        # Filter type
        type_combo = QComboBox()
        type_combo.addItems(['pattern', 'file-type', 'file-size', 'name-length', 'date-modified', 'custom'])
        header_layout.addWidget(QLabel("Type:"))
        header_layout.addWidget(type_combo)
        
        header_layout.addStretch()
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_filter(filter_widget))
        header_layout.addWidget(remove_btn)
        
        main_layout.addLayout(header_layout)
        
        # Configuration area that changes based on filter type
        config_area = QWidget()
        config_layout = QFormLayout(config_area)
        main_layout.addWidget(config_area)
        
        # Connect type change to update config area
        type_combo.currentTextChanged.connect(
            lambda filter_type: self.update_filter_config(config_area, config_layout, filter_type)
        )
        
        # Initialize with first filter type
        self.update_filter_config(config_area, config_layout, type_combo.currentText())
        
        self.scroll_layout.addWidget(filter_widget)
        self.filters.append((invert_check, type_combo, config_area))
    
    def update_filter_config(self, config_area, config_layout, filter_type):
        """Update configuration UI based on selected filter type."""
        # Clear existing config widgets
        for i in reversed(range(config_layout.count())):
            item = config_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                # Handle nested layouts
                nested_layout = item.layout()
                for j in reversed(range(nested_layout.count())):
                    nested_item = nested_layout.itemAt(j)
                    if nested_item.widget():
                        nested_item.widget().setParent(None)
        
        if filter_type == 'pattern':
            # Include pattern
            include_input = QLineEdit()
            include_input.setPlaceholderText("e.g., *.pdf, *_report_*")
            include_input.setObjectName("include")
            config_layout.addRow("Include Pattern:", include_input)
            
            # Exclude pattern (optional)
            exclude_input = QLineEdit()
            exclude_input.setPlaceholderText("e.g., *_backup_*, *_temp_*")
            exclude_input.setObjectName("exclude")
            config_layout.addRow("Exclude Pattern:", exclude_input)
            
        elif filter_type == 'file-type':
            # File types
            types_input = QLineEdit()
            types_input.setPlaceholderText("e.g., pdf,docx,xlsx")
            types_input.setObjectName("types")
            config_layout.addRow("File Types:", types_input)
            
        elif filter_type == 'file-size':
            # Min and max size
            min_size_input = QLineEdit()
            min_size_input.setPlaceholderText("e.g., 1MB, 500KB")
            min_size_input.setObjectName("min_size")
            config_layout.addRow("Min Size:", min_size_input)
            
            max_size_input = QLineEdit()
            max_size_input.setPlaceholderText("e.g., 100MB, 1GB")
            max_size_input.setObjectName("max_size")
            config_layout.addRow("Max Size:", max_size_input)
            
        elif filter_type == 'name-length':
            # Min and max length
            min_length_input = QSpinBox()
            min_length_input.setRange(0, 1000)
            min_length_input.setValue(0)
            min_length_input.setObjectName("min_length")
            config_layout.addRow("Min Length:", min_length_input)
            
            max_length_input = QSpinBox()
            max_length_input.setRange(0, 1000)
            max_length_input.setValue(255)
            max_length_input.setObjectName("max_length")
            config_layout.addRow("Max Length:", max_length_input)
            
        elif filter_type == 'date-modified':
            # Date threshold
            date_input = QLineEdit()
            date_input.setPlaceholderText("e.g., 2024-01-01, '1 week ago'")
            date_input.setObjectName("date_threshold")
            config_layout.addRow("Date Threshold:", date_input)
            
        elif filter_type == 'custom':
            # Use the reusable custom function selector
            custom_selector = CustomFunctionSelector("filter function")
            custom_selector.setObjectName("custom_selector")
            config_layout.addRow("Custom Function:", custom_selector)
    
    def remove_filter(self, widget):
        """Remove a filter widget."""
        widget.setParent(None)
        self.filters = [(invert, combo, config_area) for invert, combo, config_area in self.filters 
                       if combo.parent() != widget]
    
    def get_filter_configs(self) -> List[Dict]:
        """Return list of filter configurations."""
        configs = []
        for invert_check, type_combo, config_area in self.filters:
            filter_type = type_combo.currentText()
            pos_args = []
            
            if filter_type == 'pattern':
                include_widget = config_area.findChild(QLineEdit, "include")
                exclude_widget = config_area.findChild(QLineEdit, "exclude")
                
                if include_widget and include_widget.text().strip():
                    pos_args.append(include_widget.text().strip())
                    
                if exclude_widget and exclude_widget.text().strip():
                    pos_args.append(exclude_widget.text().strip())
                    
            elif filter_type == 'file-type':
                types_widget = config_area.findChild(QLineEdit, "types")
                
                if types_widget and types_widget.text().strip():
                    # Split comma-separated types into individual args
                    types = [t.strip() for t in types_widget.text().split(',') if t.strip()]
                    pos_args.extend(types)
                    
            elif filter_type == 'file-size':
                min_size_widget = config_area.findChild(QLineEdit, "min_size")
                max_size_widget = config_area.findChild(QLineEdit, "max_size")
                
                size_args = []
                if min_size_widget and min_size_widget.text().strip():
                    size_args.append(min_size_widget.text().strip())
                if max_size_widget and max_size_widget.text().strip():
                    size_args.append(max_size_widget.text().strip())
                
                if size_args:
                    pos_args = [','.join(size_args)]  # Pass as single comma-separated string
                    
            elif filter_type == 'name-length':
                min_length_widget = config_area.findChild(QSpinBox, "min_length")
                max_length_widget = config_area.findChild(QSpinBox, "max_length")
                
                if min_length_widget and max_length_widget:
                    pos_args = [f"{min_length_widget.value()},{max_length_widget.value()}"]
                    
            elif filter_type == 'date-modified':
                date_widget = config_area.findChild(QLineEdit, "date_threshold")
                
                if date_widget and date_widget.text().strip():
                    pos_args = [date_widget.text().strip()]
                    
            elif filter_type == 'custom':
                custom_selector = config_area.findChild(CustomFunctionSelector, "custom_selector")
                
                if custom_selector and custom_selector.is_configured():
                    config = custom_selector.get_config()
                    if config:
                        file_path, function_name, pos_args, kwargs = config
                        
                        configs.append({
                            'name': file_path,  # Use file path as name for custom
                            'positional': [function_name] + pos_args,  # Function name as first arg
                            'keyword': kwargs,
                            'inverted': invert_check.isChecked()
                        })
                        continue  # Skip the standard config addition below
            
            # Only add filter if we have valid configuration
            if pos_args:
                configs.append({
                    'name': filter_type,
                    'positional': pos_args,
                    'keyword': {},
                    'inverted': invert_check.isChecked()
                })
        
        return configs


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


class BatchRenameGUI(QMainWindow):
    """Main GUI application window."""
    
    def __init__(self):
        super().__init__()
        print("BatchRenameGUI.__init__ called - Version 3.0")  # Debug version check
        self.input_folder = None
        self.processing_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        print("=== STARTING INIT_UI - VERSION 3.0 ===")
        self.setWindowTitle("Batch File Rename Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Folder selection
        print("Creating folder selection")
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Input Folder:"))
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; }")
        folder_layout.addWidget(self.folder_label, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        
        self.recursive_check = QCheckBox("Include Subdirectories")
        folder_layout.addWidget(self.recursive_check)
        
        main_layout.addLayout(folder_layout)
        
        # Mode selection at the top
        print("Creating mode selection")
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Processing Mode:"))
        
        self.mode_group = QButtonGroup()
        self.modular_radio = QRadioButton("Modular Components")
        self.allinone_radio = QRadioButton("All-in-One Script")
        
        # Block signals during initialization to prevent early firing
        self.modular_radio.blockSignals(True)
        self.allinone_radio.blockSignals(True)
        
        print("Setting modular radio checked")
        self.modular_radio.setChecked(True)  # Default to modular
        print("Modular radio checked")
        
        self.mode_group.addButton(self.modular_radio)
        self.mode_group.addButton(self.allinone_radio)
        
        mode_layout.addWidget(self.modular_radio)
        mode_layout.addWidget(self.allinone_radio)
        mode_layout.addStretch()
        
        main_layout.addLayout(mode_layout)

        # Debug: Test if radio button changes are detected
        self.modular_radio.clicked.connect(lambda: print("Modular radio clicked"))
        self.allinone_radio.clicked.connect(lambda: print("All-in-one radio clicked"))

        # Main content area with splitter
        print("Creating main content area")
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Use QStackedWidget for clean mode switching
        self.config_stack = QStackedWidget()
        
        # Create and add both config panels
        print("About to create config panels")
        self.modular_config = self.create_modular_config()
        self.allinone_config = self.create_allinone_config()
        print("Config panels created")
        
        self.config_stack.addWidget(self.modular_config)  # Index 0
        self.config_stack.addWidget(self.allinone_config)  # Index 1
        self.config_stack.setCurrentIndex(0)  # Default to modular
        
        splitter.addWidget(self.config_stack)
        
        # Right panel - Preview
        print("Creating preview panel")
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        preview_layout.addWidget(QLabel("Preview:"))
        self.preview_table = PreviewTable()
        preview_layout.addWidget(self.preview_table)
        
        # Preview and Execute buttons
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Update Preview")
        self.preview_btn.clicked.connect(self.update_preview)
        button_layout.addWidget(self.preview_btn)
        
        self.execute_btn = QPushButton("Execute Rename")
        self.execute_btn.clicked.connect(self.execute_rename)
        self.execute_btn.setEnabled(False)
        button_layout.addWidget(self.execute_btn)
        
        button_layout.addStretch()
        preview_layout.addLayout(button_layout)
        
        splitter.addWidget(preview_widget)
        
        # Set splitter proportions (30% config, 70% preview)
        splitter.setSizes([360, 840])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        print("Creating status bar")
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")
        
        # Connect mode change signals AFTER everything is initialized
        # Unblock signals and connect them
        print("Connecting mode change signals")
        self.modular_radio.blockSignals(False)
        self.allinone_radio.blockSignals(False)
        
        self.modular_radio.toggled.connect(self.on_mode_changed)
        self.allinone_radio.toggled.connect(self.on_mode_changed)
        
        print("GUI initialization complete - signals connected")
    
    def create_modular_config(self):
        """Create the modular configuration tab widget."""
        print("Creating modular config")
        config_panel = QTabWidget()
        
        # Extractor tab
        self.extractor_panel = ExtractorPanel()
        config_panel.addTab(self.extractor_panel, "Extractor")
        
        # Converter tab
        self.converter_panel = ConverterPanel()
        config_panel.addTab(self.converter_panel, "Converters")
        
        # Template tab
        self.template_panel = TemplatePanel()
        config_panel.addTab(self.template_panel, "Template")
        
        # Filter tab
        self.filter_panel = FilterPanel()
        config_panel.addTab(self.filter_panel, "Filters")
        
        print("Modular config created")
        return config_panel
    
    def create_allinone_config(self):
        """Create the all-in-one script configuration panel."""
        print("Creating all-in-one config")
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title_label = QLabel("All-in-One Script Configuration")
        title_label.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Select a Python file and function that handles extraction, conversion, and formatting in one step.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("QLabel { color: #666; }")
        layout.addWidget(desc_label)
        
        # Custom function selector
        self.allinone_selector = CustomFunctionSelector("all-in-one processing function")
        layout.addWidget(self.allinone_selector)
        
        layout.addStretch()
        print("All-in-one config created")
        return panel
        
        file_layout.addLayout(file_select_layout)
        layout.addWidget(file_group)
        
        # Function selection
        func_group = QGroupBox("Function Selection")
        func_layout = QVBoxLayout(func_group)
        
        func_select_layout = QHBoxLayout()
        func_select_layout.addWidget(QLabel("Function:"))
        self.allinone_function_combo = QComboBox()
        self.allinone_function_combo.setEnabled(False)
        self.allinone_function_combo.currentTextChanged.connect(self.on_function_selected)
        func_select_layout.addWidget(self.allinone_function_combo)
        func_select_layout.addStretch()
        func_layout.addLayout(func_select_layout)
        
        # Validation status
        self.validation_label = QLabel("")
        self.validation_label.setWordWrap(True)
        func_layout.addWidget(self.validation_label)
        
        layout.addWidget(func_group)
        
        # Function arguments
        self.args_group = QGroupBox("Function Arguments")
        self.args_layout = QFormLayout(self.args_group)
        self.args_group.setVisible(False)
        layout.addWidget(self.args_group)
        
        layout.addStretch()
        print("All-in-one config created")
        return panel
    
    def on_mode_changed(self, checked):
        """Handle switching between modular and all-in-one modes."""
        print(f"on_mode_changed called: checked={checked}, modular_checked={self.modular_radio.isChecked()}")
        
        # Use QStackedWidget for clean switching
        if hasattr(self, 'config_stack'):
            if self.modular_radio.isChecked():
                self.config_stack.setCurrentIndex(0)  # Modular config
                print("Switched to modular config")
            else:
                self.config_stack.setCurrentIndex(1)  # All-in-one config
                print("Switched to all-in-one config")
        else:
            print("config_stack not ready yet")
    
    def browse_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Input Folder", str(Path.home())
        )
        if folder:
            self.input_folder = Path(folder)
            self.folder_label.setText(str(self.input_folder))
            self.preview_btn.setEnabled(True)
            self.statusbar.showMessage(f"Selected folder: {folder}")
    
    def browse_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Input Folder", str(Path.home())
        )
        if folder:
            self.input_folder = Path(folder)
            self.folder_label.setText(str(self.input_folder))
            self.preview_btn.setEnabled(True)
            self.statusbar.showMessage(f"Selected folder: {folder}")
    
    def update_preview(self):
        """Update the preview table with potential renames."""
        if not self.input_folder:
            QMessageBox.warning(self, "Error", "Please select an input folder first.")
            return
        
        try:
            config = self.build_config(preview_mode=True)
            self.statusbar.showMessage("Updating preview...")
            
            # Run processing in background thread
            self.processing_thread = ProcessingThread(config)
            self.processing_thread.finished.connect(self.on_preview_finished)
            self.processing_thread.error.connect(self.on_processing_error)
            self.processing_thread.start()
            
            self.preview_btn.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", str(e))
    
    def on_preview_finished(self, result):
        """Handle preview processing completion."""
        self.preview_table.update_preview(result.preview_data)
        
        message = f"Preview: {result.files_analyzed} files analyzed, {result.files_to_rename} would be renamed"
        if result.collisions > 0:
            message += f", {result.collisions} conflicts detected"
        
        self.statusbar.showMessage(message)
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(result.files_to_rename > 0)
        
        if result.collisions > 0:
            QMessageBox.warning(self, "Conflicts Detected", 
                              f"Found {result.collisions} naming conflicts. "
                              "Please review the configuration.")
    
    def execute_rename(self):
        """Execute the actual file renames."""
        # Confirm with user
        reply = QMessageBox.question(
            self, "Confirm Rename",
            "Are you sure you want to rename the files?\n"
            "This operation cannot be easily undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                config = self.build_config(preview_mode=False)
                self.statusbar.showMessage("Executing renames...")
                
                # Run processing in background thread
                self.processing_thread = ProcessingThread(config)
                self.processing_thread.finished.connect(self.on_execute_finished)
                self.processing_thread.error.connect(self.on_processing_error)
                self.processing_thread.start()
                
                self.execute_btn.setEnabled(False)
                self.preview_btn.setEnabled(False)
                
            except Exception as e:
                QMessageBox.critical(self, "Configuration Error", str(e))
    
    def on_execute_finished(self, result):
        """Handle execution completion."""
        message = f"Execution complete: {result.files_renamed} files renamed"
        if result.errors > 0:
            message += f", {result.errors} errors"
        
        self.statusbar.showMessage(message)
        
        if result.errors > 0:
            QMessageBox.warning(self, "Execution Complete", 
                              f"Renamed {result.files_renamed} files with {result.errors} errors.")
        else:
            QMessageBox.information(self, "Success", 
                                  f"Successfully renamed {result.files_renamed} files.")
        
        # Re-enable buttons and clear preview
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(False)
        self.preview_table.setRowCount(0)
    
    def on_processing_error(self, error_msg):
        """Handle processing errors."""
        self.statusbar.showMessage("Error occurred")
        QMessageBox.critical(self, "Processing Error", error_msg)
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(False)
    
    def build_config(self, preview_mode=True) -> RenameConfig:
        """Build RenameConfig from GUI settings."""
        if not self.input_folder:
            raise ValueError("No input folder selected")
        
        if self.modular_radio.isChecked():
            # Modular mode - use existing logic
            return self.build_modular_config(preview_mode)
        else:
            # All-in-one mode
            return self.build_allinone_config(preview_mode)
    
    def build_modular_config(self, preview_mode=True) -> RenameConfig:
        """Build config for modular mode."""
        # Get extractor configuration
        extractor_name, pos_args, kwargs = self.extractor_panel.get_extractor_config()
        extractor_args = {
            'positional': pos_args,
            'keyword': kwargs
        }
        
        # Get converter configurations
        converters = self.converter_panel.get_converter_configs()
        
        # Get template configuration and add to converters if enabled
        template_config = self.template_panel.get_template_config()
        if template_config:
            converters.append(template_config)
        
        # Require at least one converter (including template)
        if not converters:
            raise ValueError("At least one converter or template is required")
        
        # Get filter configurations
        filters = self.filter_panel.get_filter_configs()
        
        return RenameConfig(
            input_folder=self.input_folder,
            extractor=extractor_name,
            extractor_args=extractor_args,
            converters=converters,
            filters=filters,
            recursive=self.recursive_check.isChecked(),
            preview_mode=preview_mode
        )
        """Build config for all-in-one mode."""
        if not self.allinone_selector.is_configured():
            raise ValueError("All-in-one script function must be selected")
        
        config = self.allinone_selector.get_config()
        if config is None:
            raise ValueError("All-in-one script is not properly configured")
        
        file_path, function_name, pos_args, kwargs = config
        
        # For all-in-one mode, we use a special extractor that calls the custom function
        # The custom function will handle extraction, conversion, and formatting
        return RenameConfig(
            input_folder=self.input_folder,
            extractor=file_path,  # Use file path as extractor
            extractor_args={
                'positional': [function_name] + pos_args,  # Function name as first arg
                'keyword': kwargs  # Additional function arguments
            },
            converters=[],  # No separate converters needed
            filters=[],  # No filters in all-in-one mode for now
            recursive=self.recursive_check.isChecked(),
            preview_mode=preview_mode
        )


def main():
    """Main entry point for GUI application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Batch File Rename Tool")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = BatchRenameGUI()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())