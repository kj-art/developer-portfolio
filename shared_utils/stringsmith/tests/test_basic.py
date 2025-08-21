"""
Basic tests for StringSmith functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

# Use direct imports like the working test runner
try:
    from formatter import TemplateFormatter
    from exceptions import StringSmithError, MissingMandatoryFieldError
except ImportError:
    # Fallback to package imports if running as installed package
    from stringsmith import TemplateFormatter
    from stringsmith.exceptions import StringSmithError, MissingMandatoryFieldError


class TestBasicFormatting:
    """Test basic template formatting functionality."""
    
    def test_simple_variable(self):
        """Test simple variable substitution."""
        formatter = TemplateFormatter("{{name}}")
        assert formatter.format(name="Alice") == "Alice"
        assert formatter.format() == ""
    
    def test_prefix_variable(self):
        """Test variable with prefix."""
        formatter = TemplateFormatter("{{Hello ;name}}")
        assert formatter.format(name="Alice") == "Hello Alice"
        assert formatter.format() == ""
    
    def test_prefix_variable_suffix(self):
        """Test variable with prefix and suffix."""
        formatter = TemplateFormatter("{{Hello ;name;!}}")
        assert formatter.format(name="Alice") == "Hello Alice!"
        assert formatter.format() == ""
    
    def test_multiple_sections(self):
        """Test multiple sections."""
        formatter = TemplateFormatter("{{greeting}} {{name}}!")
        assert formatter.format(greeting="Hello", name="Alice") == "Hello Alice!"
        assert formatter.format(greeting="Hello") == "Hello !"
        assert formatter.format(name="Alice") == " Alice!"
        assert formatter.format() == " !"
    
    def test_text_between_sections(self):
        """Test literal text between sections."""
        formatter = TemplateFormatter("Score: {{points}} - Grade: {{grade}}")
        assert formatter.format(points=95, grade="A") == "Score: 95 - Grade: A"
        assert formatter.format(points=95) == "Score: 95 - Grade: "
        assert formatter.format() == "Score:  - Grade: "


class TestMandatorySections:
    """Test mandatory section functionality."""
    
    def test_mandatory_simple(self):
        """Test simple mandatory section."""
        formatter = TemplateFormatter("{{!name}}")
        assert formatter.format(name="Alice") == "Alice"
        
        with pytest.raises(MissingMandatoryFieldError):
            formatter.format()
    
    def test_mandatory_with_prefix_suffix(self):
        """Test mandatory section with prefix and suffix."""
        formatter = TemplateFormatter("{{!Hello ;name;!}}")
        assert formatter.format(name="Alice") == "Hello Alice!"
        
        with pytest.raises(MissingMandatoryFieldError):
            formatter.format()
    
    def test_mixed_mandatory_optional(self):
        """Test mix of mandatory and optional sections."""
        formatter = TemplateFormatter("{{!required}} {{optional}}")
        assert formatter.format(required="test", optional="opt") == "test opt"
        assert formatter.format(required="test") == "test "
        
        with pytest.raises(MissingMandatoryFieldError):
            formatter.format(optional="opt")


class TestPositionalArguments:
    """Test positional argument functionality."""
    
    def test_positional_simple(self):
        """Test simple positional arguments."""
        formatter = TemplateFormatter("{{first}} {{second}}")
        assert formatter.format("Hello", "World") == "Hello World"
        assert formatter.format("Hello") == "Hello "
        assert formatter.format() == " "
    
    def test_positional_with_prefixes(self):
        """Test positional arguments with prefixes and suffixes."""
        formatter = TemplateFormatter("{{Name: ;first;}} {{Score: ;second; pts}}")
        assert formatter.format("Alice", 100) == "Name: Alice Score: 100 pts"
        assert formatter.format("Alice") == "Name: Alice "
    
    def test_positional_mandatory(self):
        """Test mandatory positional arguments."""
        formatter = TemplateFormatter("{{!first}} {{second}}")
        assert formatter.format("Hello", "World") == "Hello World"
        assert formatter.format("Hello") == "Hello "
        
        with pytest.raises(MissingMandatoryFieldError, match="Required positional argument 0"):
            formatter.format()
    
    def test_no_mixing_args_kwargs(self):
        """Test that positional and keyword args cannot be mixed."""
        formatter = TemplateFormatter("{{first}} {{second}}")
        
        with pytest.raises(StringSmithError, match="Cannot mix positional and keyword"):
            formatter.format("Hello", second="World")


class TestCustomDelimiter:
    """Test custom delimiter functionality."""
    
    def test_pipe_delimiter(self):
        """Test using pipe as delimiter."""
        formatter = TemplateFormatter("{{prefix|variable|suffix}}", delimiter="|")
        assert formatter.format(variable="test") == "prefixtestsuffix"
        assert formatter.format() == ""
    
    def test_colon_delimiter(self):
        """Test using colon as delimiter."""
        formatter = TemplateFormatter("{{Label:value:!}}", delimiter=":")
        assert formatter.format(value="test") == "Labeltest!"


class TestEscaping:
    """Test escape sequence functionality."""
    
    def test_escape_braces(self):
        """Test escaping curly braces."""
        formatter = TemplateFormatter("Use \\{name\\} for {{name}}")
        assert formatter.format(name="variables") == "Use {name} for variables"
    
    def test_escape_delimiter(self):
        """Test escaping delimiters."""
        formatter = TemplateFormatter("{{Ratio\\;percent;value;}}")
        assert formatter.format(value="50") == "Ratio;percent50"
    
    def test_escape_backslash(self):
        """Test escaping backslashes."""
        formatter = TemplateFormatter("Path: \\\\{{path}}")
        result = formatter.format(path="home/user")
        assert result == "Path: \\home/user"
    
    def test_custom_escape_character(self):
        """Test using custom escape character."""
        formatter = TemplateFormatter("Use ~{name~} for {{name}}", escape_char="~")
        result = formatter.format(name="variables")
        assert result == "Use {name} for variables"
    
    def test_custom_escape_delimiter(self):
        """Test escaping delimiter with custom escape char."""
        formatter = TemplateFormatter("{{Ratio~;percent;value;}}", escape_char="~")
        result = formatter.format(value="50")
        assert result == "Ratio;percent50"
    
    def test_escape_custom_escape_char(self):
        """Test escaping the custom escape character itself."""
        formatter = TemplateFormatter("Path: ~~{{path}}", escape_char="~")
        result = formatter.format(path="home/user")
        assert result == "Path: ~home/user"


if __name__ == "__main__":
    pytest.main([__file__])