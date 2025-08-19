"""
Sample templates and test data for dynamic formatting tests.

Provides reusable template patterns, test data sets, and common
function definitions used across multiple test modules.
"""

from typing import Dict, List, Callable, Any


# Basic template patterns
BASIC_TEMPLATES = {
    "simple": "{{Hello ;name}}",
    "with_prefix": "{{Error: ;message}}",
    "with_suffix": "{{count; items}}",
    "with_both": "{{Error: ;message;!}}",
    "multiple_fields": "{{Error: ;message}} {{Code: ;code}}",
    "empty_field": "{{}}",
    "positional_with_prefix": "{{Error: ;}}",
    "positional_multiple": "{{}} {{}}",
}

# Color formatting templates
COLOR_TEMPLATES = {
    "simple_color": "{{#red;Error: ;message}}",
    "hex_color": "{{#ff0000;Alert: ;message}}",
    "multiple_colors": "{{#red#blue;Message: ;text}}",
    "color_with_prefix": "{{#green;Success: ;message}}",
    "positional_color": "{{#red;}}",
}

# Text formatting templates
TEXT_TEMPLATES = {
    "bold": "{{@bold;Important: ;message}}",
    "italic": "{{@italic;Note: ;message}}",
    "underline": "{{@underline;Link: ;url}}",
    "combined_styles": "{{@bold@italic;Emphasis: ;text}}",
    "style_reset": "{{@bold@reset;Normal: ;text}}",
    "positional_style": "{{@bold;}}",
}

# Complex formatting templates
COMPLEX_TEMPLATES = {
    "color_and_style": "{{#red@bold;Error: ;message}}",
    "all_formatting": "{{#blue@bold@italic;Complex: ;text}}",
    "multiple_sections": "{{#red;Error: ;error}} {{#green;Success: ;success}}",
    "mixed_formatting": "{{#red@bold;Critical: ;message}} {{Count: ;count}} {{Duration: ;time;s}}",
}

# Conditional templates
CONDITIONAL_TEMPLATES = {
    "section_conditional": "{{?has_value;Found: ;data}}",
    "inline_conditional": "{{Message{?is_urgent} - URGENT: ;text}}",
    "multiple_conditionals": "{{?has_data;Processing ;count; items}} {{?has_errors;with ;error_count; errors}}",
    "complex_conditional": "{{#level_color@bold;[;level;]}} {{message}} {{?has_duration;in ;duration;s}}",
}

# Real-world application templates
REAL_WORLD_TEMPLATES = {
    "log_entry": "{{#level_color@bold;[;levelname;]}} {{message}} {{Duration: ;duration;s}} {{Memory: ;memory;MB}}",
    "api_response": "{{#status_color;HTTP ;status_code}} {{Records: ;count}} {{Errors: ;error_count}} {{Response time: ;response_time;ms}}",
    "build_status": "{{#build_color@bold;Build ;status}} {{in ;duration;s}} {{- ;test_count; tests passed}}",
    "file_processing": "{{#progress_color;Processing: ;current}}/{{total}} {{at ;rate; files/sec}} {{Errors: ;failures}}",
    "system_status": "{{#health_color@bold;System ;status}} {{CPU: ;cpu_usage;%}} {{Memory: ;memory_usage;%}} {{Uptime: ;uptime}}",
}


def get_test_functions() -> Dict[str, Callable]:
    """Get a dictionary of common test functions"""
    
    def level_color(level: str) -> str:
        """Map log levels to colors"""
        mapping = {
            "DEBUG": "cyan",
            "INFO": "green", 
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "magenta"
        }
        return mapping.get(level.upper(), "white")
    
    def status_color(status: str) -> str:
        """Map status to colors"""
        if "error" in status.lower() or "fail" in status.lower():
            return "red"
        elif "warn" in status.lower():
            return "yellow"
        elif "success" in status.lower() or "ok" in status.lower():
            return "green"
        else:
            return "blue"
    
    def has_value(value: Any) -> bool:
        """Check if value exists and is not empty"""
        return bool(value and str(value).strip())
    
    def has_items(count: int) -> bool:
        """Check if count is greater than 0"""
        return count > 0
    
    def is_urgent(priority: int) -> bool:
        """Check if priority is urgent (> 7)"""
        return priority > 7
    
    def has_duration(duration: float) -> bool:
        """Check if duration is provided and > 0"""
        return duration is not None and duration > 0
    
    def has_memory(memory: float) -> bool:
        """Check if memory is provided and > 0"""
        return memory is not None and memory > 0
    
    def has_errors(error_count: int) -> bool:
        """Check if there are any errors"""
        return error_count > 0
    
    return {
        "level_color": level_color,
        "status_color": status_color,
        "has_value": has_value,
        "has_items": has_items,
        "is_urgent": is_urgent,
        "has_duration": has_duration,
        "has_memory": has_memory,
        "has_errors": has_errors,
    }


def create_large_template(section_count: int) -> str:
    """Create a template with many sections for performance testing"""
    sections = [f"{{{{Section{i}: ;field{i}}}}}" for i in range(section_count)]
    return " ".join(sections)


def create_large_data_set(size: int) -> Dict[str, Any]:
    """Create a large data set for performance testing"""
    return {f"field{i}": f"value{i}" for i in range(size)}


# Export commonly used items
__all__ = [
    "BASIC_TEMPLATES",
    "COLOR_TEMPLATES", 
    "TEXT_TEMPLATES",
    "COMPLEX_TEMPLATES",
    "CONDITIONAL_TEMPLATES",
    "REAL_WORLD_TEMPLATES",
    "get_test_functions",
    "create_large_template",
    "create_large_data_set",
]