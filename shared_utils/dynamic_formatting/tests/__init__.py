"""
Dynamic Formatting Test Suite

Professional test suite for the dynamic formatting package using pytest.
Provides comprehensive coverage of all features including positional arguments,
function fallback, error handling, and performance characteristics.

Run tests with:
    pytest shared_utils/dynamic_formatting/tests/
    
Run with coverage:
    pytest --cov=shared_utils.dynamic_formatting shared_utils/dynamic_formatting/tests/
    
Run specific test categories:
    pytest -m "core" shared_utils/dynamic_formatting/tests/
    pytest -m "performance" shared_utils/dynamic_formatting/tests/
    pytest -m "regression" shared_utils/dynamic_formatting/tests/

Test marks:
    - core: Basic functionality tests
    - positional: Positional argument feature tests  
    - fallback: Function fallback system tests
    - error: Error handling and edge cases
    - performance: Performance and benchmarking tests
    - regression: Backward compatibility tests
    - integration: Full system integration tests
"""

__version__ = "1.0.0"