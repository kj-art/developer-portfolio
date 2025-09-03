# Add to core/config.py or create new core/processing_config.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

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
            read_options={'sep': ';', 'encoding': 'utf-8'},
            write_options={'na_rep': 'NULL'}
        )
        processor.process_folder_streaming(config)
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
    
    # File operation options
    read_options: Dict[str, Any] = field(default_factory=dict)
    write_options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.input_folder:
            raise ValueError("input_folder is required")
        
        # Normalize file_type_filter to list
        if isinstance(self.file_type_filter, str):
            self.file_type_filter = [self.file_type_filter]
        
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
        return cls(
            input_folder=args.input_folder,
            output_file=getattr(args, 'output_file', None),
            recursive=getattr(args, 'recursive', False),
            file_type_filter=getattr(args, 'filetype', None),
            schema_map=None,  # Will be loaded separately if args.schema exists
            to_lower=getattr(args, 'to_lower', True),
            spaces_to_underscores=getattr(args, 'spaces_to_underscores', True),
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
            read_options=self.read_options.copy(),
            write_options=self.write_options.copy()
        )