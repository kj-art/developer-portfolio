# data_pipeline/tests/test_index_manager.py

import pytest
import pandas as pd

from data_pipeline.core.indexing import IndexManager
from data_pipeline.core.processing_config import IndexMode


class TestIndexManager:
    """Test IndexManager functionality"""
    
    def test_none_mode(self):
        """Test NONE index mode"""
        manager = IndexManager(IndexMode.NONE)
        
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        result = manager.process_chunk(df)
        
        # Should return original dataframe unchanged
        pd.testing.assert_frame_equal(result, df)
        assert '__index__' not in result.columns
    
    def test_none_mode_with_none_value(self):
        """Test None value (same as NONE mode)"""
        manager = IndexManager(None)
        
        df = pd.DataFrame({'col1': [1, 2, 3]})
        result = manager.process_chunk(df)
        
        pd.testing.assert_frame_equal(result, df)
        assert '__index__' not in result.columns
    
    def test_local_mode_single_file(self):
        """Test LOCAL mode with single file"""
        manager = IndexManager(IndexMode.LOCAL, start_value=0)
        
        # First chunk of a file
        df1 = pd.DataFrame({'col1': [1, 2]})
        result1 = manager.process_chunk(df1, is_new_file=True)
        
        assert '__index__' in result1.columns
        assert result1['__index__'].tolist() == [0, 1]
        
        # Second chunk of same file
        df2 = pd.DataFrame({'col1': [3, 4, 5]})
        result2 = manager.process_chunk(df2, is_new_file=False)
        
        assert result2['__index__'].tolist() == [2, 3, 4]
    
    def test_local_mode_multiple_files(self):
        """Test LOCAL mode with multiple files"""
        manager = IndexManager(IndexMode.LOCAL, start_value=1)
        
        # First file
        df1 = pd.DataFrame({'col1': [1, 2]})
        result1 = manager.process_chunk(df1, is_new_file=True)
        assert result1['__index__'].tolist() == [1, 2]
        
        # Second file should restart numbering
        df2 = pd.DataFrame({'col1': [3, 4, 5]})
        result2 = manager.process_chunk(df2, is_new_file=True)
        assert result2['__index__'].tolist() == [1, 2, 3]
    
    def test_sequential_mode(self):
        """Test SEQUENTIAL mode"""
        manager = IndexManager(IndexMode.SEQUENTIAL, start_value=100)
        
        # First chunk
        df1 = pd.DataFrame({'col1': [1, 2]})
        result1 = manager.process_chunk(df1, is_new_file=True)
        assert result1['__index__'].tolist() == [100, 101]
        
        # Second chunk continues numbering
        df2 = pd.DataFrame({'col1': [3, 4, 5]})
        result2 = manager.process_chunk(df2, is_new_file=True)
        assert result2['__index__'].tolist() == [102, 103, 104]
        
        # Third chunk from same file continues
        df3 = pd.DataFrame({'col1': [6]})
        result3 = manager.process_chunk(df3, is_new_file=False)
        assert result3['__index__'].tolist() == [105]
    
    def test_finalize_in_memory_index(self):
        """Test finalizing index for in-memory processing"""
        manager = IndexManager(IndexMode.SEQUENTIAL)
        
        # Process chunks to add __index__ column
        df1 = pd.DataFrame({'col1': [1, 2]})
        processed1 = manager.process_chunk(df1, is_new_file=True)
        
        df2 = pd.DataFrame({'col1': [3, 4]})
        processed2 = manager.process_chunk(df2, is_new_file=False)
        
        # Combine chunks
        combined = pd.concat([processed1, processed2], ignore_index=True)
        
        # Finalize index
        final = manager.finalize_in_memory_index(combined)
        
        # Should have proper index set
        assert final.index.tolist() == [0, 1, 2, 3]
        assert '__index__' not in final.columns
        assert final.index.name is None
    
    def test_finalize_streaming_chunk(self):
        """Test finalizing chunk for streaming output"""
        manager = IndexManager(IndexMode.LOCAL)
        
        df = pd.DataFrame({'col1': [1, 2, 3]})
        processed = manager.process_chunk(df, is_new_file=True)
        
        # Finalize for streaming
        final = manager.finalize_streaming_chunk(processed)
        
        assert final.index.tolist() == [0, 1, 2]
        assert '__index__' not in final.columns
        assert final.index.name is None
    
    def test_finalize_missing_index_column(self):
        """Test error when __index__ column is missing"""
        manager = IndexManager(IndexMode.SEQUENTIAL)
        
        # DataFrame without __index__ column
        df = pd.DataFrame({'col1': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="DataFrame missing __index__ column"):
            manager.finalize_in_memory_index(df)
        
        with pytest.raises(ValueError, match="Chunk missing __index__ column"):
            manager.finalize_streaming_chunk(df)
    
    def test_apply_write_options_none_mode(self):
        """Test write options with NONE mode"""
        manager = IndexManager(IndexMode.NONE)
        
        write_options = {'sep': ',', 'na_rep': 'NULL'}
        updated = manager.apply_write_options(write_options)
        
        # Should set index=False for NONE mode
        assert updated['index'] is False
        assert updated['sep'] == ','
        assert updated['na_rep'] == 'NULL'
    
    def test_apply_write_options_sequential_mode(self):
        """Test write options with SEQUENTIAL mode"""
        manager = IndexManager(IndexMode.SEQUENTIAL)
        
        write_options = {'sep': ',', 'index': False}  # User tries to disable index
        updated = manager.apply_write_options(write_options)
        
        # IndexMode should override user setting
        assert updated['index'] is True
        assert updated['sep'] == ','
    
    def test_apply_write_options_no_mode(self):
        """Test write options when no IndexMode is set"""
        manager = IndexManager(None)
        
        write_options = {'sep': ',', 'index': True}
        updated = manager.apply_write_options(write_options)
        
        # Should preserve original index setting
        assert updated['index'] is True
        assert updated['sep'] == ','
    
    def test_should_include_index(self):
        """Test should_include_index method"""
        manager_none = IndexManager(IndexMode.NONE)
        manager_local = IndexManager(IndexMode.LOCAL)
        manager_sequential = IndexManager(IndexMode.SEQUENTIAL)
        manager_null = IndexManager(None)
        
        assert manager_none.should_include_index() is False
        assert manager_local.should_include_index() is True
        assert manager_sequential.should_include_index() is True
        assert manager_null.should_include_index() is False
    
    def test_reset_file_tracking(self):
        """Test resetting file tracking state"""
        manager = IndexManager(IndexMode.SEQUENTIAL, start_value=100)
        
        # Process some data
        df = pd.DataFrame({'col1': [1, 2]})
        manager.process_chunk(df, is_new_file=True)
        manager.process_chunk(df, is_new_file=True)
        
        # State should be modified
        assert manager.global_index_position > 100
        assert manager.file_count > 0
        
        # Reset
        manager.reset_file_tracking()
        
        # State should be back to initial
        assert manager.global_index_position == 100
        assert manager.file_count == 0
        assert manager.current_file_position == 100
    
    def test_custom_start_values(self):
        """Test various custom start values"""
        # Start from 1000
        manager1000 = IndexManager(IndexMode.SEQUENTIAL, start_value=1000)
        df = pd.DataFrame({'col1': [1, 2]})
        result = manager1000.process_chunk(df, is_new_file=True)
        assert result['__index__'].tolist() == [1000, 1001]
        
        # Start from 1 (common for non-zero-indexed systems)
        manager1 = IndexManager(IndexMode.LOCAL, start_value=1)
        result = manager1.process_chunk(df, is_new_file=True)
        assert result['__index__'].tolist() == [1, 2]
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrames"""
        manager = IndexManager(IndexMode.SEQUENTIAL)
        
        empty_df = pd.DataFrame({'col1': []})
        result = manager.process_chunk(empty_df, is_new_file=True)
        
        assert len(result) == 0
        assert '__index__' in result.columns
        assert result['__index__'].dtype == 'int64'  # Should still have correct dtype