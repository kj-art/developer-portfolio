"""
Advanced logging configuration for batch rename operations.

Provides centralized logging configuration with environment-specific
settings and professional StringSmith templates for rich output formatting.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

from shared_utils.logger import set_up_logging


class LoggingConfig:
    """
    Centralized logging configuration manager.
    
    Handles environment-specific logging setup with professional
    templates and performance optimizations.
    """
    
    # StringSmith templates for different log levels and contexts
    CONSOLE_TEMPLATES = {
        'minimal': "{{#level_color;[;levelname;]}} {{message}}",
        'standard': "{{#level_color;[;levelname;]}} {{message}}{{ (;file_count; files)}}{{ in ;duration;$format_duration}}{{ (;error_count; errors)}}",
        'detailed': "{{asctime}} {{#level_color;[;levelname;]}} {{name}} - {{message}}{{ (;file_count; files)}}{{ in ;duration;$format_duration}}{{ (;error_count; errors)}}{{ - ;operation;}}",
        'debug': "{{asctime}} {{#level_color;[;levelname;]}} {{name}}:{{lineno}} - {{funcName}} - {{message}}{{ (;file_count; files)}}{{ in ;duration;$format_duration}}{{ (;error_count; errors)}}"
    }
    
    FILE_TEMPLATES = {
        'standard': "{{asctime}} - {{name}} - {{levelname}} - {{message}}{{ (;file_count; files)}}{{ - duration: ;duration;$format_duration}}{{ - errors: ;error_count;}}",
        'detailed': "{{asctime}} - {{name}} - {{levelname}} - {{funcName}}:{{lineno}} - {{message}}{{ (;file_count; files)}}{{ - duration: ;duration;$format_duration}}{{ - size: ;file_size_mb;MB}}{{ - memory: ;memory_delta_mb;MB}}{{ - errors: ;error_count;}}",
        'operational': "{{asctime}} - {{levelname}} - OPERATION: {{operation}} - {{message}} - FILES: {{file_count}} - DURATION: {{duration}}s - SUCCESS_RATE: {{success_rate}}% - ERRORS: {{error_count}}"
    }
    
    # Environment-specific configurations
    ENVIRONMENTS = {
        'development': {
            'level': 'DEBUG',
            'console_template': 'debug',
            'file_template': 'detailed',
            'enable_colors': True,
            'max_file_size': '10MB',
            'backup_count': 3
        },
        'testing': {
            'level': 'INFO',
            'console_template': 'minimal',
            'file_template': 'standard',
            'enable_colors': False,
            'max_file_size': '5MB',
            'backup_count': 2
        },
        'production': {
            'level': 'WARNING',
            'console_template': 'standard',
            'file_template': 'operational',
            'enable_colors': False,
            'max_file_size': '50MB',
            'backup_count': 10
        },
        'cli': {
            'level': 'INFO',
            'console_template': 'standard',
            'file_template': 'detailed',
            'enable_colors': True,
            'max_file_size': '20MB',
            'backup_count': 5
        }
    }