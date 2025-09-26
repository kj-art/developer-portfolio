"""ANSI code utilities for text processing."""
import re

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')

def has_non_ansi(text: str) -> bool:
    """Check if text contains actual content beyond ANSI escape sequences."""
    stripped = ANSI_ESCAPE.sub('', text)
    return bool(stripped)

def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return ANSI_ESCAPE.sub('', text)