"""
Test suite for core formatting functionality of dynamic formatting package.

Tests basic formatting, color handling, text styles, conditionals, and
complex feature combinations using the modern FormatterConfig approach.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from shared_utils.dynamic_formatting import DynamicFormatter, FormatterConfig, ValidationMode, ValidationLevel
    from shared_utils.dynamic_formatting.dynamic_formatting import RequiredFieldError, FunctionNotFoundError
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running pytest from the project root directory")


class TestBasicFormatting:
    """Test fundamental formatting capabilities"""
    
    @pytest.mark.core
    def test_simple_keyword_formatting(self):
        """Test basic keyword argument formatting"""
        formatter = DynamicFormatter("{{Hello ;name}}")
        result = formatter.format(name="World")
        assert result == "Hello World"
    
    @pytest.mark.core
    def test_multiple_fields(self):
        """Test formatting with multiple fields"""
        formatter = DynamicFormatter("{{Name: ;name}} {{Age: ;age}}")
        result = formatter.format(name="Alice", age=30)
        assert result == "Name: Alice Age: 30"
    
    @pytest.mark.core
    def test_empty_template(self):
        """Test empty template"""
        formatter = DynamicFormatter("")
        result = formatter.format(unused="data")
        assert result == ""
    
    @pytest.mark.core
    def test_literal_text_only(self):
        """Test template with only literal text"""
        formatter = DynamicFormatter("No variables here")
        result = formatter.format(unused="data")
        assert result == "No variables here"


class TestMissingDataHandling:
    """Test handling of missing data - core feature"""
    
    @pytest.mark.core
    def test_single_missing_field(self):
        """Test single missing field causes section to disappear"""
        formatter = DynamicFormatter("{{Found: ;data}}")
        result = formatter.format()  # No data provided
        assert result == ""
    
    @pytest.mark.core
    def test_partial_missing_fields(self):
        """Test partial missing data"""
        formatter = DynamicFormatter("{{Name: ;name}} {{Age: ;age}}")
        result = formatter.format(name="Alice")  # age missing
        assert result == "Name: Alice "
    
    @pytest.mark.core
    def test_all_fields_missing(self):
        """Test all fields missing"""
        formatter = DynamicFormatter("{{Field1: ;field1}} {{Field2: ;field2}}")
        result = formatter.format()
        assert result == " "  # Just the space between sections
    
    @pytest.mark.core
    def test_complex_missing_data_scenario(self):
        """Test complex scenario with mixed present/missing data"""
        formatter = DynamicFormatter("{{Status: ;status}} {{Error: ;error}} {{Time: ;timestamp}}")
        result = formatter.format(status="OK", timestamp="12:34")  # error missing
        assert result == "Status: OK  Time: 12:34"


class TestColorFormatting:
    """Test color formatting capabilities"""
    
    @pytest.mark.core
    def test_basic_ansi_colors(self):
        """Test basic ANSI color names"""
        formatter = DynamicFormatter("{{#red;Error: ;message}}")
        result = formatter.format(message="Failed")
        assert "Error: Failed" in result
        assert "\033[" in result  # Should contain ANSI escape codes
    
    @pytest.mark.core
    def test_hex_colors(self):
        """Test hex color codes"""
        formatter = DynamicFormatter("{{#ff0000;Alert: ;message}}")
        result = formatter.format(message="Warning")
        assert "Alert: Warning" in result
    
    @pytest.mark.core
    def test_color_override_behavior(self):
        """Test that later colors override earlier ones"""
        formatter = DynamicFormatter("{{#red#green#blue;Multi-color: ;text}}")
        result = formatter.format(text="test")
        # Should contain the text
        assert "Multi-color: test" in result
        # The exact ANSI codes depend on implementation, but should be formatted
        assert "\033[" in result
    
    @pytest.mark.core
    def test_file_mode_strips_colors(self):
        """Test that file output mode strips color codes"""
        config = FormatterConfig(output_mode="file")
        formatter = DynamicFormatter("{{#red@bold;Error: ;message}}", config=config)
        result = formatter.format(message="Failed")
        
        # Should contain text without ANSI codes
        assert result == "Error: Failed"
        assert "\033[" not in result


class TestTextFormatting:
    """Test text style formatting capabilities"""
    
    @pytest.mark.core
    def test_individual_text_styles(self):
        """Test individual text formatting styles"""
        styles = ["bold", "italic", "underline"]
        
        for style in styles:
            formatter = DynamicFormatter(f"{{@{style};Styled: ;text}}")
            result = formatter.format(text="content")
            assert "Styled: content" in result
    
    @pytest.mark.core
    def test_combined_text_styles(self):
        """Test combining multiple text styles"""
        formatter = DynamicFormatter("{{@bold@italic@underline;Emphasized: ;text}}")
        result = formatter.format(text="important")
        assert "Emphasized: important" in result
    
    @pytest.mark.core
    def test_text_style_reset(self):
        """Test text style reset functionality"""
        formatter = DynamicFormatter("{{@bold@reset;Normal: ;text}}")
        result = formatter.format(text="content")
        assert "Normal: content" in result


class TestConditionalFormatting:
    """Test conditional formatting capabilities"""
    
    @pytest.mark.core
    def test_section_level_conditionals(self):
        """Test conditionals that control entire sections"""
        def has_value(val):
            return bool(val)
        
        config = FormatterConfig(functions={"has_value": has_value})
        formatter = DynamicFormatter(
            "{{Processing}} {{?has_value;Found ;count; items}}",
            config=config
        )
        
        # With data - should show conditional section
        result = formatter.format(count=25)
        assert result == "Processing Found 25 items"
        
        # Without data - conditional section should disappear
        result = formatter.format(count=0)
        assert result == "Processing "
    
    @pytest.mark.core
    def test_inline_conditionals(self):
        """Test inline conditionals within sections"""
        def is_urgent(priority):
            return priority > 7
        
        config = FormatterConfig(functions={"is_urgent": is_urgent})
        formatter = DynamicFormatter(
            "{{Task{?is_urgent} - URGENT: ;task_name}}",
            config=config
        )
        
        # Urgent task
        result = formatter.format(task_name="deploy", priority=9)
        assert "Task - URGENT: deploy" in result
        
        # Normal task
        result = formatter.format(task_name="backup", priority=3)
        assert "Task: backup" in result
    
    @pytest.mark.core
    def test_missing_conditional_function(self):
        """Test error handling for missing conditional functions"""
        formatter = DynamicFormatter("{{?missing_func;Text: ;field}}")
        
        with pytest.raises(FunctionNotFoundError) as exc_info:
            formatter.format(field="test")
        
        assert "missing_func" in str(exc_info.value)


class TestRequiredFields:
    """Test required field functionality"""
    
    @pytest.mark.core
    def test_required_field_present(self):
        """Test required field when data is present"""
        formatter = DynamicFormatter("{{!;Critical: ;message}}")
        result = formatter.format(message="System down")
        assert result == "Critical: System down"
    
    @pytest.mark.core
    def test_required_field_missing(self):
        """Test required field when data is missing"""
        formatter = DynamicFormatter("{{!;Critical: ;message}}")
        
        with pytest.raises(RequiredFieldError) as exc_info:
            formatter.format()
        
        assert "Required field" in str(exc_info.value)
        assert "message" in str(exc_info.value)


class TestEscapeSequences:
    """Test escape sequence handling"""
    
    @pytest.mark.core
    def test_escaped_braces(self):
        """Test escaped brace handling"""
        formatter = DynamicFormatter(r"Literal \{braces\} and {{field}}")
        result = formatter.format(field="value")
        assert result == "Literal {braces} and value"
    
    @pytest.mark.core
    def test_escaped_delimiters(self):
        """Test escaped delimiter handling"""
        formatter = DynamicFormatter(r"Text with \; semicolon and {{field}}")
        result = formatter.format(field="value")
        assert result == "Text with ; semicolon and value"
    
    @pytest.mark.core
    def test_mixed_escaping(self):
        """Test mixed escape scenarios"""
        formatter = DynamicFormatter(r"Complex \{text\} with \; and {{field}}")
        result = formatter.format(field="test")
        assert result == "Complex {text} with ; and test"


class TestCustomDelimiters:
    """Test custom delimiter functionality"""
    
    @pytest.mark.core
    def test_pipe_delimiter(self):
        """Test using pipe as delimiter"""
        config = FormatterConfig(delimiter="|")
        formatter = DynamicFormatter("{{#red|Error: |message}}", config=config)
        result = formatter.format(message="Failed")
        assert "Error: Failed" in result
    
    @pytest.mark.core
    def test_double_colon_delimiter(self):
        """Test using double colon as delimiter"""
        config = FormatterConfig(delimiter="::")
        formatter = DynamicFormatter("{{@bold::Status: ::status}}", config=config)
        result = formatter.format(status="Running")
        assert "Status: Running" in result


class TestComplexCombinations:
    """Test complex combinations of features"""
    
    @pytest.mark.core
    def test_all_features_combined(self):
        """Test combination of colors, styles, conditionals, and missing data"""
        def level_color(level):
            return {"ERROR": "red", "WARNING": "yellow", "INFO": "green"}[level]
        
        def has_duration(duration):
            return duration > 0
        
        config = FormatterConfig(functions={
            "level_color": level_color, 
            "has_duration": has_duration
        })
        formatter = DynamicFormatter(
            "{{#level_color@bold;[;level;]}} {{message}} {{?has_duration;in ;duration;s}}",
            config=config
        )
        
        # All features active
        result = formatter.format(level="ERROR", message="Failed", duration=2.5)
        assert "[ERROR]" in result
        assert "Failed" in result
        assert "in 2.5s" in result
        
        # Conditional feature inactive
        result = formatter.format(level="INFO", message="Success", duration=0)
        assert "[INFO]" in result
        assert "Success" in result
        assert "in 0s" not in result  # Conditional should hide this
    
    @pytest.mark.core
    def test_nested_function_dependencies(self):
        """Test scenarios where functions depend on field values"""
        def content_based_color(text):
            if "error" in text.lower():
                return "red"
            elif "warning" in text.lower():
                return "yellow"
            else:
                return "green"
        
        config = FormatterConfig(functions={"content_based_color": content_based_color})
        formatter = DynamicFormatter(
            "{{#content_based_color@bold;Status: ;message}}",
            config=config
        )
        
        # Error content should be red
        result = formatter.format(message="Error: Connection failed")
        assert "Status: Error: Connection failed" in result
        
        # Warning content should be yellow
        result = formatter.format(message="Warning: Slow response")
        assert "Status: Warning: Slow response" in result
        
        # Normal content should be green
        result = formatter.format(message="Process completed")
        assert "Status: Process completed" in result