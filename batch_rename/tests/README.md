# Batch Rename Test Suite

Comprehensive unit and integration tests for the batch rename project.

## Overview

The test suite provides thorough coverage of all core functionality including:

- **Built-in Functions**: All extractors, converters, filters, and templates
- **Custom Functions**: Loading and validation of user-defined functions  
- **Processing Pipeline**: End-to-end workflow testing
- **Error Handling**: Edge cases and error conditions
- **Performance**: Scalability and efficiency tests

## Test Structure

### Test Files

- `conftest.py` - Shared fixtures and test configuration
- `test_extractors.py` - Built-in extractor functions
- `test_converters.py` - Built-in converter functions  
- `test_filters.py` - Built-in filter functions
- `test_templates.py` - Built-in template functions
- `test_processing_context.py` - Data container and context handling
- `test_step_factory.py` - Factory pattern and step management
- `test_processor.py` - Core processing engine
- `test_config.py` - Configuration validation and handling
- `test_integration.py` - End-to-end workflows and real scenarios

### Key Fixtures

**File Management:**
- `temp_dir` - Temporary directory for test files
- `sample_files` - Realistic test file collection
- `mock_metadata` - File metadata for testing

**Processing Context:**
- `sample_context` - Basic ProcessingContext instance
- `extracted_context` - Context with extracted data

**Custom Functions:**
- `custom_extractor_file` - Example custom extractor
- `custom_converter_file` - Example custom converter
- `custom_filter_file` - Example custom filter

**Configurations:**
- `basic_config` - Minimal valid configuration
- `complex_config` - Full-featured configuration

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py all

# Run specific test categories
python run_tests.py unit
python run_tests.py integration
python run_tests.py quick

# Run tests for specific modules
python run_tests.py extractors
python run_tests.py converters
python run_tests.py processor
```

### Using Pytest Directly

```bash
# All tests with verbose output
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_extractors.py -v

# Specific test class
python -m pytest tests/test_extractors.py::TestSplitExtractor -v

# Specific test method
python -m pytest tests/test_extractors.py::TestSplitExtractor::test_split_basic -v

# Run with markers
python -m pytest tests/ -m "unit" -v
python -m pytest tests/ -m "not slow" -v
```

### Coverage Reports

```bash
# Generate coverage report
python run_tests.py coverage

# Or with pytest directly
python -m pytest tests/ --cov=core --cov-report=html --cov-report=term-missing
```

## Test Categories

### Unit Tests

Focus on individual components in isolation:

- **Extractor Functions**: Data extraction from filenames
- **Converter Functions**: Field transformation logic  
- **Filter Functions**: File selection criteria
- **Template Functions**: Filename generation
- **Utility Classes**: ProcessingContext, StepFactory

### Integration Tests

Test complete workflows and realistic scenarios:

- **Document Workflows**: HR documents, project files
- **Performance Testing**: Large file batches
- **Error Recovery**: Handling various failure modes
- **Custom Functions**: User-defined function integration

### Performance Tests

Validate scalability and efficiency:

- **Large Batches**: 100+ files processing
- **Memory Usage**: Efficient preview generation
- **Processing Time**: Linear time complexity

## Test Data

### Sample Files

Tests use realistic filename patterns:

```
HR_employee_data_2024.pdf
IT_server_logs_2024.txt
Finance_budget_report_Q3.xlsx
Marketing_campaign_draft_v1.docx
Legal_contract_final_2024-01-15.pdf
```

### Mock Metadata

Simulated file metadata for testing:

```python
{
    'size': 1024,
    'created_timestamp': datetime(2024, 1, 15).timestamp(),
    'modified_timestamp': datetime(2024, 2, 20).timestamp()
}
```

## Writing New Tests

### Test Organization

Follow the existing pattern:

```python
class TestFeatureName:
    """Test description."""
    
    def test_basic_functionality(self, fixture_name):
        """Test basic use case."""
        # Arrange
        input_data = setup_test_data()
        
        # Act  
        result = function_under_test(input_data)
        
        # Assert
        assert result == expected_output
        assert some_condition is True
```

### Using Fixtures

Leverage existing fixtures for consistency:

```python
def test_with_sample_context(self, sample_context):
    """Test using sample ProcessingContext."""
    # Context already set up with realistic file
    assert sample_context.filename == "HR_employee_data_2024.pdf"

def test_with_extracted_data(self, extracted_context):
    """Test using context with extracted data."""
    # Context has pre-extracted fields
    assert extracted_context.get_extracted_field('dept') == 'HR'
```

### Custom Test Files

For tests requiring specific files:

```python
def test_custom_scenario(self, temp_dir):
    """Test with custom file setup."""
    # Create specific test files
    test_file = temp_dir / "custom_pattern_file.ext"
    test_file.write_text("test content")
    
    # Use in test
    context = ProcessingContext(test_file, {})
    # ... rest of test
```

## Best Practices

### Test Naming

- Use descriptive test names: `test_split_extractor_with_multiple_delimiters`
- Follow pattern: `test_<what>_<condition>_<expected>`
- Group related tests in classes: `TestSplitExtractor`

### Test Independence

- Each test should be independent and isolated
- Use fixtures for shared setup
- Clean up temporary resources automatically

### Assertions

- Use specific assertions: `assert result == expected` not `assert result`
- Include helpful error messages: `assert len(results) == 3, f"Expected 3 results, got {len(results)}"`
- Test both success and failure cases

### Edge Cases

Always test edge cases:

- Empty inputs
- Invalid inputs  
- Boundary conditions
- Unicode/special characters
- Very large inputs

## Debugging Tests

### Verbose Output

```bash
# See detailed test output
python -m pytest tests/ -v -s

# Stop on first failure
python -m pytest tests/ -x

# Show local variables on failure
python -m pytest tests/ --tb=long
```

### Debugging Specific Tests

```bash
# Run single test with debugging
python -m pytest tests/test_extractors.py::TestSplitExtractor::test_split_basic -v -s

# Drop into debugger on failure
python -m pytest tests/ --pdb
```

## Continuous Integration

The test suite is designed for CI/CD integration:

- Fast execution (< 30 seconds for full suite)
- Clear pass/fail indicators
- Detailed error reporting
- Coverage metrics
- No external dependencies for core tests

## Contributing

When adding new functionality:

1. **Write tests first** (TDD approach)
2. **Ensure good coverage** (aim for >90%)
3. **Test edge cases** and error conditions
4. **Update documentation** as needed
5. **Run full test suite** before submitting

The test suite ensures code quality and prevents regressions as the project evolves.