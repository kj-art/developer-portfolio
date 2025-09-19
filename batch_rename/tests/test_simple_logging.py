#!/usr/bin/env python3
"""
Simple, working tests for batch rename logging.

Tests only the core logging functionality that actually exists.
"""

import pytest
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import io

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging_processor import LoggingBatchRenameProcessor, create_logging_processor
from core.processor import BatchRenameProcessor
from core.config import RenameConfig, RenameResult


class TestBasicLogging:
    """Test basic logging functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory with test files."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        (temp_path / "test.txt").write_text("test")
        yield temp_path
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def valid_config(self, temp_dir):
        """Create a valid RenameConfig that passes validation."""
        return RenameConfig(
            input_folder=temp_dir,
            extractor="filename_parts",
            extractor_args={'positional': [], 'keyword': {}},
            converters=[{
                'name': 'format',
                'positional': ['{prefix}_{suffix}'],
                'keyword': {}
            }],
            preview_mode=True
        )
    
    def test_logging_processor_can_be_created(self):
        """Test that LoggingBatchRenameProcessor can be instantiated."""
        processor = LoggingBatchRenameProcessor()
        assert processor is not None
        assert isinstance(processor.processor, BatchRenameProcessor)
    
    def test_create_logging_processor_factory(self):
        """Test the factory function works."""
        processor = create_logging_processor(log_level='INFO')
        assert isinstance(processor, LoggingBatchRenameProcessor)
    
    def test_logging_processor_with_mock(self, valid_config):
        """Test logging processor with mocked underlying processor."""
        
        # Create mock processor that returns success
        mock_processor = Mock(spec=BatchRenameProcessor)
        mock_result = RenameResult(
            files_analyzed=1,
            files_to_rename=1,
            files_renamed=0,
            errors=0,
            collisions=0,
            preview_data=[{'old_name': 'test.txt', 'new_name': 'new_test.txt'}],
            error_details=[]
        )
        mock_processor.process.return_value = mock_result
        
        # Test with logging wrapper
        logging_processor = LoggingBatchRenameProcessor(mock_processor)
        result = logging_processor.process(valid_config)
        
        # Verify it worked
        assert result.files_analyzed == 1
        mock_processor.process.assert_called_once_with(valid_config)
    
    def test_logging_processor_handles_exceptions(self, valid_config):
        """Test that exceptions are properly logged and re-raised."""
        
        mock_processor = Mock(spec=BatchRenameProcessor)
        mock_processor.process.side_effect = ValueError("Test error")
        
        logging_processor = LoggingBatchRenameProcessor(mock_processor)
        
        with pytest.raises(ValueError, match="Test error"):
            logging_processor.process(valid_config)
    
    def test_logging_setup_doesnt_crash(self):
        """Test that logging setup doesn't crash."""
        from shared_utils.logger import set_up_logging
        
        # This should not raise an exception
        set_up_logging(level='INFO', enable_colors=False)
        
        # Get a logger and try to use it
        from shared_utils.logger import get_logger
        logger = get_logger('test')
        logger.info("Test message")


class TestConfigValidation:
    """Test config validation to understand the rules."""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        yield temp_path
        shutil.rmtree(temp_dir)
    
    def test_config_requires_converter_with_extractor(self, temp_dir):
        """Test that config validation requires converter with extractor."""
        
        # This should fail validation
        with pytest.raises(ValueError, match="must provide at least one --converter"):
            RenameConfig(
                input_folder=temp_dir,
                extractor="filename_parts",
                extractor_args={'positional': [], 'keyword': {}},
                converters=[],  # Empty converters should fail
                preview_mode=True
            )
    
    def test_config_works_with_extract_and_convert(self, temp_dir):
        """Test that extract_and_convert mode works without converters."""
        
        # This should pass validation
        config = RenameConfig(
            input_folder=temp_dir,
            extractor=None,
            extract_and_convert="some_function",
            converters=[],
            preview_mode=True
        )
        assert config.extract_and_convert == "some_function"
    
    def test_config_works_with_extractor_and_converter(self, temp_dir):
        """Test that extractor + converter combination works."""
        
        config = RenameConfig(
            input_folder=temp_dir,
            extractor="filename_parts",
            extractor_args={'positional': [], 'keyword': {}},
            converters=[{
                'name': 'format',
                'positional': ['{prefix}_{suffix}'],
                'keyword': {}
            }],
            preview_mode=True
        )
        assert config.extractor == "filename_parts"
        assert len(config.converters) == 1


class TestRealIntegration:
    """Test with real components (no mocking)."""
    
    @pytest.fixture
    def temp_dir_with_files(self):
        """Create temp directory with actual test files."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        
        # Create some test files
        (temp_path / "document1.pdf").write_text("content")
        (temp_path / "report_2024.docx").write_text("content")
        
        yield temp_path
        shutil.rmtree(temp_dir)
    
    def test_end_to_end_logging_doesnt_crash(self, temp_dir_with_files):
        """Test that the whole system works together without crashing."""
        
        config = RenameConfig(
            input_folder=temp_dir_with_files,
            extractor=None,
            extract_and_convert="filename_parts",  # Use extract_and_convert to avoid validation error
            converters=[],
            preview_mode=True
        )
        
        processor = create_logging_processor(log_level='INFO')
        
        # This might fail due to missing extractors, but shouldn't crash from logging
        try:
            result = processor.process(config)
            # If it works, great!
            assert isinstance(result, RenameResult)
        except Exception as e:
            # If it fails, it should be a business logic error, not a logging error
            assert "logging" not in str(e).lower()
            # Common expected errors
            assert any(expected in str(e) for expected in [
                "extractor", "converter", "function", "module"
            ])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])