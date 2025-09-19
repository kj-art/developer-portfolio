"""
Pytest configuration and fixtures for batch rename tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import RenameConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    yield temp_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing extractors and filters."""
    files = {}
    
    # Standard business files
    files['hr_doc'] = temp_dir / "HR_report_20240915.pdf"
    files['finance_doc'] = temp_dir / "FINANCE_budget_Q3_2024.xlsx"
    files['marketing_doc'] = temp_dir / "MARKETING_campaign_summer.jpg"
    
    # Files with numbers needing padding
    files['project_1'] = temp_dir / "PROJECT_status_1.pdf"
    files['project_15'] = temp_dir / "PROJECT_status_15.pdf"
    
    # Mixed case files
    files['mixed_case'] = temp_dir / "hr_handbook_final.pdf"
    
    # Photo files with EXIF-like names
    files['photo1'] = temp_dir / "IMG_20240815_142030.jpg"
    files['photo2'] = temp_dir / "DSC_20240816_095522.jpg"
    
    # Create the actual files with different sizes
    for name, path in files.items():
        if 'small' in name:
            content = b"small file"
        elif name.startswith('project'):
            content = b"x" * (500 * 1024)  # 500KB
        else:
            content = f"Test content for {path.name}".encode()
        path.write_bytes(content)
    
    return files


@pytest.fixture
def valid_extract_convert_config(temp_dir):
    """Create a valid config for extractor + converter workflow."""
    return RenameConfig(
        input_folder=temp_dir,
        extractor="split",
        extractor_args={
            'positional': ['_', 'dept', 'type', 'date'],
            'keyword': {}
        },
        converters=[{
            'name': 'case',  # Use actual converter that exists
            'positional': ['dept', 'upper'],
            'keyword': {}
        }],
        preview_mode=True
    )


@pytest.fixture
def valid_all_in_one_config(temp_dir, tmp_path):
    """Create a valid config for all-in-one function workflow."""
    # Create a simple all-in-one function file
    function_file = tmp_path / "test_function.py"
    function_file.write_text("""
def rename_all(filename, file_path, metadata):
    return filename.lower().replace(' ', '_')
""")
    
    return RenameConfig(
        input_folder=temp_dir,
        extractor=str(function_file),
        extractor_args={
            'positional': ['rename_all'],
            'keyword': {}
        },
        converters=[],
        template=None,
        preview_mode=True
    )


@pytest.fixture
def complex_test_files(temp_dir):
    """Create complex test files for integration testing."""
    files = []
    
    # Subdirectory for recursive testing
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    
    # Various file patterns
    test_patterns = [
        "HR_employee_handbook_2024.pdf",
        "FINANCE_Q3_expenses_final.xlsx", 
        "marketing_hero_image_1920x1080.jpg",
        "PROJECT_alpha_status_v1.2_draft.docx",
        "backup_old_data.bak",  # For filter testing
        "temp_file.tmp",        # For filter testing
        "IMG_20240815_142030_vacation.jpg",
        "ClientABC_Project_v2.1_final_20240901.pdf"
    ]
    
    for i, pattern in enumerate(test_patterns):
        if i % 2 == 0:  # Put half in main dir
            file_path = temp_dir / pattern
        else:  # Put half in subdir
            file_path = subdir / pattern
        
        # Vary file sizes for size-based filtering
        if 'backup' in pattern or 'temp' in pattern:
            content = b"x" * 100  # Small files
        elif 'image' in pattern:
            content = b"x" * (2 * 1024 * 1024)  # Large files (2MB)
        else:
            content = f"Test content for {pattern}".encode()
        
        file_path.write_bytes(content)
        files.append(file_path)
    
    return files


@pytest.fixture
def mock_metadata():
    """Standard metadata for testing."""
    return {
        'size': 1024,
        'created': '2024-08-15',
        'modified': '2024-08-16',
        'type': 'file'
    }


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Configure logging for tests to reduce noise."""
    import logging
    
    # Suppress verbose logging during tests
    logging.getLogger('batch_rename').setLevel(logging.WARNING)
    
    yield
    
    # Reset after tests
    logging.getLogger('batch_rename').setLevel(logging.INFO)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may be skipped in quick runs)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "gui: marks tests that require GUI components (skip in CI)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark slow tests
        if "performance" in item.name or "large" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Mark integration tests
        if "integration" in item.name or "end_to_end" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Mark GUI tests
        if "gui" in str(item.fspath) or "qt" in item.name:
            item.add_marker(pytest.mark.gui)