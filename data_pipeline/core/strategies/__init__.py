"""
Data processing strategies package.

Provides different processing strategies that can be selected based on 
dataset size, output format, and performance requirements.
"""

from .streaming_processor import StreamingProcessor
from .in_memory_processor import InMemoryProcessor

__all__ = [
    'StreamingProcessor',
    'InMemoryProcessor'
]