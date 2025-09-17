"""
Built-in extractors for parsing filenames and extracting data fields.

Extractors take filenames and return dictionaries of extracted data.
"""

import re
from pathlib import Path
from typing import Dict, Any, Callable

from .function_loader import load_custom_function


"""
Built-in extractors for parsing filenames and extracting data fields.

Extractors take filenames and return dictionaries of extracted data.
"""

import re
from pathlib import Path
from typing import Dict, Any, Callable, List

from .function_loader import load_custom_function


def split_extractor(filename: str, file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Split filename on delimiter and map to field names.
    
    Positional args: [delimiter, field1, field2, field3, ...]
    Keyword args: split_on=delimiter, fields=field1,field2,field3
    
    Examples:
        split,_,dept,type,date  → delimiter="_", fields=["dept", "type", "date"]
        split,split_on=_,fields=dept,type,date  → same result
    """
    # Handle positional arguments
    if positional_args:
        split_on = positional_args[0] if len(positional_args) > 0 else '_'
        field_names = positional_args[1:] if len(positional_args) > 1 else []
    else:
        # Handle keyword arguments (legacy support)
        split_on = kwargs.get('split_on', '_')
        fields_str = kwargs.get('fields', '')
        field_names = [f.strip() for f in fields_str.split(',')] if fields_str else []
    
    if not field_names:
        raise ValueError("split extractor requires field names (either as positional args or 'fields' keyword)")
    
    # Remove extension and split
    base_name = Path(filename).stem
    parts = base_name.split(split_on)
    
    # Map parts to field names
    result = {}
    for i, field_name in enumerate(field_names):
        if field_name == '_':
            # Skip this position
            continue
        if i < len(parts):
            result[field_name] = parts[i]
        else:
            result[field_name] = None
    
    return result


def regex_extractor(filename: str, file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Extract data using named regex groups.
    
    Positional args: [pattern]
    Keyword args: pattern=regex_pattern
    
    Examples:
        regex,"(?P<dept>\\w+)_(?P<type>\\w+)_(?P<date>\\d{8})"
        regex,pattern="(?P<dept>\\w+)_(?P<type>\\w+)_(?P<date>\\d{8})"
    """
    # Handle positional arguments
    if positional_args:
        pattern = positional_args[0]
    else:
        # Handle keyword arguments
        pattern = kwargs.get('pattern')
    
    if not pattern:
        raise ValueError("regex extractor requires pattern (either as positional arg or 'pattern' keyword)")
    
    base_name = Path(filename).stem
    match = re.search(pattern, base_name)
    
    if match:
        return match.groupdict()
    else:
        return {}


def position_extractor(filename: str, file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Extract data by character positions.
    
    Positional args: [position_mappings] where mappings are like "0-2:dept,3-5:code"
    Keyword args: positions=position_mappings
    
    Examples:
        position,"0-2:dept,2-5:code,5-:type"
        position,positions="0-2:dept,2-5:code,5-:type"
    """
    # Handle positional arguments
    if positional_args:
        positions_str = positional_args[0]
    else:
        # Handle keyword arguments
        positions_str = kwargs.get('positions')
    
    if not positions_str:
        raise ValueError("position extractor requires position mappings")
    
    base_name = Path(filename).stem
    result = {}
    
    for mapping in positions_str.split(','):
        pos_part, field_name = mapping.split(':')
        
        if '-' in pos_part:
            start_str, end_str = pos_part.split('-')
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else len(base_name)
        else:
            start = int(pos_part)
            end = start + 1
        
        if start < len(base_name):
            result[field_name] = base_name[start:end]
        else:
            result[field_name] = None
    
    return result


def metadata_extractor(filename: str, file_path: Path, metadata: Dict[str, Any], positional_args: List[str], **kwargs) -> Dict[str, Any]:
    """
    Extract data from file metadata.
    
    Positional args: [field_mappings] like "created_date,modified_date,file_size"
    Keyword args: created_date=field_name, modified_date=field_name, etc.
    
    Examples:
        metadata,created,modified,size  → maps to created_date, modified_date, file_size
        metadata,created_date=created,modified_date=modified
    """
    result = {}
    
    # Handle positional arguments
    if positional_args:
        # Map positional args to standard metadata fields
        standard_fields = ['created_date', 'modified_date', 'file_size']
        for i, field_name in enumerate(positional_args):
            if i < len(standard_fields):
                kwargs[standard_fields[i]] = field_name
    
    # Process metadata extraction
    if kwargs.get('created_date'):
        import datetime
        created_dt = datetime.datetime.fromtimestamp(metadata['created'])
        result[kwargs['created_date']] = created_dt.strftime('%Y-%m-%d')
    
    if kwargs.get('modified_date'):
        import datetime
        modified_dt = datetime.datetime.fromtimestamp(metadata['modified'])
        result[kwargs['modified_date']] = modified_dt.strftime('%Y-%m-%d')
    
    if kwargs.get('file_size'):
        result[kwargs['file_size']] = metadata['size']
    
    return result


# Registry of built-in extractors
BUILTIN_EXTRACTORS = {
    'split': split_extractor,
    'regex': regex_extractor,
    'position': position_extractor,
    'metadata': metadata_extractor,
}


def get_extractor(extractor_name: str, extractor_args: Dict[str, Any]) -> Callable:
    """
    Get extractor function (built-in or custom).
    
    Args:
        extractor_name: Name of built-in extractor or path to custom function
        extractor_args: Dict with 'positional' and 'keyword' args
        
    Returns:
        Extractor function ready to call
    """
    if extractor_name in BUILTIN_EXTRACTORS:
        # Built-in extractor
        extractor_func = BUILTIN_EXTRACTORS[extractor_name]
        
        # Combine positional and keyword args
        pos_args = extractor_args.get('positional', [])
        kwargs = extractor_args.get('keyword', {})
        
        def configured_extractor(filename: str, file_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
            return extractor_func(filename, file_path, metadata, pos_args, **kwargs)
        
        return configured_extractor
    
    elif Path(extractor_name).suffix == '.py':
        # Custom extractor function
        return load_custom_function(extractor_name, 'extract_data')
    
    else:
        raise ValueError(f"Unknown extractor: {extractor_name}")