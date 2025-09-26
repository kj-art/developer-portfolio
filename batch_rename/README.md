# Batch Rename Tool

Professional batch file renaming with advanced pattern extraction, data transformation, and collision detection. Built with a sophisticated step-based architecture and powered by StringSmith conditional formatting.

## Features

### 🔍 **Smart Data Extraction**
- **Split Extractor**: Parse structured filenames like `HR_employee_data_2024.pdf`
- **Regex Extractor**: Use powerful regex patterns with named groups
- **Position Extractor**: Extract data from specific character positions
- **Metadata Extractor**: Include file creation date, size, and modification time

### 🔄 **Flexible Data Transformation**
- **Case Conversion**: upper, lower, title, capitalize
- **Number Padding**: Zero-pad sequence numbers and IDs
- **Date Formatting**: Convert between date formats (`20240115` → `2024-01-15`)
- **Chain Multiple Converters**: Apply transformations in sequence

### 📝 **Advanced Template Formatting**
- **StringSmith Integration**: Graceful handling of missing data
- **Conditional Sections**: Parts disappear when data is missing
- **Python String Formatting**: Standard `{field}` template syntax
- **Custom Templates**: Write your own formatting functions

### 🚧 **Safety & Reliability**
- **Preview-First Workflow**: See changes before executing
- **Collision Detection**: Identify naming conflicts with visual highlighting
- **Comprehensive Logging**: Structured logs with performance metrics
- **Background Processing**: Non-blocking GUI operations

### 🎛️ **Professional Interface**
- **Command Line**: Full-featured CLI with help system
- **Graphical Interface**: PyQt6 GUI with real-time preview
- **Custom Functions**: Load your own Python functions for specialized logic

## Quick Start

### Installation

```bash
# Clone or extract the tool to your desired location
cd batch-rename-tool

# Install dependencies
pip install -r requirements.txt

# Verify installation
python main.py --help
```

### Basic Usage

```bash
# Preview changes (safe - no actual renaming)
python main.py --input-folder /path/to/files \
    --extractor split,_,dept,type,date \
    --template join,dept,type,date,separator=-

# Execute the renames
python main.py --input-folder /path/to/files \
    --extractor split,_,dept,type,date \
    --template join,dept,type,date,separator=- \
    --execute
```

### GUI Mode

```bash
# Launch the graphical interface
python -m batch_rename.ui.gui
```

## Examples

### Corporate Document Standardization

Transform messy corporate filenames into standardized format:

```bash
# Input files:
# HR_employee_handbook_2024.pdf
# Marketing_branding_guidelines_draft.docx
# IT_security_policy_v2.pdf

python main.py --input-folder ./documents \
    --extractor split,_,dept,doc_type,version \
    --converter case,dept,upper \
    --converter case,doc_type,title \
    --template join,dept,doc_type,version,separator=- \
    --preview

# Output preview:
# HR_employee_handbook_2024.pdf → HR-Employee-Handbook-2024.pdf
# Marketing_branding_guidelines_draft.docx → MARKETING-Branding-Guidelines-Draft.docx
# IT_security_policy_v2.pdf → IT-Security-Policy-V2.pdf
```

### Project File Organization

Organize project files with date normalization:

```bash
# Input files:
# ProjectAlpha_Phase1_20240115_v1.2.pdf
# ProjectAlpha_Phase2_2024-02-20_v2.1.docx

python main.py --input-folder ./projects \
    --extractor split,_,project,phase,date,version \
    --converter date_format,date,%Y%m%d,%Y-%m-%d \
    --converter pad_numbers,version,2 \
    --template join,project,phase,date,version,separator=- \
    --preview

# Output preview:
# ProjectAlpha_Phase1_20240115_v1.2.pdf → ProjectAlpha-Phase1-2024-01-15-v01.2.pdf
# ProjectAlpha_Phase2_2024-02-20_v2.1.docx → ProjectAlpha-Phase2-2024-02-20-v02.1.docx
```

### Advanced Filtering and Custom Logic

Use filters and custom functions for complex scenarios:

```bash
# Only process PDF files larger than 1MB, exclude backups
python main.py --input-folder ./files \
    --filter extension,pdf \
    --filter size_range,1MB,100MB \
    --filter !pattern,*backup* \
    --extractor custom_scripts/project_extractor.py,extract_project_data \
    --template custom_scripts/project_template.py,format_project_name \
    --preview
```

## Architecture

### Step-Based Processing Pipeline

The tool uses a sophisticated step-based architecture:

```
Files → Filters → Extractor → Converters → Template → New Filename
```

1. **Filters**: Determine which files to process (AND logic, supports inversion)
2. **Extractor**: Extract structured data from filenames 
3. **Converters**: Transform extracted data (stackable, order matters)
4. **Template**: Format final filename using transformed data

### Built-in Functions

#### Extractors
- `split,delimiter,field1,field2,...` - Split by delimiter and name fields
- `regex,pattern` - Use regex with named capture groups
- `position,spec` - Extract by character position (`"0-3:dept,4-8:id"`)
- `metadata,fields...` - Include file metadata (created, modified, size)

#### Converters
- `case,field,type` - Change case (upper, lower, title, capitalize)
- `pad_numbers,field,width` - Zero-pad numbers
- `date_format,field,input_fmt,output_fmt` - Convert date formats
- `strip_prefix,field,prefix` - Remove prefix from field

#### Templates
- `join,field1,field2,...,separator=X` - Join fields with separator
- `stringsmith,template` - Advanced conditional formatting

#### Filters
- `extension,ext1,ext2,...` - Filter by file extensions
- `pattern,glob_pattern` - Filter by filename pattern
- `size_range,min,max` - Filter by file size
- `!function_name` - Invert any filter (exclude matches)

## Testing

**Important**: All tests must be run from within the `batch_rename` directory:

```bash
cd batch_rename

# Run all unit tests
python -m pytest tests -v

# Run integration tests (tests actual CLI with examples)
python -m pytest examples -v

# Run all tests
python -m pytest -v

# Run specific test file
python -m pytest tests/test_cli.py -v

# Run with coverage report
python -m pytest --cov=batch_rename --cov-report=html
```

### Test Types
- **Unit tests** (`tests/`) - Test individual components and functions
- **Integration tests** (`examples/test_all_examples.py`) - Test complete workflows using real CLI commands
- **Custom function tests** - Validate user-provided Python functions

## Custom Functions

### Writing Custom Extractors

```python
from batch_rename.core.processing_context import ProcessingContext
from typing import Dict, Any, List

def my_extractor(context: ProcessingContext, 
                 positional_args: List[str], 
                 **kwargs) -> Dict[str, Any]:
    """Extract project data from corporate filenames."""
    filename = context.filename_without_extension
    
    # Custom extraction logic here
    parts = filename.split('_')
    
    return {
        'department': parts[0] if len(parts) > 0 else '',
        'project': parts[1] if len(parts) > 1 else '',
        'date': parts[2] if len(parts) > 2 else ''
    }
```

### Using Custom Functions

```bash
python main.py --input-folder ./files \
    --extractor my_extractors.py,my_extractor,arg1,arg2 \
    --template my_templates.py,my_template \
    --preview
```

### Function Validation

All custom functions are automatically validated for:
- Correct function signatures
- Required return types
- Field consistency across processing steps

## Configuration Files

Save complex configurations as YAML or JSON files:

```yaml
# config/corporate_docs.yaml
settings:
  recursive: true

pipeline:
  extractor:
    name: split
    args: ['_', 'dept', 'doc_type', 'date']
  
  converters:
    - name: case
      args: ['dept', 'upper']
    - name: date_format
      args: ['date', '%Y%m%d', '%Y-%m-%d']
      
  template:
    name: join
    args: ['dept', 'doc_type', 'date']
    kwargs:
      separator: '-'

collision_handling:
  on_existing_collision: skip
  on_internal_collision: error
```

```bash
# Use configuration file
python main.py --config config/corporate_docs.yaml --preview
```

## Contributing

### Development Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Install development dependencies: `pip install -r requirements-dev.txt`

### Adding Built-in Functions

1. Add your function to the appropriate module in `batch_rename/core/built_ins/`
2. Register it in the `BUILTIN_*` dictionary
3. Add comprehensive tests in `batch_rename/tests/`
4. Update documentation

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for all function parameters and returns
- Include comprehensive docstrings with examples
- Maintain test coverage above 80%

## License

MIT License - See LICENSE file for details.

## Related Projects

- **StringSmith**: Conditional template formatting engine
- **Shared Utils**: Logging and utility functions

---

**Built for digital asset management and workflow automation**