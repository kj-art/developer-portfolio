"""
Configuration management for dynamic formatting system.

Provides enterprise-style configuration handling with validation modes,
performance settings, and professional deployment options.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable
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
            enable_colors=True,
            enable_performance_monitoring=False
        )
        
        # Create formatter with config
        formatter = DynamicFormatter(template, config=dev_config)
    """
    
    # Core formatting behavior
    output_mode: str = "console"                    # 'console' or 'file'
    delimiter: str = ";"                            # Template delimiter character
    enable_colors: bool = True                      # Enable color formatting
    enable_function_fallback: bool = True           # Enable function fallback system
    
    # Validation and error handling
    validation_mode: ValidationMode = ValidationMode.GRACEFUL    # How to handle invalid tokens
    validation_level: ValidationLevel = ValidationLevel.WARNING  # What to report
    enable_validation: bool = True                  # Enable template validation
    
    # Performance and monitoring
    max_recursion_depth: int = 5                    # Function fallback recursion limit
    enable_performance_monitoring: bool = False     # Track performance metrics
    max_template_sections: int = 200                # Warning threshold for large templates
    max_template_length: int = 2000                 # Warning threshold for long templates
    
    # Function registry
    functions: Dict[str, Callable] = field(default_factory=dict)  # Available functions
    
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
        Create configuration from dictionary (useful for JSON/YAML config files)
        
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
        # Handle nested function definitions if present
        if 'functions' in config_dict and isinstance(config_dict['functions'], dict):
            # Functions can't be serialized easily, so this is mainly for other config
            functions = config_dict.pop('functions')
        else:
            functions = {}
        
        # Create config without functions first
        config = cls(**config_dict)
        config.functions = functions
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary (useful for saving to JSON/YAML)
        
        Note: Functions are not included in the output as they can't be serialized.
        """
        result = {}
        for key, value in self.__dict__.items():
            if key == 'functions':
                # Skip functions as they can't be serialized
                continue
            elif isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result
    
    def copy(self, **overrides) -> 'FormatterConfig':
        """
        Create a copy of this configuration with optional overrides
        
        Args:
            **overrides: Configuration values to override
            
        Returns:
            New FormatterConfig instance
        """
        current_dict = self.to_dict()
        current_dict['functions'] = self.functions.copy()
        current_dict.update(overrides)
        return FormatterConfig.from_dict(current_dict)
    
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