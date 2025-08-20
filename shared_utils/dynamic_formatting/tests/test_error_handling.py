"""
Test suite for error handling in dynamic formatting package.

Tests various error conditions, edge cases, and graceful degradation
using the modern FormatterConfig approach.
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
    from shared_utils.dynamic_formatting.dynamic_formatting import (
        DynamicFormattingError, RequiredFieldError, FunctionNotFoundError, DynamicLoggingFormatter
    )
    from shared_utils.dynamic_formatting.formatters.base import FormatterError, FunctionExecutionError
    from shared_utils.dynamic_formatting.template_parser import ParseError
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running pytest from the project root directory")


class TestParsingErrors:
    """Test template parsing error conditions"""
    
    @pytest.mark.error
    def test_unclosed_template_section(self):
        """Test error for unclosed template sections"""
        with pytest.raises(ParseError) as exc_info:
            DynamicFormatter("{{unclosed template")
        
        assert "Unclosed template section" in str(exc_info.value)
    
    @pytest.mark.error
    def test_empty_template_sections(self):
        """Test handling of empty template sections"""
        formatter = DynamicFormatter("{{}} {{valid;field}}")
        result = formatter.format("positional", field="named")
        assert "positional named" in result


class TestRequiredFieldErrors:
    """Test required field error conditions"""
    
    @pytest.mark.error
    def test_required_field_missing_keyword(self):
        """Test required field error with keyword arguments"""
        formatter = DynamicFormatter("{{!;Critical: ;message}}")
        
        with pytest.raises(RequiredFieldError) as exc_info:
            formatter.format()
        
        error_msg = str(exc_info.value)
        assert "Required field" in error_msg
        assert "message" in error_msg
    
    @pytest.mark.error
    def test_required_field_missing_positional(self):
        """Test required field error with positional arguments"""
        formatter = DynamicFormatter("{{!}}")
        
        with pytest.raises(RequiredFieldError) as exc_info:
            formatter.format()
        
        error_msg = str(exc_info.value)
        assert "Required field" in error_msg
    
    @pytest.mark.error
    def test_required_field_with_none_value(self):
        """Test required field with None value"""
        formatter = DynamicFormatter("{{!;Critical: ;message}}")
        
        # None values should still trigger required field error
        with pytest.raises(RequiredFieldError):
            formatter.format(message=None)


class TestFormatterErrors:
    """Test formatter-specific error conditions"""
    
    @pytest.mark.error
    def test_invalid_color_token(self):
        """Test error for invalid color tokens"""
        formatter = DynamicFormatter("{{#invalid_color;Text: ;field}}")
        
        with pytest.raises(FormatterError) as exc_info:
            formatter.format(field="test")
        
        assert "invalid_color" in str(exc_info.value)
    
    @pytest.mark.error
    def test_invalid_text_style_token(self):
        """Test error for invalid text style tokens"""
        formatter = DynamicFormatter("{{@invalid_style;Text: ;field}}")
        
        with pytest.raises(FormatterError) as exc_info:
            formatter.format(field="test")
        
        assert "invalid_style" in str(exc_info.value)
    
    @pytest.mark.error
    def test_malformed_hex_color(self):
        """Test error for malformed hex colors"""
        formatter = DynamicFormatter("{{#gggggg;Text: ;field}}")  # Invalid hex
        
        with pytest.raises(FormatterError) as exc_info:
            formatter.format(field="test")
        
        assert "gggggg" in str(exc_info.value)


class TestFunctionErrors:
    """Test function-related error conditions"""
    
    @pytest.mark.error
    def test_missing_function(self):
        """Test error when function is not provided"""
        formatter = DynamicFormatter("{{#missing_func;Text: ;field}}")
        
        with pytest.raises(FormatterError) as exc_info:
            formatter.format(field="test")
        
        assert "missing_func" in str(exc_info.value)
    
    @pytest.mark.error
    def test_function_execution_failure(self):
        """Test error when function execution fails"""
        def failing_function(value):
            raise ValueError("Function failed")
        
        config = FormatterConfig(functions={"failing_function": failing_function})
        formatter = DynamicFormatter(
            "{{#failing_function;Text: ;field}}",
            config=config
        )
        
        with pytest.raises(FunctionExecutionError) as exc_info:
            formatter.format(field="test")
        
        assert "failing_function" in str(exc_info.value)
    
    @pytest.mark.error
    def test_function_wrong_return_type(self):
        """Test error when function returns wrong type"""
        def bad_function(value):
            return 123  # Should return string
        
        config = FormatterConfig(functions={"bad_function": bad_function})
        formatter = DynamicFormatter(
            "{{#bad_function;Text: ;field}}",
            config=config
        )
        
        with pytest.raises(FunctionExecutionError) as exc_info:
            formatter.format(field="test")
        
        assert "bad_function" in str(exc_info.value)
    
    @pytest.mark.error
    def test_conditional_function_not_found(self):
        """Test error when conditional function is missing"""
        formatter = DynamicFormatter("{{?missing_condition;Text: ;field}}")
        
        with pytest.raises(FunctionNotFoundError) as exc_info:
            formatter.format(field="test")
        
        assert "missing_condition" in str(exc_info.value)


class TestArgumentErrors:
    """Test argument-related error conditions"""
    
    @pytest.mark.error
    def test_mixed_positional_keyword_args(self):
        """Test error when mixing positional and keyword arguments"""
        config = FormatterConfig(strict_argument_validation=True)
        formatter = DynamicFormatter("{{}} {{field}}", config=config)
        
        with pytest.raises(DynamicFormattingError) as exc_info:
            formatter.format("pos_arg", field="keyword_arg")
        
        assert "Cannot mix positional and keyword arguments" in str(exc_info.value)
    
    @pytest.mark.error
    def test_too_many_positional_args(self):
        """Test error when providing too many positional arguments"""
        config = FormatterConfig(strict_argument_validation=True)
        formatter = DynamicFormatter("{{}} {{}}")  # Only 2 positional fields
        
        with pytest.raises(DynamicFormattingError) as exc_info:
            formatter.format("arg1", "arg2", "arg3")  # 3 arguments
        
        assert "Too many positional arguments" in str(exc_info.value)


class TestEdgeCases:
    """Test edge case scenarios"""
    
    @pytest.mark.error
    def test_empty_string_formatting(self):
        """Test formatting with empty string data"""
        formatter = DynamicFormatter("{{Prefix: ;field}}")
        result = formatter.format(field="")
        assert result == "Prefix: "
    
    @pytest.mark.error
    def test_none_value_handling(self):
        """Test handling of None values"""
        formatter = DynamicFormatter("{{Value: ;field}}")
        
        # None should cause section to disappear
        result = formatter.format(field=None)
        assert result == ""
    
    @pytest.mark.error
    def test_numeric_field_values(self):
        """Test formatting with numeric values"""
        formatter = DynamicFormatter("{{Count: ;value}} {{Price: $;cost}}")
        result = formatter.format(value=42, cost=19.99)
        assert result == "Count: 42 Price: $19.99"
    
    @pytest.mark.error
    def test_boolean_field_values(self):
        """Test formatting with boolean values"""
        formatter = DynamicFormatter("{{Active: ;status}} {{Debug: ;debug}}")
        result = formatter.format(status=True, debug=False)
        assert result == "Active: True Debug: False"
    
    @pytest.mark.error
    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters"""
        formatter = DynamicFormatter("{{Message: ;text}}")
        
        # Unicode characters
        result = formatter.format(text="Hello 世界 🌍")
        assert result == "Message: Hello 世界 🌍"
        
        # Special characters that might interfere with parsing
        result = formatter.format(text="Text with {braces} and ;semicolons;")
        assert result == "Message: Text with {braces} and ;semicolons;"


class TestOutputModeEdgeCases:
    """Test edge cases related to output modes"""
    
    @pytest.mark.error
    def test_output_mode_switching(self):
        """Test switching between output modes"""
        template = "{{#red@bold;Formatted: ;field}}"
        
        console_config = FormatterConfig(output_mode="console")
        console_formatter = DynamicFormatter(template, config=console_config)
        
        file_config = FormatterConfig(output_mode="file")
        file_formatter = DynamicFormatter(template, config=file_config)
        
        console_result = console_formatter.format(field="test")
        file_result = file_formatter.format(field="test")
        
        # Console should have ANSI codes, file should not
        assert "\033[" in console_result
        assert "\033[" not in file_result
        # Both should contain the core text
        assert "Formatted: test" in console_result
        assert "Formatted: test" in file_result


class TestLoggingFormatterErrors:
    """Test error handling specific to logging formatter"""
    
    @pytest.mark.error
    def test_logging_formatter_with_malformed_template(self):
        """Test logging formatter graceful degradation"""
        import logging
        
        # Create formatter with invalid template
        formatter = DynamicLoggingFormatter("{{unclosed template")
        
        # Should not crash when formatting a log record
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test message", args=(), exc_info=None
        )
        
        result = formatter.format(record)
        # Should contain error indication and original message
        assert "FORMATTING ERROR" in result
        assert "Test message" in result
    
    @pytest.mark.error
    def test_logging_formatter_with_missing_functions(self):
        """Test logging formatter with missing functions"""
        import logging
        
        formatter = DynamicLoggingFormatter(
            "{{#missing_func;[;levelname;]}} {{message}}"
        )
        
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test message", args=(), exc_info=None
        )
        
        result = formatter.format(record)
        # Should contain error indication
        assert "[FORMATTING ERROR" in result


class TestGracefulDegradation:
    """Test graceful degradation in various scenarios"""
    
    @pytest.mark.error
    def test_partial_template_success(self):
        """Test when part of template works and part fails"""
        def working_function(value):
            return "green"
        
        def failing_function(value):
            raise ValueError("Failed")
        
        config = FormatterConfig(
            validation_mode=ValidationMode.GRACEFUL,
            functions={"working_function": working_function, "failing_function": failing_function}
        )
        formatter = DynamicFormatter(
            "{{#working_function;Good: ;field1}} {{#failing_function;Bad: ;field2}}",
            config=config
        )
        
        # In graceful mode, should handle function failures gracefully
        result = formatter.format(field1="test1", field2="test2")
        assert "Good: test1" in result  # Working part should succeed
        # Failing part should either be omitted or show error indication
    
    @pytest.mark.error
    def test_function_fallback_chain_failure(self):
        """Test when function fallback chain fails"""
        def intermediate_function(value):
            return "nonexistent_color"  # This will fail when parsed as color
        
        config = FormatterConfig(
            validation_mode=ValidationMode.GRACEFUL,
            functions={"intermediate_function": intermediate_function}
        )
        formatter = DynamicFormatter(
            "{{#intermediate_function;Text: ;field}}",
            config=config
        )
        
        # In graceful mode, should handle cascading failures
        result = formatter.format(field="test")
        # Should either fallback gracefully or show the text without formatting
        assert "Text: test" in result or "test" in result
