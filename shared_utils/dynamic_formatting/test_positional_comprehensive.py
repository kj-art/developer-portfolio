"""
Comprehensive test suite for positional arguments implementation.

Tests all the parsing rules and use cases specified:
- {{}} - valid for positional only
- {{#red}} - valid for positional only (token indicates sectional formatting)
- {{my_field;}} - valid for both (prefix;field pattern where my_field is prefix)
- {{my_field}} - valid for both (single field)
- {{#red;my_field}} - valid for both (token;field pattern)
- {{prefix;my_field}} - valid for both (prefix;field pattern)
- {{prefix;my_field;suffix}} - valid for both (prefix;field;suffix pattern)
- {{#red@bold;prefix;my_field}} - valid for both (token;prefix;field pattern)
- {{#red@bold;prefix;my_field;suffix}} - valid for both (token;prefix;field;suffix pattern)

Also tests the core missing data behavior with positional arguments.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared_utils.dynamic_formatting import DynamicFormatter, DynamicFormattingError, RequiredFieldError


class TestPositionalArgumentParsing:
    """Test all valid positional argument parsing patterns"""
    
    def test_empty_field_positional_only(self):
        """Test {{}} - valid for positional only"""
        formatter = DynamicFormatter("{{}}")
        
        # Should work with positional args
        result = formatter.format("test")
        assert result == "test"
        
        # Should work with no args (missing data)
        result = formatter.format()
        assert result == ""
    
    def test_token_only_positional(self):
        """Test {{#red}} - valid for positional only (token indicates sectional formatting)"""
        formatter = DynamicFormatter("{{#red}}")
        
        # Should work with positional args
        result = formatter.format("test")
        assert "test" in result  # Contains the text, formatted with red
        
        # Should work with no args (missing data)
        result = formatter.format()
        assert result == ""
    
    def test_field_semicolon_pattern(self):
        """Test {{my_field;}} - valid for both (my_field is prefix, empty field)"""
        formatter = DynamicFormatter("{{my_field;}}")
        
        # Positional: my_field is treated as prefix
        result = formatter.format("test")
        assert result == "my_fieldtest"
        
        # Missing data
        result = formatter.format()
        assert result == ""
    
    def test_single_field_pattern(self):
        """Test {{my_field}} - valid for both (single field)"""
        formatter = DynamicFormatter("{{my_field}}")
        
        # Positional: field name ignored, uses positional value
        result = formatter.format("test")
        assert result == "test"
        
        # Keyword: uses field name
        result = formatter.format(my_field="test")
        assert result == "test"
        
        # Missing data
        result = formatter.format()
        assert result == ""
    
    def test_token_field_pattern(self):
        """Test {{#red;my_field}} - valid for both (token;field pattern)"""
        formatter = DynamicFormatter("{{#red;my_field}}")
        
        # Positional
        result = formatter.format("test")
        assert "test" in result  # Contains the text, formatted with red
        
        # Keyword
        result = formatter.format(my_field="test")
        assert "test" in result  # Contains the text, formatted with red
        
        # Missing data
        result = formatter.format()
        assert result == ""
    
    def test_prefix_field_pattern(self):
        """Test {{prefix;my_field}} - valid for both (prefix;field pattern)"""
        formatter = DynamicFormatter("{{prefix;my_field}}")
        
        # Positional
        result = formatter.format("test")
        assert result == "prefixtest"
        
        # Keyword
        result = formatter.format(my_field="test")
        assert result == "prefixtest"
        
        # Missing data
        result = formatter.format()
        assert result == ""
    
    def test_prefix_field_suffix_pattern(self):
        """Test {{prefix;my_field;suffix}} - valid for both (prefix;field;suffix pattern)"""
        formatter = DynamicFormatter("{{prefix;my_field;suffix}}")
        
        # Positional
        result = formatter.format("test")
        assert result == "prefixtestsuffix"
        
        # Keyword
        result = formatter.format(my_field="test")
        assert result == "prefixtestsuffix"
        
        # Missing data
        result = formatter.format()
        assert result == ""
    
    def test_token_prefix_field_pattern(self):
        """Test {{#red@bold;prefix;my_field}} - valid for both (token;prefix;field pattern)"""
        formatter = DynamicFormatter("{{#red@bold;prefix;my_field}}")
        
        # Positional
        result = formatter.format("test")
        assert "prefix" in result and "test" in result
        
        # Keyword
        result = formatter.format(my_field="test")
        assert "prefix" in result and "test" in result
        
        # Missing data
        result = formatter.format()
        assert result == ""
    
    def test_token_prefix_field_suffix_pattern(self):
        """Test {{#red@bold;prefix;my_field;suffix}} - valid for both (token;prefix;field;suffix pattern)"""
        formatter = DynamicFormatter("{{#red@bold;prefix;my_field;suffix}}")
        
        # Positional
        result = formatter.format("test")
        assert "prefix" in result and "test" in result and "suffix" in result
        
        # Keyword
        result = formatter.format(my_field="test")
        assert "prefix" in result and "test" in result and "suffix" in result
        
        # Missing data
        result = formatter.format()
        assert result == ""


class TestPositionalMissingDataBehavior:
    """Test the core missing data behavior with positional arguments"""
    
    def test_four_sections_one_argument(self):
        """Test 4 sections with 1 argument - only first section should appear"""
        formatter = DynamicFormatter("{{Error: ;}} {{Count: ;}} {{Duration: ;}} {{Memory: ;}}")
        
        result = formatter.format("Failed")
        assert result == "Error: Failed   "  # Note: trailing spaces from missing sections
    
    def test_four_sections_two_arguments(self):
        """Test 4 sections with 2 arguments - first two sections should appear"""
        formatter = DynamicFormatter("{{Error: ;}} {{Count: ;}} {{Duration: ;}} {{Memory: ;}}")
        
        result = formatter.format("Failed", 42)
        assert result == "Error: Failed Count: 42  "  # Note: trailing spaces from missing sections
    
    def test_four_sections_all_arguments(self):
        """Test 4 sections with all 4 arguments - all sections should appear"""
        formatter = DynamicFormatter("{{Error: ;}} {{Count: ;}} {{Duration: ;}} {{Memory: ;}}")
        
        result = formatter.format("Failed", 42, 12.5, 128)
        assert result == "Error: Failed Count: 42 Duration: 12.5 Memory: 128"
    
    def test_mixed_patterns_missing_data(self):
        """Test various patterns with missing data"""
        formatter = DynamicFormatter("{{#red;Status: ;}} {{prefix;}} {{;suffix}}")
        
        # One argument
        result = formatter.format("OK")
        assert "Status: OK" in result and "prefix" not in result and "suffix" not in result
        
        # Two arguments
        result = formatter.format("OK", "middle")
        expected_parts = ["Status: OK", "prefixmiddle"]
        for part in expected_parts:
            assert part in result or part.replace("Status: OK", "OK") in result
        
        # Three arguments
        result = formatter.format("OK", "middle", "end")
        # All three sections should appear in some form


class TestPositionalErrorHandling:
    """Test error conditions with positional arguments"""
    
    def test_too_many_positional_arguments(self):
        """Test error when too many positional arguments provided"""
        formatter = DynamicFormatter("{{}} {{}}")  # Only 2 positional fields
        
        with pytest.raises(DynamicFormattingError) as exc_info:
            formatter.format("first", "second", "third")  # 3 arguments
        
        assert "Too many positional arguments: expected 2, got 3" in str(exc_info.value)
    
    def test_mixed_arguments_error(self):
        """Test error when mixing positional and keyword arguments"""
        formatter = DynamicFormatter("{{}} {{}}")
        
        with pytest.raises(DynamicFormattingError) as exc_info:
            formatter.format("pos", keyword="kw")
        
        assert "Cannot mix positional and keyword arguments" in str(exc_info.value)
    
    def test_required_field_missing_positional(self):
        """Test required field error with positional arguments"""
        formatter = DynamicFormatter("{{!}}")  # Required positional field
        
        with pytest.raises(RequiredFieldError) as exc_info:
            formatter.format()  # No arguments
        
        # Should show user-friendly position description
        assert "position 1" in str(exc_info.value)
    
    def test_user_friendly_error_messages(self):
        """Test that error messages convert synthetic field names to positions"""
        formatter = DynamicFormatter("{{}} {{!}}")  # Second field is required
        
        with pytest.raises(RequiredFieldError) as exc_info:
            formatter.format("first")  # Missing required second field
        
        assert "position 2" in str(exc_info.value)


class TestPositionalWithFormatting:
    """Test positional arguments with various formatting options"""
    
    def test_positional_with_colors(self):
        """Test positional arguments with color formatting"""
        formatter = DynamicFormatter("{{#red;}} {{#green;}}")
        
        result = formatter.format("error", "success")
        assert "error" in result and "success" in result
        
        # Test missing data
        result = formatter.format("error")
        assert "error" in result and "success" not in result
    
    def test_positional_with_text_styles(self):
        """Test positional arguments with text style formatting"""
        formatter = DynamicFormatter("{{@bold;}} {{@italic;}}")
        
        result = formatter.format("bold_text", "italic_text")
        assert "bold_text" in result and "italic_text" in result
        
        # Test missing data
        result = formatter.format("bold_text")
        assert "bold_text" in result and "italic_text" not in result
    
    def test_positional_with_combined_formatting(self):
        """Test positional arguments with combined formatting"""
        formatter = DynamicFormatter("{{#red@bold;Error: ;}} {{#green@italic;Success: ;}}")
        
        result = formatter.format("Failed", "Passed")
        assert "Error: Failed" in result and "Success: Passed" in result
        
        # Test missing data
        result = formatter.format("Failed")
        assert "Error: Failed" in result and "Success: Passed" not in result


class TestPositionalWithConditionals:
    """Test positional arguments with conditional functions"""
    
    def test_positional_with_section_level_conditional(self):
        """Test positional arguments with section-level conditionals"""
        def show_errors(value):
            return value != "OK"
        
        formatter = DynamicFormatter("{{?show_errors;Error: ;}} {{Status: ;}}", 
                                   functions={'show_errors': show_errors})
        
        # Should show error section
        result = formatter.format("Failed", "Bad")
        assert "Error: Failed" in result and "Status: Bad" in result
        
        # Should hide error section
        result = formatter.format("OK", "Good")
        assert "Error:" not in result and "Status: Good" in result
    
    def test_positional_with_function_fallback(self):
        """Test positional arguments with function fallback for colors"""
        def status_color(status):
            return 'red' if status == 'error' else 'green'
        
        formatter = DynamicFormatter("{{#status_color;Status: ;}}", 
                                   functions={'status_color': status_color})
        
        result1 = formatter.format("error")
        result2 = formatter.format("success")
        
        assert "Status: error" in result1
        assert "Status: success" in result2


class TestPositionalEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_template(self):
        """Test empty template"""
        formatter = DynamicFormatter("")
        result = formatter.format("ignored")
        assert result == ""
    
    def test_literal_only_template(self):
        """Test template with only literal text"""
        formatter = DynamicFormatter("No variables here")
        
        # Should not accept positional arguments when no field sections exist
        with pytest.raises(DynamicFormattingError):
            formatter.format("ignored")
        
        # Should work with no arguments
        result = formatter.format()
        assert result == "No variables here"
    
    def test_empty_string_arguments(self):
        """Test with empty string arguments"""
        formatter = DynamicFormatter("{{}} {{}}")
        
        result = formatter.format("", "test")
        assert result == " test"
        
        result = formatter.format("test", "")
        assert result == "test "
    
    def test_none_arguments(self):
        """Test with None arguments (should cause sections to disappear)"""
        formatter = DynamicFormatter("{{}} {{}}")
        
        result = formatter.format(None, "test")
        assert result == " test"
        
        result = formatter.format("test", None)
        assert result == "test "
    
    def test_zero_positional_sections(self):
        """Test template with keyword fields when using positional args"""
        formatter = DynamicFormatter("{{named_field}}")
        
        # Should work with keyword args
        result = formatter.format(named_field="test")
        assert result == "test"
        
        # Should work with positional args - field name is ignored
        result = formatter.format("test")
        assert result == "test"


if __name__ == "__main__":
    # Run specific test classes for debugging
    pytest.main([__file__ + "::TestPositionalArgumentParsing", "-v"])
    pytest.main([__file__ + "::TestPositionalMissingDataBehavior", "-v"])
    pytest.main([__file__ + "::TestPositionalErrorHandling", "-v"])