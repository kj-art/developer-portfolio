"""
Configuration management for dynamic formatting with professional deployment support.

This module provides comprehensive configuration options for different deployment
scenarios, from development to production, with proper validation and environment
variable integration.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Callable, Optional, Union


class ValidationMode(Enum):
    """Validation modes for error handling"""
    STRICT = "strict"      # Raise errors for any issues
    GRACEFUL = "graceful"  # Handle errors gracefully, continue processing
    AUTO_CORRECT = "auto_correct"  # Try to auto-correct minor issues


class ValidationLevel(Enum):
    """Validation strictness levels"""
    ERROR = "error"      # Only show critical errors
    WARNING = "warning"  # Show warnings and errors
    INFO = "info"        # Show all validation messages


@dataclass
class FormatterConfig:
    """
    Comprehensive configuration for dynamic formatting with professional features
    
    Supports different deployment scenarios with appropriate defaults for
    development, testing, and production environments.
    """
    # Core formatting options
    delimiter: str = ';'
    output_mode: str = 'console'  # 'console' or 'file'
    enable_colors: bool = True
    
    # Validation and error handling
    validation_mode: ValidationMode = ValidationMode.GRACEFUL
    validation_level: ValidationLevel = ValidationLevel.WARNING
    enable_validation: bool = True
    strict_argument_validation: bool = True
    
    # Performance options
    cache_parsed_templates: bool = True
    max_template_sections: int = 100
    enable_performance_monitoring: bool = False
    
    # Function registry
    functions: Dict[str, Callable] = field(default_factory=dict)
    
    # Advanced options
    auto_correct_suggestions: bool = True
    enable_function_fallback: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        # Ensure enums are properly set
        if isinstance(self.validation_mode, str):
            self.validation_mode = ValidationMode(self.validation_mode)
        if isinstance(self.validation_level, str):
            self.validation_level = ValidationLevel(self.validation_level)
        
        # Ensure functions is a dict
        if self.functions is None:
            self.functions = {}
    
    @classmethod
    def from_config_file(cls, config_path: Union[str, Path]) -> 'FormatterConfig':
        """
        Load configuration from JSON file
        
        Args:
            config_path: Path to JSON configuration file
            
        Returns:
            FormatterConfig instance
            
        Example:
            config = FormatterConfig.from_config_file('configs/production.json')
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file {config_path}: {e}")
        
        return cls.from_config_dict(config_data)
    
    def to_config_file(self, config_path: Union[str, Path], nested: bool = False) -> None:
        """
        Save configuration to JSON file
        
        Args:
            config_path: Path to save configuration file
            nested: Whether to use nested structure for the JSON
        """
        config_path = Path(config_path)
        config_data = self.to_dict()
        
        if nested:
            # Create nested structure
            nested_data = {
                'formatting': {
                    'delimiter': config_data['delimiter'],
                    'output_mode': config_data['output_mode'],
                    'enable_colors': config_data['enable_colors']
                },
                'validation': {
                    'mode': config_data['validation_mode'],
                    'level': config_data['validation_level'],
                    'enable_validation': config_data['enable_validation'],
                    'strict_argument_validation': config_data['strict_argument_validation']
                },
                'performance': {
                    'cache_parsed_templates': config_data['cache_parsed_templates'],
                    'max_template_sections': config_data['max_template_sections'],
                    'enable_performance_monitoring': config_data['enable_performance_monitoring']
                },
                'advanced': {
                    'auto_correct_suggestions': config_data['auto_correct_suggestions'],
                    'enable_function_fallback': config_data['enable_function_fallback']
                }
            }
            config_data = nested_data
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
    
    @classmethod
    def from_config_dict(cls, config_dict: Dict[str, Any]) -> 'FormatterConfig':
        """
        Create configuration from dictionary
        
        Args:
            config_dict: Dictionary with configuration values
            
        Returns:
            FormatterConfig instance
        """
        # Handle nested configuration structure
        if 'formatting' in config_dict:
            # Flatten nested structure
            flat_dict = {}
            for section, values in config_dict.items():
                if isinstance(values, dict):
                    flat_dict.update(values)
                else:
                    flat_dict[section] = values
            config_dict = flat_dict
        
        # Convert string values to enums
        processed_dict = {}
        for key, value in config_dict.items():
            if key == 'validation_mode' and isinstance(value, str):
                processed_dict[key] = ValidationMode(value)
            elif key == 'validation_level' and isinstance(value, str):
                processed_dict[key] = ValidationLevel(value)
            else:
                processed_dict[key] = value
        
        return cls(**processed_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        config_dict = asdict(self)
        
        # Convert enums to strings for JSON serialization
        config_dict['validation_mode'] = self.validation_mode.value
        config_dict['validation_level'] = self.validation_level.value
        
        return config_dict
    
    @classmethod
    def from_environment(cls, prefix: str = 'FORMATTER_') -> 'FormatterConfig':
        """
        Load configuration from environment variables
        
        Args:
            prefix: Prefix for environment variables
            
        Returns:
            FormatterConfig instance loaded from environment
            
        Example:
            # Set environment variables:
            # FORMATTER_VALIDATION_MODE=graceful
            # FORMATTER_OUTPUT_MODE=file
            
            config = FormatterConfig.from_environment()
        """
        config_dict = {}
        
        # Map of environment variable names to config keys
        env_mapping = {
            f'{prefix}DELIMITER': 'delimiter',
            f'{prefix}OUTPUT_MODE': 'output_mode',
            f'{prefix}ENABLE_COLORS': 'enable_colors',
            f'{prefix}VALIDATION_MODE': 'validation_mode',
            f'{prefix}VALIDATION_LEVEL': 'validation_level',
            f'{prefix}ENABLE_VALIDATION': 'enable_validation',
            f'{prefix}STRICT_ARGUMENT_VALIDATION': 'strict_argument_validation',
            f'{prefix}CACHE_PARSED_TEMPLATES': 'cache_parsed_templates',
            f'{prefix}MAX_TEMPLATE_SECTIONS': 'max_template_sections',
            f'{prefix}ENABLE_PERFORMANCE_MONITORING': 'enable_performance_monitoring',
            f'{prefix}AUTO_CORRECT_SUGGESTIONS': 'auto_correct_suggestions',
            f'{prefix}ENABLE_FUNCTION_FALLBACK': 'enable_function_fallback',
        }
        
        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key in ['enable_colors', 'enable_validation', 'strict_argument_validation',
                                'cache_parsed_templates', 'enable_performance_monitoring',
                                'auto_correct_suggestions', 'enable_function_fallback']:
                    config_dict[config_key] = value.lower() in ('true', '1', 'yes', 'on')
                elif config_key == 'max_template_sections':
                    config_dict[config_key] = int(value)
                elif config_key == 'validation_mode':
                    config_dict[config_key] = ValidationMode(value)
                elif config_key == 'validation_level':
                    config_dict[config_key] = ValidationLevel(value)
                else:
                    config_dict[config_key] = value
        
        return cls(**config_dict)
    
    @classmethod
    def development(cls, **overrides) -> 'FormatterConfig':
        """Create configuration optimized for development"""
        base_config = {
            'validation_mode': ValidationMode.STRICT,
            'validation_level': ValidationLevel.INFO,
            'enable_validation': True,
            'auto_correct_suggestions': True,
            'cache_parsed_templates': False,  # Disable caching for development
            'enable_performance_monitoring': True,
        }
        base_config.update(overrides)
        return cls(**base_config)
    
    @classmethod
    def production(cls, **overrides) -> 'FormatterConfig':
        """Create configuration optimized for production"""
        base_config = {
            'validation_mode': ValidationMode.GRACEFUL,
            'validation_level': ValidationLevel.ERROR,
            'enable_validation': False,  # Disable validation in production for performance
            'auto_correct_suggestions': False,
            'cache_parsed_templates': True,
            'strict_argument_validation': False,  # More lenient in production
            'enable_performance_monitoring': False,  # Can be enabled if needed
        }
        base_config.update(overrides)
        return cls(**base_config)
    
    @classmethod
    def testing(cls, **overrides) -> 'FormatterConfig':
        """Create configuration optimized for testing"""
        base_config = {
            'validation_mode': ValidationMode.STRICT,
            'validation_level': ValidationLevel.WARNING,
            'enable_validation': True,
            'auto_correct_suggestions': False,
            'cache_parsed_templates': False,
            'enable_performance_monitoring': False,
        }
        base_config.update(overrides)
        return cls(**base_config)
    
    def is_strict_mode(self) -> bool:
        """Check if running in strict validation mode"""
        return self.validation_mode == ValidationMode.STRICT
    
    def is_graceful_mode(self) -> bool:
        """Check if running in graceful degradation mode"""
        return self.validation_mode == ValidationMode.GRACEFUL
    
    def should_validate(self) -> bool:
        """Check if validation is enabled"""
        return self.enable_validation
    
    def should_cache_templates(self) -> bool:
        """Check if template caching is enabled"""
        return self.cache_parsed_templates
    
    def copy(self, **overrides) -> 'FormatterConfig':
        """Create a copy of this config with optional overrides"""
        config_dict = asdict(self)
        config_dict.update(overrides)
        return FormatterConfig(**config_dict)


# Predefined configuration templates for common scenarios
def create_development_config(**overrides) -> FormatterConfig:
    """Create configuration optimized for development"""
    return FormatterConfig.development(**overrides)


def create_production_config(**overrides) -> FormatterConfig:
    """Create configuration optimized for production"""
    return FormatterConfig.production(**overrides)


def create_testing_config(**overrides) -> FormatterConfig:
    """Create configuration optimized for testing"""
    return FormatterConfig.testing(**overrides)