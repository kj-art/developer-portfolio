"""
Main processing engine for batch rename operations.

Coordinates file discovery, extraction, conversion, and renaming.
"""

import time
from pathlib import Path
from typing import List, Dict, Any

from .config import RenameConfig, RenameResult
from .extractors import get_extractor
from .converters import get_converter
from .filters import apply_filters
from .function_loader import load_custom_function


class BatchRenameProcessor:
    """Main processor for batch rename operations."""
    
    def __init__(self):
        """Initialize the processor."""
        pass
    
    def process(self, config: RenameConfig) -> RenameResult:
        """
        Process files according to configuration.
        
        Args:
            config: Rename operation configuration
            
        Returns:
            Results of the operation
        """
        start_time = time.time()
        result = RenameResult()
        
        try:
            # Discover files to process
            files = self._discover_files(config)
            result.files_analyzed = len(files)
            
            # Apply filters
            filtered_files = self._apply_filters(files, config)
            result.files_filtered_out = len(files) - len(filtered_files)
            
            # Process each file to generate rename mappings
            rename_mappings = []
            for file_path in filtered_files:
                try:
                    new_name = self._process_single_file(file_path, config)
                    if new_name and new_name != file_path.name:
                        rename_mappings.append((file_path, file_path.parent / new_name))
                except Exception as e:
                    print(f"Warning: Failed to process {file_path}: {e}")
                    result.errors += 1
            
            result.files_to_rename = len(rename_mappings)
            
            # Check for collisions
            collisions = self._detect_collisions(rename_mappings, config.input_folder)
            result.collisions = len(collisions['existing_file_collisions']) + len(collisions['internal_collisions'])
            result.existing_file_collisions = collisions['existing_file_collisions']
            result.internal_collisions = collisions['internal_collisions']
            
            # Store preview data
            result.preview_data = [
                {
                    'old_name': str(old_path.name),
                    'new_name': str(new_path.name),
                    'old_path': str(old_path),
                    'new_path': str(new_path)
                }
                for old_path, new_path in rename_mappings
            ]
            
            # Execute renames if not in preview mode
            if not config.preview_mode:
                result.files_renamed = self._execute_renames(rename_mappings, config)
            
        except Exception as e:
            print(f"Processing error: {e}")
            result.errors += 1
        
        result.processing_time = time.time() - start_time
        return result
    
    def _discover_files(self, config: RenameConfig) -> List[Path]:
        """Discover all files to potentially process."""
        files = []
        
        if config.recursive:
            # Recursively find all files
            for file_path in config.input_folder.rglob('*'):
                if file_path.is_file():
                    files.append(file_path)
        else:
            # Only files in the immediate directory
            for file_path in config.input_folder.iterdir():
                if file_path.is_file():
                    files.append(file_path)
        
        return sorted(files)
    
    def _apply_filters(self, files: List[Path], config: RenameConfig) -> List[Path]:
        """Apply filtering rules to file list."""
        if not config.filters:
            return files
        
        filtered_files = []
        for file_path in files:
            if apply_filters(file_path, config.filters):
                filtered_files.append(file_path)
        
        return filtered_files
    
    def _process_single_file(self, file_path: Path, config: RenameConfig) -> str:
        """
        Process a single file to generate new filename.
        
        Args:
            file_path: Path to file to process
            config: Processing configuration
            
        Returns:
            New filename (just the name, not full path)
        """
        # Gather file metadata
        stat = file_path.stat()
        metadata = {
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'extension': file_path.suffix
        }
        
        # Extract and convert data
        if config.extract_and_convert:
            # Single function handles both
            extract_convert_func = load_custom_function(config.extract_and_convert, 'extract_and_convert')
            data = extract_convert_func(file_path.name, file_path, metadata)
        else:
            # Separate extraction and conversion
            # Extract data
            extractor = get_extractor(config.extractor, config.extractor_args)
            data = extractor(file_path.name, file_path, metadata)
            
            # Apply converters in sequence
            for converter_config in config.converters:
                converter_args = {
                    'positional': converter_config.get('positional', []),
                    'keyword': converter_config.get('keyword', {})
                }
                converter = get_converter(converter_config['name'], converter_args)
                data = converter(data, file_path.name, file_path, metadata)
        
        # Generate final filename
        if 'formatted_name' in data:
            # One of the converters (template/stringsmith) generated the final name
            base_name = data['formatted_name']
        else:
            # Use simple formatting - reconstruct from data fields
            base_name = self._simple_format(data, file_path)
        
        # Ensure we have the extension
        if not base_name.endswith(file_path.suffix):
            base_name += file_path.suffix
            
        return base_name
    
    def _apply_template(self, template: str, data: Dict[str, Any], file_path: Path) -> str:
        """Apply template to generate filename."""
        # Simple Python format string for now
        # TODO: Add StringSmith integration
        try:
            base_name = template.format(**data)
            # Preserve the original extension
            return base_name + file_path.suffix
        except KeyError as e:
            raise ValueError(f"Template references missing field: {e}")
    
    def _simple_format(self, data: Dict[str, Any], file_path: Path) -> str:
        """Simple fallback formatting when no template provided."""
        # Join non-empty values with underscores, preserve extension
        values = [str(v) for v in data.values() if v]
        base_name = '_'.join(values) if values else file_path.stem
        return base_name + file_path.suffix
    
    def _detect_collisions(self, rename_mappings: List[tuple], input_folder: Path) -> Dict[str, List]:
        """Detect naming collisions."""
        collisions = {
            'existing_file_collisions': [],
            'internal_collisions': []
        }
        
        # Get existing files
        existing_files = {f.name for f in input_folder.rglob('*') if f.is_file()}
        
        # Track target names for internal collision detection
        target_names = {}
        
        for old_path, new_path in rename_mappings:
            new_name = new_path.name
            
            # Check collision with existing files
            if new_name in existing_files and new_name != old_path.name:
                collisions['existing_file_collisions'].append({
                    'source': str(old_path),
                    'target': new_name,
                    'existing_file': new_name
                })
            
            # Check internal collisions
            if new_name in target_names:
                collisions['internal_collisions'].append({
                    'sources': [target_names[new_name], str(old_path)],
                    'target': new_name
                })
            else:
                target_names[new_name] = str(old_path)
        
        return collisions
    
    def _execute_renames(self, rename_mappings: List[tuple], config: RenameConfig) -> int:
        """Execute the actual file renames."""
        renamed_count = 0
        
        # TODO: Implement collision handling strategies
        # TODO: Create backup manifest for rollback
        
        for old_path, new_path in rename_mappings:
            try:
                old_path.rename(new_path)
                renamed_count += 1
                print(f"Renamed: {old_path.name} -> {new_path.name}")
            except Exception as e:
                print(f"Failed to rename {old_path.name}: {e}")
        
        return renamed_count