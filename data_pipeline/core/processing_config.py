# Add to core/config.py or create new core/processing_config.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class IndexMode(Enum):
    """Index handling modes for output data"""
    NONE = 'none'           # No index column in output
    LOCAL = 'local'         # Per-file indices (0,1,2 then 0,1,2)
    SEQUENTIAL = 'sequential'  # Continuous indices across all files (0,1,2,3,4...)
    
    @classmethod
    def from_string(cls, value: str):
        """Create enum from case-insensitive string"""
        if not value:
            return None
        try:
            return cls(value.lower())
        except ValueError:
            valid_options = [e.value for e in cls]
            raise ValueError(f"Invalid index mode: '{value}'. Valid options: {valid_options}")

@dataclass
class ProcessingConfig:
    """
    Configuration object for data processing operations
    
    This centralizes all the options for processing files, making the interface
    cleaner and more maintainable than long parameter lists.
    
    Example:
        config = ProcessingConfig(
            input_folder='data',
            output_file='merged.csv',
            recursive=True,
            columns=['first_name', 'last_name', 'age'],
            force_in_memory=False,
            read_options={'sep': ';', 'encoding': 'utf-8'},
            write_options={'na_rep': 'NULL'}
        )
        processor.run(config)
    """
    
    # Required parameters
    input_folder: str
    
    # Output configuration
    output_file: Optional[str] = None
    
    # File selection
    recursive: bool = False
    file_type_filter: Optional[List[str]] = None
    
    # Schema and normalization
    schema_map: Optional[Dict[str, List[str]]] = None
    to_lower: bool = True
    spaces_to_underscores: bool = True
    
    # Index handling
    index_mode: Optional[IndexMode] = None

    index_start: int = 0
    
    # Processing strategy control
    columns: Optional[List[str]] = None
    force_in_memory: bool = False
    
    # File operation options
    read_options: Dict[str, Any] = field(default_factory=dict)
    write_options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.input_folder:
            raise ValueError("input_folder is required")
        
        # Normalize filetype to list
        if isinstance(self.file_type_filter, str):
            self.file_type_filter = [self.file_type_filter]
        
        # Normalize columns to list if provided as string
        if isinstance(self.columns, str):
            self.columns = [col.strip() for col in self.columns.split(',')]
        
        # Ensure options are dicts
        if not isinstance(self.read_options, dict):
            raise TypeError("read_options must be a dictionary")
        if not isinstance(self.write_options, dict):
            raise TypeError("write_options must be a dictionary")
    
    @classmethod
    def from_cli_args(cls, args, read_kwargs=None, write_kwargs=None):
        """
        Create ProcessingConfig from CLI arguments
        
        Args:
            args: argparse Namespace object
            read_kwargs: Read options from CLI parsing
            write_kwargs: Write options from CLI parsing
            
        Returns:
            ProcessingConfig: Configured processing object
        """
        # Convert string to enum for index_mode
        index_mode_str = getattr(args, 'index_mode', None)
        index_mode = IndexMode.from_string(index_mode_str)
        
        return cls(
            input_folder=args.input_folder,
            output_file=getattr(args, 'output_file', None),
            recursive=getattr(args, 'recursive', False),
            file_type_filter=getattr(args, 'filetype', None),
            schema_map=None,  # Will be loaded separately if args.schema exists
            to_lower=getattr(args, 'to_lower', True),
            spaces_to_underscores=getattr(args, 'spaces_to_underscores', True),
            index_mode=index_mode,
            index_start=getattr(args, 'index_start', None),
            columns=getattr(args, 'columns', None),
            force_in_memory=getattr(args, 'force_in_memory', False),
            read_options=read_kwargs or {},
            write_options=write_kwargs or {}
        )
    
    def with_schema_map(self, schema_map: Dict[str, List[str]]):
        """Return new config with updated schema_map (immutable-style update)"""
        return ProcessingConfig(
            input_folder=self.input_folder,
            output_file=self.output_file,
            recursive=self.recursive,
            file_type_filter=self.file_type_filter,
            schema_map=schema_map,
            to_lower=self.to_lower,
            spaces_to_underscores=self.spaces_to_underscores,
            index_mode=self.index_mode,
            index_start=self.index_start,
            columns=self.columns,
            force_in_memory=self.force_in_memory,
            read_options=self.read_options.copy(),
            write_options=self.write_options.copy()
        )