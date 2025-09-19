"""
Core batch rename processor with ProcessingContext integration.

Handles the main processing pipeline: extraction, conversion, filtering, and template formatting.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from .config import RenameConfig, RenameResult
from .processing_context import ProcessingContext
from .extractors import get_extractor
from .converters import get_converter
from .templates import get_template
from .filters import get_filter


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
                        new_name = self._generate_new_filename_from_template(formatted_filename, file_path)
                    else:
                        # No template - generate filename from converter data
                        new_name = self._generate_new_filename_from_data(converted_data, file_path)
                    
                    if new_name != file_path.name:
                        rename_plan.append({
                            'old_path': file_path,
                            'new_name': new_name,
                            'old_name': file_path.name,
                            'context': context,
                            'converted_data': converted_data
                        })
                    
                except Exception as e:
                    result.errors += 1
                    result.error_details.append({
                        'file': str(file_path),
                        'error': str(e)
                    })
            
            # Check for naming conflicts
            result.collisions = self._check_collisions(rename_plan)
            result.files_to_rename = len(rename_plan)
            
            # Prepare preview data
            result.preview_data = [
                {
                    'old_name': item['old_name'],
                    'new_name': item['new_name']
                }
                for item in rename_plan
            ]
            
            # Execute renames if not in preview mode
            if not config.preview_mode:
                result.files_renamed = self._execute_renames(rename_plan, result)
            
            return result
            
        except Exception as e:
            result.error_details.append({
                'file': 'GENERAL',
                'error': f"Processing failed: {str(e)}"
            })
            result.errors += 1
            return result
    
    def _get_file_list(self, config: RenameConfig) -> List[Path]:
        """Get list of files to process based on config."""
        files = []
        
        if config.recursive:
            # Recursive file discovery
            for root, dirs, filenames in os.walk(config.input_folder):
                for filename in filenames:
                    file_path = Path(root) / filename
                    if file_path.is_file():
                        files.append(file_path)
        else:
            # Non-recursive file discovery
            for item in config.input_folder.iterdir():
                if item.is_file():
                    files.append(item)
        
        return sorted(files)
    
    def _get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get file metadata for processing context."""
        try:
            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'extension': file_path.suffix
            }
        except OSError:
            return {
                'size': 0,
                'created': 0,
                'modified': 0,
                'extension': file_path.suffix
            }
    
    def _should_process_file(self, context: ProcessingContext, filters: List) -> bool:
        """Check if file should be processed based on filters."""
        if not filters:
            return True
    
    def _validate_converter_fields(self, input_fields: set, output_data: Dict[str, Any], converter_name: str):
        """Validate that converter preserved field structure properly."""
        if not isinstance(output_data, dict):
            raise ValueError(f"{converter_name} must return a dictionary, got {type(output_data).__name__}")
        
        output_fields = set(output_data.keys())
        
        # Check for missing fields (fields that were removed)
        missing_fields = input_fields - output_fields
        if missing_fields:
            available_fields = list(output_fields)
            raise ValueError(
                f"{converter_name} removed fields: {missing_fields}. "
                f"Available fields after conversion: {available_fields}. "
                f"Hint: Converters should preserve all fields using 'result = context.extracted_data.copy()'"
            )
        
        # Allow new fields but warn if it looks suspicious
        new_fields = output_fields - input_fields
        if len(new_fields) > 0:
            # This might be OK (derived fields) but could indicate problems
            # For now, just log it - don't error
            pass
    
    def _generate_new_filename_from_template(self, formatted_filename: str, original_path: Path) -> str:
        """Generate new filename from template result (string)."""
        # Template returns just the filename without extension
        # Add the original extension if not already present
        if not formatted_filename.endswith(original_path.suffix) and original_path.suffix:
            return formatted_filename + original_path.suffix
        return formatted_filename
    
    def _generate_new_filename_from_data(self, data: Dict[str, Any], original_path: Path) -> str:
        """Generate new filename from converter data (fallback when no template)."""
        # Look for formatted_name in data (legacy converter support)
        if 'formatted_name' in data:
            new_name = str(data['formatted_name'])
            if not new_name.endswith(original_path.suffix) and original_path.suffix:
                new_name += original_path.suffix
            return new_name
        
        # Fallback: use original filename
        return original_path.name
        
        # All filters must pass (AND logic)
        for filter_func in filters:
            try:
                if not filter_func(context):
                    return False
            except Exception:
                # If filter fails, exclude file
                return False
        
        return True
    
    def _generate_new_filename(self, data: Dict[str, Any], original_path: Path) -> str:
        """Generate new filename from processed data."""
        # If template was used and returned formatted_name, use it
        if 'formatted_name' in data:
            new_name = str(data['formatted_name'])
            # Preserve extension if not included
            if not new_name.endswith(original_path.suffix) and original_path.suffix:
                new_name += original_path.suffix
            return new_name
        
        # Fallback: use original filename
        return original_path.name
    
    def _check_collisions(self, rename_plan: List[Dict]) -> int:
        """Check for naming collisions in rename plan."""
        collisions = 0
        new_names = {}
        
        for item in rename_plan:
            new_name = item['new_name']
            if new_name in new_names:
                collisions += 1
            else:
                new_names[new_name] = item
        
        return collisions
    
    def _execute_renames(self, rename_plan: List[Dict], result: RenameResult) -> int:
        """Execute the actual file renames."""
        renamed_count = 0
        
        for item in rename_plan:
            try:
                old_path = item['old_path']
                new_path = old_path.parent / item['new_name']
                
                # Check if target already exists
                if new_path.exists() and new_path != old_path:
                    result.error_details.append({
                        'file': str(old_path),
                        'error': f"Target file already exists: {new_path}"
                    })
                    result.errors += 1
                    continue
                
                # Perform rename
                old_path.rename(new_path)
                renamed_count += 1
                
            except Exception as e:
                result.error_details.append({
                    'file': str(item['old_path']),
                    'error': f"Rename failed: {str(e)}"
                })
                result.errors += 1
        
        return renamed_count