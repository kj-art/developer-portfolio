# data_pipeline/tests/__init__.py

"""
Test suite for the Data Processing Pipeline.

This package contains comprehensive tests for all components of the data processing
pipeline, including unit tests, integration tests, and performance benchmarks.

Test Categories:
- Unit tests: Test individual components in isolation
- Integration tests: Test component interactions and end-to-end workflows  
- Performance tests: Benchmark processing speed and memory usage

Running Tests:
    # Run all tests
    pytest

    # Run only unit tests
    pytest -m "not slow and not integration"

    # Run with coverage
    pytest --cov=data_pipeline

    # Run specific test module
    pytest tests/test_processor.py

    # Run tests in parallel
    pytest -n auto
"""