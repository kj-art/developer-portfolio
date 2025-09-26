"""
Example Custom Converters for Batch Rename Tool

These converters transform extracted data into formatted output
for generating new filenames.

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


def convert_data(context: ProcessingContext) -> Dict[str, Any]:
    """
    Business document formatter.
    
    Formats department codes and standardizes document types.
    Creates clean, professional business filenames.
    
    Returns:
        Dictionary with formatted fields including dept_full, type_formatted, date_iso, formatted_name
    """
    if not context.has_extracted_data():
        return {'formatted_name': context.file_path.stem}
    
    result = context.extracted_data.copy()
    
    # Standardize department codes
    dept_mapping = {
        'HR': 'Human-Resources',
        'IT': 'Information-Technology', 
        'FIN': 'Finance',
        'FINANCE': 'Finance',
        'LEGAL': 'Legal',
        'OPS': 'Operations',
        'OPERATIONS': 'Operations',
        'SALES': 'Sales',
        'MARKETING': 'Marketing',
        'MKT': 'Marketing'
    }
    
    dept = context.get_extracted_field('dept')
    if dept:
        dept_upper = dept.upper()
        result['dept_full'] = dept_mapping.get(dept_upper, dept.title())
        result['dept_code'] = dept_upper
    
    # Standardize document types
    type_mapping = {
        'POLICY': 'Policy',
        'PROCEDURE': 'Procedure', 
        'REPORT': 'Report',
        'MEETING': 'Meeting-Notes',
        'CONTRACT': 'Contract',
        'INVOICE': 'Invoice',
        'PROPOSAL': 'Proposal',
        'PRESENTATION': 'Presentation'
    }
    
    doc_type = context.get_extracted_field('type')
    if doc_type:
        type_upper = doc_type.upper()
        result['type_formatted'] = type_mapping.get(type_upper, doc_type.title())
    
    # Format date consistently
    date_str = context.get_extracted_field('date')
    if date_str and date_str != 'unknown':
        # Try to parse various date formats
        try:
            if len(date_str) == 8:  # YYYYMMDD
                parsed_date = datetime.datetime.strptime(date_str, '%Y%m%d')
            elif '-' in date_str:  # YYYY-MM-DD
                parsed_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            else:
                parsed_date = None
            
            if parsed_date:
                result['date_iso'] = parsed_date.strftime('%Y-%m-%d')
                result['date_compact'] = parsed_date.strftime('%Y%m%d')
                result['year'] = parsed_date.strftime('%Y')
                result['month'] = parsed_date.strftime('%m')
        except ValueError:
            result['date_iso'] = 'unknown'
            result['date_compact'] = 'unknown'
    
    # Generate formatted filename
    if all(k in result for k in ['dept_full', 'type_formatted', 'date_iso']):
        result['formatted_name'] = f"{result['dept_full']}_{result['type_formatted']}_{result['date_iso']}"
    elif all(k in result for k in ['dept_full', 'type_formatted']):
        result['formatted_name'] = f"{result['dept_full']}_{result['type_formatted']}"
    else:
        result['formatted_name'] = context.file_path.stem
    
    return result


def convert_invoice_data(context: ProcessingContext, company_prefix: bool = True) -> Dict[str, Any]:
    """
    Invoice formatter with company prefix option.
    
    Creates standardized invoice filenames with optional company prefixes.
    
    Args:
        company_prefix: Whether to include company name as prefix in filename
    
    Returns:
        Dictionary with formatted invoice fields including company_clean, number_padded, formatted_name
    """
    if not context.has_extracted_data():
        return {'formatted_name': context.file_path.stem}
    
    result = context.extracted_data.copy()
    
    # Clean company names
    company = context.get_extracted_field('company')
    if company and company != 'unknown':
        # Remove common suffixes and clean
        company = re.sub(r'\b(inc|ltd|llc|corp|co)\b', '', company, flags=re.IGNORECASE)
        company = re.sub(r'[^\w\s-]', '', company)  # Remove special chars except hyphens
        company = re.sub(r'\s+', '-', company.strip())  # Replace spaces with hyphens
        result['company_clean'] = company.title()
    else:
        result['company_clean'] = 'Unknown-Company'
    
    # Pad invoice numbers
    number = context.get_extracted_field('number')
    if number and number != 'unknown':
        try:
            num = int(number)
            result['number_padded'] = f"{num:06d}"  # 6-digit padding
        except ValueError:
            result['number_padded'] = number
    else:
        result['number_padded'] = '000000'
    
    # Format dates
    date_str = context.get_extracted_field('date')
    if date_str and date_str != 'unknown':
        try:
            if '-' in date_str:
                parsed_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                result['date_formatted'] = parsed_date.strftime('%Y-%m-%d')
            else:
                result['date_formatted'] = date_str
        except ValueError:
            result['date_formatted'] = 'unknown'
    else:
        result['date_formatted'] = 'unknown'
    
    # Build formatted filename
    if company_prefix:
        if result['date_formatted'] != 'unknown':
            result['formatted_name'] = f"{result['company_clean']}_Invoice_{result['number_padded']}_{result['date_formatted']}"
        else:
            result['formatted_name'] = f"{result['company_clean']}_Invoice_{result['number_padded']}"
    else:
        if result['date_formatted'] != 'unknown':
            result['formatted_name'] = f"Invoice_{result['number_padded']}_{result['company_clean']}_{result['date_formatted']}"
        else:
            result['formatted_name'] = f"Invoice_{result['number_padded']}_{result['company_clean']}"
    
    return result


def convert_photo_data(context: ProcessingContext, include_device: bool = False, 
                      group_by_month: bool = True) -> Dict[str, Any]:
    """
    Photo organizer with device and grouping options.
    
    Creates organized photo filenames with optional device info and monthly grouping.
    
    Args:
        include_device: Whether to include device/camera model in filename
        group_by_month: Whether to organize photos by year-month format
    
    Returns:
        Dictionary with formatted photo fields including organized folder structure and clean filename
    """
    if not context.has_extracted_data():
        return {'formatted_name': context.file_path.stem}
    
    result = context.extracted_data.copy()
    
    # Build filename components
    components = []
    
    # Date component
    date_str = context.get_extracted_field('date')
    if date_str and date_str != 'unknown':
        if group_by_month:
            # Create YYYY-MM format for folder organization
            try:
                if '-' in date_str:
                    year_month = '-'.join(date_str.split('-')[:2])  # YYYY-MM
                else:
                    year_month = f"{date_str[:4]}-{date_str[4:6]}"  # YYYYMMDD -> YYYY-MM
                result['folder_date'] = year_month
                components.append(date_str.replace('-', ''))  # YYYYMMDD for filename
            except:
                components.append(date_str)
        else:
            components.append(date_str.replace('-', ''))
    
    # Time component
    time_str = context.get_extracted_field('time')
    if time_str and time_str != 'unknown':
        components.append(time_str.replace('-', ''))
    
    # Device component
    if include_device:
        device = context.get_extracted_field('device')
        if device and device != 'unknown':
            components.append(device)
    
    # Photo type
    photo_type = context.get_extracted_field('type')
    if photo_type and photo_type != 'Photo':  # Only add if not default
        components.append(photo_type)
    
    # Build formatted filename
    if components:
        result['formatted_name'] = '_'.join(components)
    else:
        result['formatted_name'] = context.file_path.stem
    
    # Add folder organization info
    if group_by_month and 'folder_date' in result:
        result['suggested_folder'] = f"Photos/{result['folder_date']}"
    else:
        year = context.get_extracted_field('year')
        if year:
            result['suggested_folder'] = f"Photos/{year}"
        else:
            result['suggested_folder'] = "Photos/Unsorted"
    
    return result


def convert_project_data(context: ProcessingContext, use_client_prefix: bool = True,
                        include_status: bool = False, version_format: str = "v") -> Dict[str, Any]:
    """
    Project file converter for creative work.
    
    Creates organized project filenames with client, project, version, and status information.
    
    Args:
        use_client_prefix: Whether to include client name as prefix in filename
        include_status: Whether to include status indicators (draft, final, etc.) in filename
        version_format: Version prefix format - "v" for v1.2, "r" for r1.2, or "" for 1.2
    
    Returns:
        Dictionary with formatted project fields including organized filename and folder structure
    """
    if not context.has_extracted_data():
        return {'formatted_name': context.file_path.stem}
    
    result = context.extracted_data.copy()
    
    # Build filename components
    components = []
    
    # Client prefix
    client = context.get_extracted_field('client')
    if use_client_prefix and client and client != 'unknown':
        components.append(client.replace(' ', '-'))
    
    # Project name (always include)
    project = context.get_extracted_field('project')
    if project and project != 'unknown':
        components.append(project.replace(' ', '-'))
    else:
        components.append('Project')
    
    # Version
    version = context.get_extracted_field('version')
    if version and version != 'unknown':
        if version_format:
            components.append(f"{version_format}{version}")
        else:
            components.append(version)
    
    # Status
    if include_status:
        status = context.get_extracted_field('status')
        if status and status != 'unknown':
            components.append(status.title())
    
    # Date
    date_str = context.get_extracted_field('date')
    if date_str and date_str != 'unknown':
        # Clean up date format
        clean_date = date_str.replace('-', '').replace('_', '')
        components.append(clean_date)
    
    # Build formatted filename
    result['formatted_name'] = '_'.join(components)
    
    # Create folder organization
    folder_parts = []
    if client and client != 'unknown':
        folder_parts.append(client)
    if project and project != 'unknown':
        folder_parts.append(project)
    
    if folder_parts:
        result['suggested_folder'] = '/'.join(folder_parts)
    else:
        result['suggested_folder'] = 'Projects'
    
    # Add status-based subfolder
    status = context.get_extracted_field('status')
    if status and status != 'unknown':
        if status == 'archive':
            result['suggested_folder'] += '/Archive'
        elif status == 'final':
            result['suggested_folder'] += '/Final'
        elif status == 'draft':
            result['suggested_folder'] += '/Work-in-Progress'
    
    return result


def convert_document_data(context: ProcessingContext, department_folders: bool = True,
                         date_folders: bool = False, max_filename_length: int = 50) -> Dict[str, Any]:
    """
    General document converter with folder organization.
    
    Creates clean document names with optional department and date-based folder organization.
    
    Args:
        department_folders: Whether to organize files into department-based folders
        date_folders: Whether to create date-based subfolders (YYYY/MM structure)
        max_filename_length: Maximum length for generated filenames (truncates if longer)
    
    Returns:
        Dictionary with formatted document fields including folder structure and length-limited filename
    """
    if not context.has_extracted_data():
        return {'formatted_name': context.file_path.stem[:max_filename_length]}
    
    result = context.extracted_data.copy()
    
    # Build base filename
    components = []
    
    # Department (if not using department folders)
    dept = context.get_extracted_field('dept')
    if dept and dept != 'unknown' and not department_folders:
        components.append(dept.upper())
    
    # Document type
    doc_type = context.get_extracted_field('type')
    if doc_type and doc_type != 'unknown':
        components.append(doc_type.replace(' ', '-'))
    
    # Date
    date_str = context.get_extracted_field('date')
    if date_str and date_str != 'unknown':
        clean_date = date_str.replace('-', '')
        components.append(clean_date)
    
    # Build filename and apply length limit
    if components:
        filename = '_'.join(components)
        if len(filename) > max_filename_length:
            filename = filename[:max_filename_length-3] + '...'
        result['formatted_name'] = filename
    else:
        original = context.file_path.stem
        result['formatted_name'] = original[:max_filename_length]
    
    # Build folder structure
    folder_parts = []
    
    # Department folder
    if department_folders and dept and dept != 'unknown':
        folder_parts.append(dept.upper())
    
    # Date folders
    if date_folders and date_str and date_str != 'unknown':
        try:
            if '-' in date_str:
                date_parts = date_str.split('-')
                folder_parts.extend([date_parts[0], date_parts[1]])  # YYYY/MM
            elif len(date_str) >= 6:
                folder_parts.extend([date_str[:4], date_str[4:6]])  # YYYY/MM
        except:
            pass  # Skip date folders if parsing fails
    
    # Document type folder
    if doc_type and doc_type != 'unknown':
        folder_parts.append(doc_type.replace(' ', '-'))
    
    if folder_parts:
        result['suggested_folder'] = '/'.join(folder_parts)
    else:
        result['suggested_folder'] = 'Documents'
    
    return result