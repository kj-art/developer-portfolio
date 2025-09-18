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
    """
    if not context.has_extracted_data():
        return {'formatted_name': context.base_name}
    
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
        result['formatted_name'] = context.base_name
    
    return result


def convert_invoice_data(context: ProcessingContext, company_prefix: bool = True) -> Dict[str, Any]:
    """
    Invoice formatter with company prefix option.
    
    Creates standardized invoice filenames with optional company prefixes.
    """
    if not context.has_extracted_data():
        return {'formatted_name': context.base_name}
    
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
    """
    if not context.has_extracted_data():
        return {'formatted_name': context.base_name}
    
    result = context.extracted_data.copy()
    
    # Format the date for folder organization
    date_str = context.get_extracted_field('date')
    if date_str and date_str != 'unknown':
        try:
            if len(date_str) == 8:  # YYYYMMDD
                parsed_date = datetime.datetime.strptime(date_str, '%Y%m%d')
                result['year'] = parsed_date.strftime('%Y')
                result['month'] = parsed_date.strftime('%m')
                result['month_name'] = parsed_date.strftime('%B')
                result['date_readable'] = parsed_date.strftime('%Y-%m-%d')
            else:
                result['year'] = 'unknown'
                result['month'] = 'unknown'
                result['month_name'] = 'unknown'
                result['date_readable'] = date_str
        except ValueError:
            result['year'] = 'unknown'
            result['month'] = 'unknown'
            result['month_name'] = 'unknown'
            result['date_readable'] = date_str
    
    # Create sequence number based on time if available
    time_str = context.get_extracted_field('time')
    if time_str and time_str != 'unknown':
        result['time_formatted'] = time_str
    else:
        # Use a simple counter based on filename
        import hashlib
        hash_obj = hashlib.md5(context.filename.encode())
        result['time_formatted'] = hash_obj.hexdigest()[:6]
    
    # Build the filename components
    components = []
    
    # Add date
    if result.get('date_readable', 'unknown') != 'unknown':
        components.append(result['date_readable'])
    
    # Add time/sequence
    if result.get('time_formatted'):
        components.append(result['time_formatted'])
    
    # Add device info if requested
    device = context.get_extracted_field('device')
    if include_device and device and device != 'unknown':
        components.append(device.title())
    
    # Add type
    media_type = context.get_extracted_field('type')
    if media_type:
        components.append(media_type.title())
    
    # Add size category as suffix
    size_cat = context.get_extracted_field('size_cat')
    if size_cat:
        components.append(size_cat.upper())
    
    result['formatted_name'] = '_'.join(components) if components else context.base_name
    
    # Create folder path if grouping by month
    if group_by_month and result.get('year', 'unknown') != 'unknown':
        if result.get('month_name', 'unknown') != 'unknown':
            result['folder_path'] = f"{result['year']}/{result['month_name']}"
        else:
            result['folder_path'] = f"{result['year']}/Unknown"
    else:
        result['folder_path'] = ""
    
    return result


def convert_project_data(context: ProcessingContext, include_category: bool = True, 
                        version_format: str = "v{version}") -> Dict[str, Any]:
    """
    Project file formatter with category and version formatting options.
    
    Creates consistent project filenames with customizable version formatting.
    """
    if not context.has_extracted_data():
        return {'formatted_name': context.base_name}
    
    result = context.extracted_data.copy()
    
    # Format project code
    project = context.get_extracted_field('project')
    if project and project != 'unknown':
        # Ensure project codes are uppercase and well-formatted
        project_code = project.upper().replace(' ', '-')
        result['project_formatted'] = project_code
    else:
        result['project_formatted'] = 'UNKNOWN'
    
    # Format document type
    doc_type = context.get_extracted_field('type')
    if doc_type:
        doc_type_formatted = doc_type.title().replace('_', '-').replace(' ', '-')
        result['type_formatted'] = doc_type_formatted
    else:
        result['type_formatted'] = 'Document'
    
    # Format version
    version = context.get_extracted_field('version')
    if version and version not in ['none', 'unknown']:
        try:
            # Handle versions like "1.0", "2", "1.2.3"
            version_str = str(version)
            if '.' not in version_str:
                version_str += '.0'  # Add .0 to single numbers
            result['version_formatted'] = version_format.format(version=version_str)
        except:
            result['version_formatted'] = version_format.format(version='1.0')
    else:
        result['version_formatted'] = ''
    
    # Build filename components
    components = [result['project_formatted'], result['type_formatted']]
    
    # Add category if requested and available
    category = context.get_extracted_field('category')
    if include_category and category and category != 'other':
        components.append(category.title())
    
    # Add version if present
    if result['version_formatted']:
        components.append(result['version_formatted'])
    
    result['formatted_name'] = '_'.join(components)
    
    # Create project folder structure
    result['folder_path'] = f"Projects/{result['project_formatted']}"
    if category and category != 'other':
        result['folder_path'] += f"/{category.title()}"
    
    return result


def convert_cleanup_data(context: ProcessingContext, remove_special: bool = True, 
                        max_length: int = 100) -> Dict[str, Any]:
    """
    General cleanup converter.
    
    Cleans up any filename by removing special characters, limiting length,
    and applying consistent formatting rules.
    """
    result = {}
    
    # Start with the original filename stem
    base_name = context.base_name
    
    if remove_special:
        # Remove or replace special characters
        clean_name = re.sub(r'[^\w\s.-]', '', base_name)  # Keep word chars, spaces, dots, hyphens
        clean_name = re.sub(r'\s+', '_', clean_name)      # Replace spaces with underscores
        clean_name = re.sub(r'[._-]+', '_', clean_name)   # Consolidate separators
        clean_name = clean_name.strip('_')                # Remove leading/trailing underscores
    else:
        clean_name = base_name
    
    # Limit length
    if len(clean_name) > max_length:
        clean_name = clean_name[:max_length].rstrip('_')
    
    # Apply title case to each component
    components = clean_name.split('_')
    formatted_components = []
    
    for component in components:
        if component.isdigit():
            # Keep numbers as-is
            formatted_components.append(component)
        elif re.match(r'\d+\.\d+', component):
            # Keep version numbers as-is
            formatted_components.append(component)
        else:
            # Title case for text
            formatted_components.append(component.title())
    
    result['formatted_name'] = '_'.join(formatted_components)
    
    # Add metadata
    result['original_length'] = len(base_name)
    result['new_length'] = len(result['formatted_name'])
    result['cleaned'] = base_name != result['formatted_name']
    
    return result