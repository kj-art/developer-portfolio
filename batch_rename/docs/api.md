# API Reference

Complete API documentation for the Batch Rename Tool core components.

## Core Classes

### ProcessingContext

The central data container that flows through the processing pipeline.

```python
from batch_rename.core.processing_context import ProcessingContext

@dataclass
class ProcessingContext:
    """
    Context object containing all data for custom functions.
    
    This replaces multiple separate arguments with a single consistent
    parameter across all function types.
    """
    filename: str                                    # Full filename with extension
    file_path: Path                                  # Complete file path
    metadata: Dict[str, Any]                        # File metadata (size, dates)
    extracted_data: Optional[Dict[str, Any]] = None # Extracted field data
```

#### Properties

```python
# Derived properties
context.base_name      # Filename without extension
context.extension      # File extension (including dot)
context.file_size      # File size in bytes
context.created_timestamp    # Creation timestamp
context.modified_timestamp   # Modification timestamp

# Methods
context.has_extracted_data() -> bool
context.get_extracted_field(field_name: str, default: Any = None) -> Any
```

#### Usage Example

```python
def my_extractor(context: ProcessingContext) -> Dict[str, Any]:
    # Access filename: context.filename = "report.pdf"
    # Access base name: context.base_name = "report"
    # Access extension: context.extension = ".pdf"
    # Access file size: context.file_size = 1024
    
    return {'type': 'report', 'date': '2024-01-15'}
```

### RenameConfig

Configuration object for batch rename operations.

```python
from batch_rename.core.config import RenameConfig

@dataclass
class RenameConfig:
    """Configuration for a batch rename operation."""
    
    # Required fields
    input_folder: Path                               # Source directory
    extractor: str                                   # Extractor function name
    extractor_args: Dict[str, Any]                  # Extractor arguments
    
    # Optional processing steps
    converters: List[Dict[str, Any]] = field(default_factory=list)
    template: Optional[Dict[str, Any]] = None
    filters: List[Dict[str, Any]] = field(default_factory=list)
    
    # Execution options
    recursive: bool = False                          # Process subdirectories
    preview_mode: bool = True                       # Show preview vs execute
    
    # Collision handling
    on_existing_collision: str = 'error'            # skip|error|append_number
    on_internal_collision: str = 'error'            # skip|error|append_number
    
    # Advanced options
    extract_and_convert: Optional[Dict[str, Any]] = None  # All-in-one function
```

#### Factory Methods

```python
# Create from CLI arguments
config = RenameConfig.from_cli_args(
    input_folder="/path/to/files",
    extractor="split,_,dept,type,date",
    converters=["case,dept,upper", "pad_numbers,id,3"],
    template="join,dept,type,date,separator=-"
)

# Create programmatically
config = RenameConfig(
    input_folder=Path("/path/to/files"),
    extractor="split",
    extractor_args={
        'positional': ['_', 'dept', 'type', 'date'],
        'keyword': {}
    },
    converters=[
        {
            'name': 'case',
            'positional': ['dept', 'upper'],
            'keyword': {}
        }
    ]
)
```

### RenameResult

Results and metrics from batch rename operations.

```python
from batch_rename.core.config import RenameResult

@dataclass
class RenameResult:
    """Results from a batch rename operation."""
    
    # Analysis results
    files_analyzed: int = 0                         # Total files examined
    files_to_rename: int = 0                       # Files with changes
    files_filtered_out: int = 0                    # Files excluded by filters
    
    # Execution results
    files_renamed: int = 0                         # Successfully renamed
    errors: int = 0                                # Failed operations
    
    # Collision information
    collisions: int = 0                            # Total collision count
    existing_file_collisions: List[Dict] = field(default_factory=list)
    internal_collisions: List[Dict] = field(default_factory=list)
    
    # Operation details
    processing_time: float = 0.0                   # Duration in seconds
    preview_data: List[Dict] = field(default_factory=list)  # Old→new mappings
    error_details: List[Dict] = field(default_factory=list) # Error information
```

#### Computed Properties

```python
result.success_rate          # Percentage of successful renames
result.filtering_efficiency  # Percentage of files kept after filtering
result.collision_impact      # Percentage of renames affected by collisions
```

### BatchRenameProcessor

Main processing engine that orchestrates the rename pipeline.

```python
from batch_rename.core.processor import BatchRenameProcessor

class BatchRenameProcessor:
    """Main processor for batch rename operations."""
    
    def process(self, config: RenameConfig) -> RenameResult:
        """
        Process files according to configuration.
        
        Pipeline: Filters → Extractor → Converters → Template → Rename
        
        Args:
            config: Rename configuration with all processing steps
            
        Returns:
            RenameResult with operation details and metrics
        """
```

#### Usage Example

```python
processor = BatchRenameProcessor()

config = RenameConfig(
    input_folder=Path("./files"),
    extractor="split",
    extractor_args={'positional': ['_', 'dept', 'type'], 'keyword': {}},
    preview_mode=True
)

result = processor.process(config)

print(f"Files analyzed: {result.files_analyzed}")
print(f"Files to rename: {result.files_to_rename}")
print(f"Collisions: {result.collisions}")
```

## Step System

### StepFactory

Central factory for creating and managing processing steps.

```python
from batch_rename.core.step_factory import StepFactory
from batch_rename.core.steps.base import StepType, StepConfig

class StepFactory:
    """Factory for creating and managing processing steps."""
    
    @classmethod
    def create_executable(cls, step_type: StepType, config: StepConfig) -> Callable:
        """Create executable function from configuration."""
    
    @classmethod
    def get_builtin_functions(cls, step_type: StepType) -> Dict[str, Callable]:
        """Get built-in functions for a step type."""
    
    @classmethod
    def validate_custom_function(cls, step_type: StepType, function: Callable):
        """Validate custom function for step type."""
```

#### Usage Example

```python
# Create an executable extractor
config = StepConfig(
    name='split',
    positional_args=['_', 'dept', 'type', 'date'],
    keyword_args={}
)

extractor = StepFactory.create_executable(StepType.EXTRACTOR, config)
result = extractor(context)  # Returns: {'dept': 'HR', 'type': 'employee', 'date': '2024'}

# Get available built-in functions
extractors = StepFactory.get_builtin_functions(StepType.EXTRACTOR)
# Returns: {'split': split_extractor, 'regex': regex_extractor, ...}
```

### StepConfig

Configuration for individual processing steps.

```python
from batch_rename.core.steps.base import StepConfig

@dataclass
class StepConfig:
    """Configuration for a processing step instance."""
    name: str                                       # Function name or file path
    positional_args: List[Any]                     # Positional arguments
    keyword_args: Dict[str, Any]                   # Keyword arguments
    custom_function_path: Optional[str] = None     # Path to .py file if custom
```

### StepType

Enumeration of processing step types.

```python
from batch_rename.core.steps.base import StepType

class StepType(Enum):
    """Types of processing steps in the rename pipeline."""
    FILTER = "filter"       # File filtering (execution order: 0)
    EXTRACTOR = "extractor" # Data extraction (execution order: 1)
    CONVERTER = "converter" # Data transformation (execution order: 2)
    TEMPLATE = "template"   # Filename formatting (execution order: 3)
    ALLINONE = "allinone"   # Combined extract+convert+format
```

## Built-in Functions

### Extractors

Functions that extract structured data from filenames.

#### split_extractor

```python
def split_extractor(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Split filename by delimiter and assign field names.
    
    Args:
        context: Processing context with filename and metadata
        positional_args: [delimiter, field1, field2, ...] 
        **kwargs: Not used
        
    Returns:
        Dict mapping field names to extracted values
        
    Example:
        # Filename: "HR_employee_data_2024.pdf"
        # Args: ['_', 'dept', 'type', 'category', 'year']
        # Returns: {'dept': 'HR', 'type': 'employee', 'category': 'data', 'year': '2024'}
    """
```

#### regex_extractor

```python
def regex_extractor(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Extract data using regex named groups or numbered groups with field mapping.
    
    Args:
        context: Processing context
        positional_args: [regex_pattern]
        **kwargs: field1=name1, field2=name2 (for numbered group mapping)
        
    Returns:
        Dict with named group matches or mapped numbered groups
        
    Example:
        # Filename: "HR_12345.pdf" 
        # Args: ['(?P<dept>\\w+)_(?P<num>\\d+)']
        # Returns: {'dept': 'HR', 'num': '12345'}
    """
```

#### position_extractor

```python
def position_extractor(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Extract data from specific character positions.
    
    Args:
        context: Processing context
        positional_args: ['start-end:fieldname', 'start:fieldname', ...]
        **kwargs: Not used
        
    Returns:
        Dict with field data from character positions
        
    Example:
        # Filename: "HRX123.pdf"
        # Args: ['0-2:dept', '3-5:code']  
        # Returns: {'dept': 'HRX', 'code': '123'}
    """
```

#### metadata_extractor

```python
def metadata_extractor(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Extract file metadata as fields.
    
    Args:
        context: Processing context
        positional_args: [field1, field2, ...] (created, modified, size)
        **kwargs: Not used
        
    Returns:
        Dict with requested metadata fields
        
    Example:
        # Args: ['created', 'size']
        # Returns: {'created': '2024-01-15', 'size': '1024'}
    """
```

### Converters

Functions that transform extracted data while preserving field structure.

#### case_converter

```python
def case_converter(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Convert field text case.
    
    Args:
        context: Processing context with extracted_data
        positional_args: [field_name, case_type]
        case_type: upper, lower, title, capitalize
        **kwargs: field=field_name, case=case_type
        
    Returns:
        Dict with specified field case-converted
        
    Example:
        # Input: {'dept': 'hr', 'type': 'employee'}
        # Args: ['dept', 'upper']
        # Returns: {'dept': 'HR', 'type': 'employee'}
    """
```

#### pad_numbers_converter

```python
def pad_numbers_converter(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Pad numeric fields with leading zeros.
    
    Args:
        context: Processing context with extracted_data
        positional_args: [field_name, width]
        **kwargs: field=field_name, width=width
        
    Returns:
        Dict with specified field zero-padded
        
    Example:
        # Input: {'id': '5', 'dept': 'HR'}
        # Args: ['id', '3']
        # Returns: {'id': '005', 'dept': 'HR'}
    """
```

#### date_format_converter

```python
def date_format_converter(context: ProcessingContext, positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Convert date field from one format to another.
    
    Args:
        context: Processing context with extracted_data
        positional_args: [field_name, input_format, output_format]
        **kwargs: field=field_name, input_format=fmt, output_format=fmt
        
    Returns:
        Dict with date field reformatted
        
    Example:
        # Input: {'date': '20240115', 'dept': 'HR'}
        # Args: ['date', '%Y%m%d', '%Y-%m-%d']
        # Returns: {'date': '2024-01-15', 'dept': 'HR'}
    """
```

### Templates

Functions that format the final filename from extracted/converted data.

#### stringsmith_formatter

```python
def stringsmith_formatter(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Format filename using StringSmith conditional templates.
    
    Args:
        context: Processing context with extracted_data
        positional_args: [template_string]
        **kwargs: template=template_string
        
    Returns:
        Formatted filename string (without extension)
        
    Example:
        # Input: {'dept': 'HR', 'type': 'employee', 'date': '2024-01-15'}
        # Args: ['{{dept|upper}}_{{type}}_{{date}}']
        # Returns: 'HR_employee_2024-01-15'
        
        # Missing data example:
        # Input: {'dept': 'HR'}  # Missing 'type' and 'date'
        # Args: ['{{dept}}_{{type}}_{{date}}']
        # Returns: 'HR'  # Sections with missing data disappear
    """
```

#### template_formatter

```python
def template_formatter(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Format filename using Python string formatting.
    
    Args:
        context: Processing context with extracted_data
        positional_args: [template_string]
        **kwargs: template=template_string
        
    Returns:
        Formatted filename string (without extension)
        
    Example:
        # Input: {'dept': 'HR', 'type': 'employee', 'date': '2024'}
        # Args: ['{dept}_{type}_{date}']
        # Returns: 'HR_employee_2024'
    """
```

#### join_formatter

```python
def join_formatter(context: ProcessingContext, positional_args: List[str], **kwargs) -> str:
    """
    Join specified fields with a separator.
    
    Args:
        context: Processing context with extracted_data
        positional_args: [field1, field2, field3, ...]
        **kwargs: separator=sep (default: "_")
        
    Returns:
        Joined field values as filename string
        
    Example:
        # Input: {'dept': 'HR', 'type': 'employee', 'date': '2024'}
        # Args: ['dept', 'type', 'date'], kwargs: {'separator': '-'}
        # Returns: 'HR-employee-2024'
    """
```

### Filters

Functions that determine which files to process (return bool).

#### pattern_filter

```python
def pattern_filter(context: ProcessingContext, positional_args: List[str], **kwargs) -> bool:
    """
    Filter files using glob-style patterns.
    
    Args:
        context: Processing context
        positional_args: [pattern1, pattern2, ...] (any match = True)
        **kwargs: Not used
        
    Returns:
        True if filename matches any pattern, False otherwise
        
    Example:
        # Filename: "report.pdf"
        # Args: ['*.pdf', '*report*']
        # Returns: True (matches both patterns)
    """
```

#### file_type_filter

```python
def file_type_filter(context: ProcessingContext, positional_args: List[str], **kwargs) -> bool:
    """
    Filter files by extension.
    
    Args:
        context: Processing context
        positional_args: [ext1, ext2, ...] (without dots)
        **kwargs: Not used
        
    Returns:
        True if file extension matches any in list, False otherwise
        
    Example:
        # Filename: "document.pdf"
        # Args: ['pdf', 'docx', 'txt']
        # Returns: True
    """
```

#### file_size_filter

```python
def file_size_filter(context: ProcessingContext, positional_args: List[str], **kwargs) -> bool:
    """
    Filter files by size range.
    
    Args:
        context: Processing context
        positional_args: [min_size, max_size] (supports KB, MB, GB units)
        **kwargs: Not used
        
    Returns:
        True if file size within range, False otherwise
        
    Example:
        # File size: 5MB
        # Args: ['1MB', '10MB'] 
        # Returns: True
    """
```

## Custom Function Interface

### Function Signatures

All custom functions must follow specific signatures for their step type:

#### Custom Extractor

```python
def my_extractor(context: ProcessingContext, *args, **kwargs) -> Dict[str, Any]:
    """
    Extract structured data from filename.
    
    Args:
        context: ProcessingContext with filename, path, metadata
        *args: Positional arguments from CLI/GUI
        **kwargs: Keyword arguments from CLI/GUI
        
    Returns:
        Dict[str, Any]: Extracted field data
        
    Raises:
        ValueError: If extraction fails or invalid arguments
    """
    # Access filename: context.filename or context.base_name
    # Access metadata: context.metadata['size'], etc.
    # Return extracted fields as dict
    return {'field1': 'value1', 'field2': 'value2'}
```

#### Custom Converter

```python
def my_converter(context: ProcessingContext, *args, **kwargs) -> Dict[str, Any]:
    """
    Transform extracted data while preserving field structure.
    
    Args:
        context: ProcessingContext with extracted_data populated
        *args: Positional arguments from CLI/GUI
        **kwargs: Keyword arguments from CLI/GUI
        
    Returns:
        Dict[str, Any]: Transformed data with same keys as input
        
    Raises:
        ValueError: If conversion fails or changes field structure
        
    Note:
        MUST preserve field structure - same keys in input and output
    """
    if not context.has_extracted_data():
        return {}
    
    result = context.extracted_data.copy()
    # Transform values but keep same keys
    return result
```

#### Custom Template

```python
def my_template(context: ProcessingContext, *args, **kwargs) -> str:
    """
    Format final filename from extracted/converted data.
    
    Args:
        context: ProcessingContext with extracted_data populated
        *args: Positional arguments from CLI/GUI
        **kwargs: Keyword arguments from CLI/GUI
        
    Returns:
        str: Formatted filename WITHOUT extension
        
    Raises:
        ValueError: If formatting fails
    """
    # Access converted data: context.extracted_data
    # Return formatted filename string (no extension)
    return 'formatted_filename'
```

#### Custom Filter

```python
def my_filter(context: ProcessingContext, *args, **kwargs) -> bool:
    """
    Determine whether to process a file.
    
    Args:
        context: ProcessingContext with filename, path, metadata
        *args: Positional arguments from CLI/GUI
        **kwargs: Keyword arguments from CLI/GUI
        
    Returns:
        bool: True = process file, False = skip file
        
    Raises:
        ValueError: If filter logic fails
    """
    # Access filename: context.filename
    # Access metadata: context.metadata
    # Return boolean decision
    return True  # or False
```

### Loading Custom Functions

```python
from batch_rename.core.function_loader import load_custom_function

# Load function from file
function = load_custom_function('/path/to/functions.py', 'function_name')

# Validate function for step type
from batch_rename.core.step_factory import StepFactory
validation = StepFactory.validate_custom_function(StepType.EXTRACTOR, function)

if validation.valid:
    print("Function is valid")
else:
    print(f"Validation failed: {validation.message}")
```

## Error Handling

### Exception Hierarchy

```python
# Base exceptions
class BatchRenameError(Exception):
    """Base exception for batch rename operations."""

class ConfigurationError(BatchRenameError):
    """Configuration validation errors."""

class ProcessingError(BatchRenameError):
    """Errors during file processing."""

class FunctionValidationError(BatchRenameError):
    """Custom function validation errors."""
```

### Error Context

Errors include rich context information:

```python
try:
    result = processor.process(config)
except ProcessingError as e:
    print(f"Processing failed: {e}")
    print(f"Error context: {e.context}")
    # Context includes: file_path, step_type, function_name, etc.
```

## Logging Integration

### Logger Configuration

```python
from batch_rename.config.logging_config import LoggingConfig

# Set up logging for CLI
LoggingConfig.setup_for_cli(
    level='INFO',
    log_file='batch_rename.log',
    enable_colors=True
)

# Set up logging for production
LoggingConfig.setup_for_environment('production')
```

### Performance Logging

```python
from shared_utils.logger import get_logger, log_performance

logger = get_logger(__name__)

# Automatic performance logging
with log_performance("batch_rename_operation"):
    result = processor.process(config)

# Manual logging with metrics
logger.info("Processing complete", extra={
    'files_processed': result.files_renamed,
    'duration': result.processing_time,
    'success_rate': result.success_rate,
    'memory_usage_mb': 150
})
```

### StringSmith Log Templates

The logging system uses StringSmith for conditional formatting:

```python
# Template automatically shows relevant information:
# "[INFO] Processing complete (150 files) in 2.3s (95% success)"
# "[WARNING] Collisions detected (5 conflicts)"
# "[ERROR] Processing failed in 1.2s (FileNotFoundError)"
```

## Integration Examples

### Programmatic Usage

```python
from batch_rename.core import BatchRenameProcessor, RenameConfig
from pathlib import Path

# Create configuration
config = RenameConfig(
    input_folder=Path("./files"),
    extractor="split",
    extractor_args={
        'positional': ['_', 'dept', 'type', 'date'],
        'keyword': {}
    },
    converters=[
        {
            'name': 'case',
            'positional': ['dept', 'upper'],
            'keyword': {}
        }
    ],
    template={
        'name': 'stringsmith',
        'positional': ['{{dept}}_{{type}}_{{date}}'],
        'keyword': {}
    },
    preview_mode=True
)

# Process files
processor = BatchRenameProcessor()
result = processor.process(config)

# Check results
if result.collisions > 0:
    print(f"Warning: {result.collisions} naming conflicts")

for preview in result.preview_data:
    print(f"{preview['old_name']} → {preview['new_name']}")
```

### Custom Function Integration

```python
# custom_business_logic.py
from batch_rename.core.processing_context import ProcessingContext
from typing import Dict, Any
import re

def extract_invoice_data(context: ProcessingContext, 
                        client_patterns: str = "") -> Dict[str, Any]:
    """Extract invoice data from business filenames."""
    filename = context.base_name
    
    # Parse client patterns
    clients = [c.strip() for c in client_patterns.split(',') if c.strip()]
    
    # Extract invoice number
    invoice_match = re.search(r'INV[_-]?(\d+)', filename, re.IGNORECASE)
    invoice_num = invoice_match.group(1) if invoice_match else 'unknown'
    
    # Extract client
    client = 'unknown'
    for c in clients:
        if c.lower() in filename.lower():
            client = c
            break
    
    # Extract date
    date_match = re.search(r'(\d{4}[-_]\d{2}[-_]\d{2})', filename)
    date = date_match.group(1).replace('_', '-') if date_match else 'unknown'
    
    return {
        'client': client,
        'invoice': invoice_num,
        'date': date
    }

# Usage:
# python main.py --extractor custom_business_logic.py,extract_invoice_data,"ACME,TechCorp,GlobalInc"
```

---

**This API reference provides complete documentation for integrating with and extending the Batch Rename Tool programmatically.**