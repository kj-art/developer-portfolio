"""ANSI code utilities for StringSmith."""
import re

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')

def has_non_ansi(text: str) -> bool:
    """Check if text contains non-ANSI characters."""
    stripped = ANSI_ESCAPE.sub('', text)
    return bool(stripped)

def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return ANSI_ESCAPE.sub('', text)