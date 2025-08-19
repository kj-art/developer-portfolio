"""
Error handling and edge case tests.

Tests error conditions, edge cases, malformed input handling,
and graceful degradation scenarios.
"""

import pytest
from shared_utils.dynamic_formatting import (
    DynamicFormatter,
    DynamicLoggingFormatter,
    DynamicFormattingError,
    RequiredFieldError,
    FunctionNotFoundError,
    FormatterError,
    FunctionExecutionError,
    ParseError
)


class TestParsingErrors:
    """Test template parsing error conditions"""
    
    @pytest.mark.error
    def test_unclosed_template_section(self):
        """Test error for unclosed template sections"""
        with pytest.raises(ParseError) as exc_info:
            DynamicFormatter("{{unclosed section")
        
        assert "Unclosed template section" in str(exc_info.value)
    
    @pytest.mark.error
    def test_empty_template_sections(self):
        """Test handling of empty template sections"""
        # Empty sections should be handled gracefully
        formatter = DynamicFormatter("{{}}")
        result = formatter.format("test")
        assert result == "test"


class TestRequiredFieldErrors:
    """Test required field error handling"""
    
    @pytest.mark.error
    def test_required_field_missing_keyword(self):
        """Test required field error with keyword arguments"""
        formatter = DynamicFormatter("{{!;Critical: ;message}}")
        
        with pytest.raises(RequiredFieldError) as exc_info:
            formatter.format()
        
        error_msg = str(exc_info.value)
        assert "Required field missing" in error_msg
        assert "message" in error_msg
    
    @pytest.mark.error
    def test_required_field_missing_positional(self):
        """Test required field error with positional arguments"""
        formatter = DynamicFormatter("{{!}}")
        
        with pytest.raises(RequiredFieldError) as exc_info:
            formatter.format()
        
        error_msg = str(exc_info.value)
        assert "Required field missing" in error_msg
        assert "position 1" in error_msg  # User-friendly position
    
    @pytest.mark.error
    def test_required_field_with_none_value(self):
        """Test required field error when field is explicitly None"""
        formatter = DynamicFormatter("{{!;Required: ;field}}")
        
        with pytest.raises(RequiredFieldError):
            formatter.format(field=None)


class TestFormatterErrors:
    """Test formatter-specific error conditions"""
    
    @pytest.mark.error
    def test_invalid_color_token(self):
        """Test error for invalid color tokens"""
        formatter = DynamicFormatter("{{#invalid_color;Text: ;field}}")
        
        with pytest.raises(FormatterError) as exc_info:
            formatter.format(field="test")
        
        assert "Invalid color token" in str(exc_info.value)
        assert "invalid_color" in str(exc_info.value)
    
    @pytest.mark.error
    def test_invalid_text_style_token(self):
        """Test error for invalid text style tokens"""
        formatter = DynamicFormatter("{{@invalid_style;Text: ;field}}")
        
        with pytest.raises(FormatterError) as exc_info:
            formatter.format(field="test")
        
        assert "Invalid text style token" in str(exc_info.value)
        assert "invalid_style" in str(exc_info.value)
    
    @pytest.mark.error
    def test_malformed_hex_color(self):
        """Test error for malformed hex colors"""
        formatter = DynamicFormatter("{{#gggggg;Text: ;field}}")  # Invalid hex
        
        with pytest.raises(FormatterError) as exc_info:
            formatter.format(field="test")
        
        assert "Invalid color token" in str(exc_info.value)


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
        
        formatter = DynamicFormatter(
            "{{#failing_function;Text: ;field}}",
            functions={"failing_function": failing_function}
        )
        
        with pytest.raises(FunctionExecutionError) as exc_info:
            formatter.format(field="test")
        
        assert "failing_function" in str(exc_info.value)
        assert "Function failed" in str(exc_info.value)
    
    @pytest.mark.error
    def test_function_wrong_return_type(self):
        """Test error when function returns wrong type"""
        def bad_function(value):
            return 123  # Should return string
        
        formatter = DynamicFormatter(
            "{{#bad_function;Text: ;field}}",
            functions={"bad_function": bad_function}
        )
        
        with pytest.raises(FunctionExecutionError) as exc_info:
            formatter.format(field="test")
        
        assert "must return a string" in str(exc_info.value)
    
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
        formatter = DynamicFormatter("{{}} {{}}")
        
        with pytest.raises(DynamicFormattingError) as exc_info:
            formatter.format("pos", keyword="kw")
        
        assert "Cannot mix positional and keyword arguments" in str(exc_info.value)
    
    @pytest.mark.error
    def test_too_many_positional_args(self):
        """Test error with too many positional arguments"""
        formatter = DynamicFormatter("{{}}")  # One section
        
        with pytest.raises(DynamicFormattingError) as exc_info:
            formatter.format("first", "second")
        
        error_msg = str(exc_info.value)
        assert "Too many positional arguments" in error_msg
        assert "expected 1, got 2" in error_msg


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @pytest.mark.error
    def test_empty_string_formatting(self):
        """Test formatting with empty strings"""
        formatter = DynamicFormatter("{{Prefix: ;field}}")
        
        # Empty string should work
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
        """Test handling of numeric field values"""
        formatter = DynamicFormatter("{{Count: ;number}}")
        
        # Integer
        result = formatter.format(number=42)
        assert result == "Count: 42"
        
        # Float
        result = formatter.format(number=3.14)
        assert result == "Count: 3.14"
        
        # Zero
        result = formatter.format(number=0)
        assert result == "Count: 0"
    
    @pytest.mark.error
    def test_boolean_field_values(self):
        """Test handling of boolean field values"""
        formatter = DynamicFormatter("{{Status: ;flag}}")
        
        result = formatter.format(flag=True)
        assert result == "Status: True"
        
        result = formatter.format(flag=False)
        assert result == "Status: False"
    
    @pytest.mark.error
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
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
        
        console_formatter = DynamicFormatter(template, output_mode="console")
        file_formatter = DynamicFormatter(template, output_mode="file")
        
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
        assert "[FORMATTING ERROR" in result
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
    """Test graceful degradation in error scenarios"""
    
    @pytest.mark.error
    def test_partial_template_success(self):
        """Test when part of template works and part fails"""
        def working_function(value):
            return "green"
        
        def failing_function(value):
            raise ValueError("Failed")
        
        formatter = DynamicFormatter(
            "{{#working_function;Good: ;field1}} {{#failing_function;Bad: ;field2}}",
            functions={"working_function": working_function, "failing_function": failing_function}
        )
        
        # Should fail completely rather than partial success
        with pytest.raises(FunctionExecutionError):
            formatter.format(field1="test1", field2="test2")
    
    @pytest.mark.error
    def test_function_fallback_chain_failure(self):
        """Test when function fallback chain fails"""
        def intermediate_function(value):
            return "nonexistent_color"  # This will fail when parsed as color
        
        formatter = DynamicFormatter(
            "{{#intermediate_function;Text: ;field}}",
            functions={"intermediate_function": intermediate_function}
        )
        
        with pytest.raises(FormatterError):
            formatter.format(field="test")