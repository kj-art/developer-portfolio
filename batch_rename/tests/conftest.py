"""
Test configuration and fixtures for batch rename tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from batch_rename.core.processing_context import ProcessingContext
from batch_rename.core.config import RenameConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample test files in temporary directory."""
    files = [
        "HR_employee_data_2024.pdf",
        "IT_server_logs_2024.txt", 
        "Finance_budget_report_Q3.xlsx",
        "Marketing_campaign_draft_v1.docx",
        "Legal_contract_final_2024-01-15.pdf",
        "Operations_procedures_manual.doc",
        "Sales_presentation_client_ABC.pptx",
        "Engineering_specs_rev2.pdf",
        "Training_materials_new_hire.pdf",
        "Archive_old_policies_backup.zip"
    ]
    
    created_files = []
    for filename in files:
        file_path = temp_dir / filename
        file_path.write_text(f"Sample content for {filename}")
        created_files.append(file_path)
    
    return created_files


@pytest.fixture
def mock_metadata():
    """Mock file metadata for testing."""
    return {
        'size': 1024,
        'created_timestamp': datetime(2024, 1, 15).timestamp(),
        'modified_timestamp': datetime(2024, 2, 20).timestamp()
    }


@pytest.fixture
def sample_context(sample_files, mock_metadata):
    """Create a sample ProcessingContext for testing."""
    if not sample_files:
        # Fallback if sample_files is empty
        file_path = Path("HR_employee_data_2024.pdf")
    else:
        file_path = sample_files[0]  # HR_employee_data_2024.pdf
    
    return ProcessingContext(
        filename=file_path.name,
        file_path=file_path,
        metadata=mock_metadata
    )


@pytest.fixture
def extracted_context(sample_context):
    """Create a ProcessingContext with extracted data."""
    sample_context.extracted_data = {
        'dept': 'HR',
        'type': 'employee',
        'category': 'data',
        'year': '2024'
    }
    return sample_context


@pytest.fixture
def custom_extractor_file(temp_dir):
    """Create a custom extractor file for testing."""
    extractor_content = '''
def test_extractor(context):
    """Test custom extractor function."""
    filename = context.file_path.stem
    if "_test_" in filename:
        parts = filename.split("_test_")
        return {
            'prefix': parts[0],
            'suffix': parts[1] if len(parts) > 1 else 'unknown'
        }
    return {'prefix': 'unknown', 'suffix': 'unknown'}

def invalid_extractor():
    """Invalid extractor with wrong signature."""
    return {}
'''
    
    extractor_file = temp_dir / "test_extractors.py"
    extractor_file.write_text(extractor_content)
    return extractor_file


@pytest.fixture
def custom_converter_file(temp_dir):
    """Create a custom converter file for testing."""
    converter_content = '''
def test_converter(context):
    """Test custom converter function."""
    if not context.has_extracted_data():
        return {}
    
    result = context.extracted_data.copy()
    # Add a test field
    result['converted'] = 'true'
    
    # Uppercase all string values
    for key, value in result.items():
        if isinstance(value, str):
            result[key] = value.upper()
    
    return result

def invalid_converter(wrong_args):
    """Invalid converter with wrong signature."""
    return {}
'''
    
    converter_file = temp_dir / "test_converters.py"
    converter_file.write_text(converter_content)
    return converter_file


@pytest.fixture
def custom_filter_file(temp_dir):
    """Create a custom filter file for testing."""
    filter_content = '''
def test_filter(context):
    """Test custom filter function."""
    return "_test_" in context.filename

def size_filter(context, min_size=0):
    """Filter by minimum file size."""
    return context.metadata.get('size', 0) >= min_size

def invalid_filter():
    """Invalid filter with wrong signature."""
    return True
'''
    
    filter_file = temp_dir / "test_filters.py"
    filter_file.write_text(filter_content)
    return filter_file


@pytest.fixture
def basic_config(temp_dir):
    """Create a basic RenameConfig for testing."""
    return RenameConfig(
        input_folder=temp_dir,
        extractor="split",
        extractor_args={
            'positional': ['_', 'dept', 'type', 'category', 'year'],
            'keyword': {}
        }
    )


@pytest.fixture
def complex_config(temp_dir):
    """Create a complex RenameConfig for testing."""
    return RenameConfig(
        input_folder=temp_dir,
        extractor="split",
        extractor_args={
            'positional': ['_', 'dept', 'type', 'category'],
            'keyword': {}
        },
        converters=[
            {
                'name': 'case',
                'positional': ['dept', 'upper'],
                'keyword': {}
            },
            {
                'name': 'pad_numbers',
                'positional': ['sequence'],
                'keyword': {'width': 3}
            }
        ],
        filters=[
            {
                'name': 'file_type',
                'positional': ['pdf', 'txt'],
                'keyword': {},
                'inverted': False
            }
        ],
        template={
            'name': 'stringsmith',
            'positional': ['{dept}_{type}_{category}'],
            'keyword': {}
        }
    )