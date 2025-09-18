"""
Example Custom Extractors for Batch Rename Tool

These extractors demonstrate different approaches to parsing filenames
and extracting structured data for renaming operations.

Updated to use ProcessingContext data class.
"""

from pathlib import Path
from typing import Dict, Any
import re
import datetime
import sys

# Add the processing context to path if running as standalone
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


def extract_data(context: ProcessingContext) -> Dict[str, str]:
    """
    Simple business document extractor.
    
    Extracts department, document type, and date from business filenames.
    Example: "HR_PolicyDocument_20240315.pdf" → {dept: "HR", type: "PolicyDocument", date: "20240315"}
    """
    base_name = context.base_name
    
    # Split on underscores and extract known positions
    parts = base_name.split('_')
    
    result = {}
    if len(parts) >= 3:
        result['dept'] = parts[0]
        result['type'] = parts[1] 
        result['date'] = parts[2]
    elif len(parts) == 2:
        result['dept'] = parts[0]
        result['type'] = parts[1]
        result['date'] = 'unknown'
    else:
        result['dept'] = 'misc'
        result['type'] = base_name
        result['date'] = 'unknown'
    
    return result


def extract_invoice_data(context: ProcessingContext) -> Dict[str, str]:
    """
    Invoice filename extractor.
    
    Handles various invoice naming patterns:
    - "Invoice_12345_CompanyName_2024-03-15.pdf"
    - "INV-12345-CompanyName.pdf" 
    - "12345_Invoice_CompanyName.pdf"
    """
    base_name = context.base_name
    result = {}
    
    # Pattern 1: Invoice_12345_CompanyName_2024-03-15
    pattern1 = r'Invoice[_-](\d+)[_-]([^_-]+)(?:[_-](\d{4}-\d{2}-\d{2}))?'
    match = re.search(pattern1, base_name, re.IGNORECASE)
    if match:
        result['type'] = 'Invoice'
        result['number'] = match.group(1)
        result['company'] = match.group(2)
        result['date'] = match.group(3) or 'unknown'
        return result
    
    # Pattern 2: INV-12345-CompanyName
    pattern2 = r'INV[_-](\d+)[_-]([^_-]+)'
    match = re.search(pattern2, base_name, re.IGNORECASE)
    if match:
        result['type'] = 'Invoice'
        result['number'] = match.group(1)
        result['company'] = match.group(2)
        result['date'] = 'unknown'
        return result
    
    # Pattern 3: 12345_Invoice_CompanyName
    pattern3 = r'(\d+)[_-]Invoice[_-]([^_-]+)'
    match = re.search(pattern3, base_name, re.IGNORECASE)
    if match:
        result['type'] = 'Invoice'
        result['number'] = match.group(1)
        result['company'] = match.group(2)
        result['date'] = 'unknown'
        return result
    
    # Fallback
    result['type'] = 'Document'
    result['number'] = 'unknown'
    result['company'] = 'unknown'
    result['date'] = 'unknown'
    
    return result


def extract_photo_data(context: ProcessingContext) -> Dict[str, str]:
    """
    Photo filename and metadata extractor.
    
    Combines filename parsing with file metadata to extract photo information.
    Handles phone camera names, timestamps, and location info.
    """
    base_name = context.base_name
    result = {}
    
    # Try to extract date from filename first
    # Pattern: IMG_20240315_123456, DSC_20240315_123456, etc.
    date_pattern = r'(\d{8})'
    date_match = re.search(date_pattern, base_name)
    
    if date_match:
        result['date'] = date_match.group(1)
    else:
        # Fall back to file creation date
        created_date = datetime.datetime.fromtimestamp(context.created_timestamp)
        result['date'] = created_date.strftime('%Y%m%d')
    
    # Detect camera/device type from filename patterns
    if re.match(r'IMG_\d+', base_name, re.IGNORECASE):
        result['device'] = 'phone'
        result['type'] = 'photo'
    elif re.match(r'DSC_\d+', base_name, re.IGNORECASE):
        result['device'] = 'camera'
        result['type'] = 'photo'
    elif re.match(r'VID_\d+', base_name, re.IGNORECASE):
        result['device'] = 'phone'
        result['type'] = 'video'
    elif any(ext in context.extension.lower() for ext in ['.jpg', '.jpeg', '.png', '.heic']):
        result['device'] = 'unknown'
        result['type'] = 'photo'
    elif any(ext in context.extension.lower() for ext in ['.mp4', '.mov', '.avi']):
        result['device'] = 'unknown'
        result['type'] = 'video'
    else:
        result['device'] = 'unknown'
        result['type'] = 'media'
    
    # Extract time if present
    time_pattern = r'(\d{6})'
    time_match = re.search(time_pattern, base_name.replace(result.get('date', ''), ''))
    if time_match:
        result['time'] = time_match.group(1)
    else:
        result['time'] = 'unknown'
    
    # File size category
    size_mb = context.file_size / (1024 * 1024)
    if size_mb < 1:
        result['size_cat'] = 'small'
    elif size_mb < 10:
        result['size_cat'] = 'medium'
    else:
        result['size_cat'] = 'large'
    
    return result


def extract_project_data(context: ProcessingContext, project_prefix: str = "PROJ", 
                        version_required: bool = True) -> Dict[str, str]:
    """
    Project file extractor with parameters.
    
    Extracts project code, version, and file type from project filenames.
    Supports custom project prefixes and optional version enforcement.
    
    Example: "PROJ-2024-001_Requirements_v2.1.docx" → 
             {project: "2024-001", type: "Requirements", version: "2.1"}
    """
    base_name = context.base_name
    result = {}
    
    # Build pattern based on project prefix
    pattern = rf'{re.escape(project_prefix)}[_-]([^_-]+)[_-]([^_-]+)(?:[_-]v?(\d+(?:\.\d+)?))?' 
    match = re.search(pattern, base_name, re.IGNORECASE)
    
    if match:
        result['project'] = match.group(1)
        result['type'] = match.group(2)
        version = match.group(3)
        
        if version:
            result['version'] = version
        elif version_required:
            result['version'] = '1.0'  # Default version
        else:
            result['version'] = 'none'
    else:
        # Fallback parsing without prefix
        parts = base_name.split('_')
        if len(parts) >= 2:
            result['project'] = parts[0]
            result['type'] = parts[1]
            
            # Look for version in remaining parts
            version_found = False
            for part in parts[2:]:
                version_match = re.search(r'v?(\d+(?:\.\d+)?)', part, re.IGNORECASE)
                if version_match:
                    result['version'] = version_match.group(1)
                    version_found = True
                    break
            
            if not version_found:
                result['version'] = '1.0' if version_required else 'none'
        else:
            result['project'] = 'unknown'
            result['type'] = base_name
            result['version'] = '1.0' if version_required else 'none'
    
    # Add file category based on extension
    ext = context.extension.lower()
    if ext in ['.doc', '.docx', '.txt', '.md']:
        result['category'] = 'document'
    elif ext in ['.xls', '.xlsx', '.csv']:
        result['category'] = 'spreadsheet'
    elif ext in ['.ppt', '.pptx']:
        result['category'] = 'presentation'
    elif ext in ['.pdf']:
        result['category'] = 'pdf'
    elif ext in ['.jpg', '.png', '.gif', '.svg']:
        result['category'] = 'image'
    else:
        result['category'] = 'other'
    
    return result