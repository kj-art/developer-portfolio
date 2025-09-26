"""
Unit tests for built-in templates and template functionality.
"""

import pytest

from core.step_factory import StepFactory
from core.steps.base import StepType, StepConfig


class TestStringSmithTemplate:
    """Test the StringSmith template functionality."""
    
    def test_stringsmith_basic(self, extracted_context):
        """Test basic StringSmith template formatting."""
        config = StepConfig(
            name='stringsmith',
            positional_args=['{{dept}}_{{type}}_{{category}}'],
            keyword_args={}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        assert result == 'HR_employee_data'
    
    def test_stringsmith_missing_field(self, extracted_context):
        """Test StringSmith with missing field (graceful handling)."""
        config = StepConfig(
            name='stringsmith',
            positional_args=['{{dept}}_{{missing_field}}_{{category}}'],
            keyword_args={}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        # StringSmith should gracefully handle missing fields by omitting those sections
        assert result == 'HR__data'
    
    def test_stringsmith_complex_template(self, extracted_context):
        """Test StringSmith with complex template."""
        config = StepConfig(
            name='stringsmith',
            positional_args=['{{dept}}-{{type}}_v{{year}}.{{category}}'],
            keyword_args={}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        assert result == 'HR-employee_v2024.data'
    
    def test_stringsmith_no_template(self, extracted_context):
        """Test StringSmith with empty template."""
        config = StepConfig(
            name='stringsmith',
            positional_args=[''],
            keyword_args={}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        assert result == ''


class TestJoinTemplate:
    """Test the join template functionality."""
    
    def test_join_basic(self, extracted_context):
        """Test basic join template."""
        config = StepConfig(
            name='join',
            positional_args=['dept', 'type', 'category'],
            keyword_args={'separator': '_'}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        assert result == 'HR_employee_data'
    
    def test_join_different_separator(self, extracted_context):
        """Test join template with different separator."""
        config = StepConfig(
            name='join',
            positional_args=['dept', 'type', 'category'],
            keyword_args={'separator': '-'}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        assert result == 'HR-employee-data'
    
    def test_join_missing_field(self, extracted_context):
        """Test join template with missing field."""
        config = StepConfig(
            name='join',
            positional_args=['dept', 'missing', 'category'],
            keyword_args={'separator': '_'}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        # Should skip missing fields
        assert result == 'HR_data'
    
    def test_join_no_separator(self, extracted_context):
        """Test join template with no separator."""
        config = StepConfig(
            name='join',
            positional_args=['dept', 'type'],
            keyword_args={}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        # Default separator should be underscore
        assert result == 'HR_employee'


class TestDefaultTemplate:
    """Test the default template functionality."""
    
    def test_default_template(self, extracted_context):
        """Test default template behavior."""
        config = StepConfig(
            name='template',
            positional_args=['{dept}_{type}_{year}'],
            keyword_args={}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        assert result == 'HR_employee_2024'


class TestTemplateRegistry:
    """Test the template registry and factory integration."""
    
    def test_get_builtin_functions(self):
        """Test getting builtin template functions from factory."""
        builtin_funcs = StepFactory.get_builtin_functions(StepType.TEMPLATE)
        
        assert 'template' in builtin_funcs
        assert 'stringsmith' in builtin_funcs
        assert 'join' in builtin_funcs


class TestCustomTemplateLoading:
    """Test loading and validation of custom templates."""
    
    def test_load_valid_custom_template(self, temp_dir, extracted_context):
        """Test loading a valid custom template."""
        template_content = '''
def test_template(context):
    """Simple test template."""
    if context.has_extracted_data():
        return f"{context.extracted_data.get('dept', '')}_custom"
    return context.base_name
'''
        
        template_file = temp_dir / "test_templates.py"
        template_file.write_text(template_content)
        
        config = StepConfig(
            name=str(template_file),
            positional_args=['test_template'],
            keyword_args={}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        assert result == 'HR_custom'
    
    def test_custom_template_validation(self, temp_dir):
        """Test validation of custom template functions."""
        template_content = '''
def valid_template(context):
    """Valid template function."""
    return "test"

def invalid_template():
    """Invalid template with wrong signature."""
    return "test"
'''
        
        template_file = temp_dir / "test_templates.py"
        template_file.write_text(template_content)
        
        from core.function_loader import load_custom_function
        
        # Valid function should pass validation
        valid_func = load_custom_function(template_file, 'valid_template')
        validation_result = StepFactory.validate_custom_function(StepType.TEMPLATE, valid_func)
        assert validation_result.valid
        
        # Invalid function should fail validation  
        invalid_func = load_custom_function(template_file, 'invalid_template')
        validation_result = StepFactory.validate_custom_function(StepType.TEMPLATE, invalid_func)
        assert not validation_result.valid
        assert 'parameter' in validation_result.message.lower()


class TestTemplateEdgeCases:
    """Test template edge cases and error conditions."""
    
    def test_template_no_extracted_data(self, sample_context):
        """Test template with no extracted data."""
        config = StepConfig(
            name='template',
            positional_args=['{dept}_{type}'],
            keyword_args={}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(sample_context)
        
        # Should fall back to base name when no extracted data
        assert result == sample_context.base_name
    
    def test_template_empty_extracted_data(self, sample_context):
        """Test template with empty extracted data."""
        sample_context.extracted_data = {}
        
        config = StepConfig(
            name='join',
            positional_args=['dept', 'type'],
            keyword_args={}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(sample_context)
        
        assert result == sample_context.base_name
    
    def test_template_with_special_characters(self, extracted_context):
        """Test template with special characters."""
        # Add field with special characters
        extracted_context.extracted_data['special'] = 'test-file_v1.2'
        
        config = StepConfig(
            name='template',
            positional_args=['{dept}-{special}'],
            keyword_args={}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        assert result == 'HR-test-file_v1.2'


class TestTemplateIntegration:
    """Test template integration with other processing steps."""
    
    def test_template_after_converter(self, extracted_context):
        """Test template formatting after field conversion."""
        # Simulate converter having modified data
        extracted_context.extracted_data['dept'] = 'HUMAN_RESOURCES'
        extracted_context.extracted_data['year'] = '24'  # Converted to 2-digit
        
        config = StepConfig(
            name='template',
            positional_args=['{dept}_{type}_{year}'],
            keyword_args={}
        )
        
        template_func = StepFactory.create_executable(StepType.TEMPLATE, config)
        result = template_func(extracted_context)
        
        assert result == 'HUMAN_RESOURCES_employee_24'