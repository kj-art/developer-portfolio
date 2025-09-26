"""
Abstract base class for all processing steps in the batch rename pipeline.

Defines the common interface and behavior for extractors, converters, filters, and templates.
Enables consistent GUI panel generation and pipeline management.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass
from pathlib import Path

from ..processing_context import ProcessingContext
from ..validators import ValidationResult


class StepType(Enum):
    """Types of processing steps in the rename pipeline."""
    FILTER = "filter"
    EXTRACTOR = "extractor"
    CONVERTER = "converter" 
    TEMPLATE = "template"
    ALLINONE = "allinone"


# Cache the list for O(1) execution order lookup
_STEP_ORDER_LIST = list(StepType)


@dataclass
class StepConfig:
    """Configuration for a processing step instance."""
    name: str  # Function name or built-in identifier
    positional_args: List[Any]
    keyword_args: Dict[str, Any]
    custom_function_path: Optional[str] = None  # Path to .py file if custom


class ProcessingStep(ABC):
    """
    Abstract base class for all processing steps.
    
    Each step type (extractor, converter, filter, template) inherits from this
    and implements the abstract methods to define their specific behavior.
    
    Key responsibilities:
    - Define step metadata (type, stackability, help text)
    - Validate custom functions for this step type
    - Create executable functions from configuration
    - Provide GUI generation hints
    """
    
    @property
    @abstractmethod
    def step_type(self) -> StepType:
        """Return the type of this processing step."""
        pass
    
    @property
    @abstractmethod
    def is_stackable(self) -> bool:
        """Return whether multiple instances of this step can be chained."""
        pass
    
    @property
    @abstractmethod
    def builtin_functions(self) -> Dict[str, Callable]:
        """Return dict of available built-in functions for this step type."""
        pass
    
    @abstractmethod
    def get_help_text(self) -> str:
        """Return help text describing this step and its built-in functions."""
        pass
    
    @abstractmethod
    def validate_custom_function(self, function: Callable) -> ValidationResult:
        """
        Validate that a custom function meets requirements for this step type.
        
        Args:
            function: The custom function to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        pass
    
    def create_executable(self, config: StepConfig) -> Callable:
        """
        Create an executable function from step configuration.
        
        Args:
            config: Step configuration with function name and arguments
            
        Returns:
            Callable that takes ProcessingContext and returns appropriate result
            
        Raises:
            ValueError: If configuration is invalid or function not found
        """
        if config.name in self.builtin_functions:
            return self._wrap_builtin_function(config)
        elif Path(config.name).suffix == '.py':
            return self._wrap_custom_function(config)
        else:
            raise ValueError(f"Unknown {self.step_type.value}: {config.name}")
    
    def _wrap_builtin_function(self, config: StepConfig) -> Callable:
        """Wrap a built-in function with configuration."""
        builtin_func = self.builtin_functions[config.name]
        
        def configured_builtin(context: ProcessingContext):
            return builtin_func(context, config.positional_args, **config.keyword_args)
        
        return configured_builtin
    
    def _wrap_custom_function(self, config: StepConfig) -> Callable:
        """Load and wrap a custom function with configuration."""
        from ..function_loader import load_custom_function
        
        if not config.positional_args:
            raise ValueError(f"Custom {self.step_type.value} requires function name as first argument")
        
        function_name = config.positional_args[0]
        custom_func = load_custom_function(config.name, function_name)
        
        # Validate the custom function
        validation = self.validate_custom_function(custom_func)
        if not validation.valid:
            raise ValueError(f"Invalid custom {self.step_type.value}: {validation.message}")
        
        # Get additional arguments (excluding function name)
        additional_args = config.positional_args[1:]
        
        def configured_custom(context: ProcessingContext):
            return custom_func(context, *additional_args, **config.keyword_args)
        
        return configured_custom
    
    def get_gui_hints(self) -> Dict[str, Any]:
        """
        Return hints for GUI panel generation.
        
        Override in subclasses to provide step-specific GUI configuration.
        
        Returns:
            Dict containing GUI generation hints:
            - panel_title: Display title for the panel
            - supports_custom: Whether custom functions are supported
            - add_remove_buttons: Whether to show add/remove for stacking
            - validation_style: How to display validation results
        """
        return {
            'panel_title': f"{self.step_type.value.title()} Configuration",
            'supports_custom': True,
            'add_remove_buttons': self.is_stackable,
            'validation_style': 'expandable'  # or 'inline', 'tooltip'
        }
    

    
    def get_execution_order(self) -> int:
        """
        Return the execution order for this step type in the pipeline.
        
        Lower numbers execute first. Order determined by StepType enum definition order.
        
        Returns:
            Integer representing execution order (1-based)
        """
        return _STEP_ORDER_LIST.index(self.step_type) + 1
    
    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"{self.__class__.__name__}(type={self.step_type.value}, stackable={self.is_stackable})"