"""
Intelligent template for business document formatting.
"""

from pathlib import Path


def format_business_filename(context):
    """Create intelligent business document filenames with hierarchical organization."""
    
    data = context.extracted_data
    file_extension = context.file_path.suffix
    
    # Build hierarchical path components
    department = _format_department(data)
    client = _format_client(data)
    quarter = _get_quarter(data)
    filename = _build_filename(data, file_extension)
    
    # Construct full path
    return f"{department}/{client}/{quarter}/{filename}"


def _format_department(data):
    """Format department for directory structure."""
    dept = data.get('dept', data.get('doc_type', 'General'))
    
    # Standardize common department names
    dept_mapping = {
        'hr': 'HR',
        'human resources': 'HR', 
        'it': 'IT',
        'fin': 'Finance',
        'financial': 'Finance',
        'legal': 'Legal',
        'marketing': 'Marketing',
        'ops': 'Operations',
        'operations': 'Operations',
    }
    
    dept_lower = dept.lower().strip()
    return dept_mapping.get(dept_lower, dept.title().replace(' ', '-'))


def _format_client(data):
    """Format client name for directory structure."""
    client = data.get('client', 'Unknown')
    
    # Clean and standardize client names
    client_clean = client.upper().replace('_', '-').replace(' ', '-')
    
    # Handle common corporate suffixes
    suffixes = {
        'CORPORATION': 'CORP', 
        'INCORPORATED': 'INC',
        'LIMITED': 'LTD',
        'COMPANY': 'CO'
    }
    
    for old_suffix, new_suffix in suffixes.items():
        if client_clean.endswith(f'-{old_suffix}'):
            client_clean = client_clean[:-len(old_suffix)] + new_suffix
            break
    
    return client_clean


def _get_quarter(data):
    """Get formatted quarter for directory structure."""
    quarter = data.get('quarter', '2024-Q1')
    
    # Ensure proper format (YYYY-QN)
    if not quarter or len(quarter) < 6:
        from datetime import datetime
        now = datetime.now()
        quarter = f"{now.year}-Q{(now.month-1)//3 + 1}"
    
    return quarter


def _build_filename(data, extension):
    """Build the actual filename with business logic."""
    components = []
    
    # Document type (always included)
    doc_type = data.get('doc_type', 'Document')
    components.append(_clean_component(doc_type))
    
    # Status or version
    status = _get_status_or_version(data)
    if status:
        components.append(status)
    
    # Description (if available and not redundant)
    description = data.get('description', '')
    if description and description.lower() not in doc_type.lower():
        components.append(_clean_component(description))
    
    # Join components and add extension
    filename = '-'.join(components)
    return f"{filename}{extension}"


def _clean_component(component):
    """Clean and format a filename component."""
    if not component:
        return ''
    
    # Remove special characters and normalize
    cleaned = component.replace('_', ' ').replace('-', ' ')
    
    # Title case each word
    words = cleaned.split()
    title_words = []
    
    for word in words:
        if word.upper() in ['API', 'UI', 'UX', 'IT', 'HR', 'QA']:
            title_words.append(word.upper())
        else:
            title_words.append(word.capitalize())
    
    return '-'.join(title_words)


def _get_status_or_version(data):
    """Get status or version component with proper formatting."""
    # Version takes precedence over status
    if 'version' in data and data['version']:
        version = data['version']
        
        # Normalize version format
        if not version.startswith('v'):
            version = f"v{version}"
        
        # Pad major version numbers
        import re
        version_match = re.match(r'v(\d+)\.(\d+)', version)
        if version_match:
            major = int(version_match.group(1))
            minor = version_match.group(2)
            version = f"v{major:02d}.{minor}"
        
        return version
    
    # Use status if no version
    status = data.get('status', '')
    if status:
        return _clean_component(status)
    
    return ''
