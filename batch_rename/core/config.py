"""
Configuration classes for batch rename operations.

Contains RenameConfig for operation parameters and RenameResult for operation results.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Union


@dataclass
class RenameConfig:
    """Configuration for batch rename operations."""
    
    # Required parameters
    input_folder: Union[str, Path]
    
    # Processing configuration - must have one of these
    extractor: Optional[str] = None
    extract_and_convert: Optional[str] = None
    
    # Optional processing steps
    extractor_args: Optional[Dict[str, Any]] = None
    converters: Optional[List[Dict[str, Any]]] = None
    template: Optional[Dict[str, Any]] = None
    filters: Optional[List[Dict[str, Any]]] = None
    
    # Execution options
    recursive: bool = False
    preview_mode: bool = True
    
    # Collision handling
    on_existing_collision: str = 'skip'  # skip, error, append_number
    on_internal_collision: str = 'skip'   # skip, error, append_number
    
    def __post_init__(self):
        """Validate and normalize configuration after creation."""
        # Set defaults for optional parameters
        if self.extractor_args is None:
            self.extractor_args = {}
        if self.converters is None:
            self.converters = []
        if self.filters is None:
            self.filters = []
        
        self._validate()
    
    def _validate(self):
        """Validate configuration consistency."""
        # Validate input folder
        if not self.input_folder:
            raise ValueError("input_folder is required")
        
        # Convert to Path if string
        if isinstance(self.input_folder, str):
            self.input_folder = Path(self.input_folder)
        
        # Must have either extractor or extract_and_convert
        if not self.extractor and not self.extract_and_convert:
            raise ValueError("Must specify either extractor or extract_and_convert")
        
        # Can't have both extractor and extract_and_convert
        if self.extractor and self.extract_and_convert:
            raise ValueError("Cannot specify both extractor and extract_and_convert")
        
        # For extractors, split is special - it can work without converters/templates
        # Other extractors need at least one converter OR template
        if self.extractor and not self.converters and not self.template:
            if self.extractor != "split":
                raise ValueError("When using extractor (except split), must provide at least one converter or template")
        
        # Template validation using dynamic registry
        if self.template:
            template_name = self.template.get('name', '')
            
            # Import built-in templates registry
            try:
                from .built_ins.templates import BUILTIN_TEMPLATES
                valid_builtin_templates = BUILTIN_TEMPLATES.keys()
            except ImportError:
                # Fallback to hardcoded list if import fails
                valid_builtin_templates = ['template', 'stringsmith', 'join']
            
            # Allow built-in templates or custom .py files
            if template_name not in valid_builtin_templates and not template_name.endswith('.py'):
                valid_templates_list = list(valid_builtin_templates)
                raise ValueError(f"Invalid template '{template_name}'. Must be one of {valid_templates_list} or a .py file.")


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
    
    # Backward compatibility field - can be set directly
    files_found: int = 0
    
    @property 
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.files_to_rename == 0:
            return 0.0
        return (self.files_renamed / self.files_to_rename) * 100
    
    @property
    def filtering_efficiency(self) -> float:
        """Calculate filtering efficiency as percentage of files kept."""
        total_files = self.files_found if self.files_found > 0 else self.files_analyzed
        if total_files == 0:
            return 0.0
        return ((total_files - self.files_filtered_out) / total_files) * 100
    
    @property
    def collision_impact(self) -> float:
        """Calculate collision impact as percentage of renames affected."""
        if self.files_to_rename == 0:
            return 0.0
        return (self.collisions / self.files_to_rename) * 100