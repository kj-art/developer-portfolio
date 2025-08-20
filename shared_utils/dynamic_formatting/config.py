"""
Configuration management for dynamic formatting system.

Provides enterprise-style configuration handling with validation modes,
performance settings, and professional deployment options.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, Union
from pathlib import Path
from enum import Enum


class ValidationMode(Enum):
    """Validation and error handling modes for professional deployment"""
    STRICT = "strict"           # Invalid tokens cause runtime errors (development)
    GRACEFUL = "graceful"       # Invalid tokens fall back to safe defaults (production)
    AUTO_CORRECT = "auto_correct"  # Invalid tokens auto-correct to suggestions (assisted development)


class ValidationLevel(Enum):
    """Minimum validation level to report"""
    ERROR = "error"     # Only report errors
    WARNING = "warning" # Report errors and warnings
    INFO = "info"       # Report everything
    NONE = "none"       # No validation reporting


@dataclass
class FormatterConfig:
    """
    Comprehensive configuration for dynamic formatting with enterprise features
    
    This configuration system enables professional deployment scenarios:
    - Development: strict mode with full validation for catching issues early
    - Production: graceful mode with minimal validation for reliability
    - Assisted Development: auto-correct mode for productivity
    
    Example usage:
        # Development configuration
        dev_config = FormatterConfig(
            validation_mode=ValidationMode.STRICT,
            validation_level=ValidationLevel.INFO,
            enable_performance_monitoring=True
        )
        
        # Production configuration  
        prod_config = FormatterConfig(
            validation_mode=ValidationMode.GRACEFUL,
            validation_level=ValidationLevel.ERROR,
            enable_validation=False
        )
        
        # From JSON config file
        config = FormatterConfig.from_config_file('config.json')
    """
    
    # Core formatting settings
    delimiter: str = ';'                            # Token delimiter character
    output_mode: str = 'console'                    # 'console' or 'file' output mode
    enable_colors: bool = True                      # Enable ANSI color codes
    functions: Dict[str, Callable] = field(default_factory=dict)  # Custom function registry
    
    # Validation and error handling
    validation_mode: ValidationMode = ValidationMode.GRACEFUL    # How to handle invalid tokens
    validation_level: ValidationLevel = ValidationLevel.WARNING  # Minimum level to report
    enable_validation: bool = True                  # Whether to perform validation
    
    # Performance and monitoring
    enable_performance_monitoring: bool = False     # Track performance metrics
    max_recursion_depth: int = 10                   # Maximum template nesting depth
    max_template_sections: int = 100                # Maximum number of template sections
    max_template_length: int = 10000                # Maximum template string length
    
    # Advanced options
    strict_argument_validation: bool = True         # Validate positional/keyword mixing
    auto_correct_suggestions: bool = True           # Enable suggestion system
    cache_parsed_templates: bool = True             # Cache parsed templates for reuse
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        # Convert string enums to proper enum types if needed
        if isinstance(self.validation_mode, str):
            self.validation_mode = ValidationMode(self.validation_mode.lower())
        if isinstance(self.validation_level, str):
            self.validation_level = ValidationLevel(self.validation_level.lower())
        
        # Validate numeric limits
        if self.max_recursion_depth < 1:
            raise ValueError("max_recursion_depth must be at least 1")
        if self.max_template_sections < 1:
            raise ValueError("max_template_sections must be at least 1")
        if self.max_template_length < 1:
            raise ValueError("max_template_length must be at least 1")
        
        # Validate output mode
        if self.output_mode not in ['console', 'file']:
            raise ValueError("output_mode must be 'console' or 'file'")
    
    @classmethod
    def development(cls, **overrides) -> 'FormatterConfig':
        """
        Create development configuration with strict validation
        
        Best for catching issues early during development with full feedback.
        """
        defaults = {
            'validation_mode': ValidationMode.STRICT,
            'validation_level': ValidationLevel.INFO,
            'enable_validation': True,
            'enable_performance_monitoring': True,
            'auto_correct_suggestions': True,
            'strict_argument_validation': True,
        }
        defaults.update(overrides)
        return cls(**defaults)
    
    @classmethod
    def production(cls, **overrides) -> 'FormatterConfig':
        """
        Create production configuration with graceful degradation
        
        Best for production environments where reliability is critical.
        """
        defaults = {
            'validation_mode': ValidationMode.GRACEFUL,
            'validation_level': ValidationLevel.ERROR,
            'enable_validation': False,  # Skip validation in production for performance
            'enable_performance_monitoring': False,
            'auto_correct_suggestions': False,
            'strict_argument_validation': True,
        }
        defaults.update(overrides)
        return cls(**defaults)
    
    @classmethod
    def assisted_development(cls, **overrides) -> 'FormatterConfig':
        """
        Create assisted development configuration with auto-correction
        
        Best for productivity-focused development with automatic fixes.
        """
        defaults = {
            'validation_mode': ValidationMode.AUTO_CORRECT,
            'validation_level': ValidationLevel.WARNING,
            'enable_validation': True,
            'enable_performance_monitoring': True,
            'auto_correct_suggestions': True,
            'strict_argument_validation': False,  # More forgiving
        }
        defaults.update(overrides)
        return cls(**defaults)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'FormatterConfig':
        """
        Create configuration from dictionary (useful for JSON config files)

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            FormatterConfig instance

        Example:
            config_data = {
                "validation_mode": "graceful",
                "validation_level": "warning",
                "enable_colors": True
            }
            config = FormatterConfig.from_dict(config_data)
        """
        # Make a copy to avoid modifying the original
        config_data = config_dict.copy()
        
        # Handle nested formatting structure (some configs wrap everything in "formatting")
        if 'formatting' in config_data and isinstance(config_data['formatting'], dict):
            # Extract the formatting configuration
            config_data = config_data['formatting'].copy()
        
        # Handle nested performance_monitoring configuration
        if 'performance_monitoring' in config_data:
            perf_config = config_data.pop('performance_monitoring')
            if isinstance(perf_config, dict):
                # Map nested performance_monitoring fields to flat config parameters
                if 'enabled' in perf_config:
                    config_data['enable_performance_monitoring'] = perf_config['enabled']
                # Note: Other performance_monitoring fields like memory_tracking,
                # regression_detection, etc. are used by PerformanceMonitor directly,
                # not by FormatterConfig

        # Handle nested function definitions if present
        functions = {}
        if 'functions' in config_data:
            functions_data = config_data.pop('functions')
            if isinstance(functions_data, dict):
                # For now, we can't easily serialize/deserialize actual functions
                # This would typically be handled by a more sophisticated config system
                functions = functions_data

        # Filter out any keys that aren't valid FormatterConfig parameters
        valid_fields = set(cls.__dataclass_fields__.keys())
        filtered_config = {k: v for k, v in config_data.items() if k in valid_fields}

        # Create config without functions first
        config = cls(**filtered_config)
        config.functions = functions
        return config
    
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
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_environment(cls, prefix: str = 'FORMATTER_') -> 'FormatterConfig':
        """
        Load configuration from environment variables
        
        Args:
            prefix: Environment variable prefix (default: 'FORMATTER_')
            
        Returns:
            FormatterConfig instance with values from environment
            
        Example:
            # Set environment variables:
            # FORMATTER_VALIDATION_MODE=graceful
            # FORMATTER_OUTPUT_MODE=file
            config = FormatterConfig.from_environment()
        """
        config_data = {}
        
        # Map environment variables to config fields
        env_mapping = {
            f'{prefix}VALIDATION_MODE': 'validation_mode',
            f'{prefix}VALIDATION_LEVEL': 'validation_level', 
            f'{prefix}ENABLE_VALIDATION': 'enable_validation',
            f'{prefix}OUTPUT_MODE': 'output_mode',
            f'{prefix}ENABLE_COLORS': 'enable_colors',
            f'{prefix}ENABLE_PERFORMANCE_MONITORING': 'enable_performance_monitoring',
            f'{prefix}MAX_RECURSION_DEPTH': 'max_recursion_depth',
            f'{prefix}MAX_TEMPLATE_SECTIONS': 'max_template_sections',
            f'{prefix}MAX_TEMPLATE_LENGTH': 'max_template_length',
            f'{prefix}STRICT_ARGUMENT_VALIDATION': 'strict_argument_validation',
            f'{prefix}AUTO_CORRECT_SUGGESTIONS': 'auto_correct_suggestions',
            f'{prefix}CACHE_PARSED_TEMPLATES': 'cache_parsed_templates',
        }
        
        for env_var, config_field in env_mapping.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Convert string values to appropriate types
                if config_field in ['enable_validation', 'enable_colors', 'enable_performance_monitoring',
                                   'strict_argument_validation', 'auto_correct_suggestions', 
                                   'cache_parsed_templates']:
                    config_data[config_field] = value.lower() in ('true', '1', 'yes', 'on')
                elif config_field in ['max_recursion_depth', 'max_template_sections', 'max_template_length']:
                    config_data[config_field] = int(value)
                else:
                    config_data[config_field] = value
        
        return cls.from_dict(config_data)
    
    def to_dict(self, include_functions: bool = False) -> Dict[str, Any]:
        """
        Convert configuration to dictionary (useful for JSON serialization)
        
        Args:
            include_functions: Whether to include function definitions (default: False)
            
        Returns:
            Dictionary representation of configuration
        """
        result = {}
        
        for field_name, field_def in self.__dataclass_fields__.items():
            value = getattr(self, field_name)
            
            # Convert enums to string values
            if isinstance(value, Enum):
                result[field_name] = value.value
            elif field_name == 'functions' and not include_functions:
                # Skip functions unless explicitly requested
                continue
            else:
                result[field_name] = value
        
        return result
    
    def to_config_file(self, config_path: Union[str, Path], nested: bool = True) -> None:
        """
        Save configuration to JSON file
        
        Args:
            config_path: Path where to save the configuration
            nested: Whether to use nested structure for performance_monitoring
        """
        config_path = Path(config_path)
        
        config_data = self.to_dict(include_functions=False)
        
        if nested and 'enable_performance_monitoring' in config_data:
            # Convert flat performance monitoring to nested structure
            perf_enabled = config_data.pop('enable_performance_monitoring')
            config_data['performance_monitoring'] = {
                'enabled': perf_enabled
            }
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def copy(self, **overrides) -> 'FormatterConfig':
        """
        Create a copy of this configuration with optional overrides
        
        Args:
            **overrides: Configuration fields to override
            
        Returns:
            New FormatterConfig instance
            
        Example:
            dev_config = FormatterConfig.development()
            test_config = dev_config.copy(output_mode='file', enable_colors=False)
        """
        current_config = self.to_dict(include_functions=True)
        current_config.update(overrides)
        return self.__class__.from_dict(current_config)
    
    def is_strict_mode(self) -> bool:
        """Check if validation mode is strict"""
        return self.validation_mode == ValidationMode.STRICT
    
    def is_graceful_mode(self) -> bool:
        """Check if validation mode is graceful"""
        return self.validation_mode == ValidationMode.GRACEFUL
    
    def is_auto_correct_mode(self) -> bool:
        """Check if validation mode is auto-correct"""
        return self.validation_mode == ValidationMode.AUTO_CORRECT
    
    def should_validate(self) -> bool:
        """Check if validation should be performed"""
        return self.enable_validation and self.validation_level != ValidationLevel.NONE


# Convenience factory functions for common configurations
def dev_config(**overrides) -> FormatterConfig:
    """Quick development configuration"""
    return FormatterConfig.development(**overrides)


def prod_config(**overrides) -> FormatterConfig:
    """Quick production configuration"""
    return FormatterConfig.production(**overrides)


def assisted_config(**overrides) -> FormatterConfig:
    """Quick assisted development configuration"""
    return FormatterConfig.assisted_development(**overrides)