"""
Configuration classes for batch rename operations.

Handles validation and storage of rename operation parameters.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class RenameConfig:
    """Configuration for a batch rename operation."""
    
    # Input/output
    input_folder: Path
    
    # Extraction configuration
    extractor: Optional[str] = None
    extractor_args: Dict[str, Any] = None
    
    # Conversion configuration (list of converters)
    converters: List[Dict[str, Any]] = None
    
    # Template configuration (separate from converters, optional, max one)
    template: Optional[Dict[str, Any]] = None
    
    # Combined extraction/conversion
    extract_and_convert: Optional[str] = None
    
    # Filtering (list of filters)
    filters: List[Dict[str, Any]] = None
    
    # Processing options
    recursive: bool = False
    preview_mode: bool = True
    
    # Collision handling
    on_existing_collision: str = 'skip'
    on_internal_collision: str = 'error'
    
    def __post_init__(self):
        """Initialize default values and validate configuration."""
        if self.extractor_args is None:
            self.extractor_args = {}
        if self.converters is None:
            self.converters = []
        if self.filters is None:
            self.filters = []
        
        self._validate()
    
    def _validate(self):
        """Validate configuration consistency."""
        # Must have either extractor or extract_and_convert
        if not self.extractor and not self.extract_and_convert:
            raise ValueError("Must specify either --extractor or --extract-and-convert")
        
        # Can't have both extractor and extract_and_convert
        if self.extractor and self.extract_and_convert:
            raise ValueError("Cannot specify both --extractor and --extract-and-convert")
        
        # If using separate extractor, need at least one converter OR template
        if self.extractor and not self.converters and not self.template:
            raise ValueError("When using --extractor, must provide at least one --converter or --template")
        
        # Template validation: only template and stringsmith are allowed as templates
        if self.template:
            template_name = self.template.get('name', '')
            if template_name not in ['template', 'stringsmith']:
                raise ValueError(f"Invalid template type '{template_name}'. Only 'template' and 'stringsmith' are allowed as templates.")


@dataclass
class RenameResult:
    """Results from a batch rename operation."""
    
    # Analysis results
    files_analyzed: int = 0
    files_to_rename: int = 0
    files_filtered_out: int = 0
    
    # Execution results  
    files_renamed: int = 0
    errors: int = 0
    
    # Collision information
    collisions: int = 0
    existing_file_collisions: List[Dict] = field(default_factory=list)
    internal_collisions: List[Dict] = field(default_factory=list)
    
    # Operation details
    processing_time: float = 0.0
    preview_data: List[Dict] = field(default_factory=list)  # For showing rename preview
    error_details: List[Dict] = field(default_factory=list)  # For detailed error information


@dataclass
class ProcessingContext:
    """
    Context object containing all data for processing functions.
    
    This encapsulates file information and extracted data for use by
    extractors, converters, and filters.
    """
    filename: str
    file_path: Path
    metadata: Dict[str, Any]
    extracted_data: Dict[str, Any] = None
    
    @property
    def base_name(self) -> str:
        """Return filename without extension."""
        return self.file_path.stem
    
    @property
    def extension(self) -> str:
        """Return file extension including the dot."""
        return self.file_path.suffix
    
    def has_extracted_data(self) -> bool:
        """Check if extraction has been performed and has data."""
        return self.extracted_data is not None and len(self.extracted_data) > 0
    
    def get_extracted_field(self, field_name: str, default: Any = None) -> Any:
        """Get a specific field from extracted data."""
        if not self.has_extracted_data():
            return default
        return self.extracted_data.get(field_name, default)