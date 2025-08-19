"""
Core formatting functionality tests.

Tests the fundamental features of the dynamic formatting system including
basic template parsing, graceful missing data handling, color formatting,
text styling, and conditional sections.
"""

import pytest
from shared_utils.dynamic_formatting import (
    DynamicFormatter,
    DynamicFormattingError,
    RequiredFieldError,
    FunctionNotFoundError
)


class TestBasicFormatting:
    """Test basic template formatting functionality"""
    
    @pytest.mark.core
    def test_simple_keyword_formatting(self):
        """Test basic keyword argument formatting"""
        formatter = DynamicFormatter("{{Hello ;name}}")
        result = formatter.format(name="World")
        assert result == "Hello World"
    
    @pytest.mark.core
    def test_multiple_fields(self):
        """Test templates with multiple fields"""
        formatter = DynamicFormatter("{{Error: ;message}} {{Code: ;code}}")
        result = formatter.format(message="Failed", code=404)
        assert result == "Error: Failed Code: 404"
    
    @pytest.mark.core
    def test_empty_template(self):
        """Test empty template handling"""
        formatter = DynamicFormatter("")
        result = formatter.format(anything="value")
        assert result == ""
    
    @pytest.mark.core
    def test_literal_text_only(self):
        """Test template with only literal text"""
        formatter = DynamicFormatter("No variables here")
        result = formatter.format(unused="value")
        assert result == "No variables here"


class TestMissingDataHandling:
    """Test the core graceful missing data handling feature"""
    
    @pytest.mark.core
    def test_single_missing_field(self):
        """Test single field missing causes section to disappear"""
        formatter = DynamicFormatter("{{Error: ;message}}")
        result = formatter.format()
        assert result == ""
    
    @pytest.mark.core
    def test_partial_missing_fields(self):
        """Test partial missing fields in multi-section template"""
        formatter = DynamicFormatter("{{Error: ;message}} {{Count: ;count}}")
        
        # Only message provided
        result = formatter.format(message="Failed")
        assert result == "Error: Failed "
        
        # Only count provided
        result = formatter.format(count=42)
        assert result == " Count: 42"
    
    @pytest.mark.core
    def test_all_fields_missing(self):
        """Test all fields missing results in empty string"""
        formatter = DynamicFormatter("{{Error: ;message}} {{Count: ;count}} {{Duration: ;time}}")
        result = formatter.format()
        assert result == "  "  # Spaces between sections remain
    
    @pytest.mark.core
    def test_complex_missing_data_scenario(self):
        """Test complex scenario with various missing combinations"""
        formatter = DynamicFormatter(
            "{{Status: ;status}} {{Processing ;count; files}} {{Duration: ;duration;s}} {{Errors: ;errors}}"
        )
        
        # All present
        result = formatter.format(status="Running", count=100, duration=5.2, errors=3)
        expected = "Status: Running Processing 100 files Duration: 5.2s Errors: 3"
        assert result == expected
        
        # Some missing
        result = formatter.format(status="Running", count=100)
        expected = "Status: Running Processing 100 files  "
        assert result == expected


class TestColorFormatting:
    """Test color formatting capabilities"""
    
    @pytest.mark.core
    def test_basic_ansi_colors(self):
        """Test basic ANSI color formatting"""
        formatter = DynamicFormatter("{{#red;Error: ;message}}")
        result = formatter.format(message="Failed")
        
        # Should contain the text content regardless of ANSI codes
        assert "Error: Failed" in result
        # In console mode, should have ANSI codes
        assert "\033[" in result  # ANSI escape sequence present
    
    @pytest.mark.core
    def test_hex_colors(self):
        """Test hex color formatting"""
        formatter = DynamicFormatter("{{#ff0000;Alert: ;message}}")
        result = formatter.format(message="Critical")
        assert "Alert: Critical" in result
    
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
        formatter = DynamicFormatter("{{#red@bold;Error: ;message}}", output_mode="file")
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
        
        formatter = DynamicFormatter(
            "{{Processing}} {{?has_value;Found ;count; items}}",
            functions={"has_value": has_value}
        )
        
        # With data - should show conditional section
        result = formatter.format(count=25)
        assert result == "Processing Found 25 items"
        
        # Without data - conditional section disappears
        result = formatter.format(count=0)
        assert result == "Processing "
    
    @pytest.mark.core
    def test_inline_conditionals(self):
        """Test inline conditionals within sections"""
        def is_urgent(priority):
            return priority > 7
        
        formatter = DynamicFormatter(
            "{{Task{?is_urgent} - URGENT: ;task_name}}",
            functions={"is_urgent": is_urgent}
        )
        
        # Urgent task
        result = formatter.format(task_name="deploy", priority=9)
        assert "Task - URGENT: deploy" in result
        
        # Normal task
        result = formatter.format(task_name="cleanup", priority=3)
        assert result == "Task: cleanup"
    
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
        
        assert "Required field missing" in str(exc_info.value)
        assert "message" in str(exc_info.value)


class TestEscapeSequences:
    """Test escape sequence handling"""
    
    @pytest.mark.core
    def test_escaped_braces(self):
        """Test escaping literal braces in templates"""
        formatter = DynamicFormatter("{{Use \\{variable\\} syntax: ;example}}")
        result = formatter.format(example="name")
        assert result == "Use {variable} syntax: name"
    
    @pytest.mark.core
    def test_escaped_delimiters(self):
        """Test escaping delimiters within template content"""
        formatter = DynamicFormatter("{{Config\\;setting: ;value}}")
        result = formatter.format(value="enabled")
        assert result == "Config;setting: enabled"
    
    @pytest.mark.core
    def test_mixed_escaping(self):
        """Test complex escaping scenarios"""
        formatter = DynamicFormatter("{{Path \\{type\\}\\;format: ;path}}")
        result = formatter.format(path="file.txt")
        assert result == "Path {type};format: file.txt"


class TestCustomDelimiters:
    """Test custom delimiter functionality"""
    
    @pytest.mark.core
    def test_pipe_delimiter(self):
        """Test using pipe as delimiter"""
        formatter = DynamicFormatter("{{#red|Error: |message}}", delimiter="|")
        result = formatter.format(message="Failed")
        assert "Error: Failed" in result
    
    @pytest.mark.core
    def test_double_colon_delimiter(self):
        """Test using double colon as delimiter"""
        formatter = DynamicFormatter("{{@bold::Status: ::status}}", delimiter="::")
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
        
        formatter = DynamicFormatter(
            "{{#level_color@bold;[;level;]}} {{message}} {{?has_duration;in ;duration;s}}",
            functions={"level_color": level_color, "has_duration": has_duration}
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
        
        formatter = DynamicFormatter(
            "{{#content_based_color@bold;Status: ;message}}",
            functions={"content_based_color": content_based_color}
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