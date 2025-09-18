"""
Example All-in-One Functions for Batch Rename Tool

These functions handle extraction, conversion, and formatting in a single step.
Perfect for testing the all-in-one script mode.

Updated to use ProcessingContext data class.
"""

from pathlib import Path
from typing import Dict, Any
import re
import datetime
import hashlib
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


def process_business_documents(context: ProcessingContext, department_mapping: bool = True, 
                             include_year: bool = False) -> str:
    """
    All-in-one business document processor.
    
    Extracts department, type, and date, then formats into professional filename.
    
    Args:
        department_mapping: Whether to expand department codes to full names (HR -> Human-Resources)
        include_year: Whether to include year prefix in final filename
    
    Returns:
        Formatted filename string ready for renaming
    """
    base_name = context.file_path.stem
    
    # Extract data from filename
    parts = base_name.split('_')
    
    if len(parts) >= 3:
        dept, doc_type, date = parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        dept, doc_type, date = parts[0], parts[1], 'unknown'
    else:
        dept, doc_type, date = 'misc', base_name, 'unknown'
    
    # Apply department mapping
    if department_mapping:
        dept_map = {
            'HR': 'Human-Resources',
            'IT': 'Information-Technology',
            'FIN': 'Finance',
            'LEGAL': 'Legal',
            'OPS': 'Operations',
            'SALES': 'Sales',
            'MKT': 'Marketing'
        }
        dept = dept_map.get(dept.upper(), dept.title())
    
    # Format document type
    type_map = {
        'POLICY': 'Policy',
        'PROCEDURE': 'Procedure',
        'REPORT': 'Report',
        'MEETING': 'Meeting-Notes',
        'CONTRACT': 'Contract',
        'INVOICE': 'Invoice',
        'PROPOSAL': 'Proposal'
    }
    doc_type = type_map.get(doc_type.upper(), doc_type.title())
    
    # Format date
    if date != 'unknown':
        try:
            if len(date) == 8:  # YYYYMMDD
                parsed_date = datetime.datetime.strptime(date, '%Y%m%d')
                date = parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            pass  # Keep original if parsing fails
    
    # Build final filename
    if include_year and date != 'unknown':
        try:
            year = date[:4]
            return f"{year}_{dept}_{doc_type}_{date}"
        except:
            pass
    
    if date != 'unknown':
        return f"{dept}_{doc_type}_{date}"
    else:
        return f"{dept}_{doc_type}"


def process_invoices(context: ProcessingContext, company_prefix: bool = True,
                    number_padding: int = 6) -> str:
    """
    All-in-one invoice processor.
    
    Extracts invoice data and formats into standardized invoice filename.
    
    Args:
        company_prefix: Whether to include company name as prefix
        number_padding: Number of digits to pad invoice numbers to (default 6)
    
    Returns:
        Formatted invoice filename string
    """
    base_name = context.file_path.stem
    
    # Extract invoice data using patterns
    patterns = [
        r'Invoice[_-](\d+)[_-]([^_-]+)(?:[_-](\d{4}-\d{2}-\d{2}))?',
        r'INV[_-](\d+)[_-]([^_-]+)',
        r'(\d+)[_-]Invoice[_-]([^_-]+)'
    ]
    
    number, company, date = 'unknown', 'unknown', 'unknown'
    
    for pattern in patterns:
        match = re.search(pattern, base_name, re.IGNORECASE)
        if match:
            if len(match.groups()) == 3:
                number, company, date = match.groups()
                date = date or 'unknown'
            else:
                number, company = match.groups()
            break
    
    # Clean company name
    if company != 'unknown':
        company = re.sub(r'\b(inc|ltd|llc|corp|co)\b', '', company, flags=re.IGNORECASE)
        company = re.sub(r'[^\w\s-]', '', company)
        company = re.sub(r'\s+', '-', company.strip()).title()
    else:
        company = 'Unknown-Company'
    
    # Pad invoice number
    if number != 'unknown':
        try:
            num = int(number)
            number = f"{num:0{number_padding}d}"
        except ValueError:
            pass
    else:
        number = '0' * number_padding
    
    # Build filename
    if company_prefix:
        if date != 'unknown':
            return f"{company}_Invoice_{number}_{date}"
        else:
            return f"{company}_Invoice_{number}"
    else:
        if date != 'unknown':
            return f"Invoice_{number}_{company}_{date}"
        else:
            return f"Invoice_{number}_{company}"


def process_photos(context: ProcessingContext, organize_by_month: bool = True,
                  include_device: bool = False, hash_duplicates: bool = False) -> str:
    """
    All-in-one photo processor.
    
    Extracts photo metadata and creates organized filename with optional features.
    
    Args:
        organize_by_month: Whether to include YYYY-MM prefix for monthly organization
        include_device: Whether to include device/camera info in filename
        hash_duplicates: Whether to add hash suffix to prevent duplicate names
    
    Returns:
        Formatted photo filename string
    """
    base_name = context.file_path.stem
    
    # Extract date from filename or metadata
    date_pattern = r'(\d{8})'
    time_pattern = r'(\d{6})'
    
    date_match = re.search(date_pattern, base_name)
    time_match = re.search(time_pattern, base_name)
    
    components = []
    
    # Date component
    if date_match:
        date_str = date_match.group(1)
        try:
            parsed_date = datetime.datetime.strptime(date_str, '%Y%m%d')
            if organize_by_month:
                components.append(parsed_date.strftime('%Y-%m'))
            components.append(parsed_date.strftime('%Y%m%d'))
        except ValueError:
            components.append(date_str)
    else:
        # Try file modification time
        try:
            file_stat = context.file_path.stat()
            mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
            if organize_by_month:
                components.append(mod_time.strftime('%Y-%m'))
            components.append(mod_time.strftime('%Y%m%d'))
        except:
            components.append('unknown-date')
    
    # Time component
    if time_match:
        time_str = time_match.group(1)
        components.append(time_str)
    
    # Device component
    if include_device:
        device_patterns = [
            r'^(IMG|DSC|DCIM|P\d+)_',
            r'(iPhone|Samsung|Pixel|Canon|Nikon|Sony)'
        ]
        
        for pattern in device_patterns:
            match = re.search(pattern, base_name, re.IGNORECASE)
            if match:
                components.append(match.group(1))
                break
        else:
            components.append('Camera')
    
    # Photo type
    if 'VID' in base_name.upper():
        components.append('Video')
    elif 'SCR' in base_name.upper() or 'Screenshot' in base_name:
        components.append('Screenshot')
    else:
        components.append('Photo')
    
    # Hash for duplicates
    if hash_duplicates:
        try:
            with open(context.file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()[:8]
            components.append(file_hash)
        except:
            pass  # Skip hash if file can't be read
    
    return '_'.join(components)


def process_project_files(context: ProcessingContext, client_list: str = "",
                         version_format: str = "v", include_status: bool = True) -> str:
    """
    All-in-one project file processor.
    
    Extracts project data and creates organized filename for creative work.
    
    Args:
        client_list: Comma-separated list of known client names to match against
        version_format: Version prefix format - "v" for v1.2, "r" for r1.2, or "" for 1.2
        include_status: Whether to include status indicators (draft, final, etc.)
    
    Returns:
        Formatted project filename string
    """
    base_name = context.file_path.stem
    
    # Parse client list
    known_clients = []
    if client_list:
        known_clients = [c.strip() for c in client_list.split(',')]
    
    # Extract client
    client = 'unknown'
    for c in known_clients:
        if c.lower() in base_name.lower():
            client = c.replace(' ', '-')
            break
    
    # Extract version
    version_patterns = [
        r'[vV](\d+)\.(\d+)', r'[vV](\d+)',
        r'_(\d+)\.(\d+)_', r'_(\d+)_',
        r'rev(\d+)', r'r(\d+)'
    ]
    
    version = 'unknown'
    for pattern in version_patterns:
        match = re.search(pattern, base_name)
        if match:
            if len(match.groups()) == 2:
                version = f"{match.group(1)}.{match.group(2)}"
            else:
                version = match.group(1)
            break
    
    # Extract status
    status_keywords = {
        'draft': ['draft', 'wip', 'work'],
        'review': ['review', 'rev', 'check'],
        'final': ['final', 'approved', 'delivery'],
        'archive': ['old', 'archive', 'backup']
    }
    
    status = 'unknown'
    for status_name, keywords in status_keywords.items():
        if any(keyword in base_name.lower() for keyword in keywords):
            status = status_name
            break
    
    # Extract date
    date_patterns = [
        r'(\d{4}[-_]\d{2}[-_]\d{2})',
        r'(\d{8})',
        r'(\d{2}[-_]\d{2}[-_]\d{4})'
    ]
    
    date = 'unknown'
    for pattern in date_patterns:
        match = re.search(pattern, base_name)
        if match:
            date = match.group(1).replace('-', '').replace('_', '')
            break
    
    # Extract project name (remove known components)
    project_name = base_name
    for remove_item in [client, version, status, date]:
        if remove_item != 'unknown':
            project_name = project_name.replace(remove_item, '')
    
    project_name = re.sub(r'[_\-\.]+', '_', project_name).strip('_-.')
    if not project_name:
        project_name = 'Project'
    
    # Build filename
    components = []
    
    if client != 'unknown':
        components.append(client)
    
    components.append(project_name)
    
    if version != 'unknown':
        if version_format:
            components.append(f"{version_format}{version}")
        else:
            components.append(version)
    
    if include_status and status != 'unknown':
        components.append(status.title())
    
    if date != 'unknown':
        components.append(date)
    
    return '_'.join(components)


def process_media_files(context: ProcessingContext, categorize_by_type: bool = True,
                       include_resolution: bool = False, max_length: int = 50) -> str:
    """
    All-in-one media file processor.
    
    Processes various media types (images, videos, audio) with smart categorization.
    
    Args:
        categorize_by_type: Whether to include media type in filename
        include_resolution: Whether to attempt resolution extraction from metadata
        max_length: Maximum length for generated filename
    
    Returns:
        Formatted media filename string with length limit applied
    """
    base_name = context.file_path.stem
    file_ext = context.file_path.suffix.lower()
    
    # Determine media type
    image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    audio_exts = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
    
    media_type = 'Unknown'
    if file_ext in image_exts:
        media_type = 'Image'
    elif file_ext in video_exts:
        media_type = 'Video'
    elif file_ext in audio_exts:
        media_type = 'Audio'
    
    # Extract date/time if present
    date_match = re.search(r'(\d{8})', base_name)
    time_match = re.search(r'(\d{6})', base_name)
    
    components = []
    
    # Date component
    if date_match:
        components.append(date_match.group(1))
    
    # Time component
    if time_match:
        components.append(time_match.group(1))
    
    # Media type
    if categorize_by_type:
        components.append(media_type)
    
    # Resolution (placeholder - would need actual metadata reading)
    if include_resolution:
        # This would require a library like PIL or ffprobe
        components.append('HD')  # Placeholder
    
    # Original name component (cleaned)
    clean_name = re.sub(r'[\d_\-\.]+', '', base_name)
    clean_name = re.sub(r'[^\w\s]', '', clean_name).strip()
    if clean_name and len(clean_name) > 3:
        components.append(clean_name.title())
    
    # Build filename and apply length limit
    filename = '_'.join(components) if components else base_name
    
    if len(filename) > max_length:
        filename = filename[:max_length-3] + '...'
    
    return filename