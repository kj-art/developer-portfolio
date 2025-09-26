"""
Configuration file loader for batch rename operations.

Handles loading and parsing YAML/JSON configuration files into RenameConfig objects.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Union

from ..core.config import RenameConfig


class ConfigLoader:
    """Loads configuration files and converts them to RenameConfig objects."""
    
    @staticmethod
    def load_config_file(config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from YAML or JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dictionary containing configuration data
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is unsupported or contains invalid data
        """
        path = Path(config_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() == '.json':
                    return json.load(f)
                elif path.suffix.lower() in ['.yml', '.yaml']:
                    return yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {path.suffix}")
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {path}: {e}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file {path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading config file {path}: {e}")
    
    @staticmethod
    def config_to_rename_config(config_data: Dict[str, Any], 
                              cli_overrides: Dict[str, Any] = None) -> RenameConfig:
        """
        Convert configuration dictionary to RenameConfig object.
        
        Args:
            config_data: Configuration dictionary from file
            cli_overrides: Optional CLI arguments to override config values
            
        Returns:
            RenameConfig object ready for processing
        """
        # Extract settings section
        settings = config_data.get('settings', {})
        pipeline = config_data.get('pipeline', {})
        collision_handling = config_data.get('collision_handling', {})
        
        # Build extractor configuration
        extractor_config = pipeline.get('extractor', {})
        extractor_name = extractor_config.get('name')
        extractor_args = {
            'positional': extractor_config.get('args', []),
            'keyword': extractor_config.get('kwargs', {})
        }
        
        # Build converters list
        converters = []
        for conv_config in pipeline.get('converters', []):
            converters.append({
                'name': conv_config.get('name'),
                'positional': conv_config.get('args', []),
                'keyword': conv_config.get('kwargs', {})
            })
        
        # Build template configuration
        template = None
        template_config = pipeline.get('template')
        if template_config:
            template = {
                'name': template_config.get('name'),
                'positional': template_config.get('args', []),
                'keyword': template_config.get('kwargs', {})
            }
        
        # Build filters list
        filters = []
        for filter_config in pipeline.get('filters', []):
            # Handle filter inversion (names starting with !)
            filter_name = filter_config.get('name', '')
            inverted = filter_name.startswith('!')
            if inverted:
                filter_name = filter_name[1:]  # Remove ! prefix
            
            filters.append({
                'name': filter_name,
                'positional': filter_config.get('args', []),
                'keyword': filter_config.get('kwargs', {}),
                'inverted': inverted
            })
        
        # Create base configuration from config file
        config = RenameConfig(
            input_folder=settings.get('input_folder'),
            extractor=extractor_name,
            extractor_args=extractor_args,
            converters=converters,
            template=template,
            filters=filters,
            recursive=settings.get('recursive', False),
            preview_mode=settings.get('preview_mode', True),
            on_existing_collision=collision_handling.get('on_existing_collision', 'skip'),
            on_internal_collision=collision_handling.get('on_internal_collision', 'skip')
        )
        
        # Apply CLI overrides if provided
        if cli_overrides:
            # Override specific fields if provided in CLI
            if 'input_folder' in cli_overrides and cli_overrides['input_folder']:
                config.input_folder = cli_overrides['input_folder']
            if 'recursive' in cli_overrides:
                config.recursive = cli_overrides['recursive']
            if 'preview_mode' in cli_overrides:
                config.preview_mode = cli_overrides['preview_mode']
            if 'execute' in cli_overrides and cli_overrides['execute']:
                config.preview_mode = False
        
        return config
    
    @classmethod
    def load_rename_config(cls, config_path: Union[str, Path], 
                         cli_overrides: Dict[str, Any] = None) -> RenameConfig:
        """
        Load RenameConfig directly from file with optional CLI overrides.
        
        Args:
            config_path: Path to configuration file
            cli_overrides: Optional CLI arguments to override config values
            
        Returns:
            RenameConfig object ready for processing
        """
        config_data = cls.load_config_file(config_path)
        return cls.config_to_rename_config(config_data, cli_overrides)