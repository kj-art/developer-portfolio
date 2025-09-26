"""
Compliance converter for industry-specific document formatting.
"""

from datetime import datetime, timedelta


def apply_compliance_rules(context):
    """Apply industry compliance formatting and classification rules."""
    
    data = context.extracted_data.copy()
    filename_lower = context.filename.lower()
    
    # Apply document classification
    data = _classify_document(data, filename_lower)
    
    # Determine retention requirements
    data = _set_retention_policy(data)
    
    # Apply confidentiality markings
    data = _determine_confidentiality(data, filename_lower)
    
    return data


def _classify_document(data, filename_lower):
    """Classify documents according to business taxonomy."""
    
    doc_type = data.get('doc_type', '').lower()
    dept = data.get('dept', '').lower()
    
    # Legal document classification
    legal_types = {
        'contract': 'Legal-Contract',
        'agreement': 'Legal-Agreement', 
        'compliance': 'Legal-Compliance',
    }
    
    # Financial document classification
    financial_types = {
        'audit': 'Finance-Audit',
        'budget': 'Finance-Budget',
        'financial': 'Finance-Statement',
    }
    
    # HR document classification
    hr_types = {
        'policy': 'HR-Policy',
        'handbook': 'HR-Handbook',
        'training': 'HR-Training',
    }
    
    # Apply classification logic
    classification = 'General-Document'  # Default
    
    # Check department-specific classifications
    if dept in ['legal', 'law']:
        for key, value in legal_types.items():
            if key in doc_type or key in filename_lower:
                classification = value
                break
    elif dept in ['finance', 'fin']:
        for key, value in financial_types.items():
            if key in doc_type or key in filename_lower:
                classification = value
                break
    elif dept in ['hr', 'human resources']:
        for key, value in hr_types.items():
            if key in doc_type or key in filename_lower:
                classification = value
                break
    
    data['document_classification'] = classification
    return data


def _set_retention_policy(data):
    """Set document retention requirements based on classification."""
    
    classification = data.get('document_classification', 'General-Document')
    
    # Retention periods in years
    retention_policies = {
        'Legal-Contract': 7,
        'Legal-Agreement': 7, 
        'Legal-Compliance': 10,
        'Finance-Audit': 7,
        'Finance-Budget': 5,
        'Finance-Statement': 7,
        'HR-Policy': 5,
        'HR-Handbook': 5,
        'HR-Training': 3,
        'General-Document': 3
    }
    
    retention_years = retention_policies.get(classification, 3)
    data['retention_years'] = retention_years
    
    return data


def _determine_confidentiality(data, filename_lower):
    """Determine confidentiality level based on content indicators."""
    
    classification = data.get('document_classification', '')
    
    # Check for explicit confidentiality markers
    if 'confidential' in filename_lower:
        confidentiality = 'CONFIDENTIAL'
    elif 'internal' in filename_lower:
        confidentiality = 'INTERNAL'
    elif 'public' in filename_lower:
        confidentiality = 'PUBLIC'
    else:
        # Default based on document type
        if classification.startswith('Legal-'):
            confidentiality = 'CONFIDENTIAL'
        elif classification.startswith('Finance-'):
            confidentiality = 'RESTRICTED'
        else:
            confidentiality = 'INTERNAL'
    
    data['confidentiality'] = confidentiality
    return data
