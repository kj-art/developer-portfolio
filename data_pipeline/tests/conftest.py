# data_pipeline/tests/conftest.py

"""
Shared test fixtures and configuration for data pipeline tests.

This module provides common fixtures that can be used across all test modules
without explicit imports. Pytest automatically discovers and makes these
fixtures available to all tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import json
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def temp_data_dir():
    """
    Session-scoped temporary directory for test data.
    
    Creates a temporary directory that persists for the entire test session,
    useful for expensive-to-create test data that can be shared across tests.
    """
    temp_path = Path(tempfile.mkdtemp(prefix="data_pipeline_tests_"))
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def temp_dir():
    """
    Function-scoped temporary directory.
    
    Creates a fresh temporary directory for each test function,
    ensuring test isolation and cleanup.
    """
    temp_path = Path(tempfile.mkdtemp(prefix="test_"))
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_dataframes():
    """
    Collection of sample DataFrames for testing.
    
    Provides various DataFrame structures commonly encountered in real data:
    - Simple tabular data
    - Data with missing values
    - Data with inconsistent column names
    - Data with different types
    """
    return {
        'simple': pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'value': [10.5, 20.1, 30.7]
        }),
        
        'missing_data': pd.DataFrame({
            'id': [1, 2, 3, 4],
            'name': ['Alice', None, 'Charlie', ''],
            'age': [25, 30, None, 35],
            'email': ['alice@test.com', 'bob@test.com', None, 'dave@test.com']
        }),
        
        'inconsistent_names': pd.DataFrame({
            'Customer Name': ['John Doe', 'Jane Smith'],
            'Email Address': ['john@test.com', 'jane@test.com'],
            'Years Old': [25, 30]
        }),
        
        'mixed_types': pd.DataFrame({
            'id': ['A001', 'B002', 'C003'],  # String IDs
            'value': [10, 20.5, 30],         # Mixed numeric
            'active': [True, False, None],    # Boolean with null
            'created': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03'])
        })
    }


@pytest.fixture
def test_files_simple(temp_dir):
    """
    Create a set of simple test files with consistent structure.
    
    Useful for testing basic file processing functionality
    without the complexity of schema conflicts or data issues.
    """
    files = {}
    
    # Simple CSV
    csv_data = "id,name,value\n1,Alice,10.5\n2,Bob,20.1\n"
    csv_file = temp_dir / "simple.csv"
    csv_file.write_text(csv_data)
    files['csv'] = csv_file
    
    # Simple Excel
    df = pd.DataFrame({'id': [3, 4], 'name': ['Charlie', 'David'], 'value': [30.7, 40.2]})
    excel_file = temp_dir / "simple.xlsx"
    df.to_excel(excel_file, index=False)
    files['excel'] = excel_file
    
    # Simple JSON
    json_data = [
        {"id": 5, "name": "Eve", "value": 50.9},
        {"id": 6, "name": "Frank", "value": 60.3}
    ]
    json_file = temp_dir / "simple.json"
    json_file.write_text(json.dumps(json_data))
    files['json'] = json_file
    
    return files


@pytest.fixture
def test_files_complex(temp_dir):
    """
    Create complex test files with realistic data challenges.
    
    Includes:
    - Inconsistent column names
    - Missing data
    - Type conflicts
    - Special characters
    - Multiple sheets (Excel)
    - Nested structures (JSON)
    """
    files = {}
    
    # Complex CSV with encoding issues and missing data
    csv_data = "Customer Name,Email Address,Years Old\nJohn Doe,john@test.com,25\nJané Smith,,30\n,jane@test.com,\n"
    csv_file = temp_dir / "complex.csv"
    csv_file.write_bytes(csv_data.encode('utf-8'))
    files['csv'] = csv_file
    
    # Multi-sheet Excel with different schemas
    excel_file = temp_dir / "complex.xlsx"
    with pd.ExcelWriter(excel_file) as writer:
        # Sheet 1: Customer data
        customers_df = pd.DataFrame({
            'Full Name': ['Alice Brown', 'Bob Wilson'],
            'Email': ['alice@test.com', 'bob@test.com'],
            'Age': [28, 35]
        })
        customers_df.to_excel(writer, sheet_name='Customers', index=False)
        
        # Sheet 2: Order data (different schema)
        orders_df = pd.DataFrame({
            'Order ID': ['ORD001', 'ORD002'],
            'Customer': ['Alice Brown', 'Bob Wilson'],
            'Amount': [150.50, 275.25],
            'Date': ['2023-01-15', '2023-01-16']
        })
        orders_df.to_excel(writer, sheet_name='Orders', index=False)
    
    files['excel'] = excel_file
    
    # Nested JSON structure
    json_data = {
        "employees": [
            {
                "name": "Charlie Davis",
                "contact": {
                    "email": "charlie@test.com",
                    "phone": "555-0101"
                },
                "details": {
                    "age": 32,
                    "department": "Engineering"
                }
            },
            {
                "name": "Diana Prince",
                "contact": {
                    "email": "diana@test.com",
                    "phone": "555-0102"
                },
                "details": {
                    "age": 29,
                    "department": "Marketing"
                }
            }
        ],
        "departments": [
            {"name": "Engineering", "budget": 500000},
            {"name": "Marketing", "budget": 300000}
        ]
    }
    
    json_file = temp_dir / "complex.json"
    json_file.write_text(json.dumps(json_data))
    files['json'] = json_file
    
    return files


@pytest.fixture
def malformed_files(temp_dir):
    """
    Create files with various types of corruption/malformation.
    
    Useful for testing error handling and recovery mechanisms.
    """
    files = {}
    
    # Malformed CSV (inconsistent columns)
    csv_data = "name,age,city\nJohn,25\nJane,30,Chicago,Extra\nBob\n"
    csv_file = temp_dir / "malformed.csv"
    csv_file.write_text(csv_data)
    files['csv'] = csv_file
    
    # Corrupted JSON
    json_data = '{"data": [{"name": "John", "age": 25}, {"name": "Jane", "age":}]}'  # Missing value
    json_file = temp_dir / "malformed.json"
    json_file.write_text(json_data)
    files['json'] = json_file
    
    # Empty file
    empty_file = temp_dir / "empty.csv"
    empty_file.write_text("")
    files['empty'] = empty_file
    
    # Binary file with wrong extension
    binary_file = temp_dir / "fake.csv"
    binary_file.write_bytes(b'\x89PNG\r\n\x1a\n')  # PNG header
    files['binary'] = binary_file
    
    return files


@pytest.fixture
def schema_mappings():
    """
    Sample schema mapping configurations for testing.
    
    Provides various schema mapping scenarios commonly used
    for standardizing data from different sources.
    """
    return {
        'customer_schema': {
            'name': ['Customer Name', 'Full Name', 'client_name'],
            'email': ['Email Address', 'Email', 'e_mail', 'contact_email'],
            'age': ['Age', 'Years Old', 'years', 'customer_age'],
            'phone': ['Phone Number', 'Phone', 'contact_phone', 'telephone']
        },
        
        'product_schema': {
            'product_id': ['ID', 'Product ID', 'SKU', 'product_code'],
            'name': ['Product Name', 'Name', 'title', 'product_title'],
            'price': ['Price', 'Cost', 'amount', 'product_price'],
            'category': ['Category', 'Type', 'product_type', 'classification']
        },
        
        'order_schema': {
            'order_id': ['Order ID', 'ID', 'order_number', 'reference'],
            'customer': ['Customer', 'Client', 'customer_name', 'buyer'],
            'amount': ['Amount', 'Total', 'price', 'order_total'],
            'date': ['Date', 'Order Date', 'created', 'order_date']
        }
    }


@pytest.fixture
def performance_data(temp_dir):
    """
    Create larger datasets for performance testing.
    
    Generates files with significant amounts of data to test
    streaming vs in-memory processing performance characteristics.
    """
    files = {}
    
    # Large CSV (10,000 rows)
    import io
    large_csv = temp_dir / "large.csv"
    
    with open(large_csv, 'w', newline='') as f:
        f.write("id,name,value,category\n")
        for i in range(10000):
            f.write(f"{i},User{i},{i * 1.5},Category{i % 10}\n")
    
    files['large_csv'] = large_csv
    
    # Medium Excel with multiple sheets
    medium_excel = temp_dir / "medium.xlsx"
    with pd.ExcelWriter(medium_excel) as writer:
        for sheet_num in range(5):
            df = pd.DataFrame({
                'id': range(sheet_num * 1000, (sheet_num + 1) * 1000),
                'value': [i * 2.5 for i in range(1000)],
                'category': [f'Cat{i % 5}' for i in range(1000)]
            })
            df.to_excel(writer, sheet_name=f'Sheet{sheet_num}', index=False)
    
    files['medium_excel'] = medium_excel
    
    return files


@pytest.fixture(autouse=True)
def setup_test_logging():
    """
    Configure logging for test environment.
    
    Auto-used fixture that sets up consistent logging configuration
    for all tests without cluttering test output.
    """
    import logging
    
    # Suppress verbose logging during tests
    logging.getLogger('data_pipeline').setLevel(logging.WARNING)
    logging.getLogger('shared_utils').setLevel(logging.WARNING)
    
    yield
    
    # Reset logging after tests
    logging.getLogger('data_pipeline').setLevel(logging.INFO)
    logging.getLogger('shared_utils').setLevel(logging.INFO)


@pytest.fixture
def mock_processor_config():
    """
    Mock configuration for processor testing.
    
    Provides a standardized configuration object that can be
    customized for specific test scenarios.
    """
    from data_pipeline.core.processing_config import ProcessingConfig, IndexMode
    
    return ProcessingConfig(
        input_folder="/test/input",
        output_file="/test/output.csv",
        recursive=False,
        file_type_filter=['csv', 'xlsx', 'json'],
        to_lower=True,
        spaces_to_underscores=True,
        index_mode=IndexMode.NONE,
        index_start=0,
        force_in_memory=False,
        read_options={},
        write_options={}
    )


# Pytest configuration
def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may be skipped in quick runs)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers based on test names.
    """
    for item in items:
        # Mark performance tests
        if "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)
        
        # Mark integration tests
        if "integration" in item.nodeid.lower() or "end_to_end" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests (tests that create large datasets)
        if any(keyword in item.nodeid.lower() for keyword in ["large", "bulk", "stress"]):
            item.add_marker(pytest.mark.slow)