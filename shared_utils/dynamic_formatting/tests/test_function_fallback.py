"""
Function fallback system tests.

Tests the function fallback mechanism that allows tokens like #level_color
to automatically call functions when they're not built-in formatters.
"""

import pytest
from shared_utils.dynamic_formatting import (
    DynamicFormatter,
    DynamicFormattingError,
    FunctionExecutionError,
    FormatterError
)


class TestColorFunctionFallback:
    """Test color function fallback functionality"""
    
    @pytest.mark.fallback
    def test_basic_color_function(self):
        """Test basic color function fallback"""
        def status_color(status):
            return {"error": "red", "success": "green", "warning": "yellow"}[status.lower()]
        
        formatter = DynamicFormatter(
            "{{#status_color;Status: ;status}}",
            functions={"status_color": status_color}
        )
        
        result = formatter.format(status="ERROR")
        assert "Status: ERROR" in result
    
    @pytest.mark.fallback
    def test_color_function_with_field_value(self):
        """Test color function receives the field value as parameter"""
        def field_based_color(field_value):
            if "error" in str(field_value).lower():
                return "red"
            elif "success" in str(field_value).lower():
                return "green"
            else:
                return "blue"
        
        formatter = DynamicFormatter(
            "{{#field_based_color;Message: ;message}}",
            functions={"field_based_color": field_based_color}
        )
        
        # Error message should be red
        result = formatter.format(message="Error occurred")
        assert "Message: Error occurred" in result
        
        # Success message should be green
        result = formatter.format(message="Success!")
        assert "Message: Success!" in result
        
        # Other message should be blue
        result = formatter.format(message="Processing")
        assert "Message: Processing" in result
    
    @pytest.mark.fallback
    def test_color_function_returns_hex(self):
        """Test color function returning hex values"""
        def priority_color(priority):
            if priority > 8:
                return "ff0000"  # Red hex
            elif priority > 5:
                return "ffff00"  # Yellow hex
            else:
                return "00ff00"  # Green hex
        
        formatter = DynamicFormatter(
            "{{#priority_color;Priority ;priority;: ;message}}",
            functions={"priority_color": priority_color}
        )
        
        result = formatter.format(priority=9, message="Critical")
        assert "Priority 9: Critical" in result
    
    @pytest.mark.fallback
    def test_color_function_returns_ansi_name(self):
        """Test color function returning ANSI color names"""
        def severity_color(severity):
            mapping = {
                "low": "cyan",
                "medium": "yellow", 
                "high": "red",
                "critical": "magenta"
            }
            return mapping.get(severity.lower(), "white")
        
        formatter = DynamicFormatter(
            "{{#severity_color;[;severity;] ;message}}",
            functions={"severity_color": severity_color}
        )
        
        result = formatter.format(severity="HIGH", message="Alert")
        assert "[HIGH] Alert" in result


class TestTextFunctionFallback:
    """Test text style function fallback functionality"""
    
    @pytest.mark.fallback
    def test_basic_text_function(self):
        """Test basic text style function fallback"""
        def emphasis_style(importance):
            if importance > 8:
                return "bold"
            elif importance > 5:
                return "italic"
            else:
                return "normal"
        
        formatter = DynamicFormatter(
            "{{@emphasis_style;Priority ;importance;: ;message}}",
            functions={"emphasis_style": emphasis_style}
        )
        
        result = formatter.format(importance=9, message="Critical")
        assert "Priority 9: Critical" in result
    
    @pytest.mark.fallback
    def test_text_function_with_field_content(self):
        """Test text function that analyzes field content"""
        def content_style(content):
            if content.isupper():
                return "bold"
            elif len(content) > 20:
                return "italic"
            else:
                return "normal"
        
        formatter = DynamicFormatter(
            "{{@content_style;Message: ;message}}",
            functions={"content_style": content_style}
        )
        
        # Uppercase should be bold
        result = formatter.format(message="URGENT")
        assert "Message: URGENT" in result
        
        # Long message should be italic
        result = formatter.format(message="This is a very long message that should be italic")
        assert "Message: This is a very long message that should be italic" in result
        
        # Normal message
        result = formatter.format(message="Normal")
        assert "Message: Normal" in result


class TestConditionalFunctionFallback:
    """Test conditional function functionality"""
    
    @pytest.mark.fallback
    def test_basic_conditional_function(self):
        """Test basic conditional function"""
        def has_items(count):
            return count > 0
        
        formatter = DynamicFormatter(
            "{{Processing}} {{?has_items;found ;count; items}}",
            functions={"has_items": has_items}
        )
        
        # With items
        result = formatter.format(count=25)
        assert result == "Processing found 25 items"
        
        # Without items
        result = formatter.format(count=0)
        assert result == "Processing "
    
    @pytest.mark.fallback
    def test_conditional_function_with_complex_logic(self):
        """Test conditional function with complex decision logic"""
        def should_alert(status, error_count, duration):
            return (status == "error" or 
                    error_count > 5 or 
                    duration > 30)
        
        formatter = DynamicFormatter(
            "{{Status: ;status}} {{?should_alert;ALERT: Review required}}",
            functions={"should_alert": should_alert}
        )
        
        # Should alert due to error status
        result = formatter.format(status="error", error_count=2, duration=10)
        assert "Status: error ALERT: Review required" in result
        
        # Should alert due to high error count
        result = formatter.format(status="running", error_count=10, duration=5)
        assert "Status: running ALERT: Review required" in result
        
        # Should not alert
        result = formatter.format(status="running", error_count=2, duration=5)
        assert result == "Status: running "
    
    @pytest.mark.fallback
    def test_conditional_receives_field_value(self):
        """Test that conditional functions receive the field value"""
        def is_urgent_message(message):
            urgent_keywords = ["urgent", "critical", "emergency", "failure"]
            return any(keyword in message.lower() for keyword in urgent_keywords)
        
        formatter = DynamicFormatter(
            "{{?is_urgent_message;🚨 URGENT: ;message}}",
            functions={"is_urgent_message": is_urgent_message}
        )
        
        # Urgent message
        result = formatter.format(message="Critical system failure detected")
        assert result == "🚨 URGENT: Critical system failure detected"
        
        # Normal message
        result = formatter.format(message="Process completed successfully")
        assert result == ""


class TestCombinedFunctionFallback:
    """Test combining multiple function fallback types"""
    
    @pytest.mark.fallback
    def test_color_and_text_functions_combined(self):
        """Test using both color and text functions in same template"""
        def alert_color(level):
            return {"info": "green", "warning": "yellow", "error": "red"}[level]
        
        def alert_style(level):
            return "bold" if level == "error" else "normal"
        
        formatter = DynamicFormatter(
            "{{#alert_color@alert_style;[;level;] ;message}}",
            functions={"alert_color": alert_color, "alert_style": alert_style}
        )
        
        result = formatter.format(level="error", message="System down")
        assert "[error] System down" in result
    
    @pytest.mark.fallback
    def test_all_function_types_combined(self):
        """Test color, text, and conditional functions together"""
        def priority_color(priority):
            if priority > 7:
                return "red"
            elif priority > 4:
                return "yellow"
            else:
                return "green"
        
        def priority_style(priority):
            return "bold" if priority > 7 else "normal"
        
        def has_high_priority(priority):
            return priority > 7
        
        formatter = DynamicFormatter(
            "{{#priority_color@priority_style;Task: ;task}} {{?has_high_priority;⚠️  HIGH PRIORITY}}",
            functions={
                "priority_color": priority_color,
                "priority_style": priority_style, 
                "has_high_priority": has_high_priority
            }
        )
        
        # High priority task
        result = formatter.format(task="Deploy", priority=9)
        assert "Task: Deploy" in result
        assert "⚠️  HIGH PRIORITY" in result
        
        # Normal priority task
        result = formatter.format(task="Cleanup", priority=3)
        assert "Task: Cleanup" in result
        assert "⚠️  HIGH PRIORITY" not in result


class TestFunctionParameterHandling:
    """Test how functions receive and handle parameters"""
    
    @pytest.mark.fallback
    def test_function_receives_field_value(self):
        """Test that functions receive the specific field value they're applied to"""
        def process_field(value):
            return f"processed_{value}"
        
        formatter = DynamicFormatter(
            "{{#process_field;First: ;field1}} {{#process_field;Second: ;field2}}",
            functions={"process_field": process_field}
        )
        
        result = formatter.format(field1="alpha", field2="beta")
        # Each function call should receive the corresponding field value
        assert "First: alpha" in result
        assert "Second: beta" in result
    
    @pytest.mark.fallback
    def test_function_with_no_parameters(self):
        """Test functions that don't accept field value parameters"""
        def get_timestamp():
            return "2024-01-01"
        
        formatter = DynamicFormatter(
            "{{#get_timestamp;Generated: ;message}}",
            functions={"get_timestamp": get_timestamp}
        )
        
        result = formatter.format(message="report")
        assert "Generated: report" in result
    
    @pytest.mark.fallback
    def test_function_parameter_type_handling(self):
        """Test functions with different parameter types"""
        def handle_number(value):
            if isinstance(value, (int, float)):
                return "red" if value > 50 else "green"
            else:
                return "blue"
        
        formatter = DynamicFormatter(
            "{{#handle_number;Value: ;value}}",
            functions={"handle_number": handle_number}
        )
        
        # Number over 50
        result = formatter.format(value=75)
        assert "Value: 75" in result
        
        # Number under 50
        result = formatter.format(value=25)
        assert "Value: 25" in result
        
        # String value
        result = formatter.format(value="text")
        assert "Value: text" in result


class TestFunctionErrorHandling:
    """Test error handling in function fallback system"""
    
    @pytest.mark.fallback
    @pytest.mark.error
    def test_function_not_found_error(self):
        """Test error when function is not found"""
        formatter = DynamicFormatter("{{#missing_function;Color: ;value}}")
        
        with pytest.raises(FormatterError) as exc_info:
            formatter.format(value="test")
        
        assert "missing_function" in str(exc_info.value)
    
    @pytest.mark.fallback
    @pytest.mark.error
    def test_function_execution_error(self):
        """Test error when function execution fails"""
        def failing_function(value):
            raise ValueError("Intentional failure")
        
        formatter = DynamicFormatter(
            "{{#failing_function;Value: ;value}}",
            functions={"failing_function": failing_function}
        )
        
        with pytest.raises(FunctionExecutionError) as exc_info:
            formatter.format(value="test")
        
        assert "failing_function" in str(exc_info.value)
        assert "Intentional failure" in str(exc_info.value)
    
    @pytest.mark.fallback
    @pytest.mark.error
    def test_function_returns_invalid_type(self):
        """Test error when function returns invalid type"""
        def bad_return_function(value):
            return 123  # Should return string
        
        formatter = DynamicFormatter(
            "{{#bad_return_function;Value: ;value}}",
            functions={"bad_return_function": bad_return_function}
        )
        
        with pytest.raises(FunctionExecutionError) as exc_info:
            formatter.format(value="test")
        
        assert "must return a string" in str(exc_info.value)
    
    @pytest.mark.fallback
    @pytest.mark.error
    def test_conditional_function_not_found(self):
        """Test error when conditional function is not found"""
        formatter = DynamicFormatter("{{?missing_conditional;Text: ;value}}")
        
        with pytest.raises(FormatterError) as exc_info:
            formatter.format(value="test")
        
        assert "missing_conditional" in str(exc_info.value)


class TestRecursiveFunctionFallback:
    """Test recursive function fallback scenarios"""
    
    @pytest.mark.fallback
    def test_function_returns_another_token(self):
        """Test function that returns another valid token"""
        def get_error_color(severity):
            # Return different color names based on severity
            return {"low": "yellow", "high": "red", "critical": "magenta"}[severity]
        
        formatter = DynamicFormatter(
            "{{#get_error_color;Alert: ;message}}",
            functions={"get_error_color": get_error_color}
        )
        
        result = formatter.format(message="System issue", severity="high")
        assert "Alert: System issue" in result
    
    @pytest.mark.fallback
    def test_function_returns_hex_color(self):
        """Test function that returns hex color for recursive parsing"""
        def dynamic_hex_color(intensity):
            # Return hex colors based on intensity
            if intensity > 80:
                return "ff0000"  # Bright red
            elif intensity > 50:
                return "ff8800"  # Orange
            else:
                return "ffff00"  # Yellow
        
        formatter = DynamicFormatter(
            "{{#dynamic_hex_color;Intensity ;intensity;%: ;status}}",
            functions={"dynamic_hex_color": dynamic_hex_color}
        )
        
        result = formatter.format(intensity=95, status="Critical")
        assert "Intensity 95%: Critical" in result


class TestComplexFunctionScenarios:
    """Test complex real-world function scenarios"""
    
    @pytest.mark.fallback
    def test_log_level_formatting(self):
        """Test realistic log level formatting scenario"""
        def log_level_color(level):
            mapping = {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow", 
                "ERROR": "red",
                "CRITICAL": "magenta"
            }
            return mapping.get(level.upper(), "white")
        
        def log_level_style(level):
            return "bold" if level.upper() in ["ERROR", "CRITICAL"] else "normal"
        
        def should_timestamp(level):
            return level.upper() in ["ERROR", "CRITICAL"]
        
        formatter = DynamicFormatter(
            "{{#log_level_color@log_level_style;[;level;]}} {{message}} {{?should_timestamp;at ;timestamp}}",
            functions={
                "log_level_color": log_level_color,
                "log_level_style": log_level_style,
                "should_timestamp": should_timestamp
            }
        )
        
        # Error level with timestamp
        result = formatter.format(
            level="ERROR", 
            message="Connection failed",
            timestamp="2024-01-01 12:00:00"
        )
        assert "[ERROR]" in result
        assert "Connection failed" in result
        assert "at 2024-01-01 12:00:00" in result
        
        # Info level without timestamp
        result = formatter.format(
            level="INFO",
            message="Process started", 
            timestamp="2024-01-01 12:00:00"
        )
        assert "[INFO]" in result
        assert "Process started" in result
        assert "at 2024-01-01 12:00:00" not in result
    
    @pytest.mark.fallback
    def test_performance_monitoring_scenario(self):
        """Test realistic performance monitoring scenario"""
        def performance_color(duration):
            if duration > 5.0:
                return "red"
            elif duration > 1.0:
                return "yellow"
            else:
                return "green"
        
        def performance_indicator(duration):
            if duration < 0.1:
                return "⚡"
            elif duration < 1.0:
                return "✓"
            elif duration < 5.0:
                return "⏳"
            else:
                return "🐌"
        
        def is_slow(duration):
            return duration > 5.0
        
        formatter = DynamicFormatter(
            "{{Operation: ;operation}} {{#performance_color;took ;duration;s}} {{performance_indicator}} {{?is_slow;SLOW OPERATION}}",
            functions={
                "performance_color": performance_color,
                "performance_indicator": performance_indicator,
                "is_slow": is_slow
            }
        )
        
        # Fast operation
        result = formatter.format(operation="database_query", duration=0.05)
        assert "Operation: database_query" in result
        assert "took 0.05s" in result
        assert "⚡" in result
        assert "SLOW OPERATION" not in result
        
        # Slow operation
        result = formatter.format(operation="file_upload", duration=8.5)
        assert "Operation: file_upload" in result
        assert "took 8.5s" in result
        assert "🐌" in result
        assert "SLOW OPERATION" in result