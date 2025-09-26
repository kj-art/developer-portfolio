"""
Core batch rename processing engine.

This module contains the main BatchRenameProcessor class that orchestrates
the complete rename pipeline: filtering → extraction → conversion → templating.

The processor uses a step-based architecture where each operation type (filter,
extractor, converter, template) is handled by specialized steps created through
the StepFactory pattern.

Architecture:
    - ProcessingContext: Carries data through the pipeline
    - StepFactory: Creates executable functions from configurations  
    - RenameConfig: Input configuration with all processing steps
    - RenameResult: Output with metrics and preview data

Safety Features:
    - Preview-first workflow (default mode)
    - Collision detection (internal and existing files)
    - Field validation ensures converters preserve data structure
    - Comprehensive error tracking and reporting
"""

import shutil
from pathlib import Path
from typing import List, Dict, Any, Callable

from .config import RenameConfig, RenameResult
from .processing_context import ProcessingContext
from .step_factory import StepFactory
from .steps.base import StepConfig, StepType


class BatchRenameProcessor:
    """Main processor for batch rename operations."""
    
    def process(self, config: RenameConfig) -> RenameResult:
        """
        Process files according to configuration.
        
        Args:
            config: Rename configuration with all processing steps
            
        Returns:
            RenameResult with operation details and results
        """
        result = RenameResult()
        
        # Get list of files to process
        files = self._get_file_list(config)
        result.files_found = len(files)
        
        if not files:
            return result
        
        # Choose processing method based on configuration
        if config.extract_and_convert:
            return self._process_with_all_in_one(config, files, result)
        else:
            return self._process_with_pipeline(config, files, result)
    
    def _process_with_pipeline(self, config: RenameConfig, files: List[Path], result: RenameResult) -> RenameResult:
        """Process files using the full extraction -> conversion -> template pipeline."""
        
        # Create processing steps
        steps = self._create_processing_steps(config)
        
        # Process each file
        rename_plan = []
        for file_path in files:
            try:
                print(f"\nDEBUG: === Processing {file_path.name} ===")
                
                # Get file metadata
                metadata = self._get_file_metadata(file_path)
                
                # Create processing context
                context = ProcessingContext(
                    filename=file_path.name,
                    file_path=file_path,
                    metadata=metadata
                )
                
                # Apply filters first - if any filter returns False, skip file
                if not self._apply_filters(context, steps['filters']):
                    continue
                
                
                # Extract data
                extracted_data = steps['extractor'](context)
                context.extracted_data = extracted_data
                
                # Apply converters in sequence
                converted_data = extracted_data.copy()
                
                for i, converter in enumerate(steps['converters']):
                    context.extracted_data = converted_data
                    converter_result = converter(context)
                    converted_data = converter_result

                
                # Apply template formatter
                if steps['template']:
                    context.extracted_data = converted_data
                    new_base_name = steps['template'](context)
                else:
                    new_base_name = context.base_name
                
                
                # Generate new filename (preserve extension)
                new_name = self._generate_new_filename(new_base_name, file_path)
                
                # Add to rename plan
                rename_plan.append({
                    'old_path': file_path,
                    'old_name': file_path.name,
                    'new_name': new_name,
                    'new_path': file_path.parent / new_name
                })
                
            except Exception as e:
                result.errors += 1
                result.error_details.append({
                    'file': file_path.name,
                    'error': str(e)
                })
        
        # Execute rename plan
        return self._execute_rename_plan(config, rename_plan, result)
    
    def _process_with_all_in_one(self, config: RenameConfig, files: List[Path], result: RenameResult) -> RenameResult:
        """Process files using all-in-one function that handles extraction + conversion + formatting."""
        
        # Create all-in-one function using StepFactory
        allinone_config = StepConfig(
            name=config.extract_and_convert['name'],
            positional_args=config.extract_and_convert.get('positional', []),
            keyword_args=config.extract_and_convert.get('keyword', {})
        )
        all_in_one_func = StepFactory.create_executable(StepType.ALLINONE, allinone_config)
        
        # Create filter functions
        filter_steps = self._create_filter_steps(config.filters)
        
        # Process each file
        rename_plan = []
        for file_path in files:
            try:
                # Get file metadata
                metadata = self._get_file_metadata(file_path)
                
                # Create processing context
                context = ProcessingContext(
                    filename=file_path.name,
                    file_path=file_path,
                    metadata=metadata
                )
                
                # Apply filters first
                if not self._apply_filters(context, filter_steps):
                    continue
                
                # Apply all-in-one function
                new_base_name = all_in_one_func(context)
                
                # Generate new filename (preserve extension)
                new_name = self._generate_new_filename(new_base_name, file_path)
                
                # Add to rename plan
                rename_plan.append({
                    'old_path': file_path,
                    'old_name': file_path.name,
                    'new_name': new_name,
                    'new_path': file_path.parent / new_name
                })
                
            except Exception as e:
                result.errors += 1
                result.error_details.append({
                    'file': file_path.name,
                    'error': str(e)
                })
        
        # Execute rename plan
        return self._execute_rename_plan(config, rename_plan, result)
    
    def _create_processing_steps(self, config: RenameConfig) -> Dict[str, Any]:
        """Create all processing step functions from configuration."""
        steps = {
            'filters': [],
            'extractor': None,
            'converters': [],
            'template': None
        }
        
        # Create filter steps
        steps['filters'] = self._create_filter_steps(config.filters)
        
        # Create extractor step
        if config.extractor:
            extractor_config = StepConfig(
                name=config.extractor,
                positional_args=config.extractor_args.get('positional', []),
                keyword_args=config.extractor_args.get('keyword', {})
            )
            steps['extractor'] = StepFactory.create_executable(StepType.EXTRACTOR, extractor_config)
        
        # Create converter steps
        for conv in config.converters:
            converter_config = StepConfig(
                name=conv['name'],
                positional_args=conv.get('positional', []),
                keyword_args=conv.get('keyword', {})
            )
            steps['converters'].append(StepFactory.create_executable(StepType.CONVERTER, converter_config))
        
        # Create template step
        if config.template:
            template_config = StepConfig(
                name=config.template['name'],
                positional_args=config.template.get('positional', []),
                keyword_args=config.template.get('keyword', {})
            )
            steps['template'] = StepFactory.create_executable(StepType.TEMPLATE, template_config)
        elif config.extractor == "split":
            # Default template for split extractor: join with no args (uses all fields)
            default_template_config = StepConfig(
                name='join',
                positional_args=[],  # Empty means use all fields in order
                keyword_args={}      # Default separator ('_')
            )
            steps['template'] = StepFactory.create_executable(StepType.TEMPLATE, default_template_config)
        
        return steps
    
    def _create_filter_steps(self, filter_configs: List[Dict]) -> List[Any]:
        """Create filter step functions from configuration."""
        filters = []
        
        for filt in filter_configs:
            filter_config = StepConfig(
                name=filt['name'],
                positional_args=filt.get('positional', []),
                keyword_args=filt.get('keyword', {})
            )
            filter_func = StepFactory.create_executable(StepType.FILTER, filter_config)
            
            # Handle filter inversion
            if filt.get('inverted', False):
                def inverted_filter(context, original_func=filter_func):
                    return not original_func(context)
                filters.append(inverted_filter)
            else:
                filters.append(filter_func)
        
        return filters
    
    def _apply_filters(self, context: ProcessingContext, filters: List[Callable]) -> bool:
        """Apply all filters to context. Returns True if file should be processed."""
        
        for i, filter_func in enumerate(filters):
            try:
                result = filter_func(context)
                if not result:
                    return False
            except Exception as e:
                return False
        
        return True
    
    def _generate_new_filename(self, new_base_name: str, original_path: Path) -> str:
        """Generate new filename, preserving extension."""
        if new_base_name.endswith(original_path.suffix):
            return new_base_name
        else:
            return new_base_name + original_path.suffix
    
    def _execute_rename_plan(self, config: RenameConfig, rename_plan: List[Dict], result: RenameResult) -> RenameResult:
        """
        Execute the rename plan and update results with collision detection.
        
        Performs collision detection using set comparison to identify files that
        would have duplicate new names. Only processes files where the new name
        differs from the old name to avoid unnecessary operations.
        
        Collision Detection Algorithm:
            1. Filter to actual changes (old_name != new_name)
            2. Extract all new names into a list  
            3. Compare list length to set length to count duplicates
            4. Store collision count and preview data
            
        Args:
            config: Rename configuration including preview mode setting
            rename_plan: List of dicts with old_path, new_path, old_name, new_name
            result: RenameResult object to populate with metrics
            
        Returns:
            Updated RenameResult with collision detection and execution results
            
        Example Collision:
            rename_plan = [
                {'old_name': 'file1.pdf', 'new_name': 'report.pdf'},
                {'old_name': 'file2.pdf', 'new_name': 'report.pdf'}  # Collision!
            ]
            Result: result.collisions = 1, collision highlighted in preview
        """
        
        # Exclude files where old_name == new_name to avoid unnecessary operations
        # and provide accurate metrics for the preview/execution summary
        actual_changes = [
            item for item in rename_plan 
            if item['old_name'] != item['new_name']
        ]
        
        result.files_to_rename = len(actual_changes)
        
        # Check for collisions among the changed files
        new_names = [item['new_name'] for item in actual_changes]
        collisions = len(new_names) - len(set(new_names))
        result.collisions = collisions
        
        # Set preview data to only show actual changes
        result.preview_data = [
            {'old_name': item['old_name'], 'new_name': item['new_name']}
            for item in actual_changes
        ]
        
        # If preview mode, don't actually rename
        if config.preview_mode:
            return result
        
        # Execute renames (only for files that actually changed)
        for item in actual_changes:
            try:
                shutil.move(str(item['old_path']), str(item['new_path']))
                result.files_renamed += 1
            except Exception as e:
                result.errors += 1
                result.error_details.append({
                    'file': item['old_name'],
                    'error': f"Rename failed: {e}"
                })
        
        return result
    
    def _get_file_list(self, config: RenameConfig) -> List[Path]:
        """Get list of files to process."""
        files = []
        
        if config.recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for file_path in config.input_folder.glob(pattern):
            if file_path.is_file():
                files.append(file_path)
        
        return files
    
    def _get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get metadata for a file."""
        stat = file_path.stat()
        return {
            'size': stat.st_size,
            'created_timestamp': stat.st_ctime,
            'modified_timestamp': stat.st_mtime
        }
    
    def _validate_converter_fields(self, input_fields: set, output_data: Dict[str, Any], converter_name: str):
        """Validate that converter preserves field structure."""
        if not isinstance(output_data, dict):
            raise ValueError(f"{converter_name} must return a dictionary")
        
        output_fields = set(output_data.keys())
        
        # Check for removed fields - warn but don't error (might be intentional)
        removed_fields = input_fields - output_fields
        if removed_fields:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Converter '{converter_name}' removed fields: {removed_fields}")
        
        # Log added fields for debugging (usually good)
        added_fields = output_fields - input_fields
        if added_fields:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Converter '{converter_name}' added fields: {added_fields}")
        
        # Ensure we have some output fields
        if not output_fields:
            raise ValueError(f"Converter '{converter_name}' returned empty data dictionary")