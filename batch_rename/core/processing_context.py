"""
Processing Context Data Class for Batch Rename Tool

Encapsulates all automatic arguments passed by the processor to custom functions.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class ProcessingContext:
    """
    Context object containing all automatic arguments for custom functions.
    
    This replaces the multiple separate arguments (filename, file_path, metadata, extracted_data)
    with a single consistent parameter across all function types.
    """
    filename: str
    file_path: Path
    metadata: Dict[str, Any]
    extracted_data: Optional[Dict[str, Any]] = None
    
    @property
    def base_name(self) -> str:
        """Get filename without extension."""
        return self.file_path.stem
    
    @property
    def extension(self) -> str:
        """Get file extension."""
        return self.file_path.suffix
    
    @property
    def file_size(self) -> int:
        """Get file size in bytes."""
        return self.metadata.get('size', 0)
    
    @property
    def created_timestamp(self) -> float:
        """Get creation timestamp."""
        return self.metadata.get('created', 0)
    
    @property
    def modified_timestamp(self) -> float:
        """Get modification timestamp."""
        return self.metadata.get('modified', 0)
    
    def has_extracted_data(self) -> bool:
        """Check if extracted data is available and non-empty."""
        return self.extracted_data is not None and bool(self.extracted_data)
    
    def get_extracted_field(self, field_name: str, default: Any = None) -> Any:
        """Safely get a field from extracted data."""
        if self.extracted_data is None:
            return default
        return self.extracted_data.get(field_name, default)