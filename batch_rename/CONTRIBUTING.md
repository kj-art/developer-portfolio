# Contributing Guide

Thank you for your interest in contributing to the Batch Rename Tool! This guide will help you get started with development, testing, and submitting contributions.

## Quick Start for Contributors

### Development Environment Setup

```

### Security Considerations

- **Custom function execution**: Validate user-provided Python code
- **File system access**: Prevent directory traversal attacks
- **Input validation**: Sanitize all user inputs
- **Path handling**: Use pathlib for safe path operations

```python
# Good: Safe path handling
def validate_file_path(file_path: Path, base_folder: Path) -> bool:
    """Ensure file operations stay within base folder."""
    try:
        file_path.resolve().relative_to(base_folder.resolve())
        return True
    except ValueError:
        raise SecurityError(f"Path outside base folder: {file_path}")

# Bad: Unsafe path handling
def unsafe_path_handling(filename: str):
    # Vulnerable to directory traversal
    with open(f"/base/folder/{filename}", 'r') as f:
        return f.read()
```

## Documentation Standards

### Code Documentation

#### Module Level
```python
"""
Module for processing business document filename patterns.

This module provides extractors and templates specifically designed for
corporate document management workflows, including standardized naming
conventions and metadata extraction.

Example:
    from batch_rename.business import corporate_extractor
    
    result = corporate_extractor(context, "HR,IT,Finance")
    # Returns: {'department': 'HR', 'doc_type': 'handbook', ...}
"""
```

#### Class Level
```python
class BusinessDocumentProcessor:
    """
    Specialized processor for corporate document renaming workflows.
    
    This processor extends the base BatchRenameProcessor with business-specific
    logic for handling corporate naming conventions, department codes, and
    document classification.
    
    Attributes:
        department_codes: Dict mapping department abbreviations to full names
        document_types: List of recognized document type patterns
        
    Example:
        processor = BusinessDocumentProcessor(['HR', 'IT', 'Finance'])
        result = processor.process_corporate_docs(config)
    """
```

### README Updates

When adding significant features, update the main README:

```markdown
## New Features in v2.1

### CSV Extractor
Extract data from comma-separated filename patterns:

```bash
# Extract from CSV-like filenames
python main.py --extractor csv,",",category,year,quarter,type \
    --input-folder ./data \
    --preview
```

### File Validation
Validate files before processing:

```bash
# Check file integrity and naming conventions
python main.py --validator file_integrity \
    --validator naming_convention,"^[A-Z]+_" \
    --input-folder ./documents \
    --preview
```
```

## Community Guidelines

### Code of Conduct

- **Be respectful**: Treat all contributors with respect and professionalism
- **Be inclusive**: Welcome contributors of all backgrounds and skill levels
- **Be constructive**: Provide helpful feedback and suggestions
- **Be patient**: Remember that everyone is learning and improving

### Communication

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Pull Requests**: Use clear, descriptive titles and thorough descriptions
- **Code Comments**: Explain complex logic and design decisions

### Getting Help

#### For Contributors

- **Documentation**: Check existing docs first (README, API docs, examples)
- **Code Examples**: Look at examples/ directory for patterns
- **Tests**: Examine test files to understand expected behavior
- **Issues**: Search existing issues before creating new ones

#### For Maintainers

- **Response time**: Aim to respond to issues within 48 hours
- **Review process**: Provide constructive feedback on PRs
- **Documentation**: Keep docs updated with code changes
- **Release notes**: Document all changes in releases

## Release Process

### Version Numbering

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes that require user action
- **MINOR**: New features that are backward compatible
- **PATCH**: Bug fixes and small improvements

### Release Checklist

#### Pre-release
- [ ] All tests pass on main branch
- [ ] Documentation is up to date
- [ ] CHANGELOG.md is updated
- [ ] Version number is bumped
- [ ] Performance benchmarks are within acceptable ranges

#### Release
- [ ] Create release tag: `git tag v1.2.3`
- [ ] Push tag: `git push origin v1.2.3`
- [ ] Create GitHub release with changelog
- [ ] Build and test standalone executables
- [ ] Update package registries if applicable

#### Post-release
- [ ] Verify release artifacts work correctly
- [ ] Update documentation site
- [ ] Announce release in discussions
- [ ] Monitor for issues and bug reports

## Advanced Development Topics

### Custom Function Development Best Practices

#### Function Signature Design
```python
# Good: Clear, typed parameters with sensible defaults
def extract_invoice_data(context: ProcessingContext,
                        client_patterns: str = "",
                        date_format: str = "%Y-%m-%d",
                        require_invoice_number: bool = True) -> Dict[str, Any]:
    """Extract invoice data with configurable options."""

# Bad: Unclear parameters, no types, no defaults
def extract_data(c, p, f, r):
    """Extract some data."""
```

#### Error Handling in Custom Functions
```python
def robust_extractor(context: ProcessingContext, **kwargs) -> Dict[str, Any]:
    """Extractor with comprehensive error handling."""
    try:
        # Main extraction logic
        result = extract_core_data(context.base_name)
        
        # Validate extracted data
        if not result:
            logger.warning("No data extracted", extra={'filename': context.filename})
            return {}
        
        # Additional processing
        return enhance_extracted_data(result, kwargs)
        
    except re.error as e:
        # Specific regex errors
        raise ValueError(f"Invalid regex pattern in extractor: {e}") from e
    except KeyError as e:
        # Missing required parameters
        raise ValueError(f"Missing required parameter: {e}") from e
    except Exception as e:
        # Unexpected errors - log and re-raise with context
        logger.error("Unexpected error in extractor", extra={
            'filename': context.filename,
            'error_type': type(e).__name__,
            'error_message': str(e)
        })
        raise ProcessingError(f"Extractor failed for {context.filename}: {e}") from e
```

### Performance Optimization

#### Memory Management
```python
# Good: Generator for large file sets
def process_files_efficiently(files: Iterator[Path]) -> Iterator[RenameResult]:
    """Process files using generators to minimize memory usage."""
    for file_batch in chunk_iterator(files, 100):  # Process in batches
        yield process_batch(file_batch)

# Bad: Loading everything into memory
def process_files_inefficiently(files: List[Path]) -> List[RenameResult]:
    """Loads all results into memory at once."""
    return [process_file(f) for f in files]  # Memory usage grows with file count
```

#### Template Optimization
```python
# Good: Reuse compiled templates
class TemplateManager:
    def __init__(self):
        self._cache = {}
    
    def get_formatter(self, template: str) -> TemplateFormatter:
        if template not in self._cache:
            self._cache[template] = TemplateFormatter(template)
        return self._cache[template]

# Bad: Recompile templates every time
def format_filename(template: str, data: dict) -> str:
    formatter = TemplateFormatter(template)  # Expensive compilation
    return formatter.format(**data)
```

### Testing Strategies

#### Parameterized Tests
```python
@pytest.mark.parametrize("filename,expected", [
    ("HR_handbook_2024.pdf", {"dept": "HR", "type": "handbook", "year": "2024"}),
    ("IT_policy_v2.docx", {"dept": "IT", "type": "policy", "version": "v2"}),
    ("Finance_report_Q1.xlsx", {"dept": "Finance", "type": "report", "quarter": "Q1"}),
])
def test_corporate_extractor_variations(filename, expected):
    """Test extractor with various filename patterns."""
    context = ProcessingContext(filename, Path(filename), {})
    result = corporate_extractor(context, "HR,IT,Finance")
    
    for key, value in expected.items():
        assert result[key] == value
```

#### Integration Test Patterns
```python
class TestCompleteWorkflow:
    """Integration tests for complete rename workflows."""
    
    @pytest.fixture
    def corporate_files(self, tmp_path):
        """Create realistic corporate test files."""
        files = [
            "HR_employee_handbook_2024_v1.2.pdf",
            "IT_security_policy_final.docx",
            "Finance_quarterly_report_Q1_2024.xlsx"
        ]
        
        for filename in files:
            (tmp_path / filename).write_text(f"Content for {filename}")
        
        return tmp_path
    
    def test_corporate_standardization_workflow(self, corporate_files):
        """Test complete corporate document standardization."""
        config = RenameConfig(
            input_folder=corporate_files,
            extractor="corporate_extractor",
            extractor_args={"positional": ["HR,IT,Finance"], "keyword": {}},
            converters=[
                {"name": "case", "positional": ["dept", "upper"], "keyword": {}}
            ],
            template={
                "name": "stringsmith", 
                "positional": ["{{dept}}-{{type}}-{{year}}"], 
                "keyword": {}
            }
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        # Verify results
        assert result.errors == 0
        assert result.files_to_rename == 3
        
        # Check specific transformations
        preview_data = {item['old_name']: item['new_name'] for item in result.preview_data}
        assert "HR_employee_handbook_2024_v1.2.pdf" in preview_data
        assert preview_data["HR_employee_handbook_2024_v1.2.pdf"] == "HR-employee_handbook-2024.pdf"
```

### Debugging and Troubleshooting

#### Debug Mode Implementation
```python
# Enable debug mode with environment variable
import os
DEBUG_MODE = os.getenv('BATCH_RENAME_DEBUG', 'false').lower() == 'true'

def debug_log(message: str, **kwargs):
    """Log debug information when debug mode is enabled."""
    if DEBUG_MODE:
        logger = get_logger(__name__)
        logger.debug(message, extra=kwargs)

# Usage in functions
def complex_extractor(context: ProcessingContext) -> Dict[str, Any]:
    debug_log("Starting extraction", filename=context.filename)
    
    # Extraction steps with debug logging
    patterns = extract_patterns(context.base_name)
    debug_log("Extracted patterns", patterns=patterns)
    
    result = process_patterns(patterns)
    debug_log("Processing complete", result=result)
    
    return result
```

#### Common Issues and Solutions

**Issue: Custom function not found**
```python
# Debug function loading
def debug_function_loading():
    """Helper to debug custom function loading issues."""
    import sys
    from pathlib import Path
    
    function_file = Path("my_functions.py")
    
    print(f"Function file exists: {function_file.exists()}")
    print(f"Function file path: {function_file.absolute()}")
    print(f"Python path: {sys.path}")
    
    try:
        from batch_rename.core.function_loader import load_custom_function
        func = load_custom_function(str(function_file), "my_function")
        print(f"Function loaded successfully: {func}")
    except Exception as e:
        print(f"Loading failed: {e}")
        import traceback
        traceback.print_exc()
```

**Issue: Template formatting errors**
```python
# Debug StringSmith templates
def debug_template_formatting():
    """Helper to debug template formatting issues."""
    from shared_utils.stringsmith import TemplateFormatter
    
    template = "{{dept}}_{{type}}_{{date}}"
    data = {"dept": "HR", "type": "handbook"}  # Missing 'date'
    
    try:
        formatter = TemplateFormatter(template)
        result = formatter.format(**data)
        print(f"Template result: '{result}'")
    except Exception as e:
        print(f"Template error: {e}")
        
        # Try simpler template
        simple_template = "{{dept}}_{{type}}"
        simple_formatter = TemplateFormatter(simple_template)
        simple_result = simple_formatter.format(**data)
        print(f"Simple template works: '{simple_result}'")
```

## Deployment and Distribution

### Building Standalone Executables

```bash
# Install PyInstaller
pip install pyinstaller

# Build single file executable
pyinstaller --onefile --windowed \
    --name batch-rename-tool \
    --add-data "shared_utils:shared_utils" \
    --add-data "batch_rename/ui/gui:batch_rename/ui/gui" \
    main.py

# Test the executable
./dist/batch-rename-tool --help
```

### Container Deployment

```dockerfile
# Dockerfile for container deployment
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pyqt6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash batchrename
USER batchrename

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
```

### Configuration Management

```python
# config/deployment.py
import os
from typing import Dict, Any

def get_deployment_config() -> Dict[str, Any]:
    """Get deployment-specific configuration."""
    env = os.getenv('BATCH_RENAME_ENV', 'development')
    
    configs = {
        'development': {
            'log_level': 'DEBUG',
            'enable_colors': True,
            'max_files': 10000,
            'performance_monitoring': True
        },
        'production': {
            'log_level': 'WARNING',
            'enable_colors': False,
            'max_files': 100000,
            'performance_monitoring': False
        },
        'testing': {
            'log_level': 'ERROR',
            'enable_colors': False,
            'max_files': 1000,
            'performance_monitoring': False
        }
    }
    
    return configs.get(env, configs['development'])
```

---

# 1. Set up development environment
python -m venv dev_env
source dev_env/bin/activate  # On Windows: dev_env\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 isort mypy

# 3. Run tests to verify setup
python -m pytest tests/ -v

# 4. Run the tool to ensure it works
python main.py --help
```bash
### Development Workflow

When making changes to the codebase:

1. **Create a backup** of your working version
2. **Test thoroughly** with your specific use cases
3. **Document changes** in comments and docstrings
4. **Run the test suite** to ensure nothing breaks
5. **Update examples** if adding new features
```

### Code Standards

#### Python Style Guide

We follow PEP 8 with some project-specific conventions:

```python
# Good: Descriptive function names with type hints
def extract_project_data(context: ProcessingContext, 
                        client_patterns: str = "") -> Dict[str, Any]:
    """
    Extract project data from structured filenames.
    
    Args:
        context: Processing context with filename and metadata
        client_patterns: Comma-separated list of client name patterns
        
    Returns:
        Dict containing extracted project fields
        
    Raises:
        ValueError: If filename doesn't match expected pattern
        
    Example:
        >>> context = ProcessingContext("ACME_Project_Phase1.pdf", ...)
        >>> result = extract_project_data(context, "ACME,TechCorp")
        >>> assert result == {'client': 'ACME', 'project': 'Project', 'phase': 'Phase1'}
    """
    # Implementation here
    return extracted_data

# Bad: Vague names, missing types, no documentation
def extract(c, p=""):
    # No docstring, unclear purpose
    return {}
```

#### Docstring Requirements

All public functions, classes, and modules must have comprehensive docstrings:

```python
def custom_extractor_template(context: ProcessingContext, 
                             param1: str,
                             param2: int = 10) -> Dict[str, Any]:
    """
    One-line summary of what the function does.
    
    Longer description explaining the purpose, algorithm, or important
    details about the function's behavior.
    
    Args:
        context: Processing context containing filename and metadata
        param1: Description of first parameter
        param2: Description of second parameter with default value
        
    Returns:
        Dictionary containing extracted field data with keys:
        - field1: Description of field1
        - field2: Description of field2
        
    Raises:
        ValueError: When filename doesn't match expected pattern
        FileNotFoundError: When referenced file doesn't exist
        
    Example:
        >>> context = ProcessingContext("example_file.txt", ...)
        >>> result = custom_extractor_template(context, "pattern", 5)
        >>> assert 'field1' in result
        
    Note:
        Additional notes about performance, limitations, or usage patterns.
    """
```

#### Import Organization

```python
# Standard library imports
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Third-party imports
import pytest
from PyQt6.QtWidgets import QWidget

# Local imports
from batch_rename.core.processing_context import ProcessingContext
from batch_rename.core.step_factory import StepFactory
from shared_utils.stringsmith import TemplateFormatter
```

### Testing Requirements

#### Test Coverage Standards

- **Minimum coverage**: 80% overall
- **Critical components**: 95% coverage required
  - Core processor
  - Step factory
  - Built-in functions
  - Configuration validation

#### Test Categories

**Unit Tests** - Test individual components in isolation:
```python
# tests/test_extractors.py
def test_split_extractor_basic():
    """Test basic split extraction functionality."""
    context = ProcessingContext(
        filename="HR_employee_data.pdf",
        file_path=Path("test.pdf"),
        metadata={'size': 1024}
    )
    
    result = split_extractor(context, ['_', 'dept', 'type', 'category'])
    
    assert result == {
        'dept': 'HR',
        'type': 'employee', 
        'category': 'data'
    }

def test_split_extractor_edge_cases():
    """Test split extractor with edge cases."""
    # Test fewer parts than fields
    # Test more parts than fields
    # Test empty filename
    # Test special characters
```

**Integration Tests** - Test component interactions:
```python
# tests/test_integration.py
def test_full_pipeline_execution():
    """Test complete processing pipeline."""
    config = RenameConfig(
        input_folder=test_folder,
        extractor="split",
        extractor_args={'positional': ['_', 'dept', 'type'], 'keyword': {}},
        template={'name': 'join', 'positional': ['dept', 'type'], 'keyword': {}}
    )
    
    processor = BatchRenameProcessor()
    result = processor.process(config)
    
    assert result.errors == 0
    assert len(result.preview_data) > 0
```

**Performance Tests** - Ensure scalability:
```python
# tests/test_performance.py
def test_large_file_set_performance():
    """Test performance with large file sets."""
    # Create 1000 test files
    files = create_test_files(1000)
    
    start_time = time.time()
    result = processor.process(config)
    duration = time.time() - start_time
    
    # Should process at least 100 files per second
    assert len(files) / duration > 100
```

#### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=batch_rename --cov-report=html --cov-report=term-missing

# Run specific test category
python -m pytest tests/test_extractors.py -v

# Run performance tests
python -m pytest tests/test_performance.py -v --slow

# Run tests for specific feature
python -m pytest tests/ -k "split_extractor" -v
```

## Adding New Features

### Adding Built-in Functions

#### 1. Implement the Function

```python
# batch_rename/core/built_ins/extractors.py
def csv_extractor(context: ProcessingContext, 
                 positional_args: List[str], 
                 **kwargs) -> Dict[str, Any]:
    """
    Extract data from CSV-like filename patterns.
    
    Args:
        context: Processing context
        positional_args: [delimiter, field1, field2, ...]
        **kwargs: Additional options
        
    Returns:
        Dict with extracted CSV-like data
        
    Example:
        # Filename: "data,2024,Q1,sales.csv"
        # Args: [',', 'category', 'year', 'quarter', 'type']
        # Returns: {'category': 'data', 'year': '2024', 'quarter': 'Q1', 'type': 'sales'}
    """
    if not positional_args:
        raise ValueError("csv extractor requires delimiter and field names")
    
    delimiter = positional_args[0]
    field_names = positional_args[1:]
    
    # Remove extension and split
    base_name = context.base_name
    parts = base_name.split(delimiter)
    
    result = {}
    for i, field_name in enumerate(field_names):
        if i < len(parts):
            result[field_name] = parts[i].strip()
        else:
            result[field_name] = ""
    
    return result
```

#### 2. Register the Function

```python
# In the same file, add to registry
BUILTIN_EXTRACTORS = {
    'split': split_extractor,
    'regex': regex_extractor,
    'position': position_extractor,
    'metadata': metadata_extractor,
    'csv': csv_extractor,  # Add new function
}
```

#### 3. Add Comprehensive Tests

```python
# tests/test_extractors.py
class TestCsvExtractor:
    """Test the CSV extractor functionality."""
    
    def test_csv_extractor_basic(self):
        """Test basic CSV extraction."""
        context = ProcessingContext(
            filename="sales,2024,Q1,report.csv",
            file_path=Path("test.csv"),
            metadata={}
        )
        
        result = csv_extractor(context, [',', 'type', 'year', 'quarter', 'category'])
        
        assert result == {
            'type': 'sales',
            'year': '2024', 
            'quarter': 'Q1',
            'category': 'report'
        }
    
    def test_csv_extractor_missing_fields(self):
        """Test CSV extractor with missing fields."""
        context = ProcessingContext(
            filename="sales,2024.csv",
            file_path=Path("test.csv"),
            metadata={}
        )
        
        result = csv_extractor(context, [',', 'type', 'year', 'quarter'])
        
        assert result == {
            'type': 'sales',
            'year': '2024',
            'quarter': ''  # Missing field gets empty string
        }
    
    def test_csv_extractor_validation(self):
        """Test CSV extractor parameter validation."""
        context = ProcessingContext("test.csv", Path("test.csv"), {})
        
        with pytest.raises(ValueError, match="requires delimiter"):
            csv_extractor(context, [])
```

#### 4. Update Documentation

```python
# Update the function's docstring with CLI examples
"""
CLI Usage:
    --extractor csv,DELIMITER,field1,field2,field3
    
Examples:
    # Extract from comma-separated filename
    --extractor csv,",",category,year,quarter,type
    
    # Extract from pipe-separated filename  
    --extractor csv,"|",project,phase,version
"""
```

#### 5. Add GUI Support

```python
# batch_rename/ui/gui/panels/extractor.py
def add_csv_config(self, layout: QFormLayout):
    """Add configuration for CSV extractor."""
    delimiter_input = QLineEdit(",")
    delimiter_input.setObjectName("csv_delimiter")
    delimiter_input.setPlaceholderText("Delimiter character")
    layout.addRow("Delimiter:", delimiter_input)
    
    fields_input = QLineEdit("field1,field2,field3")
    fields_input.setObjectName("csv_fields")
    fields_input.setPlaceholderText("Field names separated by commas")
    layout.addRow("Field Names:", fields_input)

# Add to create_builtin_config method
elif function_type == 'csv':
    self.add_csv_config(layout)
```

### Adding New Step Types

To add a completely new step type (e.g., "VALIDATOR"):

#### 1. Add to StepType Enum

```python
# batch_rename/core/steps/base.py
class StepType(Enum):
    FILTER = "filter"
    EXTRACTOR = "extractor"
    CONVERTER = "converter" 
    TEMPLATE = "template"
    VALIDATOR = "validator"  # New step type
    ALLINONE = "allinone"
```

#### 2. Implement Step Class

```python
# batch_rename/core/steps/validator.py
from .base import ProcessingStep, StepType, StepConfig
from ..processing_context import ProcessingContext
from ..validators import ValidationResult, validate_validator_function

class ValidatorStep(ProcessingStep):
    """Processing step for file validation."""
    
    @property
    def step_type(self) -> StepType:
        return StepType.VALIDATOR
    
    @property
    def is_stackable(self) -> bool:
        return True  # Multiple validators can be chained
    
    @property
    def builtin_functions(self) -> Dict[str, Callable]:
        return {
            'file_integrity': file_integrity_validator,
            'naming_convention': naming_convention_validator,
            'metadata_check': metadata_validator
        }
    
    def get_help_text(self) -> str:
        return """
        VALIDATORS - Validate files before processing
        
        Built-in validators:
          file_integrity    - Check file corruption
          naming_convention - Validate naming patterns
          metadata_check    - Verify file metadata
        
        Custom validators:
          Load from .py files with validation functions
          Must return ValidationResult object
        """
    
    def validate_custom_function(self, function: Callable) -> ValidationResult:
        return validate_validator_function(function)
```

#### 3. Register in Factory

```python
# batch_rename/core/step_factory.py
_STEP_CLASSES[StepType.VALIDATOR] = ValidatorStep
```

#### 4. Update Processing Pipeline

```python
# batch_rename/core/processor.py
def _process_with_pipeline(self, config: RenameConfig, files: List[Path], result: RenameResult):
    # ... existing code ...
    
    # Add validation step after filters
    validators = self._create_validator_steps(config.validators)
    
    for file_path in files:
        context = ProcessingContext(...)
        
        # Apply filters
        if not self._apply_filters(context, filters):
            continue
        
        # Apply validators (new step)
        validation_results = []
        for validator in validators:
            validation_result = validator(context)
            validation_results.append(validation_result)
            if not validation_result.is_valid:
                result.errors += 1
                result.error_details.append({
                    'file': file_path.name,
                    'error': f"Validation failed: {validation_result.message}"
                })
                break  # Skip file if validation fails
        
        # Continue with extraction if validation passed
        # ... rest of pipeline
```

### Adding GUI Components

#### 1. Create Panel Class

```python
# batch_rename/ui/gui/panels/validator.py
from .base import StackableStepPanel
from ....core.steps.base import StepType

class ValidatorPanel(StackableStepPanel):
    """Panel for configuring validation steps."""
    
    def __init__(self):
        super().__init__(StepType.VALIDATOR)
    
    def create_builtin_config(self, function_type: str, layout: QFormLayout):
        if function_type == 'file_integrity':
            self.add_integrity_config(layout)
        elif function_type == 'naming_convention':
            self.add_naming_config(layout)
    
    def add_integrity_config(self, layout: QFormLayout):
        """Configuration for file integrity validation."""
        check_size = QCheckBox("Check file size")
        layout.addRow("Size Check:", check_size)
        
        check_corruption = QCheckBox("Check for corruption")
        layout.addRow("Corruption Check:", check_corruption)
```

#### 2. Integrate into Main GUI

```python
# batch_rename/ui/gui/gui.py
def create_modular_config(self) -> QWidget:
    # ... existing panels ...
    
    # Add validator panel
    self.validator_panel = ValidatorPanel()
    layout.addWidget(self.validator_panel)
    
    return widget
```

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass:**
```bash
python -m pytest tests/ -v --cov=batch_rename
```

2. **Check code style:**
```bash
black batch_rename/ tests/
flake8 batch_rename/ tests/
mypy batch_rename/
```

3. **Update documentation:**
- Add docstrings to new functions
- Update README if adding major features  
- Add examples if applicable

4. **Test your changes:**
```bash
# Test CLI functionality
python main.py --help

# Test GUI functionality  
python -m batch_rename.ui.gui

# Test with real files
python main.py --input-folder examples/sample_files/corporate --extractor split,_,dept,type --preview
```

### Pull Request Template

When creating a pull request, use this template:

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Changes Made
- Added CSV extractor for comma-separated filename patterns
- Implemented corresponding GUI panel
- Added comprehensive tests with 95% coverage
- Updated documentation and examples

## Testing
- [ ] All existing tests pass
- [ ] New tests added and passing
- [ ] Manual testing completed
- [ ] Performance impact assessed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added for new functionality
- [ ] No breaking changes without version bump
```

### Review Process

1. **Automated checks** must pass (tests, linting, coverage)
2. **Code review** by maintainer(s)
3. **Testing** on different platforms if applicable
4. **Documentation review** for completeness
5. **Merge** to develop branch
6. **Release** planning if needed

## Development Guidelines

### Performance Considerations

- **Large file sets**: Test with 1000+ files
- **Memory usage**: Monitor memory consumption
- **UI responsiveness**: Use background threads for long operations
- **Template caching**: Reuse compiled StringSmith templates

### Error Handling

```python
# Good: Specific exception handling with context
try:
    result = process_file(file_path)
except FileNotFoundError as e:
    logger.error("File not found during processing", extra={
        'file_path': str(file_path),
        'error': str(e)
    })
    raise ProcessingError(f"Cannot process missing file: {file_path}") from e
except PermissionError as e:
    logger.error("Permission denied", extra={
        'file_path': str(file_path),
        'error': str(e)  
    })
    raise ProcessingError(f"Permission denied for file: {file_path}") from e

# Bad: Generic exception handling
try:
    result = process_file(file_path)
except Exception as e:
    print(f"Error: {e}")  # No context, no logging
    return None