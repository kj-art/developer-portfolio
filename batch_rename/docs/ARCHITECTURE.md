# Architecture Documentation

Comprehensive overview of the Batch Rename Tool's architecture, design decisions, and extensibility patterns.

## High-Level Architecture

### System Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  User Interface │    │  Core Processing │    │  StringSmith    │
│                 │    │                  │    │  Templates      │
│  ┌─────────────┐│    │ ┌──────────────┐ │    │                 │
│  │     CLI     ││────│ │ Step Factory │ │    │ ┌─────────────┐ │
│  └─────────────┘│    │ └──────────────┘ │    │ │ Conditional │ │
│                 │    │                  │    │ │ Formatting  │ │
│  ┌─────────────┐│    │ ┌──────────────┐ │────│ │ Engine      │ │
│  │     GUI     ││────│ │  Processor   │ │    │ └─────────────┘ │
│  └─────────────┘│    │ └──────────────┘ │    │                 │
│                 │    │                  │    │ ┌─────────────┐ │
│                 │    │ ┌──────────────┐ │    │ │   Logging   │ │
│                 │    │ │    Config    │ │    │ │ Integration │ │
│                 │    │ └──────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Design Principles

#### 1. **Separation of Concerns**
- **Core Logic**: Business logic isolated from UI concerns
- **UI Layer**: CLI and GUI as thin wrappers around core functionality
- **Processing Steps**: Each step type handles one responsibility
- **Configuration**: Centralized configuration management

#### 2. **Extensibility**
- **Step Factory Pattern**: Easy addition of new step types
- **Custom Functions**: User-defined logic integration
- **Plugin Architecture**: Modular function loading
- **Template System**: Flexible formatting with StringSmith

#### 3. **Safety & Reliability**
- **Preview-First**: Default to safe preview mode
- **Immutable Processing**: No side effects during preview
- **Collision Detection**: Comprehensive conflict identification
- **Error Isolation**: Failures don't cascade

#### 4. **Performance**
- **Lazy Evaluation**: Process only when needed
- **Background Threading**: Non-blocking GUI operations
- **Template Caching**: StringSmith optimization
- **Memory Efficiency**: Minimal overhead for large file sets

## Core Components

### Processing Pipeline

The heart of the system is a linear processing pipeline:

```
Input Files → Filters → Extractor → Converters → Template → Output Names
     ↓           ↓         ↓           ↓           ↓           ↓
   File List   Filter   Extract    Transform   Format    New Names
              Boolean   Dict[str]   Dict[str]   String    String
```

#### Pipeline Stages

1. **File Discovery**: Scan input directory for target files
2. **Filtering**: Apply AND-logic filters to determine which files to process
3. **Extraction**: Parse filenames to extract structured data
4. **Conversion**: Transform extracted data through converter chain
5. **Templating**: Format final filename from converted data
6. **Collision Detection**: Identify naming conflicts
7. **Execution**: Perform actual renames (or generate preview)

#### Data Flow

```python
# Stage 1: File Discovery
files: List[Path] = get_files(config.input_folder)

# Stage 2: Filtering  
for file in files:
    context = ProcessingContext(filename, file_path, metadata)
    if not all(filter_func(context) for filter_func in filters):
        continue  # Skip this file
    
    # Stage 3: Extraction
    extracted_data = extractor(context)
    context.extracted_data = extracted_data
    
    # Stage 4: Conversion (chain multiple converters)
    converted_data = extracted_data.copy()
    for converter in converters:
        context.extracted_data = converted_data
        converted_data = converter(context)
    
    # Stage 5: Templating
    context.extracted_data = converted_data
    new_filename = template(context)
    
    # Stage 6: Collision Detection
    check_collisions(new_filename, existing_files, renamed_files)
```

### Step Factory Pattern

The Step Factory provides a unified interface for creating and managing processing steps.

#### Factory Hierarchy

```
StepFactory (Static Factory)
├── get_step(step_type) → ProcessingStep
├── create_executable(step_type, config) → Callable
├── get_builtin_functions(step_type) → Dict[str, Callable]
└── validate_custom_function(step_type, function) → ValidationResult

ProcessingStep (Abstract Base)
├── ExtractorStep
├── ConverterStep  
├── FilterStep
├── TemplateStep
└── AllInOneStep
```

#### Step Creation Flow

```python
# 1. Factory method receives configuration
StepFactory.create_executable(StepType.EXTRACTOR, config)

# 2. Factory gets appropriate step instance (singleton)
step = StepFactory.get_step(StepType.EXTRACTOR)  # → ExtractorStep()

# 3. Step instance creates executable function
executable = step.create_executable(config)

# 4. Step handles built-in vs custom function loading
if config.name.endswith('.py'):
    function = load_custom_function(config.name, config.positional_args[0])
    validate_custom_function(function)
else:
    function = step.builtin_functions[config.name]

# 5. Step creates wrapper with standard calling convention
def wrapper(context: ProcessingContext):
    return function(context, config.positional_args, **config.keyword_args)

return wrapper
```

#### Benefits of Step Factory

- **Uniform Interface**: All step types created through same API
- **Type Safety**: Step-specific validation for custom functions
- **Extensibility**: Easy to add new step types
- **Testing**: Individual step types can be tested in isolation
- **Performance**: Singleton pattern reuses step instances

### Processing Context

The ProcessingContext is the data container that flows through the pipeline.

#### Context Evolution

```python
# Initial creation (File Discovery)
context = ProcessingContext(
    filename="HR_employee_data_2024.pdf",
    file_path=Path("/files/HR_employee_data_2024.pdf"),
    metadata={'size': 1024, 'created_timestamp': 1704067200.0}
)

# After extraction
context.extracted_data = {
    'dept': 'HR', 
    'type': 'employee', 
    'category': 'data', 
    'year': '2024'
}

# After conversion chain
context.extracted_data = {
    'dept': 'HR',           # unchanged
    'type': 'EMPLOYEE',     # case conversion
    'category': 'data',     # unchanged
    'year': '2024'          # unchanged
}

# Template uses final converted data
new_name = template(context)  # "HR_EMPLOYEE_data_2024"
```

#### Context Properties

```python
@property
def base_name(self) -> str:
    """Filename without extension for processing."""
    return self.file_path.stem

@property
def extension(self) -> str:
    """File extension (preserved automatically)."""
    return self.file_path.suffix

def has_extracted_data(self) -> bool:
    """Check if extraction has occurred."""
    return self.extracted_data is not None and bool(self.extracted_data)
```

## Configuration System

### Configuration Hierarchy

```
RenameConfig (Top Level)
├── input_folder: Path
├── extractor: str + extractor_args: Dict
├── converters: List[Dict] (stackable)
├── template: Dict (optional)
├── filters: List[Dict] (stackable)  
├── execution_options: preview_mode, recursive, collision_handling
└── advanced_options: extract_and_convert, logging

StepConfig (Individual Steps)
├── name: str (function name or file path)
├── positional_args: List[Any]
├── keyword_args: Dict[str, Any]
└── custom_function_path: Optional[str]
```

### Configuration Validation

```python
# CLI argument parsing validates syntax
"split,_,dept,type,date" → StepConfig(
    name='split',
    positional_args=['_', 'dept', 'type', 'date'],
    keyword_args={}
)

# Step factory validates function existence and arguments
StepFactory.create_executable(StepType.EXTRACTOR, config)
# → Validates 'split' exists and arguments are correct

# Custom function validation checks signatures
validation = StepFactory.validate_custom_function(step_type, function)
# → Ensures function has correct signature for step type
```

## StringSmith Integration

### Template Engine Architecture

StringSmith provides advanced conditional formatting with graceful missing data handling.

#### Template Processing Pipeline

```
Template String → Parser → AST → Optimizer → Formatter → Output
      ↓             ↓       ↓        ↓           ↓         ↓
"{{dept}}_{{id}}" → Sections → Cache → Render → "HR_123" or "HR"
```

#### Conditional Sections

```python
# Template: "{{Department: ;dept;}} {{(ID: ;id;}}"
# Data: {'dept': 'HR'}  # Missing 'id'

# Processing:
# Section 1: "{{Department: ;dept;}}" → "Department: HR " (dept exists)
# Section 2: "{{(ID: ;id;}}" → "" (id missing, section disappears)
# Result: "Department: HR "
```

#### StringSmith Benefits

- **Graceful Degradation**: Missing data doesn't break templates
- **Rich Formatting**: Colors, emphasis, conditional logic
- **Performance**: Templates compiled once, reused efficiently
- **Extensibility**: Custom functions for complex logic

### Logging Integration

StringSmith powers the logging system with conditional formatting:

```python
# Log template automatically adapts to available data:
template = "{{#level_color;[;levelname;]}} {{message}}{{ (;file_count; files)}}{{ in ;duration;$format_duration}}"

# With full data:
# "[INFO] Processing complete (150 files) in 2.3s"

# With partial data:  
# "[INFO] Processing complete"

# The template gracefully handles missing file_count and duration
```

## GUI Architecture

### Component Hierarchy

```
BatchRenameGUI (Main Window)
├── MenuBar + ToolBar
├── ConfigurationArea
│   ├── FolderSelection
│   ├── ModeSelection (Modular vs All-in-One)
│   └── ConfigStack
│       ├── ModularConfig
│       │   ├── ExtractorPanel (SingleStepPanel)
│       │   ├── ConverterPanel (StackableStepPanel)
│       │   ├── TemplatePanel (SingleStepPanel)
│       │   └── FilterPanel (StackableStepPanel)
│       └── AllInOneConfig
│           └── AllInOnePanel
├── PreviewArea
│   ├── PreviewTable (old → new names)
│   └── ProgressBar
└── ControlButtons
    ├── PreviewButton
    ├── ExecuteButton
    └── ClearButton
```

### Panel Architecture

#### Base Panel Classes

```python
# Abstract base for all configuration panels
class StepPanel(ABC):
    @abstractmethod
    def get_config(self) -> Dict[str, Any]
    
    @abstractmethod
    def validate_config(self) -> bool

# Single-instance steps (Extractor, Template)
class SingleStepPanel(StepPanel):
    # One function selector + parameter inputs

# Multi-instance steps (Converter, Filter)  
class StackableStepPanel(StepPanel):
    # Add/Remove buttons + list of configurations
```

#### Dynamic Panel Generation

```python
# Panels automatically adapt to selected functions
def on_function_changed(self, function_name):
    # Get function from step factory
    step = StepFactory.get_step(self.step_type)
    
    if function_name.endswith('.py'):
        # Custom function - load and inspect signature
        function = load_custom_function(function_name, 'function_name')
        parameters = inspect.signature(function).parameters
    else:
        # Built-in function - get predefined configuration
        self.create_builtin_config(function_name)
    
    # Generate input widgets for parameters
    self.create_parameter_inputs(parameters)
```

### Background Processing

```python
class ProcessingThread(QThread):
    """Background thread prevents GUI freezing during operations."""
    
    finished = pyqtSignal(object)  # RenameResult
    error = pyqtSignal(str)        # Error message
    
    def run(self):
        try:
            processor = BatchRenameProcessor()
            result = processor.process(self.config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# Main GUI connects to signals
thread.finished.connect(self.on_processing_finished)
thread.error.connect(self.on_processing_error)
```

## Error Handling Strategy

### Error Categories

#### 1. **Configuration Errors** (Early Detection)
- Invalid function names
- Missing required arguments
- File path errors
- Caught during configuration validation

#### 2. **Processing Errors** (Runtime)
- Custom function failures
- Data transformation errors
- File system errors
- Caught during pipeline execution

#### 3. **System Errors** (Environment)
- Permission denied errors
- Disk space issues
- Memory allocation failures
- Network drive problems

### Error Handling Implementation

```python
# Hierarchical error handling with context
try:
    result = processor.process(config)
except ConfigurationError as e:
    # Configuration problems - show user-friendly message
    logger.error("Configuration invalid", extra={'error': str(e), 'config': config})
    return f"Configuration error: {e}"
    
except ProcessingError as e:
    # Runtime processing problems - include file context
    logger.error("Processing failed", extra={
        'error': str(e),
        'file_path': e.context.get('file_path'),
        'step_type': e.context.get('step_type')
    })
    return f"Processing error: {e}"
    
except SystemError as e:
    # System-level problems - suggest solutions
    logger.error("System error", extra={'error': str(e)})
    return f"System error: {e}. Check permissions and disk space."
```

### Error Recovery

```python
# Graceful degradation strategies
def process_with_recovery(self, config):
    results = []
    errors = []
    
    for file_path in files:
        try:
            result = process_single_file(file_path, config)
            results.append(result)
        except ProcessingError as e:
            # Log error but continue with other files
            errors.append({'file': file_path, 'error': str(e)})
            continue
    
    return RenameResult(
        files_processed=len(results),
        errors=len(errors),
        error_details=errors
    )
```

## Performance Considerations

### Scalability Strategies

#### Memory Management
```python
# For large file sets, use generators instead of lists
def get_files_iterator(folder: Path, recursive: bool):
    """Generator that yields files on demand."""
    if recursive:
        yield from folder.rglob('*')
    else:
        yield from folder.glob('*')

# Process files in chunks to control memory usage
def process_in_chunks(files, chunk_size=1000):
    for i in range(0, len(files), chunk_size):
        chunk = files[i:i+chunk_size]
        yield process_chunk(chunk)
```

#### Template Optimization
```python
# StringSmith templates are compiled once and cached
class TemplateCache:
    _cache = {}
    
    @classmethod
    def get_formatter(cls, template_string):
        if template_string not in cls._cache:
            cls._cache[template_string] = TemplateFormatter(template_string)
        return cls._cache[template_string]
```

#### Background Processing
```python
# GUI uses worker threads to prevent blocking
class BackgroundProcessor:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_async(self, config, callback):
        future = self.executor.submit(self.process, config)
        future.add_done_callback(callback)
```

### Performance Metrics

The system tracks performance metrics for optimization:

```python
@dataclass
class PerformanceMetrics:
    files_per_second: float
    memory_usage_mb: float
    template_cache_hits: int
    error_rate: float
    
    # Benchmark targets:
    # - Small sets (<100 files): >1000 files/sec
    # - Medium sets (100-1000 files): >500 files/sec  
    # - Large sets (1000+ files): >100 files/sec
    # - Memory usage: <50MB + 1KB per file
```

## Extension Points

### Adding New Step Types

To add a new step type (e.g., "VALIDATOR"):

1. **Add to StepType enum:**
```python
class StepType(Enum):
    FILTER = "filter"
    EXTRACTOR = "extractor" 
    CONVERTER = "converter"
    TEMPLATE = "template"
    VALIDATOR = "validator"  # New step type
```

2. **Implement ProcessingStep subclass:**
```python
class ValidatorStep(ProcessingStep):
    @property
    def step_type(self) -> StepType:
        return StepType.VALIDATOR
    
    @property
    def is_stackable(self) -> bool:
        return True  # Multiple validators allowed
    
    def create_executable(self, config: StepConfig) -> Callable:
        # Implementation for creating validator functions
```

3. **Register in StepFactory:**
```python
_STEP_CLASSES[StepType.VALIDATOR] = ValidatorStep
```

4. **Add to processing pipeline:**
```python
# Insert at appropriate point in pipeline
validators = create_validator_steps(config.validators)
for validator in validators:
    validation_result = validator(context)
    if not validation_result.is_valid:
        errors.append(validation_result.error)
```

### Adding Built-in Functions

To add a new built-in extractor:

1. **Implement function with required signature:**
```python
def csv_extractor(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """Extract data from CSV-like filename patterns."""
    # Implementation here
    return extracted_data
```

2. **Register in BUILTIN_EXTRACTORS:**
```python
BUILTIN_EXTRACTORS = {
    'split': split_extractor,
    'regex': regex_extractor,
    'csv': csv_extractor,  # New function
    # ...
}
```

3. **Add tests:**
```python
def test_csv_extractor():
    context = ProcessingContext(...)
    result = csv_extractor(context, ['delimiter', 'field1', 'field2'])
    assert result == expected_data
```

### Custom Function Development

#### Development Workflow

1. **Create function file:**
```python
# custom_extractors.py
def business_extractor(context: ProcessingContext, 
                      department_codes: str = "") -> Dict[str, Any]:
    """Extract business-specific data patterns."""
    # Implementation
    return extracted_data
```

2. **Test function:**
```python
from batch_rename.core.processing_context import ProcessingContext
from pathlib import Path

context = ProcessingContext(
    filename="ACCT_Q1_2024_REPORT_v2.pdf",
    file_path=Path("test.pdf"),
    metadata={'size': 1024}
)

result = business_extractor(context, "ACCT,SALES,MKTG")
print(result)  # {'dept': 'ACCT', 'quarter': 'Q1', 'year': '2024', ...}
```

3. **Use in CLI:**
```bash
python main.py --extractor custom_extractors.py,business_extractor,"ACCT,SALES,MKTG"
```

## Security Considerations

### Code Execution Safety

Custom functions execute arbitrary Python code, so security measures are important:

```python
# Function validation includes basic safety checks
def validate_custom_function_safety(function_path: Path) -> bool:
    """Basic safety validation for custom functions."""
    
    # Check file permissions
    if not function_path.exists() or not function_path.is_file():
        raise SecurityError(f"Function file not found: {function_path}")
    
    # Basic static analysis (can be extended)
    source = function_path.read_text()
    
    # Flag potentially dangerous imports
    dangerous_imports = ['os', 'subprocess', 'shutil', 'sys', '__import__']
    for imp in dangerous_imports:
        if f"import {imp}" in source:
            logger.warning(f"Custom function imports potentially dangerous module: {imp}")
    
    return True
```

### File System Safety

```python
# Prevent directory traversal and unsafe operations
def validate_file_path(file_path: Path, base_folder: Path) -> bool:
    """Ensure file operations stay within base folder."""
    try:
        file_path.resolve().relative_to(base_folder.resolve())
        return True
    except ValueError:
        raise SecurityError(f"File path outside base folder: {file_path}")
```

## Testing Strategy

### Test Pyramid

```
                    E2E Tests (GUI + CLI)
                   /                    \
                 /                        \
              Integration Tests              \
            (Full Pipeline)                   \
           /                                   \
         /                                      \
    Unit Tests                              Performance Tests
   (Individual                             (Scalability &
    Components)                             Memory Usage)
```

### Test Categories

#### Unit Tests
- Individual extractors, converters, templates, filters
- Step factory functionality
- Configuration validation
- Error handling

#### Integration Tests  
- Full pipeline execution
- CLI argument parsing
- GUI workflow simulation
- Custom function loading

#### Performance Tests
- Large file set processing
- Memory usage monitoring  
- Template rendering performance
- Collision detection efficiency

#### End-to-End Tests
- Complete CLI workflows
- GUI user interactions
- Error recovery scenarios
- Cross-platform compatibility

## Deployment Architecture

### Distribution Strategies

#### Development Mode
```bash
# Editable installation for development
pip install -e .
python main.py --help
```

#### Standalone Executable
```bash
# PyInstaller packaging
pyinstaller --onefile --windowed main.py
./dist/batch_rename --help
```

#### Container Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENTRYPOINT ["python", "main.py"]
```

### Configuration Management

#### Environment-Specific Settings
```python
# config/environments.py
ENVIRONMENTS = {
    'development': {
        'log_level': 'DEBUG',
        'enable_colors': True,
        'performance_monitoring': True
    },
    'production': {
        'log_level': 'WARNING', 
        'enable_colors': False,
        'performance_monitoring': False
    }
}
```

## Future Enhancements

### Planned Features

#### Advanced Collision Resolution
- Automatic numbering strategies
- User-configurable resolution patterns
- Conflict preview with suggested solutions

#### Workflow Automation
- Batch configuration files
- Scheduled processing
- Watch folder automation

#### Enhanced Custom Functions
- Function validation IDE
- Visual function builder
- Function marketplace/sharing

#### Performance Optimization
- Parallel processing for large file sets
- Database-backed file indexing
- Incremental processing

### Architectural Evolution

#### Microservices Architecture
For enterprise deployment, the system could be split into services:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │    │  Processing     │    │  Function       │
│   Service       │────│  Service        │────│  Registry       │
│   (React/Vue)   │    │  (FastAPI)      │    │  Service        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   File Storage  │
                    │   Service       │
                    │   (S3/MinIO)    │
                    └─────────────────┘
```

#### Plugin Architecture
```python
# Future plugin system
class PluginManager:
    def load_plugin(self, plugin_path: Path):
        """Load external plugins with isolated environments."""
        
    def register_step_type(self, step_type: str, implementation: Type[ProcessingStep]):
        """Register new step types from plugins."""
```

---

**This architecture documentation provides a comprehensive understanding of the system's design, implementation patterns, and future evolution possibilities.**