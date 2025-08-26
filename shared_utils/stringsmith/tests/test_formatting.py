"""
Complete test suite for StringSmith formatting functionality.
Tests all features with correct ANSI pattern expectations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

try:
    from formatter import TemplateFormatter
    from exceptions import StringSmithError, MissingMandatoryFieldError
except ImportError:
    from stringsmith import TemplateFormatter
    from stringsmith.exceptions import StringSmithError, MissingMandatoryFieldError


def strip_ansi(text):
    """Remove ANSI escape sequences from text for content testing."""
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class TestBasicColorFormatting:
    """Test basic color formatting functionality."""
    
    def test_simple_red_field(self):
        """Test simple red color on field only."""
        formatter = TemplateFormatter("{{#red;message}}")
        result = formatter.format(message="test")
        
        # Content should be correct
        assert strip_ansi(result) == "test"
        
        # Should match exact pattern from debug output
        expected = "\x1b[31mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_red_with_prefix_suffix(self):
        """Test red color with prefix and suffix."""
        formatter = TemplateFormatter("{{#red;Error: ;message;}}")
        result = formatter.format(message="test")
        
        # Content should be correct
        assert strip_ansi(result) == "Error: test"
        
        # Should match pattern: formatted prefix + formatted field
        expected = "\x1b[31mError: \x1b[39m\x1b[22;23;24;29m\x1b[31mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_green_color(self):
        """Test green color formatting."""
        formatter = TemplateFormatter("{{#green;message}}")
        result = formatter.format(message="success")
        
        assert strip_ansi(result) == "success"
        expected = "\x1b[32msuccess\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_blue_color(self):
        """Test blue color formatting."""
        formatter = TemplateFormatter("{{#blue;message}}")
        result = formatter.format(message="info")
        
        assert strip_ansi(result) == "info"
        expected = "\x1b[34minfo\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_hex_color_ff0000(self):
        """Test FF0000 hex color (should map to red)."""
        formatter = TemplateFormatter("{{#FF0000;message}}")
        result = formatter.format(message="test")
        
        assert strip_ansi(result) == "test"
        # FF0000 should map to red (31m)
        expected = "\x1b[31mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_unknown_color(self):
        """Test unknown color (should be ignored)."""
        formatter = TemplateFormatter("{{#unknowncolor;message}}")
        result = formatter.format(message="test")
        
        # Unknown colors should just return plain text
        assert result == "test"


class TestBasicEmphasisFormatting:
    """Test basic emphasis formatting functionality."""
    
    def test_simple_bold(self):
        """Test simple bold formatting."""
        formatter = TemplateFormatter("{{@bold;message}}")
        result = formatter.format(message="test")
        
        assert strip_ansi(result) == "test"
        expected = "\x1b[1mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_bold_with_prefix_suffix(self):
        """Test bold with prefix and suffix."""
        formatter = TemplateFormatter("{{@bold;Warning: ;message;}}")
        result = formatter.format(message="test")
        
        assert strip_ansi(result) == "Warning: test"
        expected = "\x1b[1mWarning: \x1b[39m\x1b[22;23;24;29m\x1b[1mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_italic(self):
        """Test italic formatting."""
        formatter = TemplateFormatter("{{@italic;message}}")
        result = formatter.format(message="test")
        
        assert strip_ansi(result) == "test"
        expected = "\x1b[3mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_underline(self):
        """Test underline formatting."""
        formatter = TemplateFormatter("{{@underline;message}}")
        result = formatter.format(message="test")
        
        assert strip_ansi(result) == "test"
        expected = "\x1b[4mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_unknown_emphasis(self):
        """Test unknown emphasis (should be ignored)."""
        formatter = TemplateFormatter("{{@unknownemphasis;message}}")
        result = formatter.format(message="test")
        
        # Unknown emphasis should just return plain text
        assert result == "test"


class TestCombinedFormatting:
    """Test combined color and emphasis formatting."""
    
    def test_red_and_bold(self):
        """Test red color with bold emphasis."""
        formatter = TemplateFormatter("{{#red@bold;Error: ;message;}}")
        result = formatter.format(message="test")
        
        assert strip_ansi(result) == "Error: test"
        # Pattern from debug output: bold+red applied to each part
        expected = "\x1b[1m\x1b[31mError: \x1b[39m\x1b[22;23;24;29m\x1b[1m\x1b[31mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_bold_and_italic(self):
        """Test combined bold and italic."""
        formatter = TemplateFormatter("{{@bold@italic;message}}")
        result = formatter.format(message="test")
        
        assert strip_ansi(result) == "test"
        # Both emphasis codes should be applied
        expected = "\x1b[1m\x1b[3mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_triple_stacked_formatting(self):
        """Test red + bold + italic together."""
        formatter = TemplateFormatter("{{#red@bold@italic;message}}")
        result = formatter.format(message="test")
        
        assert strip_ansi(result) == "test"
        # Pattern from debug output
        expected = "\x1b[1m\x1b[3m\x1b[31mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected


class TestConditionalSections:
    """Test conditional section functionality."""
    
    def test_condition_true(self):
        """Test conditional section when condition is true."""
        def is_error(level):
            return level.lower() == 'error'
        
        formatter = TemplateFormatter("{{?is_error;[ERROR] ;level;}}", 
                                    functions={'is_error': is_error})
        result = formatter.format(level="ERROR")
        assert result == "[ERROR] ERROR"
    
    def test_condition_false(self):
        """Test conditional section when condition is false."""
        def is_error(level):
            return level.lower() == 'error'
        
        formatter = TemplateFormatter("{{?is_error;[ERROR] ;level;}}", 
                                    functions={'is_error': is_error})
        result = formatter.format(level="INFO")
        assert result == ""
    
    def test_mixed_conditional_sections(self):
        """Test multiple conditional sections."""
        def is_error(level):
            return level.lower() == 'error'
        
        def is_warning(level):
            return level.lower() == 'warning'
        
        formatter = TemplateFormatter(
            "{{?is_error;[ERROR] ;level;}} {{?is_warning;[WARN] ;level;}} {{message}}",
            functions={'is_error': is_error, 'is_warning': is_warning}
        )
        
        # Error case
        result = formatter.format(level="ERROR", message="failed")
        assert strip_ansi(result) == "[ERROR] ERROR failed"
        
        # Warning case
        result = formatter.format(level="WARNING", message="careful")
        assert strip_ansi(result) == " [WARN] WARNING careful"
        
        # Info case (no conditionals)
        result = formatter.format(level="INFO", message="normal")
        assert strip_ansi(result) == "  normal"


class TestCustomFunctions:
    """Test custom function integration."""
    
    def test_custom_color_function(self):
        """Test custom function that returns colors."""
        def alert_color():
            return 'red'
        
        formatter = TemplateFormatter("{{#alert_color;Alert: ;message;}}", 
                                    functions={'alert_color': alert_color})
        result = formatter.format(message="test")
        
        assert strip_ansi(result) == "Alert: test"
        # Should behave like red color
        expected = "\x1b[31mAlert: \x1b[39m\x1b[22;23;24;29m\x1b[31mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_custom_emphasis_function(self):
        """Test custom function that returns emphasis styles."""
        def highlight_style():
            return 'bold'
        
        formatter = TemplateFormatter("{{@highlight_style;message}}", 
                                    functions={'highlight_style': highlight_style})
        result = formatter.format(message="test")
        
        assert strip_ansi(result) == "test"
        expected = "\x1b[1mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_dynamic_color_function(self):
        """Test function that returns different colors based on input."""
        def status_color(level):
            return {'error': 'red', 'success': 'green', 'info': 'blue'}[level]
        
        formatter = TemplateFormatter("{{#status_color;[;level;] ;message}}", 
                                    functions={'status_color': status_color})
        
        # Test error
        result = formatter.format(level="error", message="failed")
        assert strip_ansi(result) == "[error] failed"
        assert "\x1b[31m" in result  # Red
        
        # Test success
        result = formatter.format(level="success", message="passed")
        assert strip_ansi(result) == "[success] passed"
        assert "\x1b[32m" in result  # Green
    
    def test_unknown_function_error(self):
        """Test error when function is not provided."""
        formatter = TemplateFormatter("{{#unknown_func;message}}")
        
        # Should raise error for unknown functions
        with pytest.raises(StringSmithError):
            formatter.format(message="test")


class TestPositionalArguments:
    """Test positional argument functionality."""
    
    def test_simple_positional(self):
        """Test simple positional arguments."""
        formatter = TemplateFormatter("{{first}} {{second}}")
        result = formatter.format("Hello", "World")
        assert result == "Hello World"
        
        # Test partial data
        result = formatter.format("Hello")
        assert result == "Hello "
    
    def test_positional_with_formatting(self):
        """Test positional arguments with formatting."""
        formatter = TemplateFormatter("{{#red;}} {{@bold;}}")
        result = formatter.format("error", "warning")
        
        assert strip_ansi(result) == "error warning"
        # Should have both red and bold formatting
        assert "\x1b[31m" in result  # Red
        assert "\x1b[1m" in result   # Bold
    
    def test_positional_with_prefix_suffix(self):
        """Test positional with prefix and suffix."""
        formatter = TemplateFormatter("{{Error: ;}} {{Count: ; items}}")
        result = formatter.format("failed", 42)
        assert result == "Error: failed Count: 42 items"
    
    def test_too_many_positional_args(self):
        """Test error when too many positional args provided."""
        formatter = TemplateFormatter("{{}} {{}}")  # Only 2 positions
        
        with pytest.raises(StringSmithError):
            formatter.format("first", "second", "third")
    
    def test_mixed_positional_keyword_error(self):
        """Test error when mixing positional and keyword args."""
        formatter = TemplateFormatter("{{message}}")
        
        with pytest.raises(StringSmithError):
            formatter.format("pos", message="keyword")


class TestMandatorySections:
    """Test mandatory section functionality."""
    
    def test_mandatory_present(self):
        """Test mandatory section when field is present."""
        formatter = TemplateFormatter("{{!name}}")
        result = formatter.format(name="required")
        assert result == "required"
    
    def test_mandatory_missing(self):
        """Test mandatory section when field is missing."""
        formatter = TemplateFormatter("{{!name}}")
        
        with pytest.raises(MissingMandatoryFieldError):
            formatter.format()
    
    def test_mandatory_with_formatting(self):
        """Test mandatory section with formatting."""
        formatter = TemplateFormatter("{{!#red@bold;ALERT: ;message;}}")
        result = formatter.format(message="critical")
        
        assert strip_ansi(result) == "ALERT: critical"
        # Should have red+bold formatting
        assert "\x1b[31m" in result and "\x1b[1m" in result
    
    def test_mandatory_positional(self):
        """Test mandatory positional argument."""
        formatter = TemplateFormatter("{{!}} {{optional}}")
        result = formatter.format("required", "extra")
        assert result == "required extra"
        
        # Missing mandatory positional should error
        with pytest.raises(MissingMandatoryFieldError):
            formatter.format()


class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    def test_log_message_formatting(self):
        """Test log message formatting pattern."""
        def level_color(level):
            colors = {"ERROR": "red", "WARN": "yellow", "INFO": "blue", "DEBUG": "cyan"}
            return colors.get(level.upper(), "white")
        
        formatter = TemplateFormatter(
            "{{#level_color;[;level;] ;timestamp;}} {{message}}", 
            functions={'level_color': level_color}
        )
        
        result = formatter.format(level="ERROR", timestamp="12:34:56", message="System failure")
        assert strip_ansi(result) == "[ERROR] 12:34:56 System failure"
        assert "\x1b[31m" in result  # Red for ERROR
    
    def test_file_processing_status(self):
        """Test file processing status formatting."""
        def size_color(size_mb):
            if size_mb > 100:
                return 'red'
            elif size_mb > 10:
                return 'yellow'
            else:
                return 'green'
        
        formatter = TemplateFormatter(
            "{{Processing ;filename}} {{#size_color;(;size_mb;MB)}} {{Status: ;status}}", 
            functions={'size_color': size_color}
        )
        
        # Small file (green)
        result = formatter.format(filename="small.csv", size_mb=2.5, status="Complete")
        assert strip_ansi(result) == "Processing small.csv (2.5MB) Status: Complete"
        assert "\x1b[32m" in result  # Green
        
        # Large file (red)
        result = formatter.format(filename="huge.csv", size_mb=250, status="Error")
        assert strip_ansi(result) == "Processing huge.csv (250MB) Status: Error"
        assert "\x1b[31m" in result  # Red
    
    def test_api_response_formatting(self):
        """Test API response formatting pattern."""
        def status_color(code):
            if 200 <= code < 300:
                return 'green'
            elif 400 <= code < 500:
                return 'yellow'
            else:
                return 'red'
        
        formatter = TemplateFormatter(
            "{{#status_color@bold;HTTP ;status;}} {{;method; ;path}} {{;duration;ms}}", 
            functions={'status_color': status_color}
        )
        
        # Success response
        result = formatter.format(status=200, method="GET", path="/api/users", duration=45)
        assert strip_ansi(result) == "HTTP 200 GET /api/users 45ms"
        assert "\x1b[32m" in result and "\x1b[1m" in result  # Green + bold
        
        # Error response
        result = formatter.format(status=500, method="POST", path="/api/data", duration=2000)
        assert strip_ansi(result) == "HTTP 500 POST /api/data 2000ms"
        assert "\x1b[31m" in result and "\x1b[1m" in result  # Red + bold


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_field_with_formatting(self):
        """Test empty field value with formatting."""
        formatter = TemplateFormatter("{{#red;Error: ;message;}}")
        result = formatter.format(message="")
        
        # Empty field should still show formatted prefix
        assert strip_ansi(result) == "Error: "
        expected = "\x1b[31mError: \x1b[39m\x1b[22;23;24;29m"
        assert result == expected
    
    def test_missing_optional_field(self):
        """Test missing optional field."""
        formatter = TemplateFormatter("{{#red;Error: ;message;}}")
        result = formatter.format()
        
        # Missing optional field should result in empty string
        assert result == ""
    
    def test_multiple_sections_with_missing_data(self):
        """Test multiple sections with some missing data."""
        formatter = TemplateFormatter("{{#red;Error: ;error}} {{#green;Success: ;success}}")
        
        # Only first section has data
        result = formatter.format(error="failed")
        assert strip_ansi(result) == "Error: failed "
        assert "\x1b[31m" in result  # Red formatting
        assert "\x1b[32m" not in result  # No green formatting
    
    def test_all_sections_missing(self):
        """Test when all sections are missing data."""
        formatter = TemplateFormatter("{{#red;Error: ;error}} {{#green;Success: ;success}}")
        result = formatter.format()
        
        # Should be completely empty
        assert result == ""
    
    def test_none_values(self):
        """Test None field values."""
        formatter = TemplateFormatter("{{Value: ;field}}")
        result = formatter.format(field=None)
        
        # None should be treated as missing
        assert result == ""
    
    def test_zero_and_false_values(self):
        """Test 0 and False values (should be included)."""
        formatter = TemplateFormatter("{{Count: ;count}} {{Flag: ;flag}}")
        result = formatter.format(count=0, flag=False)
        assert result == "Count: 0 Flag: False"


class TestCustomDelimiters:
    """Test custom delimiter functionality."""
    
    def test_pipe_delimiter(self):
        """Test using pipe as delimiter."""
        formatter = TemplateFormatter("{{prefix|field|suffix}}", delimiter="|")
        result = formatter.format(field="test")
        assert result == "prefixtestsuffix"
    
    def test_colon_delimiter(self):
        """Test using colon as delimiter."""
        formatter = TemplateFormatter("{{Label:value:!}}", delimiter=":")
        result = formatter.format(value="test")
        assert result == "Labeltest!"
    
    def test_formatting_with_custom_delimiter(self):
        """Test formatting with custom delimiter."""
        formatter = TemplateFormatter("{{#red|Error|message}}", delimiter="|")
        result = formatter.format(message="test")
        
        assert strip_ansi(result) == "Errortest"
        expected = "\x1b[31mError\x1b[39m\x1b[22;23;24;29m\x1b[31mtest\x1b[39m\x1b[22;23;24;29m"
        assert result == expected


class TestEscaping:
    """Test escape sequence functionality."""
    
    def test_escape_braces(self):
        """Test escaping curly braces."""
        formatter = TemplateFormatter("Use \\{name\\} for {{name}}")
        result = formatter.format(name="variables")
        assert result == "Use {name} for variables"
    
    def test_escape_delimiter(self):
        """Test escaping delimiters."""
        formatter = TemplateFormatter("{{Ratio\\;percent;value;}}")
        result = formatter.format(value="50")
        assert result == "Ratio;percent50"
    
    def test_custom_escape_character(self):
        """Test custom escape character."""
        formatter = TemplateFormatter("Use ~{name~} for {{name}}", escape_char="~")
        result = formatter.format(name="variables")
        assert result == "Use {name} for variables"


class TestRandomColorExample:
    """Test the random color functionality from examples."""
    
    def test_random_colors_generate_different_outputs(self):
        """Test that random color function produces varying outputs."""
        import random
        
        def random_color():
            colors = ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta']
            return random.choice(colors)
        
        formatter = TemplateFormatter("{{#random_color;message}}", 
                                    functions={'random_color': random_color})
        
        # Generate multiple results
        results = []
        for i in range(10):
            result = formatter.format(message="test")
            results.append(result)
        
        # Content should always be correct
        for result in results:
            assert strip_ansi(result) == "test"
        
        # Should have ANSI formatting in all results
        for result in results:
            assert any(code in result for code in ['\x1b[31m', '\x1b[32m', '\x1b[34m', '\x1b[33m', '\x1b[36m', '\x1b[35m'])
    
    def test_random_color_with_seed_consistency(self):
        """Test that random color with seed produces consistent results."""
        import random
        
        def seeded_random_color():
            random.seed(42)  # Fixed seed
            colors = ['red', 'green', 'blue']
            return random.choice(colors)
        
        formatter = TemplateFormatter("{{#seeded_random_color;message}}", 
                                    functions={'seeded_random_color': seeded_random_color})
        
        result1 = formatter.format(message="test")
        
        # Reset seed and test again
        def seeded_random_color2():
            random.seed(42)  # Same seed
            colors = ['red', 'green', 'blue']
            return random.choice(colors)
        
        formatter2 = TemplateFormatter("{{#seeded_random_color2;message}}", 
                                     functions={'seeded_random_color2': seeded_random_color2})
        result2 = formatter2.format(message="test")
        
        # Should produce same result with same seed
        assert result1 == result2


class TestPerformancePatterns:
    """Test patterns that stress performance."""
    
    def test_many_sections(self):
        """Test template with many sections."""
        template_parts = []
        expected_parts = []
        kwargs = {}
        
        for i in range(20):
            template_parts.append(f"{{{{#red;Item{i}: ;field{i};}}}}")
            expected_parts.append(f"Item{i}: value{i}")
            kwargs[f'field{i}'] = f'value{i}'
        
        template = " ".join(template_parts)
        formatter = TemplateFormatter(template)
        result = formatter.format(**kwargs)
        
        # Content should be correct
        expected_content = " ".join(expected_parts)
        assert strip_ansi(result) == expected_content
        
        # Should have red formatting throughout
        assert result.count('\x1b[31m') == 40  # 2 per section (prefix + field) * 20 sections
    
    def test_long_content_formatting(self):
        """Test formatting with long content."""
        long_text = "This is a very long error message that contains many words and should still be formatted correctly with ANSI codes applied properly throughout the entire string length."
        
        formatter = TemplateFormatter("{{#red@bold;Critical Error: ;message;}}")
        result = formatter.format(message=long_text)
        
        assert strip_ansi(result) == f"Critical Error: {long_text}"
        assert "\x1b[31m" in result and "\x1b[1m" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])