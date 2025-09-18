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
        context: Processing context with filename and metadata
        department_mapping: Whether to use full department names vs codes
        include_year: Whether to include year prefix in output
    
    Returns:
        Formatted filename string
    """
    base_name = context.base_name
    
    # Extract data
    parts = base_name.split('_')
    
    if len(parts) >= 3:
        dept, doc_type, date_str = parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        dept, doc_type, date_str = parts[0], parts[1], 'unknown'
    else:
        dept, doc_type, date_str = 'misc', base_name, 'unknown'
    
    # Department mapping
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
        dept_formatted = dept_map.get(dept.upper(), dept.title())
    else:
        dept_formatted = dept.upper()
    
    # Document type formatting
    doc_type_formatted = doc_type.title()
    
    # Date formatting
    if date_str != 'unknown' and len(date_str) == 8 and date_str.isdigit():
        try:
            parsed_date = datetime.datetime.strptime(date_str, '%Y%m%d')
            date_formatted = parsed_date.strftime('%Y-%m-%d')
            year = parsed_date.strftime('%Y')
        except ValueError:
            date_formatted = date_str
            year = 'unknown'
    else:
        date_formatted = date_str
        year = 'unknown'
    
    # Build output filename
    if include_year and year != 'unknown':
        if date_formatted != 'unknown':
            return f"{year}_{dept_formatted}_{doc_type_formatted}_{date_formatted}"
        else:
            return f"{year}_{dept_formatted}_{doc_type_formatted}"
    else:
        if date_formatted != 'unknown':
            return f"{dept_formatted}_{doc_type_formatted}_{date_formatted}"
        else:
            return f"{dept_formatted}_{doc_type_formatted}"


def process_photo_organizer(context: ProcessingContext, date_prefix: bool = True, 
                           include_hash: bool = False, folder_structure: bool = False) -> str:
    """
    All-in-one photo organizer.
    
    Extracts date and device info from photos and creates organized filenames.
    
    Args:
        context: Processing context with filename and metadata
        date_prefix: Whether to start filename with date
        include_hash: Whether to include unique hash for duplicates
        folder_structure: Whether to include folder path in output
    
    Returns:
        Formatted filename string (may include folder path)
    """
    base_name = context.base_name
    
    # Extract date from filename or use current date
    date_match = re.search(r'(\d{8})', base_name)
    if date_match:
        date_str = date_match.group(1)
        try:
            parsed_date = datetime.datetime.strptime(date_str, '%Y%m%d')
            date_formatted = parsed_date.strftime('%Y-%m-%d')
            year = parsed_date.strftime('%Y')
            month = parsed_date.strftime('%B')
        except ValueError:
            date_formatted = date_str
            year = 'unknown'
            month = 'unknown'
    else:
        # Use current date as fallback
        now = datetime.datetime.now()
        date_formatted = now.strftime('%Y-%m-%d')
        year = now.strftime('%Y')
        month = now.strftime('%B')
    
    # Detect device/camera type
    if re.match(r'IMG_\d+', base_name, re.IGNORECASE):
        device_type = 'Phone'
        media_type = 'Photo'
    elif re.match(r'DSC_\d+', base_name, re.IGNORECASE):
        device_type = 'Camera'
        media_type = 'Photo'
    elif re.match(r'VID_\d+', base_name, re.IGNORECASE):
        device_type = 'Phone'
        media_type = 'Video'
    elif context.extension.lower() in ['.jpg', '.jpeg', '.png', '.heic']:
        device_type = 'Unknown'
        media_type = 'Photo'
    elif context.extension.lower() in ['.mp4', '.mov', '.avi']:
        device_type = 'Unknown'
        media_type = 'Video'
    else:
        device_type = 'Unknown'
        media_type = 'Media'
    
    # Extract time if present
    time_match = re.search(r'(\d{6})', base_name.replace(date_match.group(1) if date_match else '', ''))
    if time_match:
        time_str = time_match.group(1)
        time_formatted = f"{time_str[:2]}-{time_str[2:4]}-{time_str[4:6]}"
    else:
        time_formatted = None
    
    # Build filename components
    components = []
    
    if date_prefix:
        components.append(date_formatted)
    
    if time_formatted:
        components.append(time_formatted)
    
    components.extend([device_type, media_type])
    
    # Add unique hash if requested
    if include_hash:
        hash_obj = hashlib.md5(context.filename.encode())
        unique_hash = hash_obj.hexdigest()[:8]
        components.append(unique_hash)
    
    new_filename = '_'.join(components)
    
    # Add folder structure if requested
    if folder_structure and year != 'unknown':
        if month != 'unknown':
            return f"{year}/{month}/{new_filename}"
        else:
            return f"{year}/{new_filename}"
    else:
        return new_filename


def process_invoice_standardizer(context: ProcessingContext, company_first: bool = True, 
                               pad_numbers: int = 6, include_type: bool = True) -> str:
    """
    All-in-one invoice standardizer.
    
    Handles various invoice filename formats and creates standardized output.
    
    Args:
        context: Processing context with filename and metadata
        company_first: Whether to put company name first in output
        pad_numbers: How many digits to pad invoice numbers to
        include_type: Whether to include "Invoice" in the filename
    
    Returns:
        Formatted filename string
    """
    base_name = context.base_name
    
    # Initialize extracted data
    invoice_number = 'unknown'
    company_name = 'unknown'
    date_str = 'unknown'
    
    # Pattern 1: Invoice_12345_CompanyName_2024-03-15
    pattern1 = r'Invoice[_-](\d+)[_-]([^_-]+)(?:[_-](\d{4}-\d{2}-\d{2}))?'
    match = re.search(pattern1, base_name, re.IGNORECASE)
    if match:
        invoice_number = match.group(1)
        company_name = match.group(2)
        date_str = match.group(3) or 'unknown'
    else:
        # Pattern 2: INV-12345-CompanyName
        pattern2 = r'INV[_-](\d+)[_-]([^_-]+)'
        match = re.search(pattern2, base_name, re.IGNORECASE)
        if match:
            invoice_number = match.group(1)
            company_name = match.group(2)
        else:
            # Pattern 3: 12345_Invoice_CompanyName
            pattern3 = r'(\d+)[_-]Invoice[_-]([^_-]+)'
            match = re.search(pattern3, base_name, re.IGNORECASE)
            if match:
                invoice_number = match.group(1)
                company_name = match.group(2)
            else:
                # Fallback: try to extract any number and company-like text
                number_match = re.search(r'(\d{3,})', base_name)
                if number_match:
                    invoice_number = number_match.group(1)
                
                # Remove common invoice keywords and extract company
                cleaned = re.sub(r'\b(invoice|inv|bill|billing)\b', '', base_name, flags=re.IGNORECASE)
                cleaned = re.sub(r'\d+', '', cleaned)  # Remove numbers
                cleaned = re.sub(r'[_-]+', ' ', cleaned).strip()
                if cleaned:
                    company_name = cleaned
    
    # Clean and format company name
    if company_name != 'unknown':
        # Remove common business suffixes
        company_clean = re.sub(r'\b(inc|ltd|llc|corp|co|company)\b', '', company_name, flags=re.IGNORECASE)
        company_clean = re.sub(r'[^\w\s-]', '', company_clean)  # Remove special chars
        company_clean = re.sub(r'\s+', '-', company_clean.strip())  # Replace spaces with hyphens
        company_clean = company_clean.title()
    else:
        company_clean = 'Unknown-Company'
    
    # Format invoice number with padding
    if invoice_number != 'unknown':
        try:
            num = int(invoice_number)
            padded_number = f"{num:0{pad_numbers}d}"
        except ValueError:
            padded_number = invoice_number
    else:
        padded_number = '0' * pad_numbers
    
    # Format date
    if date_str != 'unknown':
        try:
            if '-' in date_str:
                parsed_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                date_formatted = parsed_date.strftime('%Y-%m-%d')
            else:
                date_formatted = date_str
        except ValueError:
            date_formatted = date_str
    else:
        date_formatted = None
    
    # Build output filename
    components = []
    
    if company_first:
        components.append(company_clean)
        if include_type:
            components.append('Invoice')
        components.append(padded_number)
    else:
        if include_type:
            components.append('Invoice')
        components.append(padded_number)
        components.append(company_clean)
    
    if date_formatted:
        components.append(date_formatted)
    
    return '_'.join(components)


def process_project_files(context: ProcessingContext, project_prefix: str = "PROJ", 
                         auto_version: bool = True, include_category: bool = True) -> str:
    """
    All-in-one project file processor.
    
    Standardizes project filenames with automatic version detection and categorization.
    
    Args:
        context: Processing context with filename and metadata
        project_prefix: Expected project prefix in filenames
        auto_version: Whether to automatically assign version 1.0 if missing
        include_category: Whether to include file category in output
    
    Returns:
        Formatted filename string
    """
    base_name = context.base_name
    extension = context.extension.lower()
    
    # Initialize extracted data
    project_code = 'unknown'
    document_type = 'unknown'
    version = 'none'
    
    # Try to extract project data with prefix
    pattern = rf'{re.escape(project_prefix)}[_-]([^_-]+)[_-]([^_-]+)(?:[_-]v?(\d+(?:\.\d+)?))?' 
    match = re.search(pattern, base_name, re.IGNORECASE)
    
    if match:
        project_code = match.group(1)
        document_type = match.group(2)
        version = match.group(3) or 'none'
    else:
        # Fallback: try to parse without prefix
        parts = base_name.split('_')
        if len(parts) >= 2:
            project_code = parts[0]
            document_type = parts[1]
            
            # Look for version in remaining parts
            for part in parts[2:]:
                version_match = re.search(r'v?(\d+(?:\.\d+)?)', part, re.IGNORECASE)
                if version_match:
                    version = version_match.group(1)
                    break
        else:
            project_code = 'MISC'
            document_type = base_name
    
    # Format project code
    project_formatted = project_code.upper().replace(' ', '-')
    
    # Format document type
    doc_type_formatted = document_type.title().replace('_', '-').replace(' ', '-')
    
    # Handle version
    if version == 'none' and auto_version:
        version = '1.0'
    elif version != 'none':
        # Ensure version has decimal if it's just a number
        if '.' not in version:
            version += '.0'
    
    # Determine file category
    category = 'Other'
    if extension in ['.doc', '.docx', '.txt', '.md']:
        category = 'Document'
    elif extension in ['.xls', '.xlsx', '.csv']:
        category = 'Spreadsheet'
    elif extension in ['.ppt', '.pptx']:
        category = 'Presentation'
    elif extension in ['.pdf']:
        category = 'PDF'
    elif extension in ['.jpg', '.png', '.gif', '.svg']:
        category = 'Image'
    elif extension in ['.py', '.js', '.html', '.css']:
        category = 'Code'
    
    # Build output filename
    components = [project_formatted, doc_type_formatted]
    
    if include_category and category != 'Other':
        components.append(category)
    
    if version != 'none':
        components.append(f"v{version}")
    
    return '_'.join(components)


def process_media_organizer(context: ProcessingContext, date_format: str = "YYYY-MM-DD", 
                          device_detection: bool = True, size_category: bool = False) -> str:
    """
    All-in-one media file organizer.
    
    Organizes photos and videos with date extraction and device detection.
    
    Args:
        context: Processing context with filename and metadata
        date_format: How to format dates ("YYYY-MM-DD", "YYYYMMDD", or "DD-MM-YYYY")
        device_detection: Whether to detect and include device type
        size_category: Whether to include file size category
    
    Returns:
        Formatted filename string
    """
    base_name = context.base_name
    extension = context.extension.lower()
    
    # Extract date from filename
    date_patterns = [
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})',  # YYYY-MM-DD or YYYYMMDD
        r'(\d{2})[-_]?(\d{2})[-_]?(\d{4})',  # DD-MM-YYYY
        r'(\d{8})'  # YYYYMMDD
    ]
    
    extracted_date = None
    for pattern in date_patterns:
        match = re.search(pattern, base_name)
        if match:
            groups = match.groups()
            if len(groups) == 1 and len(groups[0]) == 8:
                # YYYYMMDD format
                date_str = groups[0]
                year, month, day = date_str[:4], date_str[4:6], date_str[6:8]
            elif len(groups) == 3:
                if len(groups[0]) == 4:  # Year first
                    year, month, day = groups[0], groups[1], groups[2]
                else:  # Day first
                    day, month, year = groups[0], groups[1], groups[2]
            
            try:
                parsed_date = datetime.datetime(int(year), int(month), int(day))
                extracted_date = parsed_date
                break
            except ValueError:
                continue
    
    # Use current date if no date found
    if not extracted_date:
        extracted_date = datetime.datetime.now()
    
    # Format date according to preference
    if date_format == "YYYY-MM-DD":
        date_str = extracted_date.strftime('%Y-%m-%d')
    elif date_format == "YYYYMMDD":
        date_str = extracted_date.strftime('%Y%m%d')
    elif date_format == "DD-MM-YYYY":
        date_str = extracted_date.strftime('%d-%m-%Y')
    else:
        date_str = extracted_date.strftime('%Y-%m-%d')
    
    # Detect device and media type
    media_type = 'Unknown'
    device_type = 'Unknown'
    
    if device_detection:
        if re.match(r'IMG_\d+', base_name, re.IGNORECASE):
            device_type = 'Phone'
            media_type = 'Photo'
        elif re.match(r'DSC_\d+', base_name, re.IGNORECASE):
            device_type = 'Camera'
            media_type = 'Photo'
        elif re.match(r'VID_\d+', base_name, re.IGNORECASE):
            device_type = 'Phone'
            media_type = 'Video'
        elif re.match(r'MVI_\d+', base_name, re.IGNORECASE):
            device_type = 'Camera'
            media_type = 'Video'
    
    # Determine media type from extension if not detected
    if media_type == 'Unknown':
        if extension in ['.jpg', '.jpeg', '.png', '.heic', '.raw', '.tiff']:
            media_type = 'Photo'
        elif extension in ['.mp4', '.mov', '.avi', '.mkv', '.wmv']:
            media_type = 'Video'
        else:
            media_type = 'Media'
    
    # Extract time if present
    time_match = re.search(r'(\d{6})', base_name)
    if time_match:
        time_str = time_match.group(1)
        time_formatted = f"{time_str[:2]}{time_str[2:4]}{time_str[4:6]}"
    else:
        # Generate time from hash for consistency
        hash_obj = hashlib.md5(context.filename.encode())
        time_formatted = hash_obj.hexdigest()[:6]
    
    # Build filename components
    components = [date_str]
    
    if time_formatted:
        components.append(time_formatted)
    
    if device_detection and device_type != 'Unknown':
        components.append(device_type)
    
    components.append(media_type)
    
    # Add size category if requested
    if size_category:
        size_mb = context.file_size / (1024 * 1024)
        if size_mb < 1:
            components.append('Small')
        elif size_mb < 10:
            components.append('Medium')
        else:
            components.append('Large')
    
    return '_'.join(components)


def process_document_cleanup(context: ProcessingContext, max_length: int = 80, 
                           remove_special: bool = True, title_case: bool = True) -> str:
    """
    All-in-one document cleanup processor.
    
    Cleans up any document filename with configurable options.
    
    Args:
        context: Processing context with filename and metadata
        max_length: Maximum length for output filename
        remove_special: Whether to remove special characters
        title_case: Whether to apply title case formatting
    
    Returns:
        Cleaned filename string
    """
    base_name = context.base_name
    
    # Start with the base name
    cleaned_name = base_name
    
    if remove_special:
        # Remove or replace special characters
        cleaned_name = re.sub(r'[^\w\s.-]', '', cleaned_name)  # Keep letters, numbers, spaces, dots, hyphens
        cleaned_name = re.sub(r'\s+', '_', cleaned_name)       # Replace spaces with underscores
        cleaned_name = re.sub(r'[._-]+', '_', cleaned_name)    # Consolidate separators
        cleaned_name = cleaned_name.strip('_')                 # Remove leading/trailing underscores
    
    # Apply title case if requested
    if title_case:
        components = cleaned_name.split('_')
        formatted_components = []
        
        for component in components:
            if component.isdigit():
                # Keep numbers as-is
                formatted_components.append(component)
            elif re.match(r'\d+\.\d+', component):
                # Keep version numbers as-is
                formatted_components.append(component)
            elif len(component) <= 3 and component.isupper():
                # Keep short acronyms as-is
                formatted_components.append(component)
            else:
                # Title case for regular text
                formatted_components.append(component.title())
        
        cleaned_name = '_'.join(formatted_components)
    
    # Trim to max length
    if len(cleaned_name) > max_length:
        cleaned_name = cleaned_name[:max_length].rstrip('_')
    
    # Ensure we don't return an empty string
    if not cleaned_name:
        cleaned_name = 'Document'
    
    return cleaned_name
    """
    All-in-one business document processor.
    
    Extracts department, type, and date, then formats into professional filename.
    
    Args:
        filename: Input filename to process
        department_mapping: Whether to use full department names vs codes
        include_year: Whether to include year prefix in output
    
    Returns:
        Formatted filename string
    """
    file_path = Path(filename)
    base_name = file_path.stem
    
    # Extract data
    parts = base_name.split('_')
    
    if len(parts) >= 3:
        dept, doc_type, date_str = parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        dept, doc_type, date_str = parts[0], parts[1], 'unknown'
    else:
        dept, doc_type, date_str = 'misc', base_name, 'unknown'
    
    # Department mapping
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
        dept_formatted = dept_map.get(dept.upper(), dept.title())
    else:
        dept_formatted = dept.upper()
    
    # Document type formatting
    doc_type_formatted = doc_type.title()
    
    # Date formatting
    if date_str != 'unknown' and len(date_str) == 8 and date_str.isdigit():
        try:
            parsed_date = datetime.datetime.strptime(date_str, '%Y%m%d')
            date_formatted = parsed_date.strftime('%Y-%m-%d')
            year = parsed_date.strftime('%Y')
        except ValueError:
            date_formatted = date_str
            year = 'unknown'
    else:
        date_formatted = date_str
        year = 'unknown'
    
    # Build output filename
    if include_year and year != 'unknown':
        if date_formatted != 'unknown':
            return f"{year}_{dept_formatted}_{doc_type_formatted}_{date_formatted}"
        else:
            return f"{year}_{dept_formatted}_{doc_type_formatted}"
    else:
        if date_formatted != 'unknown':
            return f"{dept_formatted}_{doc_type_formatted}_{date_formatted}"
        else:
            return f"{dept_formatted}_{doc_type_formatted}"


def process_photo_organizer(filename: str, date_prefix: bool = True, 
                           include_hash: bool = False, folder_structure: bool = False) -> str:
    """
    All-in-one photo organizer.
    
    Extracts date and device info from photos and creates organized filenames.
    
    Args:
        filename: Input filename to process
        date_prefix: Whether to start filename with date
        include_hash: Whether to include unique hash for duplicates
        folder_structure: Whether to include folder path in output
    
    Returns:
        Formatted filename string (may include folder path)
    """
    file_path = Path(filename)
    base_name = file_path.stem
    
    # Extract date from filename or use current date
    date_match = re.search(r'(\d{8})', base_name)
    if date_match:
        date_str = date_match.group(1)
        try:
            parsed_date = datetime.datetime.strptime(date_str, '%Y%m%d')
            date_formatted = parsed_date.strftime('%Y-%m-%d')
            year = parsed_date.strftime('%Y')
            month = parsed_date.strftime('%B')
        except ValueError:
            date_formatted = date_str
            year = 'unknown'
            month = 'unknown'
    else:
        # Use current date as fallback
        now = datetime.datetime.now()
        date_formatted = now.strftime('%Y-%m-%d')
        year = now.strftime('%Y')
        month = now.strftime('%B')
    
    # Detect device/camera type
    if re.match(r'IMG_\d+', base_name, re.IGNORECASE):
        device_type = 'Phone'
        media_type = 'Photo'
    elif re.match(r'DSC_\d+', base_name, re.IGNORECASE):
        device_type = 'Camera'
        media_type = 'Photo'
    elif re.match(r'VID_\d+', base_name, re.IGNORECASE):
        device_type = 'Phone'
        media_type = 'Video'
    elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic']:
        device_type = 'Unknown'
        media_type = 'Photo'
    elif file_path.suffix.lower() in ['.mp4', '.mov', '.avi']:
        device_type = 'Unknown'
        media_type = 'Video'
    else:
        device_type = 'Unknown'
        media_type = 'Media'
    
    # Extract time if present
    time_match = re.search(r'(\d{6})', base_name.replace(date_match.group(1) if date_match else '', ''))
    if time_match:
        time_str = time_match.group(1)
        time_formatted = f"{time_str[:2]}-{time_str[2:4]}-{time_str[4:6]}"
    else:
        time_formatted = None
    
    # Build filename components
    components = []
    
    if date_prefix:
        components.append(date_formatted)
    
    if time_formatted:
        components.append(time_formatted)
    
    components.extend([device_type, media_type])
    
    # Add unique hash if requested
    if include_hash:
        hash_obj = hashlib.md5(filename.encode())
        unique_hash = hash_obj.hexdigest()[:8]
        components.append(unique_hash)
    
    new_filename = '_'.join(components)
    
    # Add folder structure if requested
    if folder_structure and year != 'unknown':
        if month != 'unknown':
            return f"{year}/{month}/{new_filename}"
        else:
            return f"{year}/{new_filename}"
    else:
        return new_filename


def process_invoice_standardizer(filename: str, company_first: bool = True, 
                               pad_numbers: int = 6, include_type: bool = True) -> str:
    """
    All-in-one invoice standardizer.
    
    Handles various invoice filename formats and creates standardized output.
    
    Args:
        filename: Input filename to process
        company_first: Whether to put company name first in output
        pad_numbers: How many digits to pad invoice numbers to
        include_type: Whether to include "Invoice" in the filename
    
    Returns:
        Formatted filename string
    """
    file_path = Path(filename)
    base_name = file_path.stem
    
    # Initialize extracted data
    invoice_number = 'unknown'
    company_name = 'unknown'
    date_str = 'unknown'
    
    # Pattern 1: Invoice_12345_CompanyName_2024-03-15
    pattern1 = r'Invoice[_-](\d+)[_-]([^_-]+)(?:[_-](\d{4}-\d{2}-\d{2}))?'
    match = re.search(pattern1, base_name, re.IGNORECASE)
    if match:
        invoice_number = match.group(1)
        company_name = match.group(2)
        date_str = match.group(3) or 'unknown'
    else:
        # Pattern 2: INV-12345-CompanyName
        pattern2 = r'INV[_-](\d+)[_-]([^_-]+)'
        match = re.search(pattern2, base_name, re.IGNORECASE)
        if match:
            invoice_number = match.group(1)
            company_name = match.group(2)
        else:
            # Pattern 3: 12345_Invoice_CompanyName
            pattern3 = r'(\d+)[_-]Invoice[_-]([^_-]+)'
            match = re.search(pattern3, base_name, re.IGNORECASE)
            if match:
                invoice_number = match.group(1)
                company_name = match.group(2)
            else:
                # Fallback: try to extract any number and company-like text
                number_match = re.search(r'(\d{3,})', base_name)
                if number_match:
                    invoice_number = number_match.group(1)
                
                # Remove common invoice keywords and extract company
                cleaned = re.sub(r'\b(invoice|inv|bill|billing)\b', '', base_name, flags=re.IGNORECASE)
                cleaned = re.sub(r'\d+', '', cleaned)  # Remove numbers
                cleaned = re.sub(r'[_-]+', ' ', cleaned).strip()
                if cleaned:
                    company_name = cleaned
    
    # Clean and format company name
    if company_name != 'unknown':
        # Remove common business suffixes
        company_clean = re.sub(r'\b(inc|ltd|llc|corp|co|company)\b', '', company_name, flags=re.IGNORECASE)
        company_clean = re.sub(r'[^\w\s-]', '', company_clean)  # Remove special chars
        company_clean = re.sub(r'\s+', '-', company_clean.strip())  # Replace spaces with hyphens
        company_clean = company_clean.title()
    else:
        company_clean = 'Unknown-Company'
    
    # Format invoice number with padding
    if invoice_number != 'unknown':
        try:
            num = int(invoice_number)
            padded_number = f"{num:0{pad_numbers}d}"
        except ValueError:
            padded_number = invoice_number
    else:
        padded_number = '0' * pad_numbers
    
    # Format date
    if date_str != 'unknown':
        try:
            if '-' in date_str:
                parsed_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                date_formatted = parsed_date.strftime('%Y-%m-%d')
            else:
                date_formatted = date_str
        except ValueError:
            date_formatted = date_str
    else:
        date_formatted = None
    
    # Build output filename
    components = []
    
    if company_first:
        components.append(company_clean)
        if include_type:
            components.append('Invoice')
        components.append(padded_number)
    else:
        if include_type:
            components.append('Invoice')
        components.append(padded_number)
        components.append(company_clean)
    
    if date_formatted:
        components.append(date_formatted)
    
    return '_'.join(components)


def process_project_files(filename: str, project_prefix: str = "PROJ", 
                         auto_version: bool = True, include_category: bool = True) -> str:
    """
    All-in-one project file processor.
    
    Standardizes project filenames with automatic version detection and categorization.
    
    Args:
        filename: Input filename to process
        project_prefix: Expected project prefix in filenames
        auto_version: Whether to automatically assign version 1.0 if missing
        include_category: Whether to include file category in output
    
    Returns:
        Formatted filename string
    """
    file_path = Path(filename)
    base_name = file_path.stem
    extension = file_path.suffix.lower()
    
    # Initialize extracted data
    project_code = 'unknown'
    document_type = 'unknown'
    version = 'none'
    
    # Try to extract project data with prefix
    pattern = rf'{re.escape(project_prefix)}[_-]([^_-]+)[_-]([^_-]+)(?:[_-]v?(\d+(?:\.\d+)?))?' 
    match = re.search(pattern, base_name, re.IGNORECASE)
    
    if match:
        project_code = match.group(1)
        document_type = match.group(2)
        version = match.group(3) or 'none'
    else:
        # Fallback: try to parse without prefix
        parts = base_name.split('_')
        if len(parts) >= 2:
            project_code = parts[0]
            document_type = parts[1]
            
            # Look for version in remaining parts
            for part in parts[2:]:
                version_match = re.search(r'v?(\d+(?:\.\d+)?)', part, re.IGNORECASE)
                if version_match:
                    version = version_match.group(1)
                    break
        else:
            project_code = 'MISC'
            document_type = base_name
    
    # Format project code
    project_formatted = project_code.upper().replace(' ', '-')
    
    # Format document type
    doc_type_formatted = document_type.title().replace('_', '-').replace(' ', '-')
    
    # Handle version
    if version == 'none' and auto_version:
        version = '1.0'
    elif version != 'none':
        # Ensure version has decimal if it's just a number
        if '.' not in version:
            version += '.0'
    
    # Determine file category
    category = 'Other'
    if extension in ['.doc', '.docx', '.txt', '.md']:
        category = 'Document'
    elif extension in ['.xls', '.xlsx', '.csv']:
        category = 'Spreadsheet'
    elif extension in ['.ppt', '.pptx']:
        category = 'Presentation'
    elif extension in ['.pdf']:
        category = 'PDF'
    elif extension in ['.jpg', '.png', '.gif', '.svg']:
        category = 'Image'
    elif extension in ['.py', '.js', '.html', '.css']:
        category = 'Code'
    
    # Build output filename
    components = [project_formatted, doc_type_formatted]
    
    if include_category and category != 'Other':
        components.append(category)
    
    if version != 'none':
        components.append(f"v{version}")
    
    return '_'.join(components)


def process_media_organizer(filename: str, date_format: str = "YYYY-MM-DD", 
                          device_detection: bool = True, size_category: bool = False) -> str:
    """
    All-in-one media file organizer.
    
    Organizes photos and videos with date extraction and device detection.
    
    Args:
        filename: Input filename to process
        date_format: How to format dates ("YYYY-MM-DD", "YYYYMMDD", or "DD-MM-YYYY")
        device_detection: Whether to detect and include device type
        size_category: Whether to include file size category (requires file access)
    
    Returns:
        Formatted filename string
    """
    file_path = Path(filename)
    base_name = file_path.stem
    extension = file_path.suffix.lower()
    
    # Extract date from filename
    date_patterns = [
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})',  # YYYY-MM-DD or YYYYMMDD
        r'(\d{2})[-_]?(\d{2})[-_]?(\d{4})',  # DD-MM-YYYY
        r'(\d{8})'  # YYYYMMDD
    ]
    
    extracted_date = None
    for pattern in date_patterns:
        match = re.search(pattern, base_name)
        if match:
            groups = match.groups()
            if len(groups) == 1 and len(groups[0]) == 8:
                # YYYYMMDD format
                date_str = groups[0]
                year, month, day = date_str[:4], date_str[4:6], date_str[6:8]
            elif len(groups) == 3:
                if len(groups[0]) == 4:  # Year first
                    year, month, day = groups[0], groups[1], groups[2]
                else:  # Day first
                    day, month, year = groups[0], groups[1], groups[2]
            
            try:
                parsed_date = datetime.datetime(int(year), int(month), int(day))
                extracted_date = parsed_date
                break
            except ValueError:
                continue
    
    # Use current date if no date found
    if not extracted_date:
        extracted_date = datetime.datetime.now()
    
    # Format date according to preference
    if date_format == "YYYY-MM-DD":
        date_str = extracted_date.strftime('%Y-%m-%d')
    elif date_format == "YYYYMMDD":
        date_str = extracted_date.strftime('%Y%m%d')
    elif date_format == "DD-MM-YYYY":
        date_str = extracted_date.strftime('%d-%m-%Y')
    else:
        date_str = extracted_date.strftime('%Y-%m-%d')
    
    # Detect device and media type
    media_type = 'Unknown'
    device_type = 'Unknown'
    
    if device_detection:
        if re.match(r'IMG_\d+', base_name, re.IGNORECASE):
            device_type = 'Phone'
            media_type = 'Photo'
        elif re.match(r'DSC_\d+', base_name, re.IGNORECASE):
            device_type = 'Camera'
            media_type = 'Photo'
        elif re.match(r'VID_\d+', base_name, re.IGNORECASE):
            device_type = 'Phone'
            media_type = 'Video'
        elif re.match(r'MVI_\d+', base_name, re.IGNORECASE):
            device_type = 'Camera'
            media_type = 'Video'
    
    # Determine media type from extension if not detected
    if media_type == 'Unknown':
        if extension in ['.jpg', '.jpeg', '.png', '.heic', '.raw', '.tiff']:
            media_type = 'Photo'
        elif extension in ['.mp4', '.mov', '.avi', '.mkv', '.wmv']:
            media_type = 'Video'
        else:
            media_type = 'Media'
    
    # Extract time if present
    time_match = re.search(r'(\d{6})', base_name)
    if time_match:
        time_str = time_match.group(1)
        time_formatted = f"{time_str[:2]}{time_str[2:4]}{time_str[4:6]}"
    else:
        # Generate time from hash for consistency
        hash_obj = hashlib.md5(filename.encode())
        time_formatted = hash_obj.hexdigest()[:6]
    
    # Build filename components
    components = [date_str]
    
    if time_formatted:
        components.append(time_formatted)
    
    if device_detection and device_type != 'Unknown':
        components.append(device_type)
    
    components.append(media_type)
    
    # Add size category if requested (placeholder - would need actual file access)
    if size_category:
        # This would require actual file size checking
        # For demo purposes, we'll use a placeholder
        size_hash = int(hashlib.md5(filename.encode()).hexdigest()[:2], 16)
        if size_hash < 85:
            components.append('Small')
        elif size_hash < 170:
            components.append('Medium')
        else:
            components.append('Large')
    
    return '_'.join(components)


def process_document_cleanup(filename: str, max_length: int = 80, 
                           remove_special: bool = True, title_case: bool = True) -> str:
    """
    All-in-one document cleanup processor.
    
    Cleans up any document filename with configurable options.
    
    Args:
        filename: Input filename to process
        max_length: Maximum length for output filename
        remove_special: Whether to remove special characters
        title_case: Whether to apply title case formatting
    
    Returns:
        Cleaned filename string
    """
    file_path = Path(filename)
    base_name = file_path.stem
    
    # Start with the base name
    cleaned_name = base_name
    
    if remove_special:
        # Remove or replace special characters
        cleaned_name = re.sub(r'[^\w\s.-]', '', cleaned_name)  # Keep letters, numbers, spaces, dots, hyphens
        cleaned_name = re.sub(r'\s+', '_', cleaned_name)       # Replace spaces with underscores
        cleaned_name = re.sub(r'[._-]+', '_', cleaned_name)    # Consolidate separators
        cleaned_name = cleaned_name.strip('_')                 # Remove leading/trailing underscores
    
    # Apply title case if requested
    if title_case:
        components = cleaned_name.split('_')
        formatted_components = []
        
        for component in components:
            if component.isdigit():
                # Keep numbers as-is
                formatted_components.append(component)
            elif re.match(r'\d+\.\d+', component):
                # Keep version numbers as-is
                formatted_components.append(component)
            elif len(component) <= 3 and component.isupper():
                # Keep short acronyms as-is
                formatted_components.append(component)
            else:
                # Title case for regular text
                formatted_components.append(component.title())
        
        cleaned_name = '_'.join(formatted_components)
    
    # Trim to max length
    if len(cleaned_name) > max_length:
        cleaned_name = cleaned_name[:max_length].rstrip('_')
    
    # Ensure we don't return an empty string
    if not cleaned_name:
        cleaned_name = 'Document'
    
    return cleaned_name