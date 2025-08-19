"""
Positional arguments feature tests.

Comprehensive tests for the positional arguments functionality including
basic usage, formatting, conditionals, error handling, and backward
compatibility with keyword arguments.
"""

import pytest
from shared_utils.dynamic_formatting import (
    DynamicFormatter,
    DynamicFormattingError,
    RequiredFieldError,
    FunctionNotFoundError
)


class TestBasicPositionalArgs:
    """Test basic positional argument functionality"""
    
    @pytest.mark.positional
    def test_single_positional_field(self):
        """Test single positional field"""
        formatter = DynamicFormatter("{{}}")
        result = formatter.format("test")
        assert result == "test"
    
    @pytest.mark.positional
    def test_multiple_positional_fields(self):
        """Test multiple positional fields"""
        formatter = DynamicFormatter("{{}} {{}}")
        result = formatter.format("hello", "world")
        assert result == "hello world"
    
    @pytest.mark.positional
    def test_positional_with_prefix(self):
        """Test positional field with prefix"""
        formatter = DynamicFormatter("{{Error: ;}}")
        result = formatter.format("Failed")
        assert result == "Error: Failed"
    
    @pytest.mark.positional
    def test_positional_with_suffix(self):
        """Test positional field with suffix"""
        formatter = DynamicFormatter("{{;;!}}")
        result = formatter.format("Warning")
        assert result == "Warning!"
    
    @pytest.mark.positional
    def test_positional_with_prefix_and_suffix(self):
        """Test positional field with both prefix and suffix"""
        formatter = DynamicFormatter("{{Error: ;;!}}")
        result = formatter.format("Failed")
        assert result == "Error: Failed!"


class TestPositionalMissingData:
    """Test positional arguments with missing data (graceful handling)"""
    
    @pytest.mark.positional
    def test_fewer_args_than_sections(self):
        """Test providing fewer arguments than template sections"""
        formatter = DynamicFormatter("{{First: ;}} {{Second: ;}} {{Third: ;}}")
        
        # One argument
        result = formatter.format("A")
        assert result == "First: A  "
        
        # Two arguments  
        result = formatter.format("A", "B")
        assert result == "First: A Second: B "
        
        # Three arguments
        result = formatter.format("A", "B", "C")
        assert result == "First: A Second: B Third: C"
    
    @pytest.mark.positional
    def test_no_arguments_provided(self):
        """Test providing no arguments to positional template"""
        formatter = DynamicFormatter("{{First: ;}} {{Second: ;}}")
        result = formatter.format()
        assert result == "  "  # Spaces between sections remain
    
    @pytest.mark.positional
    def test_empty_string_arguments(self):
        """Test empty string arguments"""
        formatter = DynamicFormatter("{{}} {{}}")
        
        # Empty string should work
        result = formatter.format("", "test")
        assert result == " test"
        
        # None should cause section to disappear
        result = formatter.format(None, "test")
        assert result == " test"


class TestPositionalWithFormatting:
    """Test positional arguments with color and text formatting"""
    
    @pytest.mark.positional
    def test_positional_with_colors(self):
        """Test positional arguments with color formatting"""
        formatter = DynamicFormatter("{{#red;}}")
        result = formatter.format("test")
        assert "test" in result
        assert "\033[" in result  # Should have ANSI codes
    
    @pytest.mark.positional
    def test_positional_with_text_styles(self):
        """Test positional arguments with text formatting"""
        formatter = DynamicFormatter("{{@bold;}}")
        result = formatter.format("test")
        assert "test" in result
    
    @pytest.mark.positional
    def test_positional_with_combined_formatting(self):
        """Test positional arguments with combined formatting"""
        formatter = DynamicFormatter("{{#red@bold;}}")
        result = formatter.format("test")
        assert "test" in result
    
    @pytest.mark.positional
    def test_multiple_formatted_positional_sections(self):
        """Test multiple positional sections with different formatting"""
        formatter = DynamicFormatter("{{#red;}} {{#blue;}} {{@bold;}}")
        result = formatter.format("first", "second", "third")
        assert "first" in result
        assert "second" in result
        assert "third" in result
    
    @pytest.mark.positional
    def test_complex_positional_formatting(self):
        """Test complex positional formatting with prefix/suffix"""
        formatter = DynamicFormatter("{{#red@bold;Warning: ;;!}}")
        result = formatter.format("Low disk space")
        assert "Warning: Low disk space!" in result


class TestPositionalWithConditionals:
    """Test positional arguments with conditional functions"""
    
    @pytest.mark.positional
    def test_positional_section_level_conditional(self):
        """Test section-level conditionals with positional args"""
        def has_value(val):
            return bool(val and str(val).strip())
        
        formatter = DynamicFormatter(
            "{{?has_value;Found: ;}}",
            functions={"has_value": has_value}
        )
        
        # Should show with valid value
        result = formatter.format("test")
        assert result == "Found: test"
        
        # Should hide with empty value
        result = formatter.format("")
        assert result == ""
        
        # Should hide with None
        result = formatter.format(None)
        assert result == ""
    
    @pytest.mark.positional
    def test_positional_inline_conditional(self):
        """Test inline conditionals with positional args"""
        def is_urgent(priority):
            return priority > 7
        
        formatter = DynamicFormatter(
            "{{Task{?is_urgent} URGENT: ;}}",
            functions={"is_urgent": is_urgent}
        )
        
        # Urgent task
        result = formatter.format("deploy", priority=9)
        assert "Task URGENT: deploy" in result
        
        # Normal task
        result = formatter.format("cleanup", priority=3)
        assert result == "Task: cleanup"
    
    @pytest.mark.positional
    def test_multiple_positional_conditionals(self):
        """Test multiple sections with conditionals and positional args"""
        def has_data(val):
            return bool(val)
        
        def is_error(val):
            return "error" in str(val).lower()
        
        formatter = DynamicFormatter(
            "{{?has_data;Status: ;}} {{?is_error;ERROR: ;}}",
            functions={"has_data": has_data, "is_error": is_error}
        )
        
        # Both conditions true
        result = formatter.format("Running", "Error occurred")
        assert result == "Status: Running ERROR: Error occurred"
        
        # Only first condition true
        result = formatter.format("Running", "Success")
        assert result == "Status: Running "
        
        # Only second condition true
        result = formatter.format("", "Error occurred")
        assert result == " ERROR: Error occurred"


class TestPositionalWithFunctionFallback:
    """Test positional arguments with function fallback system"""
    
    @pytest.mark.positional
    @pytest.mark.fallback
    def test_positional_color_function_fallback(self):
        """Test color function fallback with positional args"""
        def status_color(status):
            return {"error": "red", "success": "green", "warning": "yellow"}[status.lower()]
        
        formatter = DynamicFormatter(
            "{{#status_color;}}",
            functions={"status_color": status_color}
        )
        
        result = formatter.format("ERROR")
        assert "ERROR" in result
    
    @pytest.mark.positional
    @pytest.mark.fallback
    def test_positional_text_function_fallback(self):
        """Test text style function fallback with positional args"""
        def emphasis_level(text):
            if len(text) > 10:
                return "bold"
            elif len(text) > 5:
                return "italic"
            return "normal"
        
        formatter = DynamicFormatter(
            "{{@emphasis_level;}}",
            functions={"emphasis_level": emphasis_level}
        )
        
        # Long text should be bold
        result = formatter.format("very long message here")
        assert "very long message here" in result
        
        # Medium text should be italic
        result = formatter.format("medium")
        assert "medium" in result
        
        # Short text should be normal
        result = formatter.format("hi")
        assert "hi" in result
    
    @pytest.mark.positional
    @pytest.mark.fallback
    def test_chained_function_calls(self):
        """Test scenarios where functions process field values"""
        def priority_to_level(priority):
            if priority > 8:
                return "CRITICAL"
            elif priority > 5:
                return "WARNING"
            return "INFO"
        
        def level_color(level):
            return {"CRITICAL": "red", "WARNING": "yellow", "INFO": "green"}[level]
        
        # Manual chaining for this test
        formatter = DynamicFormatter(
            "{{Priority ;}} becomes {{#level_color;}}",
            functions={"level_color": level_color}
        )
        
        # Test high priority
        priority = 9
        level = priority_to_level(priority)
        result = formatter.format(priority, level)
        assert "Priority 9" in result
        assert "becomes CRITICAL" in result


class TestPositionalErrorConditions:
    """Test error conditions specific to positional arguments"""
    
    @pytest.mark.positional
    @pytest.mark.error
    def test_mixed_positional_and_keyword_args(self):
        """Test error when mixing positional and keyword arguments"""
        formatter = DynamicFormatter("{{}} {{}}")
        
        with pytest.raises(DynamicFormattingError) as exc_info:
            formatter.format("pos", keyword="kw")
        
        assert "Cannot mix positional and keyword arguments" in str(exc_info.value)
    
    @pytest.mark.positional
    @pytest.mark.error
    def test_too_many_positional_arguments(self):
        """Test error when providing too many positional arguments"""
        formatter = DynamicFormatter("{{}}")  # Only one positional section
        
        with pytest.raises(DynamicFormattingError) as exc_info:
            formatter.format("first", "second")
        
        error_msg = str(exc_info.value)
        assert "Too many positional arguments" in error_msg
        assert "expected 1, got 2" in error_msg
    
    @pytest.mark.positional
    @pytest.mark.error
    def test_required_positional_field_missing(self):
        """Test error when required positional field is missing"""
        formatter = DynamicFormatter("{{!}}")  # Required field
        
        with pytest.raises(RequiredFieldError) as exc_info:
            formatter.format()  # No arguments
        
        error_msg = str(exc_info.value)
        assert "Required field missing" in error_msg
        assert "position 1" in error_msg  # Should show user-friendly position
    
    @pytest.mark.positional
    @pytest.mark.error
    def test_missing_conditional_function_positional(self):
        """Test error when conditional function is missing with positional args"""
        formatter = DynamicFormatter("{{?missing_func;}}")
        
        with pytest.raises(FunctionNotFoundError) as exc_info:
            formatter.format("test")
        
        assert "missing_func" in str(exc_info.value)


class TestPositionalEdgeCases:
    """Test edge cases specific to positional arguments"""
    
    @pytest.mark.positional
    @pytest.mark.error
    def test_empty_template_with_positional_args(self):
        """Test empty template with positional arguments"""
        formatter = DynamicFormatter("")
        result = formatter.format("ignored")
        assert result == ""
    
    @pytest.mark.positional
    def test_literal_only_template_with_positional_args(self):
        """Test literal-only template with positional arguments"""
        formatter = DynamicFormatter("No variables here")
        result = formatter.format("ignored")
        assert result == "No variables here"
    
    @pytest.mark.positional
    def test_mixed_positional_and_named_sections(self):
        """Test template with both positional and named field sections"""
        formatter = DynamicFormatter("{{}} {{named_field}}")
        
        # With positional args only - named field section should disappear
        result = formatter.format("pos_value")
        assert result == "pos_value "
        
        # With keyword args only - positional section should get the value  
        result = formatter.format(named_field="named_value")
        assert result == " named_value"
    
    @pytest.mark.positional
    def test_zero_positional_sections_with_args(self):
        """Test template with no positional sections but positional args provided"""
        formatter = DynamicFormatter("{{named_field}}")
        
        # Should work - positional args are mapped to field sections in order
        result = formatter.format("test")
        assert result == "test"


class TestPositionalSyntaxPatterns:
    """Test all documented positional syntax patterns"""
    
    @pytest.mark.positional
    @pytest.mark.regression
    def test_all_positional_syntax_variations(self):
        """Test all valid positional syntax patterns"""
        test_cases = [
            # (template, args, expected_content)
            ("{{}}", ["test"], "test"),
            ("{{#red}}", ["test"], "test"),
            ("{{@bold}}", ["test"], "test"),  
            ("{{prefix;}}", ["test"], "prefixtest"),
            ("{{;suffix}}", ["test"], "testsuffix"),
            ("{{prefix;suffix}}", ["test"], "prefixtestsuffix"),
            ("{{#red@bold;}}", ["test"], "test"),
            ("{{#red@bold;prefix;}}", ["test"], "prefixtest"),
            ("{{#red@bold;prefix;suffix}}", ["test"], "prefixtestsuffix"),
        ]
        
        for template, args, expected_content in test_cases:
            formatter = DynamicFormatter(template)
            result = formatter.format(*args)
            
            # For formatted text, just check that the expected content is present
            assert expected_content in result, f"Template '{template}' with args {args} failed. Expected '{expected_content}' in result '{result}'"
    
    @pytest.mark.positional
    def test_complex_positional_combinations(self):
        """Test complex combinations of positional features"""
        def has_value(val):
            return bool(val)
        
        def status_color(status):
            return {"error": "red", "success": "green"}[status.lower()]
        
        formatter = DynamicFormatter(
            "{{#status_color@bold;Status: ;}} {{?has_value;Count: ;}} {{Duration: ;s}}",
            functions={"has_value": has_value, "status_color": status_color}
        )
        
        # All arguments provided
        result = formatter.format("SUCCESS", 150, 2.5)
        assert "Status: SUCCESS" in result
        assert "Count: 150" in result
        assert "Duration: 2.5s" in result
        
        # Some arguments missing
        result = formatter.format("ERROR", 0)  # Count is 0, so conditional should hide
        assert "Status: ERROR" in result
        assert "Count: 0" not in result  # Conditional should hide this
        assert "Duration: s" not in result  # Missing duration should hide section


class TestBackwardCompatibility:
    """Ensure positional arguments don't break existing keyword functionality"""
    
    @pytest.mark.positional
    @pytest.mark.regression
    def test_keyword_args_still_work(self):
        """Test that keyword arguments continue to work as before"""
        formatter = DynamicFormatter("{{Error: ;message}} {{Count: ;count}}")
        
        # Complete data
        result = formatter.format(message="Failed", count=42)
        assert result == "Error: Failed Count: 42"
        
        # Partial data
        result = formatter.format(message="Failed")
        assert result == "Error: Failed "
    
    @pytest.mark.positional
    @pytest.mark.regression
    def test_complex_keyword_formatting_unchanged(self):
        """Test that complex keyword formatting works exactly as before"""
        def level_color(level):
            return {"ERROR": "red", "INFO": "green"}[level]
        
        formatter = DynamicFormatter(
            "{{#level_color@bold;[;level;]}} {{message}}",
            functions={"level_color": level_color}
        )
        
        result = formatter.format(level="ERROR", message="test")
        assert "[ERROR]" in result
        assert "test" in result
    
    @pytest.mark.positional
    @pytest.mark.regression
    def test_keyword_conditionals_unchanged(self):
        """Test that keyword conditionals work exactly as before"""
        def has_value(val):
            return bool(val)
        
        formatter = DynamicFormatter(
            "{{?has_value;Found: ;data}}",
            functions={"has_value": has_value}
        )
        
        result = formatter.format(data="test")
        assert result == "Found: test"
        
        result = formatter.format(data="")
        assert result == ""