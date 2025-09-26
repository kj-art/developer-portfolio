"""
Configuration management for batch rename operations.

This package provides loading and parsing of YAML/JSON configuration files
for batch rename workflows, enabling reusable processing templates.
"""

from .config_loader import ConfigLoader

__all__ = ['ConfigLoader']