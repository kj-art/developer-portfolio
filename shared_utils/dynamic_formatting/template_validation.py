"""
Template validation system for dynamic formatting.

Provides proactive error prevention by validating templates at creation time,
catching common mistakes early, and offering helpful suggestions for improvement.
This professional-grade validation system helps developers catch issues during
development rather than at runtime.
"""

import re
from typing import List, Dict, Set, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """Severity levels for validation warnings"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"


@dataclass
class ValidationWarning:
    """A validation warning with context and suggestions"""
    level: ValidationLevel
    message: str
    position: Optional[int] = None
    suggestion: Optional[str] = None
    category: str = "general"
    
    def __str__(self) -> str:
        prefix = {
            ValidationLevel.INFO: "ℹ️",
            ValidationLevel.WARNING: "⚠️", 
            ValidationLevel.ERROR: "❌"
        }
        
        result = f"{prefix[self.level]} {self.message}"
        if self.position is not None:
            result += f" (position {self.position})"
        if self.suggestion:
            result += f"\n   💡 Suggestion: {self.suggestion}"
        return result


class TemplateValidator:
    """
    Comprehensive template validator with enterprise-grade checking
    
    Validates templates for:
    - Syntax errors and malformed sections
    - Invalid formatting tokens with suggestions
    - Performance anti-patterns 
    - Best practice violations
    - Function availability
    - Template complexity metrics
    """
    
    def __init__(self, formatter_registry: Dict[str, Any], 
                 function_registry: Optional[Dict[str, Callable]] = None):
        self.formatters = formatter_registry
        self.functions = function_registry or {}
        
        # Build valid token sets for suggestions
        self._build_token_sets()
        
        # Performance thresholds (configurable for different environments)
        self.max_sections_warning = 50
        self.max_sections_error = 200
        self.max_template_length_warning = 1000
        self.max_nesting_depth = 5
    
    def _build_token_sets(self) -> None:
        """Build sets of valid tokens for each formatter family"""
        self.valid_tokens: Dict[str, Set[str]] = {}
        
        for formatter in self.formatters.values():
            family = formatter.get_family_name()
            if hasattr(formatter, '_get_valid_tokens'):
                # Get tokens without function info for cleaner suggestions
                tokens = formatter._get_valid_tokens()
                clean_tokens = {t for t in tokens if not t.startswith('functions:')}
                self.valid_tokens[family] = clean_tokens
            else:
                self.valid_tokens[family] = set()
    
    def validate_template(self, template: str) -> List[ValidationWarning]:
        """
        Perform comprehensive template validation
        
        Args:
            template: Template string to validate
            
        Returns:
            List of validation warnings sorted by severity and position
        """
        warnings: List[ValidationWarning] = []
        
        # Basic syntax validation
        warnings.extend(self._validate_syntax(template))
        
        # Performance analysis
        warnings.extend(self._validate_performance(template))
        
        # Token validation
        warnings.extend(self._validate_tokens(template))
        
        # Function validation
        warnings.extend(self._validate_functions(template))
        
        # Best practices check
        warnings.extend(self._validate_best_practices(template))
        
        # Template complexity analysis
        warnings.extend(self._validate_complexity(template))
        
        # Sort by severity and position for better readability
        warnings.sort(key=lambda w: (w.level.value, w.position or 0))
        
        return warnings
    
    def _validate_syntax(self, template: str) -> List[ValidationWarning]:
        """Validate basic template syntax"""
        warnings: List[ValidationWarning] = []
        
        # Check for unmatched braces
        open_count = template.count('{{')
        close_count = template.count('}}')
        
        if open_count != close_count:
            warnings.append(ValidationWarning(
                ValidationLevel.ERROR,
                f"Unmatched template braces: {open_count} opening '{{{{', {close_count} closing '}}}}'",
                category="syntax",
                suggestion="Ensure every '{{' has a matching '}}'"
            ))
        
        # Check for empty template sections
        empty_sections = re.finditer(r'\{\{\s*\}\}', template)
        for match in empty_sections:
            pos = match.start()
            # Empty sections are valid for positional args, but warn if many
            if template.count('{{}}') > 10:
                warnings.append(ValidationWarning(
                    ValidationLevel.WARNING,
                    "Many empty template sections detected",
                    position=pos,
                    category="syntax",
                    suggestion="Consider using named fields for better readability in complex templates"
                ))
                break  # Only warn once
        
        # Check for malformed sections
        malformed = re.finditer(r'\{(?!\{).*?\}(?!\})', template)
        for match in malformed:
            pos = match.start()
            warnings.append(ValidationWarning(
                ValidationLevel.WARNING,
                f"Single braces detected: '{match.group()}'",
                position=pos,
                category="syntax",
                suggestion="Use double braces '{{...}}' for template sections"
            ))
        
        # Check for nested braces
        nested = re.finditer(r'\{\{[^}]*\{\{', template)
        for match in nested:
            pos = match.start()
            warnings.append(ValidationWarning(
                ValidationLevel.ERROR,
                "Nested template sections not allowed",
                position=pos,
                category="syntax",
                suggestion="Close the first section before starting a new one"
            ))
        
        return warnings
    
    def _validate_performance(self, template: str) -> List[ValidationWarning]:
        """Analyze template for performance issues"""
        warnings: List[ValidationWarning] = []
        
        # Count template sections
        section_count = template.count('{{')
        
        if section_count > self.max_sections_error:
            warnings.append(ValidationWarning(
                ValidationLevel.ERROR,
                f"Extremely large template with {section_count} sections will be very slow",
                category="performance",
                suggestion=f"Consider breaking into smaller templates (recommended: <{self.max_sections_warning} sections)"
            ))
        elif section_count > self.max_sections_warning:
            warnings.append(ValidationWarning(
                ValidationLevel.WARNING,
                f"Large template with {section_count} sections may impact performance",
                category="performance",
                suggestion="Consider optimizing for fewer template sections or using streaming processing"
            ))
        
        # Check template length
        if len(template) > self.max_template_length_warning:
            warnings.append(ValidationWarning(
                ValidationLevel.WARNING,
                f"Very long template ({len(template)} characters) may be hard to maintain",
                category="performance",
                suggestion="Consider breaking into smaller, reusable template components"
            ))
        
        # Check for repeated patterns that could be optimized
        sections = re.findall(r'\{\{[^}]+\}\}', template)
        section_counts = {}
        for section in sections:
            section_counts[section] = section_counts.get(section, 0) + 1
        
        duplicates = {s: count for s, count in section_counts.items() if count > 3}
        if duplicates:
            most_common = max(duplicates.items(), key=lambda x: x[1])
            warnings.append(ValidationWarning(
                ValidationLevel.INFO,
                f"Repeated template section '{most_common[0]}' appears {most_common[1]} times",
                category="performance",
                suggestion="Consider using loops or template composition for repeated patterns"
            ))
        
        return warnings
    
    def _validate_tokens(self, template: str) -> List[ValidationWarning]:
        """Validate formatting tokens and suggest corrections"""
        warnings: List[ValidationWarning] = []
        
        # Extract all token usage
        sections = re.finditer(r'\{\{([^}]+)\}\}', template)
        
        for section_match in sections:
            section_content = section_match.group(1)
            section_pos = section_match.start()
            
            # Find formatting tokens in this section
            for token_char, formatter in self.formatters.items():
                family = formatter.get_family_name()
                
                # Look for tokens like #color, @style, ?function
                token_pattern = f'\\{token_char}([^;{{}}\\{token_char}]+)'
                tokens = re.finditer(token_pattern, section_content)
                
                for token_match in tokens:
                    token_value = token_match.group(1)
                    token_pos = section_pos + token_match.start()
                    
                    # Skip function validation here (handled separately)
                    if family == 'conditional':
                        continue
                    
                    # Check if token is valid
                    if not self._is_valid_token(family, token_value):
                        suggestion = self._suggest_similar_token(family, token_value)
                        warnings.append(ValidationWarning(
                            ValidationLevel.WARNING,
                            f"Unknown {family} token '{token_value}'",
                            position=token_pos,
                            category="tokens",
                            suggestion=f"Did you mean '{suggestion}'?" if suggestion else f"Valid {family} tokens: {', '.join(sorted(list(self.valid_tokens.get(family, set()))[:5]))}"
                        ))
        
        # Check for redundant formatting
        warnings.extend(self._check_redundant_formatting(template))
        
        return warnings
    
    def _validate_functions(self, template: str) -> List[ValidationWarning]:
        """Validate function availability and usage"""
        warnings: List[ValidationWarning] = []
        
        # Extract function references
        function_patterns = [
            (r'\?([^;{}]+)', 'conditional'),  # ?function_name
            (r'#([^;{}]+)', 'color'),         # #function_name (potential)
            (r'@([^;{}]+)', 'text'),          # @function_name (potential)
        ]
        
        for pattern, context in function_patterns:
            functions = re.finditer(pattern, template)
            for match in functions:
                func_name = match.group(1).strip()
                pos = match.start()
                
                # For conditionals, functions are required
                if context == 'conditional':
                    if not self.functions or func_name not in self.functions:
                        available = list(self.functions.keys()) if self.functions else []
                        suggestion = self._suggest_similar_function(func_name, available)
                        
                        warnings.append(ValidationWarning(
                            ValidationLevel.WARNING,
                            f"Conditional function '{func_name}' not found",
                            position=pos,
                            category="functions",
                            suggestion=f"Did you mean '{suggestion}'?" if suggestion else 
                                      f"Available functions: {', '.join(available[:5])}" if available else
                                      "No conditional functions registered"
                        ))
                
                # For colors/text, check if it's likely a function (not a built-in token)
                else:
                    formatter = next(f for f in self.formatters.values() if f.get_family_name() == context)
                    if hasattr(formatter, '_get_valid_tokens'):
                        valid_tokens = formatter._get_valid_tokens()
                        # If it's not a built-in token, it's probably intended as a function
                        if func_name not in valid_tokens and func_name not in self.functions:
                            warnings.append(ValidationWarning(
                                ValidationLevel.INFO,
                                f"'{func_name}' will be treated as a function fallback",
                                position=pos,
                                category="functions",
                                suggestion=f"Ensure function '{func_name}' is registered or use a built-in {context} token"
                            ))
        
        return warnings
    
    def _validate_best_practices(self, template: str) -> List[ValidationWarning]:
        """Check for best practice violations"""
        warnings: List[ValidationWarning] = []
        
        # Check for excessive formatting in single section
        sections = re.findall(r'\{\{([^}]+)\}\}', template)
        for section in sections:
            format_count = len(re.findall(r'[#@?]', section))
            if format_count > 5:
                warnings.append(ValidationWarning(
                    ValidationLevel.WARNING,
                    f"Section has {format_count} formatting tokens - may be hard to read",
                    category="best_practices",
                    suggestion="Consider simplifying formatting or splitting into multiple sections"
                ))
        
        # Check for mixed argument styles (potential confusion)
        has_named = bool(re.search(r'\{\{[^}]*[a-zA-Z_][a-zA-Z0-9_]*[^}]*\}\}', template))
        has_positional = '{{}}' in template
        
        if has_named and has_positional:
            warnings.append(ValidationWarning(
                ValidationLevel.INFO,
                "Template mixes named fields and positional arguments",
                category="best_practices",
                suggestion="Consider using consistent argument style for clarity"
            ))
        
        # Check for very long field names (readability)
        long_fields = re.findall(r'\{\{[^}]*([a-zA-Z_][a-zA-Z0-9_]{30,})[^}]*\}\}', template)
        if long_fields:
            warnings.append(ValidationWarning(
                ValidationLevel.INFO,
                f"Very long field name detected: '{long_fields[0][:30]}...'",
                category="best_practices",
                suggestion="Consider shorter, more readable field names"
            ))
        
        return warnings
    
    def _validate_complexity(self, template: str) -> List[ValidationWarning]:
        """Analyze template complexity metrics"""
        warnings: List[ValidationWarning] = []
        
        # Calculate complexity score
        section_count = template.count('{{')
        format_count = len(re.findall(r'[#@?]', template))
        function_count = len(re.findall(r'\?[^;{}]+', template))
        nesting_depth = self._calculate_nesting_depth(template)
        
        complexity_score = section_count + (format_count * 2) + (function_count * 3) + (nesting_depth * 5)
        
        if complexity_score > 100:
            warnings.append(ValidationWarning(
                ValidationLevel.WARNING,
                f"High template complexity (score: {complexity_score})",
                category="complexity",
                suggestion="Consider breaking into smaller, focused templates"
            ))
        elif complexity_score > 200:
            warnings.append(ValidationWarning(
                ValidationLevel.ERROR,
                f"Extremely high template complexity (score: {complexity_score})",
                category="complexity",
                suggestion="Template is too complex for maintainable code - refactor required"
            ))
        
        return warnings
    
    def _check_redundant_formatting(self, template: str) -> List[ValidationWarning]:
        """Check for redundant or conflicting formatting"""
        warnings: List[ValidationWarning] = []
        
        # Check for multiple colors in same section (only last one applies)
        sections = re.finditer(r'\{\{([^}]+)\}\}', template)
        for section_match in sections:
            section = section_match.group(1)
            colors = re.findall(r'#([^;{}#@?]+)', section)
            
            if len(colors) > 1:
                pos = section_match.start()
                warnings.append(ValidationWarning(
                    ValidationLevel.INFO,
                    f"Multiple colors in section: {', '.join(colors)} - only '{colors[-1]}' will be visible",
                    position=pos,
                    category="redundancy",
                    suggestion=f"Remove redundant colors, keep only '#{colors[-1]}'"
                ))
        
        return warnings
    
    def _is_valid_token(self, family: str, token: str) -> bool:
        """Check if a token is valid for the given family"""
        valid_tokens = self.valid_tokens.get(family, set())
        return token.lower() in {t.lower() for t in valid_tokens}
    
    def _suggest_similar_token(self, family: str, token: str) -> Optional[str]:
        """Suggest a similar valid token using fuzzy matching"""
        valid_tokens = self.valid_tokens.get(family, set())
        if not valid_tokens:
            return None
        
        # Simple similarity check - could be enhanced with proper fuzzy matching
        token_lower = token.lower()
        
        # Exact substring matches
        for valid_token in valid_tokens:
            if token_lower in valid_token.lower() or valid_token.lower() in token_lower:
                return valid_token
        
        # Edit distance approximation (simple version)
        best_match = None
        best_score = float('inf')
        
        for valid_token in valid_tokens:
            # Simple score: length difference + character differences
            score = abs(len(token) - len(valid_token))
            for i, char in enumerate(token_lower):
                if i < len(valid_token) and char != valid_token[i].lower():
                    score += 1
            
            if score < best_score and score <= 3:  # Only suggest if reasonably close
                best_score = score
                best_match = valid_token
        
        return best_match
    
    def _suggest_similar_function(self, func_name: str, available: List[str]) -> Optional[str]:
        """Suggest a similar function name"""
        if not available:
            return None
        
        func_lower = func_name.lower()
        
        # Look for substring matches first
        for func in available:
            if func_lower in func.lower() or func.lower() in func_lower:
                return func
        
        # Simple similarity
        best_match = None
        best_score = float('inf')
        
        for func in available:
            score = abs(len(func_name) - len(func))
            for i, char in enumerate(func_lower):
                if i < len(func) and char != func[i].lower():
                    score += 1
            
            if score < best_score and score <= 2:
                best_score = score
                best_match = func
        
        return best_match
    
    def _calculate_nesting_depth(self, template: str) -> int:
        """Calculate the maximum nesting depth of inline formatting"""
        max_depth = 0
        current_depth = 0
        
        i = 0
        while i < len(template):
            if template[i:i+2] == '{{':
                i += 2
                # Inside a template section, look for inline formatting
                while i < len(template) and template[i:i+2] != '}}':
                    if template[i] == '{' and i + 1 < len(template) and template[i+1] in '#@?':
                        current_depth += 1
                        max_depth = max(max_depth, current_depth)
                    elif template[i] == '}':
                        current_depth = max(0, current_depth - 1)
                    i += 1
                if i < len(template):
                    i += 2  # Skip }}
            else:
                i += 1
        
        return max_depth


def create_validation_summary(warnings: List[ValidationWarning]) -> str:
    """Create a formatted summary of validation results"""
    if not warnings:
        return "✅ Template validation passed - no issues found!"
    
    # Group by category and level
    by_level = {level: [] for level in ValidationLevel}
    by_category = {}
    
    for warning in warnings:
        by_level[warning.level].append(warning)
        if warning.category not in by_category:
            by_category[warning.category] = []
        by_category[warning.category].append(warning)
    
    summary = []
    
    # Summary counts
    error_count = len(by_level[ValidationLevel.ERROR])
    warning_count = len(by_level[ValidationLevel.WARNING])
    info_count = len(by_level[ValidationLevel.INFO])
    
    summary.append(f"📊 Template Validation Results:")
    summary.append(f"   ❌ {error_count} errors, ⚠️ {warning_count} warnings, ℹ️ {info_count} info")
    summary.append("")
    
    # Show warnings by category
    for category, cat_warnings in by_category.items():
        summary.append(f"🏷️ {category.title()}:")
        for warning in cat_warnings[:3]:  # Limit to first 3 per category
            summary.append(f"   {warning}")
        if len(cat_warnings) > 3:
            summary.append(f"   ... and {len(cat_warnings) - 3} more {category} issues")
        summary.append("")
    
    return "\n".join(summary)