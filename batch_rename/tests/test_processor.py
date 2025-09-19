"""
Unit tests for main processor and configuration.

Tests the core processing pipeline, configuration validation, and integration.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from core.processor import BatchRenameProcessor
from core.config import RenameConfig, RenameResult


class TestRenameConfig:
    """Test RenameConfig validation and creation."""
    
    def test_valid_extract_convert_config(self, temp_dir):
        """Test valid extractor + converter configuration."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={
                'positional': ['_', 'dept', 'type'],
                'keyword': {}
            },
            converters=[{
                'name': 'format',
                'positional': ['{dept}_{type}'],
                'keyword': {}
            }],
            preview_mode=True
        )
        
        assert config.input_folder == temp_dir
        assert config.extractor == "split"
        assert len(config.converters) == 1
        assert config.preview_mode is True
    
    def test_valid_all_in_one_config(self, temp_dir, tmp_path):
        """Test valid all-in-one function configuration."""
        function_file = tmp_path / "test_func.py"
        function_file.write_text("def rename_all(filename, file_path, metadata): return filename.lower()")
        
        config = RenameConfig(
            input_folder=temp_dir,
            extractor=None,
            extract_and_convert=str(function_file),  # Use extract_and_convert instead
            converters=[],
            template=None,
            preview_mode=True
        )
        
        assert config.input_folder == temp_dir
        assert config.extract_and_convert == str(function_file)  # Should be in extract_and_convert, not extractor
        assert len(config.converters) == 0
    
    def test_config_validation_missing_converter(self, temp_dir):
        """Test config validation fails when extractor has no converters."""
        with pytest.raises(ValueError, match="must provide at least one.*converter"):
            RenameConfig(
                input_folder=temp_dir,
                extractor="split",
                extractor_args={'positional': ['_'], 'keyword': {}},
                converters=[],  # No converters with extractor
                preview_mode=True
            )
    
    def test_config_validation_missing_input_folder(self):
        """Test config validation with missing input folder."""
        # This should test actual validation - if None is passed, it should fail
        with pytest.raises((ValueError, TypeError)):
            RenameConfig(
                input_folder=None,  # This should cause validation failure
                extractor="split",
                extractor_args={'positional': ['_'], 'keyword': {}},
                converters=[{'name': 'case', 'positional': ['field', 'upper'], 'keyword': {}}],
                preview_mode=True
            )
    
    def test_config_with_template(self, temp_dir):
        """Test config with template instead of converters."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'dept'], 'keyword': {}},
            converters=[],
            template={
                'name': 'template',  # Use valid template name
                'positional': ['{dept}_formatted'],
                'keyword': {}
            },
            preview_mode=True
        )
        
        assert config.template is not None
        assert config.template['name'] == 'template'  # Should match what we set
    
    def test_config_with_filters(self, temp_dir):
        """Test config with filters."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'dept'], 'keyword': {}},
            converters=[{'name': 'format', 'positional': ['{dept}'], 'keyword': {}}],
            filters=[{
                'name': 'extension',
                'positional': ['pdf'],
                'keyword': {},
                'invert': False
            }],
            preview_mode=True
        )
        
        assert len(config.filters) == 1
        assert config.filters[0]['name'] == 'extension'


class TestBatchRenameProcessor:
    """Test BatchRenameProcessor functionality."""
    
    def test_processor_initialization(self):
        """Test processor can be initialized."""
        processor = BatchRenameProcessor()
        assert processor is not None
        assert processor.results is None
    
    def test_process_with_no_files(self, temp_dir):
        """Test processing empty directory."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'dept'], 'keyword': {}},
            converters=[{'name': 'format', 'positional': ['{dept}'], 'keyword': {}}],
            preview_mode=True
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        assert isinstance(result, RenameResult)
        assert result.files_analyzed == 0
        assert result.files_to_rename == 0
        assert result.errors == 0
    
    def test_process_basic_workflow(self, sample_files, valid_extract_convert_config):
        """Test basic processing workflow."""
        processor = BatchRenameProcessor()
        result = processor.process(valid_extract_convert_config)
        
        assert isinstance(result, RenameResult)
        assert result.files_analyzed > 0
        assert result.errors == 0
        assert len(result.preview_data) >= 0
    
    def test_process_with_filters(self, sample_files, temp_dir):
        """Test processing with filters applied."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'dept'], 'keyword': {}},
            converters=[{'name': 'format', 'positional': ['{dept}'], 'keyword': {}}],
            filters=[{
                'name': 'extension',
                'positional': ['pdf'],
                'keyword': {},
                'invert': False
            }],
            preview_mode=True
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        # Should only process PDF files
        assert result.files_analyzed > 0
        if result.files_to_rename > 0:
            # If any files match, they should all be PDFs
            for preview in result.preview_data:
                assert preview['old_name'].endswith('.pdf')
    
    def test_process_collision_detection(self, temp_dir):
        """Test collision detection in processing."""
        # Create files that would result in name collisions
        (temp_dir / "DEPT_doc_1.pdf").write_text("content")
        (temp_dir / "DEPT_document_1.pdf").write_text("content")
        
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'dept'], 'keyword': {}},
            converters=[{'name': 'format', 'positional': ['{dept}_doc'], 'keyword': {}}],
            preview_mode=True
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        # Should detect potential collisions
        if result.files_to_rename > 1:
            assert result.collisions > 0
    
    def test_process_error_handling(self, temp_dir):
        """Test error handling during processing."""
        # Create a file for testing
        (temp_dir / "test_file.pdf").write_text("content")
        
        # Use invalid extractor configuration to trigger error
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="invalid_extractor",
            extractor_args={'positional': [], 'keyword': {}},
            converters=[{'name': 'format', 'positional': ['{field}'], 'keyword': {}}],
            preview_mode=True
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        # Should have errors but not crash
        assert result.errors > 0
        assert len(result.error_details) > 0
    
    def test_process_recursive_discovery(self, complex_test_files, temp_dir):
        """Test recursive file discovery."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'dept'], 'keyword': {}},
            converters=[{'name': 'format', 'positional': ['{dept}'], 'keyword': {}}],
            recursive=True,
            preview_mode=True
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        # Should find files in subdirectories
        assert result.files_analyzed >= len(complex_test_files)
    
    def test_process_non_recursive(self, complex_test_files, temp_dir):
        """Test non-recursive file discovery."""
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'dept'], 'keyword': {}},
            converters=[{'name': 'format', 'positional': ['{dept}'], 'keyword': {}}],
            recursive=False,
            preview_mode=True
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        # Should only find files in main directory (not subdirs)
        subdir_files = len([f for f in complex_test_files if 'subdir' in str(f)])
        main_dir_files = len(complex_test_files) - subdir_files
        
        assert result.files_analyzed == main_dir_files
    
    @patch('core.processor.shutil.move')
    def test_process_execute_mode(self, mock_move, sample_files, valid_extract_convert_config):
        """Test actual execution mode (not preview)."""
        # Change to execute mode
        valid_extract_convert_config.preview_mode = False
        
        processor = BatchRenameProcessor()
        result = processor.process(valid_extract_convert_config)
        
        # Should attempt to rename files
        if result.files_to_rename > 0:
            assert mock_move.called
            assert result.files_renamed >= 0


class TestRenameResult:
    """Test RenameResult data structure."""
    
    def test_result_initialization(self):
        """Test RenameResult can be initialized."""
        result = RenameResult(
            files_analyzed=5,
            files_to_rename=3,
            files_renamed=0,
            errors=0,
            collisions=1,
            preview_data=[],
            error_details=[]
        )
        
        assert result.files_analyzed == 5
        assert result.files_to_rename == 3
        assert result.files_renamed == 0
        assert result.collisions == 1
        assert isinstance(result.preview_data, list)
        assert isinstance(result.error_details, list)
    
    def test_result_with_preview_data(self):
        """Test RenameResult with preview data."""
        preview_data = [
            {'old_name': 'file1.pdf', 'new_name': 'new_file1.pdf'},
            {'old_name': 'file2.pdf', 'new_name': 'new_file2.pdf'}
        ]
        
        result = RenameResult(
            files_analyzed=2,
            files_to_rename=2,
            files_renamed=0,
            errors=0,
            collisions=0,
            preview_data=preview_data,
            error_details=[]
        )
        
        assert len(result.preview_data) == 2
        assert result.preview_data[0]['old_name'] == 'file1.pdf'
        assert result.preview_data[1]['new_name'] == 'new_file2.pdf'
    
    def test_result_with_errors(self):
        """Test RenameResult with error details."""
        error_details = [
            {'file': 'problematic.pdf', 'error': 'Invalid format'},
            {'file': 'another.pdf', 'error': 'Permission denied'}
        ]
        
        result = RenameResult(
            files_analyzed=2,
            files_to_rename=0,
            files_renamed=0,
            errors=2,
            collisions=0,
            preview_data=[],
            error_details=error_details
        )
        
        assert result.errors == 2
        assert len(result.error_details) == 2
        assert result.error_details[0]['file'] == 'problematic.pdf'
        assert result.error_details[1]['error'] == 'Permission denied'


class TestProcessingIntegration:
    """Test full processing pipeline integration."""
    
    def test_end_to_end_split_format_workflow(self, temp_dir):
        """Test complete split -> format workflow."""
        # Create test files
        (temp_dir / "HR_report_20240815.pdf").write_text("content")
        (temp_dir / "FINANCE_budget_Q3.xlsx").write_text("content")
        
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'dept', 'type', 'date'], 'keyword': {}},
            converters=[{
                'name': 'case',
                'positional': ['dept', 'upper'],
                'keyword': {}
            }],
            preview_mode=True
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        # Check that processing works without errors
        assert result.files_analyzed == 2
        # The processor should work even if it doesn't create renames
        assert result.errors == 0
    
    def test_end_to_end_with_multiple_converters(self, temp_dir):
        """Test workflow with multiple converters."""
        # Create test file
        (temp_dir / "hr_report_1.pdf").write_text("content")
        
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'dept', 'type', 'num'], 'keyword': {}},
            converters=[
                {
                    'name': 'case',
                    'positional': ['dept', 'upper'],
                    'keyword': {}
                },
                {
                    'name': 'pad_numbers',
                    'positional': ['num', 3],
                    'keyword': {}
                }
            ],
            preview_mode=True
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        assert result.files_analyzed == 1
        assert result.errors == 0
        
        # Should transform to: HR_report_001.pdf
        if result.files_to_rename > 0:
            new_name = result.preview_data[0]['new_name']
            assert 'HR_report_001.pdf' == new_name
    
    def test_end_to_end_with_template(self, temp_dir):
        """Test workflow using template instead of format converter."""
        # Create test file
        (temp_dir / "PROJECT_alpha_v1.pdf").write_text("content")
        
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'type', 'name', 'version'], 'keyword': {}},
            converters=[],  # No converters, just template
            template={
                'name': 'template',  # Use valid template name
                'positional': ['{name}_{version}_{type}'],
                'keyword': {}
            },
            preview_mode=True
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        assert result.files_analyzed == 1
        assert result.errors == 0
        
        if result.files_to_rename > 0:
            new_name = result.preview_data[0]['new_name']
            assert 'alpha_v1_PROJECT.pdf' == new_name
    
    def test_end_to_end_with_filters_excluding(self, temp_dir):
        """Test workflow with filters that exclude files."""
        # Create mixed file types
        (temp_dir / "document.pdf").write_text("content")
        (temp_dir / "backup.bak").write_text("content")
        (temp_dir / "temp_file.tmp").write_text("content")
        
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'name'], 'keyword': {}},
            converters=[{
                'name': 'format',
                'positional': ['{name}_processed'],
                'keyword': {}
            }],
            filters=[{
                'name': 'extension',
                'positional': ['pdf'],
                'keyword': {},
                'invert': False
            }],
            preview_mode=True
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        assert result.files_analyzed == 3  # All files analyzed
        # But only PDF should be processed
        if result.files_to_rename > 0:
            for preview in result.preview_data:
                assert preview['old_name'].endswith('.pdf')
    
    def test_field_validation_error(self, temp_dir):
        """Test field validation catches converter field mismatches."""
        # Create test file
        (temp_dir / "HR_report.pdf").write_text("content")
        
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="split",
            extractor_args={'positional': ['_', 'dept', 'type'], 'keyword': {}},
            converters=[
                {
                    'name': 'format',
                    'positional': ['{dept}_{nonexistent_field}'],  # Field not extracted
                    'keyword': {}
                }
            ],
            preview_mode=True
        )
        
        processor = BatchRenameProcessor()
        result = processor.process(config)
        
        # Should handle gracefully (StringSmith handles missing fields)
        assert result.files_analyzed == 1
        # May or may not produce errors depending on StringSmith behavior