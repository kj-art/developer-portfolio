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
        
        # Handle nested configuration structure
        if 'formatting' in config_data:
            # Flatten nested structure
            flat_config = {}
            for key, value in config_data.items():
                if isinstance(value, dict):
                    flat_config.update(value)
                else:
                    flat_config[key] = value
            config_data = flat_config
        
        # Convert string enums back to enum instances
        if 'validation_mode' in config_data:
            config_data['validation_mode'] = ValidationMode(config_data['validation_mode'])
        if 'validation_level' in config_data:
            config_data['validation_level'] = ValidationLevel(config_data['validation_level'])
        
        # Functions can't be serialized, so they're not loaded from config files
        config_data.pop('functions', None)
        
        # Handle unknown fields gracefully by filtering them out
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_config = {k: v for k, v in config_data.items() if k in valid_fields}
        
        return cls(**filtered_config)
    
    def to_config_file(self, config_path: Union[str, Path], nested: bool = False) -> None:
        """
        Save configuration to JSON file
        
        Args:
            config_path: Path to write JSON configuration file
            nested: Whether to use nested structure
        """
        config_path = Path(config_path)
        
        # Convert config to dictionary
        config_dict = asdict(self)
        
        # Convert enums to string values
        config_dict['validation_mode'] = self.validation_mode.value
        config_dict['validation_level'] = self.validation_level.value
        
        # Remove functions (can't be serialized)
        config_dict.pop('functions', None)
        
        if nested:
            # Create nested structure
            nested_config = {
                'formatting': {
                    'delimiter': config_dict.pop('delimiter'),
                    'output_mode': config_dict.pop('output_mode'),
                    'enable_colors': config_dict.pop('enable_colors'),
                }
            }
            # Add remaining fields at top level
            nested_config.update(config_dict)
            config_dict = nested_config
        
        # Write to file
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def from_environment(cls, prefix: str = "FORMATTER") -> 'FormatterConfig':
        """
        Load configuration from environment variables
        
        Args:
            prefix: Environment variable prefix (default: FORMATTER)
            
        Returns:
            FormatterConfig instance
            
        Environment variables:
            {PREFIX}_VALIDATION_MODE: strict, graceful, auto_correct
            {PREFIX}_OUTPUT_MODE: console, file
            {PREFIX}_ENABLE_COLORS: true, false
            etc.
        """
        config_dict = {}
        
        # Map environment variables to config fields
        env_mappings = {
            f"{prefix}_DELIMITER": 'delimiter',
            f"{prefix}_OUTPUT_MODE": 'output_mode',
            f"{prefix}_ENABLE_COLORS": 'enable_colors',
            f"{prefix}_VALIDATION_MODE": 'validation_mode',
            f"{prefix}_VALIDATION_LEVEL": 'validation_level',
            f"{prefix}_ENABLE_VALIDATION": 'enable_validation',
            f"{prefix}_STRICT_ARGUMENT_VALIDATION": 'strict_argument_validation',
            f"{prefix}_CACHE_PARSED_TEMPLATES": 'cache_parsed_templates',
            f"{prefix}_MAX_TEMPLATE_SECTIONS": 'max_template_sections',
            f"{prefix}_AUTO_CORRECT_SUGGESTIONS": 'auto_correct_suggestions',
            f"{prefix}_ENABLE_FUNCTION_FALLBACK": 'enable_function_fallback',
            f"{prefix}_ENABLE_PERFORMANCE_MONITORING": 'enable_performance_monitoring',
        }
        
        for env_var, config_key in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Type conversion
                if config_key in ['enable_colors', 'enable_validation', 'strict_argument_validation',
                                'cache_parsed_templates', 'auto_correct_suggestions', 'enable_function_fallback',
                                'enable_performance_monitoring']:
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
        return cls(
            validation_mode=ValidationMode.STRICT,
            validation_level=ValidationLevel.INFO,
            enable_validation=True,
            auto_correct_suggestions=True,
            cache_parsed_templates=False,  # Disable caching for development
            enable_performance_monitoring=True,
            **overrides
        )
    
    @classmethod
    def production(cls, **overrides) -> 'FormatterConfig':
        """Create configuration optimized for production"""
        return cls(
            validation_mode=ValidationMode.GRACEFUL,
            validation_level=ValidationLevel.ERROR,
            enable_validation=True,
            auto_correct_suggestions=False,
            cache_parsed_templates=True,
            strict_argument_validation=False,  # More lenient in production
            enable_performance_monitoring=False,  # Can be enabled if needed
            **overrides
        )
    
    @classmethod
    def testing(cls, **overrides) -> 'FormatterConfig':
        """Create configuration optimized for testing"""
        return cls(
            validation_mode=ValidationMode.STRICT,
            validation_level=ValidationLevel.WARNING,
            enable_validation=True,
            auto_correct_suggestions=False,
            cache_parsed_templates=False,
            enable_performance_monitoring=False,
            **overrides
        )
    
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