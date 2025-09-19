"""
Example Custom Template Functions for Batch Rename Tool

Template functions take a ProcessingContext and return a dictionary with 'formatted_name' 
for the final filename generation. They are applied AFTER all converters.

Template functions should return: {'formatted_name': 'new_filename_without_extension'}
"""

from pathlib import Path
from typing import Dict, Any
import re
import datetime

# Import ProcessingContext - adjust path as needed
try:
    from batch_rename.core.processing_context import ProcessingContext
except ImportError:
    # If running standalone, define a minimal version
    from dataclasses import dataclass
    
    @dataclass
    class ProcessingContext:
        filename: str
        file_path: Path
        metadata: Dict[str, Any]
        extracted_data: Dict[str, Any] = None


def format_business_filename(context: ProcessingContext) -> str:
    """
    Professional business document formatter.
    
    Creates clean, standardized business filenames with department codes,
    document types, and date formatting.
    
    Expected extracted data: dept, type, date
    Returns: Formatted filename string (without extension)
    """
    if not context.has_extracted_data():
        return context.file_path.stem
    
    data = context.extracted_data
    
    # Standardize department codes
    dept_map = {
        'hr': 'HR', 'human resources': 'HR',
        'it': 'IT', 'tech': 'IT', 'technology': 'IT',
        'fin': 'Finance', 'finance': 'Finance', 'accounting': 'Finance',
        'sales': 'Sales', 'marketing': 'Marketing', 'mkt': 'Marketing',
        'ops': 'Operations', 'operations': 'Operations'
    }
    
    dept = data.get('dept', 'Unknown').lower()
    clean_dept = dept_map.get(dept, dept.title())
    
    # Standardize document types
    type_map = {
        'rpt': 'Report', 'report': 'Report',
        'doc': 'Document', 'document': 'Document',
        'pres': 'Presentation', 'presentation': 'Presentation',
        'memo': 'Memo', 'memorandum': 'Memo'
    }
    
    doc_type = data.get('type', 'Document').lower()
    clean_type = type_map.get(doc_type, doc_type.title())
    
    # Format date if present
    date_str = data.get('date', '')
    if date_str:
        # Try to parse and reformat date
        try:
            if len(date_str) == 8 and date_str.isdigit():  # YYYYMMDD
                date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')
                formatted_date = date_obj.strftime('%Y-%m-%d')
            else:
                formatted_date = date_str
        except:
            formatted_date = date_str
    else:
        formatted_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Build filename components
    components = []
    if clean_dept != 'Unknown':
        components.append(clean_dept)
    components.append(clean_type)
    components.append(formatted_date)
    
    formatted_name = '_'.join(components)
    return formatted_name


def format_project_filename(context: ProcessingContext, 
                          project_prefix: str = '', 
                          include_version: bool = True) -> str:
    """
    Project-based filename formatter with optional parameters.
    
    Creates project-structured filenames with version control and status indicators.
    
    Args:
        project_prefix: Optional prefix to add to all filenames
        include_version: Whether to include version numbers in filename
    
    Expected extracted data: project, version, status, date
    Returns: Formatted filename string (without extension)
    """
    if not context.has_extracted_data():
        return context.file_path.stem
    
    data = context.extracted_data
    
    components = []
    
    # Add project prefix if specified
    if project_prefix:
        components.append(project_prefix)
    
    # Project name
    project = data.get('project', 'Project').replace(' ', '-')
    components.append(project)
    
    # Version (if enabled and present)
    if include_version:
        version = data.get('version', '')
        if version:
            if not version.startswith('v'):
                version = f"v{version}"
            components.append(version)
    
    # Status indicator
    status = data.get('status', '').lower()
    if status in ['draft', 'review', 'final', 'archive']:
        components.append(status.title())
    
    # Date
    date_str = data.get('date', '')
    if date_str:
        # Clean up date format
        clean_date = re.sub(r'[^\d]', '', date_str)  # Remove non-digits
        if len(clean_date) >= 6:  # At least YYMMDD
            components.append(clean_date[:8])  # Take first 8 digits
    
    formatted_name = '_'.join(components)
    return formatted_name


def format_creative_filename(context: ProcessingContext) -> str:
    """
    Creative/media filename formatter.
    
    Handles creative project files with artist, medium, dimension info.
    
    Expected extracted data: artist, medium, dimensions, date
    Returns: Formatted filename string (without extension)
    """
    if not context.has_extracted_data():
        return context.file_path.stem
    
    data = context.extracted_data
    
    # Artist name (clean for filename)
    artist = data.get('artist', 'Unknown')
    clean_artist = re.sub(r'[^\w\s-]', '', artist).replace(' ', '_')
    
    # Medium/type
    medium = data.get('medium', data.get('type', 'artwork'))
    clean_medium = medium.replace(' ', '_').lower()
    
    # Dimensions (if present)
    dimensions = data.get('dimensions', '')
    if dimensions:
        # Clean dimensions format: 1920x1080 or 24x36in
        clean_dims = re.sub(r'[^\dx]', '', dimensions.lower())
        if clean_dims:
            dimensions = clean_dims
    
    # Build filename
    components = [clean_artist, clean_medium]
    
    if dimensions:
        components.append(dimensions)
    
    # Date
    date_str = data.get('date', '')
    if date_str:
        components.append(date_str)
    
    formatted_name = '_'.join(components)
    return formatted_name


def format_with_sequence(context: ProcessingContext, 
                        pattern: str = "{base}_{seq:03d}") -> str:
    """
    Sequential filename formatter with customizable pattern.
    
    Adds sequence numbers to filenames to avoid collisions.
    Note: This is a simple example - real sequential numbering would need
    to track numbers across the entire batch operation.
    
    Args:
        pattern: Format string for filename. Use {base} for base name, {seq} for sequence
    
    Returns: Formatted filename string (without extension)
    """
    if not context.has_extracted_data():
        base_name = context.file_path.stem
    else:
        # Use first non-None field as base name
        data = context.extracted_data
        base_name = None
        for key, value in data.items():
            if value and value != 'unknown':
                base_name = str(value)
                break
        
        if not base_name:
            base_name = context.file_path.stem
    
    # Clean base name for filename safety
    clean_base = re.sub(r'[^\w\s-]', '', base_name).replace(' ', '_')
    
    # For demo purposes, use a simple hash-based sequence
    # In real implementation, this would track across all files
    import hashlib
    file_hash = hashlib.md5(context.filename.encode()).hexdigest()
    sequence_num = int(file_hash[:4], 16) % 1000  # Simple pseudo-sequence
    
    try:
        formatted_name = pattern.format(base=clean_base, seq=sequence_num)
    except KeyError as e:
        # Fallback if pattern is invalid
        formatted_name = f"{clean_base}_{sequence_num:03d}"
    
    return formatted_name