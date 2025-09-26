"""
Exception hierarchy for StringSmith error handling and diagnostics.

Provides structured exception types for different categories of StringSmith
errors, enabling precise error handling and debugging in professional applications.

Exception Categories:
    StringSmithError: Base exception for all StringSmith-related errors
    MissingMandatoryFieldError: Specific error for required fields marked with '!'
    ParseError: Errors during template parsing and syntax validation
    FormattingError: Runtime errors during template formatting operations

Error Context:
    Exceptions include relevant context like template content, field names,
    and position information to support debugging and error reporting.

Usage in Professional Environments:
    - Structured error handling allows applications to distinguish between
      configuration errors (bad templates) and runtime errors (missing data)
    - Rich error context supports logging and debugging workflows
    - Exception hierarchy enables both catch-all and specific error handling
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