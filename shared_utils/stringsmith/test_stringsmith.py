"""
Comprehensive test suite for StringSmith template formatter.

Tests core functionality based on the actual StringSmith implementation.
"""

import pytest
import sys
import os

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from formatter import TemplateFormatter
from exceptions import StringSmithError, MissingMandatoryFieldError


class TestBasicFormatting:
    """Test core template formatting functionality."""
    
    def test_simple_field_only(self):
        """Test simple field substitution."""
        formatter = TemplateFormatter("{{name}}")
        result = formatter.format(name="World")
        assert result == "World"
    
    def test_field_with_prefix(self):
        """Test field with prefix."""
        formatter = TemplateFormatter("{{Hello ;name}}")
        result = formatter.format(name="World")
        assert result == "Hello World"
    
    def test_field_with_prefix_and_suffix(self):
        """Test field with prefix and suffix."""
        formatter = TemplateFormatter("{{Hello ;name;!}}")
        result = formatter.format(name="World")
        assert result == "Hello World!"
    
    def test_multiple_sections(self):
        """Test multiple template sections."""
        formatter = TemplateFormatter("{{Hello ;name;}} and {{;other}}")
        result = formatter.format(name="Alice", other="Bob")
        assert result == "Hello Alice and Bob"
    
    def test_missing_optional_field(self):
        """Test missing optional field omits section."""
        formatter = TemplateFormatter("Hello{{, ;name}}")
        result = formatter.format()
        assert result == "Hello"
    
    def test_positional_arguments(self):
        """Test positional argument handling."""
        formatter = TemplateFormatter("{{;}} + {{;}} = {{;}}")
        result = formatter.format("2", "3", "5")
        assert result == "2 + 3 = 5"
    
    def test_mixed_arguments_error(self):
        """Test that mixing positional and keyword arguments raises error."""
        formatter = TemplateFormatter("{{name}}")
        with pytest.raises(StringSmithError, match="Cannot mix positional and keyword arguments"):
            formatter.format("value", name="other")


class TestMandatorySections:
    """Test mandatory section behavior."""
    
    def test_mandatory_section_present(self):
        """Test mandatory section when field is present."""
        formatter = TemplateFormatter("{{!name}}")
        result = formatter.format(name="Required")
        assert result == "Required"
    
    def test_mandatory_section_missing(self):
        """Test mandatory section when field is missing."""
        formatter = TemplateFormatter("{{!name}}")
        with pytest.raises(MissingMandatoryFieldError):
            formatter.format()


class TestSectionLevelFormatting:
    """Test section-level formatting tokens."""
    
    def test_section_color_formatting(self):
        """Test section-level color formatting."""
        formatter = TemplateFormatter("{{#red;message}}")
        result = formatter.format(message="error")
        assert "\033[31m" in result  # ANSI red code
        assert "\033[0m" in result   # Reset code
        assert "error" in result
    
    def test_section_emphasis_formatting(self):
        """Test section-level emphasis formatting."""
        formatter = TemplateFormatter("{{@bold;message}}")
        result = formatter.format(message="important")
        assert "\033[1m" in result   # ANSI bold code
        assert "\033[0m" in result   # Reset code
        assert "important" in result
    
    def test_section_combined_formatting(self):
        """Test section-level combined formatting."""
        formatter = TemplateFormatter("{{#blue@italic;message}}")
        result = formatter.format(message="styled")
        assert "\033[34m" in result  # ANSI blue code
        assert "\033[3m" in result   # ANSI italic code
        assert "\033[0m" in result   # Reset code
        assert "styled" in result


class TestSectionLevelConditionals:
    """Test section-level conditional functionality."""
    
    def test_section_conditional_true(self):
        """Test section conditional when true."""
        def always_true(field):
            return True
        
        formatter = TemplateFormatter("{{?always_true;message}}", 
                                    functions={'always_true': always_true})
        result = formatter.format(message="visible")
        assert result == "visible"
    
    def test_section_conditional_false(self):
        """Test section conditional when false."""
        def always_false(field):
            return False
        
        formatter = TemplateFormatter("{{?always_false;message}}", 
                                    functions={'always_false': always_false})
        result = formatter.format(message="hidden")
        assert result == ""


class TestInlineFormatting:
    """Test inline formatting within sections."""
    
    def test_inline_color_change(self):
        """Test inline color formatting."""
        formatter = TemplateFormatter("{{Status: {#green}OK{#normal};message}}")
        result = formatter.format(message="test")
        assert "Status: " in result
        assert "\033[32m" in result  # Green for OK
        assert "\033[0m" in result   # Reset
        assert "test" in result
    
    def test_inline_emphasis_change(self):
        """Test inline emphasis formatting."""
        formatter = TemplateFormatter("{{Result: {@bold}SUCCESS{@normal};message}}")
        result = formatter.format(message="completed")
        assert "Result: " in result
        assert "\033[1m" in result   # Bold for SUCCESS
        assert "\033[0m" in result   # Reset
        assert "completed" in result


class TestInlineConditionals:
    """Test inline conditional formatting."""
    
    def test_simple_inline_conditional_true(self):
        """Test simple inline conditional when true."""
        def always_true(field):
            return True
        
        formatter = TemplateFormatter("{{before{?always_true}after;field}}", 
                                    functions={'always_true': always_true})
        result = formatter.format(field="test")
        assert "before" in result
        assert "after" in result
    
    def test_simple_inline_conditional_false(self):
        """Test simple inline conditional when false."""
        def always_false(field):
            return False
        
        formatter = TemplateFormatter("{{before{?always_false}after;field}}", 
                                    functions={'always_false': always_false})
        result = formatter.format(field="test")
        assert "before" in result
        assert "after" not in result
    
    def test_multiple_inline_conditionals(self):
        """Test multiple inline conditionals."""
        def check1(field):
            return "show1" in field
        
        def check2(field):
            return "show2" in field
        
        formatter = TemplateFormatter("{{start{?check1} first{?check2} second;field}}", 
                                    functions={'check1': check1, 'check2': check2})
        
        # Test first conditional true
        result1 = formatter.format(field="show1")
        assert "start" in result1
        assert "first" in result1
        assert "second" not in result1
        
        # Test second conditional true
        result2 = formatter.format(field="show2")
        assert "start" in result2
        assert "first" not in result2
        assert "second" in result2
        
        # Test both true
        result_both = formatter.format(field="show1 show2")
        assert "start" in result_both
        assert "first" in result_both
        assert "second" in result_both
    
    def test_conditional_reset_with_default(self):
        """Test conditional reset using default token."""
        def always_false(field):
            return False
        
        formatter = TemplateFormatter("{{start{?always_false} hidden{?default} shown;field}}", 
                                    functions={'always_false': always_false})
        result = formatter.format(field="test")
        assert "start" in result
        assert "hidden" not in result
        assert "shown" in result


class TestCustomFunctions:
    """Test custom function functionality."""
    
    def test_custom_color_function(self):
        """Test custom color function."""
        def status_color(field):
            return "green" if field == "ok" else "red"
        
        formatter = TemplateFormatter("{{#status_color;message}}", 
                                    functions={'status_color': status_color})
        
        result_ok = formatter.format(message="ok")
        assert "\033[32m" in result_ok  # Green
        
        result_error = formatter.format(message="error")
        assert "\033[31m" in result_error  # Red
    
    def test_custom_emphasis_function(self):
        """Test custom emphasis function."""
        def priority_style(field):
            return "bold" if field == "high" else "normal"
        
        formatter = TemplateFormatter("{{@priority_style;priority}}", 
                                    functions={'priority_style': priority_style})
        
        result_high = formatter.format(priority="high")
        assert "\033[1m" in result_high  # Bold
        
        result_low = formatter.format(priority="low")
        assert "low" in result_low and "\033[1m" not in result_low


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_unknown_function_color(self):
        """Test error when using unknown color function."""
        formatter = TemplateFormatter("{{#unknown_func;text}}")
        with pytest.raises(StringSmithError, match="Unknown function"):
            formatter.format(text="test")
    
    def test_unknown_function_conditional(self):
        """Test error when using unknown conditional function."""
        formatter = TemplateFormatter("{{?unknown_func;text}}")
        with pytest.raises(StringSmithError, match="Unknown conditional function"):
            formatter.format(text="test")
    
    def test_empty_template(self):
        """Test handling of empty template."""
        formatter = TemplateFormatter("")
        result = formatter.format()
        assert result == ""
    
    def test_literal_text_only(self):
        """Test template with only literal text."""
        formatter = TemplateFormatter("Just plain text")
        result = formatter.format()
        assert result == "Just plain text"
    
    def test_empty_field_value(self):
        """Test handling of empty field values."""
        formatter = TemplateFormatter("{{Value: ;field}}")
        result = formatter.format(field="")
        assert result == "Value: "
    
    def test_none_field_optional(self):
        """Test handling of None field values in optional sections."""
        formatter = TemplateFormatter("{{Value: ;field}}")
        result = formatter.format()  # field not provided
        assert result == ""  # Section omitted


class TestRealWorldScenarios:
    """Test realistic professional use cases."""
    
    def test_log_formatting(self):
        """Test log message formatting."""
        def level_color(field):
            colors = {"ERROR": "red", "WARN": "yellow", "INFO": "blue"}
            return colors.get(field.upper(), "white")
        
        formatter = TemplateFormatter(
            "{{[{#level_color};level;{#normal}] ;message}}", 
            functions={'level_color': level_color}
        )
        
        result = formatter.format(level="ERROR", message="System failure")
        assert "[" in result
        assert "]" in result
        assert "System failure" in result
        assert "\033[31m" in result  # Red for ERROR
    
    def test_status_reporting(self):
        """Test status reporting template."""
        def is_complete(field):
            return field == "completed"
        
        formatter = TemplateFormatter(
            "{{Task: ;task}} {{Status: ;status}}{?is_complete} ✓{{Duration: ;duration; seconds}}}",
            functions={'is_complete': is_complete}
        )
        
        # Completed task
        result_done = formatter.format(task="Deploy", status="completed", duration=45)
        assert "Task: Deploy" in result_done
        assert "Status: completed" in result_done
        assert "✓" in result_done
        assert "Duration: 45 seconds" in result_done
        
        # In progress task
        result_progress = formatter.format(task="Deploy", status="running")
        assert "Task: Deploy" in result_progress
        assert "Status: running" in result_progress
        assert "✓" not in result_progress
        assert "Duration:" not in result_progress


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic tests...")
        
        # Run a subset of tests manually
        test_basic = TestBasicFormatting()
        test_basic.test_simple_field_only()
        test_basic.test_field_with_prefix()
        test_basic.test_field_with_prefix_and_suffix()
        print("✓ Basic formatting tests passed")
        
        test_mandatory = TestMandatorySections()
        test_mandatory.test_mandatory_section_present()
        print("✓ Mandatory section tests passed")
        
        test_section = TestSectionLevelFormatting()
        test_section.test_section_color_formatting()
        print("✓ Section formatting tests passed")
        
        print("All basic tests completed successfully!")