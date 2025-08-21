"""
Exception classes for StringSmith.
"""


class StringSmithError(Exception):
    """Base exception for StringSmith errors."""
    pass


class MissingMandatoryFieldError(StringSmithError):
    """Raised when a mandatory field is not provided."""
    pass


class ParseError(StringSmithError):
    """Raised when template parsing fails."""
    pass


class FormattingError(StringSmithError):
    """Raised when formatting application fails."""
    pass