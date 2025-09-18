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
    
    Returns:
        Dictionary with extracted fields: dept, type, date
    """
    base_name = context.file_path.stem
    
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
    
    Returns:
        Dictionary with extracted fields: type, number, company, date
    """
    base_name = context.file_path.stem
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


def extract_photo_data(context: ProcessingContext, include_location: bool = False, 
                      extract_device: bool = True) -> Dict[str, str]:
    """
    Photo filename and metadata extractor.
    
    Combines filename parsing with file metadata to extract photo information.
    Handles phone camera names, timestamps, and location info.
    
    Args:
        include_location: Whether to attempt location extraction from EXIF data
        extract_device: Whether to extract device/camera model from metadata
    
    Returns:
        Dictionary with extracted photo fields: date, time, device, location, etc.
    """
    base_name = context.file_path.stem
    result = {}
    
    # Try to extract date from filename first
    # Pattern: IMG_20240315_123456, DSC_20240315_123456, etc.
    date_pattern = r'(\d{8})'
    time_pattern = r'(\d{6})'
    
    date_match = re.search(date_pattern, base_name)
    time_match = re.search(time_pattern, base_name)
    
    if date_match:
        date_str = date_match.group(1)
        try:
            parsed_date = datetime.datetime.strptime(date_str, '%Y%m%d')
            result['date'] = parsed_date.strftime('%Y-%m-%d')
            result['year'] = parsed_date.strftime('%Y')
            result['month'] = parsed_date.strftime('%m')
            result['day'] = parsed_date.strftime('%d')
        except ValueError:
            result['date'] = 'unknown'
    else:
        # Try to get from file metadata
        try:
            file_stat = context.file_path.stat()
            mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
            result['date'] = mod_time.strftime('%Y-%m-%d')
            result['year'] = mod_time.strftime('%Y')
            result['month'] = mod_time.strftime('%m')
            result['day'] = mod_time.strftime('%d')
        except:
            result['date'] = 'unknown'
    
    if time_match:
        time_str = time_match.group(1)
        try:
            parsed_time = datetime.datetime.strptime(time_str, '%H%M%S')
            result['time'] = parsed_time.strftime('%H-%M-%S')
            result['hour'] = parsed_time.strftime('%H')
        except ValueError:
            result['time'] = 'unknown'
    else:
        result['time'] = 'unknown'
    
    # Extract camera/device info from filename
    if extract_device:
        device_patterns = [
            r'^(IMG|DSC|DCIM|P\d+)_',  # Camera prefixes
            r'(iPhone|Samsung|Pixel|Canon|Nikon|Sony)',  # Device names
        ]
        
        for pattern in device_patterns:
            match = re.search(pattern, base_name, re.IGNORECASE)
            if match:
                result['device'] = match.group(1)
                break
        else:
            result['device'] = 'unknown'
    
    # Location extraction placeholder
    if include_location:
        # In a real implementation, this would read EXIF GPS data
        result['location'] = 'unknown'
        result['city'] = 'unknown'
        result['country'] = 'unknown'
    
    # Determine photo type
    if 'IMG' in base_name.upper():
        result['type'] = 'Photo'
    elif 'VID' in base_name.upper():
        result['type'] = 'Video'
    elif 'SCR' in base_name.upper() or 'Screenshot' in base_name:
        result['type'] = 'Screenshot'
    else:
        result['type'] = 'Media'
    
    return result


def extract_project_data(context: ProcessingContext, client_list: str = "",
                        extract_version: bool = True) -> Dict[str, str]:
    """
    Project file extractor for creative work.
    
    Extracts client, project name, version, and date from project filenames.
    Handles various creative industry naming conventions.
    
    Args:
        client_list: Comma-separated list of known client names to match against
        extract_version: Whether to extract version numbers from filenames
    
    Returns:
        Dictionary with extracted project fields: client, project, version, date, status
    """
    base_name = context.file_path.stem
    result = {}
    
    # Parse client list if provided
    known_clients = []
    if client_list:
        known_clients = [c.strip() for c in client_list.split(',')]
    
    # Try to identify client from known list
    result['client'] = 'unknown'
    for client in known_clients:
        if client.lower() in base_name.lower():
            result['client'] = client
            break
    
    # Extract version information
    if extract_version:
        version_patterns = [
            r'[vV](\d+)\.(\d+)',  # v1.2, V1.2
            r'[vV](\d+)',         # v1, V1
            r'_(\d+)\.(\d+)_',    # _1.2_
            r'_(\d+)_',           # _1_
            r'rev(\d+)',          # rev1, rev2
            r'r(\d+)',            # r1, r2
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, base_name)
            if match:
                if len(match.groups()) == 2:
                    result['version'] = f"{match.group(1)}.{match.group(2)}"
                else:
                    result['version'] = match.group(1)
                break
        else:
            result['version'] = 'unknown'
    
    # Extract status indicators
    status_keywords = {
        'draft': ['draft', 'wip', 'work'],
        'review': ['review', 'rev', 'check'],
        'final': ['final', 'approved', 'delivery'],
        'archive': ['old', 'archive', 'backup']
    }
    
    result['status'] = 'unknown'
    for status, keywords in status_keywords.items():
        if any(keyword in base_name.lower() for keyword in keywords):
            result['status'] = status
            break
    
    # Extract date
    date_patterns = [
        r'(\d{4}[-_]\d{2}[-_]\d{2})',  # YYYY-MM-DD or YYYY_MM_DD
        r'(\d{8})',                    # YYYYMMDD
        r'(\d{2}[-_]\d{2}[-_]\d{4})',  # MM-DD-YYYY or MM_DD_YYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, base_name)
        if match:
            result['date'] = match.group(1)
            break
    else:
        result['date'] = 'unknown'
    
    # Extract project name (everything else)
    # Remove client, version, status, and date to get core project name
    project_name = base_name
    for remove_item in [result.get('client', ''), result.get('version', ''), 
                       result.get('status', ''), result.get('date', '')]:
        if remove_item and remove_item != 'unknown':
            project_name = project_name.replace(remove_item, '')
    
    # Clean up project name
    project_name = re.sub(r'[_\-\.]+', '_', project_name)
    project_name = project_name.strip('_-.')
    result['project'] = project_name if project_name else 'unknown'
    
    return result