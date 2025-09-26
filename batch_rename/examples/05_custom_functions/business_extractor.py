"""
Business document extractor for corporate filename patterns.
"""

import re
from datetime import datetime


def extract_business_document(filename, file_path, metadata):
    """Extract structured data from business document filenames."""
    
    # Remove file extension for pattern matching
    base_name = filename.rsplit('.', 1)[0].lower()
    
    # Define extraction patterns
    patterns = [
        # Pattern: CLIENT_DEPT_DOCTYPE_STATUS_YYYYMMDD
        r'(?P<client>[^_]+)_(?P<dept>[^_]+)_(?P<doc_type>[^_]+)_(?P<status>[^_]+)_(?P<date>\d{8})',
        # Pattern: CLIENT_DEPT_DOCTYPE_vVERSION_STATUS  
        r'(?P<client>[^_]+)_(?P<dept>[^_]+)_(?P<doc_type>[^_]+)_v(?P<version>[\d.]+)_(?P<status>[^_]+)',
        # Pattern: CLIENT_DOCTYPE_DESCRIPTION_DATE
        r'(?P<client>[^_]+)_(?P<doc_type>[^_]+)_(?P<description>[^_]+)_(?P<date>\d{6,8})',
    ]
    
    # Try each pattern
    extracted_data = None
    for pattern in patterns:
        match = re.search(pattern, base_name)
        if match:
            extracted_data = match.groupdict()
            break
    
    # Fallback extraction
    if not extracted_data:
        parts = re.split(r'[_-]', base_name)
        extracted_data = {
            'client': parts[0] if len(parts) > 0 else 'unknown',
            'doc_type': parts[1] if len(parts) > 1 else 'document', 
            'description': '_'.join(parts[2:]) if len(parts) > 2 else 'general',
        }
    
    # Business logic enrichment
    extracted_data = _enrich_business_data(extracted_data)
    
    return extracted_data


def _enrich_business_data(data):
    """Apply business logic to enrich extracted data."""
    
    # Client tier classification
    client = data.get('client', '').lower()
    if any(indicator in client for indicator in ['corp', 'global', 'mega', 'enterprise']):
        data['client_tier'] = 'enterprise'
    elif any(indicator in client for indicator in ['startup', 'tech', 'labs']):
        data['client_tier'] = 'startup'
    else:
        data['client_tier'] = 'standard'
    
    # Quarter calculation
    if 'date' in data and data['date']:
        data['quarter'] = _calculate_quarter(data['date'])
    else:
        now = datetime.now()
        data['quarter'] = f"{now.year}-Q{(now.month-1)//3 + 1}"
    
    # Standardize field formats
    for field in ['client', 'dept', 'doc_type', 'status', 'description']:
        if field in data and data[field]:
            data[field] = data[field].replace('_', ' ').title()
    
    return data


def _calculate_quarter(date_str):
    """Calculate quarter from date string."""
    try:
        if len(date_str) == 8:  # YYYYMMDD
            year = int(date_str[:4])
            month = int(date_str[4:6])
        elif len(date_str) == 6:  # MMDDYY
            month = int(date_str[:2])
            year = 2000 + int(date_str[4:6])
        else:
            now = datetime.now()
            return f"{now.year}-Q{(now.month-1)//3 + 1}"
        
        quarter = (month - 1) // 3 + 1
        return f"{year}-Q{quarter}"
        
    except (ValueError, IndexError):
        now = datetime.now()
        return f"{now.year}-Q{(now.month-1)//3 + 1}"
