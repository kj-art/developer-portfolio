"""
Core batch rename processor with ProcessingContext integration.

Handles the main processing pipeline: extraction, conversion, filtering, and template formatting.
"""

import shutil
from pathlib import Path
from typing import List, Dict, Any

from .config import RenameConfig, RenameResult
from .processing_context import ProcessingContext
from .built_ins.extractors import get_extractor
from .built_ins.converters import get_converter
from .built_ins.templates import get_template
from .built_ins.filters import get_filter
from .built_ins.all_in_ones import get_builtin_all_in_one, is_builtin_all_in_one
from .function_loader import load_custom_function


class BatchRenameProcessor:
    """
    Main processor for batch rename operations.
    
    Coordinates extraction, conversion, filtering, and template formatting using ProcessingContext.
    Templates are applied after all converters and are treated separately from converters.
    """
    
    def __init__(self):
        self.results = None
    
    def process(self, config: RenameConfig) -> RenameResult:
        """
        Process files according to the configuration.
        
        Args:
            config: RenameConfig object with all processing settings
            
        Returns:
            RenameResult with operation results and statistics
        """
        # Initialize result tracking
        result = RenameResult(
            files_analyzed=0,
            files_to_rename=0,
            files_renamed=0,
            errors=0,
            collisions=0,
            preview_data=[],
            error_details=[]
        )
        
        try:
            # Get file list
            files = self._get_file_list(config)
            result.files_analyzed = len(files)
            
            if len(files) == 0:
                return result
            
            # Check if using all-in-one function
            if config.extract_and_convert:
                return self._process_with_all_in_one(config, files, result)
            else:
                return self._process_with_pipeline(config, files, result)
                
        except Exception as e:
            result.errors = result.files_analyzed
            result.error_details.append({
                'file': 'SYSTEM',
                'error': str(e)
            })
            return result
    
    def _process_with_all_in_one(self, config: RenameConfig, files: List[Path], result: RenameResult) -> RenameResult:
        """Process files using all-in-one function (extract_and_convert)."""
        
        # Set up all-in-one function
        all_in_one_func = self._get_all_in_one_function(config.extract_and_convert)
        
        # Set up filters
        filters = [get_filter(filt['name'], filt) for filt in config.filters]
        
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
                if not self._should_process_file(context, filters):
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
        
        # Process rename plan
        return self._execute_rename_plan(config, rename_plan, result)
    
    def _process_with_pipeline(self, config: RenameConfig, files: List[Path], result: RenameResult) -> RenameResult:
        """Process files using the extraction -> conversion -> template pipeline."""
        
        # Set up processing functions
        extractor = get_extractor(config.extractor, config.extractor_args)
        converters = [get_converter(conv['name'], conv) for conv in config.converters]
        filters = [get_filter(filt['name'], filt) for filt in config.filters]
        
        # Set up template formatter (separate from converters)
        template_formatter = None
        if config.template:
            template_formatter = get_template(config.template['name'], config.template)
        
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
                if not self._should_process_file(context, filters):
                    continue
                
                # Extract data
                extracted_data = extractor(context)
                
                # Update context with extracted data for converters
                context.extracted_data = extracted_data
                
                # Apply converters (but not templates)
                converted_data = extracted_data.copy()
                for i, converter in enumerate(converters):
                    try:
                        input_fields = set(converted_data.keys())
                        
                        # Update context for this converter
                        context.extracted_data = converted_data
                        converter_result = converter(context)
                        
                        # Validate field consistency
                        self._validate_converter_fields(
                            input_fields, converter_result, f"converter #{i+1}"
                        )
                        
                        # Update data for next converter
                        converted_data = converter_result
                        
                    except Exception as e:
                        raise ValueError(f"Converter #{i+1} failed: {e}")
                
                # Apply template formatter AFTER all converters (if specified)
                if template_formatter:
                    # Update context with final converter data
                    context.extracted_data = converted_data
                    formatted_filename = template_formatter(context)  # Returns string directly
                    
                    # Generate new filename from template result
                    new_name = self._generate_new_filename(formatted_filename, file_path)
                else:
                    # No template - use converted data directly (should not happen with current validation)
                    # This branch exists for safety but shouldn't be reached
                    new_name = file_path.name
                
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
        
        # Process rename plan
        return self._execute_rename_plan(config, rename_plan, result)
    
    def _get_all_in_one_function(self, extract_and_convert_spec: str):
        """Get the all-in-one function (built-in or custom)."""
        
        # Check if it's a built-in function call (e.g., "replace,old,new")
        if ',' in extract_and_convert_spec and not extract_and_convert_spec.endswith('.py'):
            parts = extract_and_convert_spec.split(',')
            function_name = parts[0]
            
            if is_builtin_all_in_one(function_name):
                # Built-in all-in-one function
                function_args = {
                    'positional': parts[1:],
                    'keyword': {}
                }
                return get_builtin_all_in_one(function_name, function_args)
            else:
                raise ValueError(f"Unknown built-in all-in-one function: {function_name}")
        
        elif extract_and_convert_spec.endswith('.py'):
            # Custom .py file - assume function is named "rename_all"
            custom_func = load_custom_function(extract_and_convert_spec, "rename_all")
            
            def custom_all_in_one(context: ProcessingContext) -> str:
                # Call with legacy signature for compatibility
                return custom_func(context.filename, context.file_path, context.metadata)
            
            return custom_all_in_one
        else:
            raise ValueError(f"Invalid extract_and_convert specification: {extract_and_convert_spec}")
    
    def _generate_new_filename(self, new_base_name: str, original_path: Path) -> str:
        """Generate new filename preserving extension."""
        if new_base_name.endswith(original_path.suffix):
            return new_base_name
        else:
            return new_base_name + original_path.suffix
    
    def _execute_rename_plan(self, config: RenameConfig, rename_plan: List[Dict], result: RenameResult) -> RenameResult:
        """Execute the rename plan and update results."""
        
        # Filter to only include actual changes
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
    
    def _should_process_file(self, context: ProcessingContext, filters: List) -> bool:
        """Check if file should be processed based on filters."""
        for filter_func in filters:
            if not filter_func(context):
                return False
        return True
    
    def _validate_converter_fields(self, input_fields: set, output_data: Dict[str, Any], converter_name: str):
        """Validate that converter preserves field structure."""
        output_fields = set(output_data.keys())
        
        if input_fields != output_fields:
            missing = input_fields - output_fields
            extra = output_fields - input_fields
            
            errors = []
            if missing:
                errors.append(f"removed fields: {list(missing)}")
            if extra:
                errors.append(f"added fields: {list(extra)}")
            
            raise ValueError(f"{converter_name} changed field structure - {', '.join(errors)}")