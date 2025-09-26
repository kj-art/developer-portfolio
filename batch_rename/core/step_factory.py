"""
Factory for creating processing step instances.

Centralizes step creation and provides easy access to step functionality.
"""

from typing import Dict, Type, List, Callable
from .steps.base import ProcessingStep, StepType, StepConfig
from .steps import ExtractorStep, ConverterStep, FilterStep, TemplateStep, AllInOneStep


class StepFactory:
    """Factory for creating and managing processing steps."""
    
    # Registry of step classes by type
    _STEP_CLASSES: Dict[StepType, Type[ProcessingStep]] = {
        StepType.EXTRACTOR: ExtractorStep,
        StepType.CONVERTER: ConverterStep,
        StepType.FILTER: FilterStep,
        StepType.TEMPLATE: TemplateStep,
        StepType.ALLINONE: AllInOneStep,
    }
    
    # Singleton instances for reuse
    _instances: Dict[StepType, ProcessingStep] = {}
    
    @classmethod
    def get_step(cls, step_type: StepType) -> ProcessingStep:
        """
        Get a processing step instance.
        
        Args:
            step_type: Type of step to create
            
        Returns:
            ProcessingStep instance
        """
        if step_type not in cls._instances:
            step_class = cls._STEP_CLASSES[step_type]
            cls._instances[step_type] = step_class()
        
        return cls._instances[step_type]
    
    @classmethod
    def get_all_steps(cls) -> List[ProcessingStep]:
        """
        Get all processing step instances in execution order.
        
        Returns:
            List of all step instances sorted by execution order
        """
        steps = [cls.get_step(step_type) for step_type in StepType]
        return sorted(steps, key=lambda step: step.get_execution_order())
    
    @classmethod
    def create_executable(cls, step_type: StepType, config: StepConfig) -> Callable:
        """
        Create an executable function from step configuration.
        
        This factory method handles both built-in and custom functions, performing
        validation and creating appropriate wrappers that standardize the calling
        convention for the processing pipeline.
        
        Args:
            step_type: Type of processing step (EXTRACTOR, CONVERTER, etc.)
            config: Step configuration with function name and arguments
            
        Returns:
            Callable that accepts ProcessingContext and returns step-appropriate data
            
        Raises:
            ValueError: If function name is not found or validation fails
            ImportError: If custom function file cannot be loaded
            
        Example:
            config = StepConfig(name='split', positional_args=['_', 'dept', 'type'])
            func = StepFactory.create_executable(StepType.EXTRACTOR, config)
            result = func(context)  # Returns {'dept': 'HR', 'type': 'employee'}
        """
        step = cls.get_step(step_type)
        return step.create_executable(config)
    
    @classmethod
    def get_builtin_functions(cls, step_type: StepType) -> Dict[str, Callable]:
        """
        Get built-in functions for a step type.
        
        Args:
            step_type: Type of processing step
            
        Returns:
            Dict of built-in function names to functions
        """
        step = cls.get_step(step_type)
        return step.builtin_functions
    
    @classmethod
    def validate_custom_function(cls, step_type: StepType, function: Callable):
        """
        Validate a custom function for a step type.
        
        Args:
            step_type: Type of processing step
            function: Function to validate
            
        Returns:
            ValidationResult
        """
        step = cls.get_step(step_type)
        return step.validate_custom_function(function)