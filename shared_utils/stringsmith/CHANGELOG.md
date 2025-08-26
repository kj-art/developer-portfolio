# Changelog

All notable changes to StringSmith will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation improvements
- Professional package structure
- Enhanced error handling with context

### Changed
- Improved module organization for better maintainability

## [0.1.0] - 2025-01-15

### Added
- Initial release with conditional template formatting
- Core `TemplateFormatter` class with section-based templating
- Conditional sections that disappear when variables are missing
- Mandatory field validation with `!` prefix syntax
- Color formatting support:
  - Matplotlib named colors (red, blue, green, etc.)
  - Hex color codes (#FF0000, ff0000)
  - Custom color functions
- Text emphasis formatting:
  - Bold (`@bold`)
  - Italic (`@italic`)
  - Underline (`@underline`)
  - Strikethrough (`@strikethrough`)
  - Dim (`@dim`)
- Custom function integration for formatting and conditionals
- Positional argument support with empty field names
- Flexible delimiter configuration (default `;`)
- Escape sequence support for literal braces and delimiters
- Template "baking" for optimized runtime performance
- Comprehensive exception hierarchy:
  - `StringSmithError` (base exception)
  - `MissingMandatoryFieldError` (required field missing)
  - `ParseError` (template syntax errors)
  - `FormattingError` (runtime formatting errors)

### Performance
- Templates parsed once during initialization for optimal reuse
- ANSI code generation cached to minimize string operations
- Memory-efficient AST representation for template sections
- O(sections) runtime complexity for format operations

### Testing
- Comprehensive test suite with 95%+ code coverage
- Tests for all formatting combinations and edge cases
- Error condition testing with proper exception validation
- Performance benchmarks for optimization validation

### Documentation
- Professional README with enterprise use cases
- Complete API reference with examples
- Integration patterns for logging and CLI applications
- Performance characteristics and thread safety notes

### Development
- Modern Python packaging with setuptools
- Code quality tooling integration
- Professional project structure