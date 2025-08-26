"""
Pytest configuration and shared fixtures for StringSmith tests.

This module provides common test fixtures and configuration that can be used
across all test modules. Fixtures are automatically available in all test
functions without explicit imports.
"""

import pytest
import sys
import os

# Add the project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stringsmith import TemplateFormatter
from stringsmith.exceptions import StringSmithError, MissingMandatoryFieldError


# Basic formatter fixtures
@pytest.fixture
def basic_formatter():
    """Basic formatter for simple testing."""
    return TemplateFormatter("{{Hello ;name;}}")


@pytest.fixture
def empty_formatter():
    """Formatter with no template sections."""
    return TemplateFormatter("Just plain text")


@pytest.fixture
def multi_section_formatter():
    """Formatter with multiple sections for complex testing."""
    return TemplateFormatter("{{User: ;username;}} {{(ID: ;user_id;)}} {{Level: ;level;}}")


@pytest.fixture
def mandatory_formatter():
    """Formatter with mandatory fields."""
    return TemplateFormatter("{{!required}} and {{optional}}")


@pytest.fixture
def positional_formatter():
    """Formatter for positional argument testing."""
    return TemplateFormatter("{{first}} + {{second}} = {{result}}")


# Formatting fixtures
@pytest.fixture
def color_formatter():
    """Formatter with color formatting."""
    return TemplateFormatter("{{#red;Error: ;message;}}")


@pytest.fixture
def emphasis_formatter():
    """Formatter with text emphasis."""
    return TemplateFormatter("{{@bold;Warning: ;message;}}")


@pytest.fixture
def combined_formatting_formatter():
    """Formatter with both color and emphasis."""
    return TemplateFormatter("{{#blue@italic;Info: ;message;}}")


@pytest.fixture
def hex_color_formatter():
    """Formatter with hex color codes."""
    return TemplateFormatter("{{#FF5733;Status: ;status;}}")


# Custom function fixtures
@pytest.fixture
def sample_functions():
    """Dictionary of sample custom functions for testing."""
    def is_error(level):
        return level and level.lower() == 'error'
    
    def is_warning(level):
        return level and level.lower() == 'warning'
    
    def priority_color(priority):
        if priority is None:
            return 'white'
        try:
            p = int(priority)
            if p > 5:
                return 'red'
            elif p > 2:
                return 'yellow'
            else:
                return 'green'
        except (ValueError, TypeError):
            return 'white'
    
    def status_color(status):
        colors = {
            'error': 'red',
            'warning': 'yellow', 
            'success': 'green',
            'info': 'blue',
            'running': 'yellow',
            'complete': 'green',
            'failed': 'red'
        }
        return colors.get(status.lower() if status else '', 'white')
    
    def is_urgent(priority):
        try:
            return priority and int(priority) > 7
        except (ValueError, TypeError):
            return False
    
    def has_user(user_id):
        return user_id is not None and str(user_id).strip() != ''
    
    return {
        'is_error': is_error,
        'is_warning': is_warning,
        'priority_color': priority_color,
        'status_color': status_color,
        'is_urgent': is_urgent,
        'has_user': has_user,
    }


@pytest.fixture
def conditional_formatter(sample_functions):
    """Formatter with conditional functions."""
    return TemplateFormatter(
        "{{?is_error;[ERROR] ;level;}} {{message}}",
        functions=sample_functions
    )


@pytest.fixture
def complex_formatter(sample_functions):
    """Complex formatter combining multiple features."""
    return TemplateFormatter(
        "{{#priority_color;[;priority;];}} {{?is_urgent;🚨 URGENT 🚨 ;}} {{message}}",
        functions=sample_functions
    )


# Delimiter and escaping fixtures
@pytest.fixture
def pipe_delimiter_formatter():
    """Formatter using pipe delimiter."""
    return TemplateFormatter("{{Error|message|!}}", delimiter="|")


@pytest.fixture
def colon_delimiter_formatter():
    """Formatter using colon delimiter."""
    return TemplateFormatter("{{Label:value:}}", delimiter=":")


@pytest.fixture
def escape_formatter():
    """Formatter with escape sequences."""
    return TemplateFormatter("Use \\{name\\} for {{name}}")


@pytest.fixture
def custom_escape_formatter():
    """Formatter with custom escape character."""
    return TemplateFormatter("Use ~{name~} for {{name}}", escape_char="~")


# Sample data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'username': 'admin',
        'user_id': 12345,
        'level': 'administrator',
        'email': 'admin@example.com',
        'last_login': '2025-01-15 10:30:00'
    }


@pytest.fixture
def sample_log_data():
    """Sample log data for testing."""
    return {
        'timestamp': '2025-01-15 10:30:15',
        'level': 'ERROR',
        'module': 'auth',
        'message': 'Login failed',
        'user_id': 'user123',
        'ip_address': '192.168.1.100'
    }


@pytest.fixture
def sample_status_data():
    """Sample status data for testing."""
    return {
        'operation': 'Backup',
        'status': 'running',
        'progress': 45,
        'eta': '5 min',
        'priority': 8
    }


# Utility fixtures
@pytest.fixture
def strip_ansi():
    """Function to strip ANSI codes from strings for content testing."""
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return lambda text: ansi_escape.sub('', text)


# Test data generators
@pytest.fixture
def color_test_cases():
    """Test cases for color formatting."""
    return [
        ('red', '\x1b[31m', '\x1b[39m'),
        ('green', '\x1b[32m', '\x1b[39m'),
        ('blue', '\x1b[34m', '\x1b[39m'),
        ('yellow', '\x1b[33m', '\x1b[39m'),
        ('white', '\x1b[37m', '\x1b[39m'),
    ]


@pytest.fixture
def emphasis_test_cases():
    """Test cases for emphasis formatting."""
    return [
        ('bold', '\x1b[1m'),
        ('italic', '\x1b[3m'),
        ('underline', '\x1b[4m'),
        ('dim', '\x1b[2m'),
    ]


# Configuration fixtures
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for all tests."""
    # Add any global test setup here
    yield
    # Add any global test cleanup here


# Parametrized fixtures for comprehensive testing
@pytest.fixture(params=[';', '|', ':', ','])
def delimiter(request):
    """Parametrized delimiter fixture for testing different delimiters."""
    return request.param


@pytest.fixture(params=['\\', '~', '^', '`'])
def escape_char(request):
    """Parametrized escape character fixture."""
    return request.param


# Performance testing fixtures
@pytest.fixture
def large_template():
    """Large template for performance testing."""
    sections = []
    for i in range(100):
        sections.append(f"{{{{Section {i}: ;field_{i};}}}}")
    return " ".join(sections)


@pytest.fixture
def performance_data():
    """Large dataset for performance testing."""
    return {f"field_{i}": f"value_{i}" for i in range(100)}


# Error testing fixtures
@pytest.fixture
def invalid_color_template():
    """Template with invalid color for error testing."""
    return "{{#invalidcolor;message}}"


@pytest.fixture
def invalid_emphasis_template():
    """Template with invalid emphasis for error testing."""
    return "{{@invalidemphasis;message}}"


@pytest.fixture
def malformed_templates():
    """Collection of malformed templates for error testing."""
    return [
        "{{unclosed section",
        "unclosed}} section",
        "{{#;incomplete;token}}",
        "{{@;incomplete;token}}",
        "{{?;incomplete;token}}",
        "{{#red@;incomplete;combo}}",
        "{{nested {{sections}} not}} allowed",
    ]