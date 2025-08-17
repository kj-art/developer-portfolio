"""
Dynamic Formatting Library - Family-Based Formatting Implementation

Clean implementation with inline formatting support and family-based state management.
Supports stacking within families and proper isolation between formatting families.
"""

import logging
from typing import Dict, Any, Callable, Optional, Union, List
from .formatters import TOKEN_FORMATTERS


class DynamicFormattingError(Exception):
    pass


class RequiredFieldError(DynamicFormattingError):
    pass


class FunctionNotFoundError(DynamicFormattingError):
    pass


class StackingError(DynamicFormattingError):
    pass


class FormattingState:
    """Tracks formatting state across families"""
    
    def __init__(self):
        # Each family maintains its own list of active formatting tokens
        self.family_states = {}  # family_name -> list of parsed tokens
    
    def add_tokens(self, family_name: str, tokens: List[Any], allow_stacking: bool):
        """Add formatting tokens to a family"""
        if family_name not in self.family_states:
            self.family_states[family_name] = []
        
        family_tokens = self.family_states[family_name]
        
        for token in tokens:
            # Handle reset tokens
            if str(token) == 'reset':
                family_tokens.clear()
                continue
            
            # Check stacking rules
            if not allow_stacking and family_tokens:
                # Find non-reset tokens
                non_reset_tokens = [t for t in family_tokens if str(t) != 'reset']
                if non_reset_tokens:
                    raise StackingError(f"Formatter family '{family_name}' does not allow stacking. "
                                      f"Already has: {non_reset_tokens}, trying to add: {token}")
            
            family_tokens.append(token)
    
    def get_family_tokens(self, family_name: str) -> List[Any]:
        """Get active tokens for a family"""
        return self.family_states.get(family_name, [])
    
    def copy(self):
        """Create a copy of the current state"""
        new_state = FormattingState()
        for family_name, tokens in self.family_states.items():
            new_state.family_states[family_name] = tokens.copy()
        return new_state


class FormattedSpan:
    def __init__(self, text: str, formatting_tokens: Optional[Dict[str, List]] = None):
        self.text = text
        self.formatting_tokens = formatting_tokens or {}  # family_name -> list of parsed tokens


class FormatSection:
    def __init__(self, field_name: str, is_required: bool = False, 
                 prefix: Union[str, List[FormattedSpan]] = "", 
                 suffix: Union[str, List[FormattedSpan]] = "", 
                 field_formatting_tokens: Optional[Dict[str, List]] = None,
                 function_name: Optional[str] = None,
                 prefix_function: Optional[str] = None,
                 suffix_function: Optional[str] = None,
                 whole_section_formatting_tokens: Optional[Dict[str, List]] = None):
        self.field_name = field_name
        self.is_required = is_required
        self.prefix = prefix
        self.suffix = suffix
        self.field_formatting_tokens = field_formatting_tokens or {}
        self.function_name = function_name
        self.prefix_function = prefix_function
        self.suffix_function = suffix_function
        self.whole_section_formatting_tokens = whole_section_formatting_tokens or {}


class DynamicFormatter:
    def __init__(self, format_string: str, delimiter: str = ';', 
                 functions: Optional[Dict[str, Callable]] = None,
                 output_mode: str = 'console'):
        self.format_string = format_string
        self.delimiter = delimiter
        self.functions = functions or {}
        self.output_mode = output_mode
        self.sections = self._parse_format_string()
    
    def _parse_format_string(self) -> List[Union[str, FormatSection]]:
        sections = []
        i = 0
        current_literal = ""
        
        while i < len(self.format_string):
            char = self.format_string[i]
            
            if char == '{' and i + 1 < len(self.format_string) and self.format_string[i + 1] == '{':
                if current_literal:
                    sections.append(current_literal)
                    current_literal = ""
                
                i += 2  # Skip {{
                template_content = ""
                while i < len(self.format_string):
                    if (i + 1 < len(self.format_string) and 
                        self.format_string[i] == '}' and self.format_string[i + 1] == '}'):
                        break
                    template_content += self.format_string[i]
                    i += 1
                
                if i + 1 < len(self.format_string):
                    i += 2  # Skip }}
                
                section = self._parse_template_content(template_content)
                sections.append(section)
            else:
                current_literal += char
                i += 1
        
        if current_literal:
            sections.append(current_literal)
        
        return sections
    
    def _parse_template_content(self, content: str) -> FormatSection:
        # Handle required
        is_required = False
        if content.startswith('!'):
            is_required = True
            content = content[1:]
        
        # Extract leading tokens (functions and formatting that apply to whole section)
        function_name = None
        whole_section_tokens = {}
        
        while True:
            found_token = False
            
            # Look for function
            if content.startswith('$') and ';' in content:
                end_pos = content.find(';')
                function_name = content[1:end_pos]
                content = content[end_pos + 1:]
                found_token = True
                continue
            
            # Look for formatting tokens
            for token_char, formatter in TOKEN_FORMATTERS.items():
                if content.startswith(token_char):
                    # Find the end of this token value
                    # For consecutive tokens like @bold@italic, we need to stop at the next @ or ;
                    i = 1  # Start after the token character
                    token_value = ""
                    
                    while i < len(content):
                        char = content[i]
                        if char == ';':
                            # Semicolon ends this token and moves to next part
                            break
                        elif char in TOKEN_FORMATTERS:
                            # Another token character starts a new token
                            break
                        else:
                            token_value += char
                            i += 1
                    
                    if not token_value:
                        # No value found, skip this
                        break
                    
                    family_name = formatter.get_family_name()
                    if family_name not in whole_section_tokens:
                        whole_section_tokens[family_name] = []
                    
                    parsed_token = formatter.parse_token(token_value)
                    
                    # Check stacking rules BEFORE adding the token
                    if not formatter.self_stacking and whole_section_tokens[family_name]:
                        # Check if there are any non-reset tokens already
                        existing_non_reset = [t for t in whole_section_tokens[family_name] if str(t) != 'reset']
                        if existing_non_reset and str(parsed_token) != 'reset':
                            raise StackingError(f"Formatter '{token_char}' does not allow self-stacking. "
                                              f"Already has: {existing_non_reset}, trying to add: {parsed_token}")
                    
                    whole_section_tokens[family_name].append(parsed_token)
                    
                    # Move past this token
                    content = content[i:]
                    if content.startswith(';'):
                        content = content[1:]
                    
                    found_token = True
                    break
            
            if not found_token:
                break
        
        # Parse remaining content
        parts = self._split_content(content)
        
        if len(parts) == 1:
            field_name, field_formatting = self._parse_field_with_formatting(parts[0])
            return FormatSection(
                field_name=field_name, 
                is_required=is_required,
                field_formatting_tokens=field_formatting,
                function_name=function_name,
                whole_section_formatting_tokens=whole_section_tokens
            )
        elif len(parts) == 2:
            prefix = self._parse_formatted_text(parts[0])
            field_name, field_formatting = self._parse_field_with_formatting(parts[1])
            
            return FormatSection(
                field_name=field_name, 
                is_required=is_required,
                prefix=prefix,
                field_formatting_tokens=field_formatting,
                function_name=function_name,
                whole_section_formatting_tokens=whole_section_tokens
            )
        elif len(parts) == 3:
            prefix_text, field_part, suffix_text = parts
            
            field_name, field_formatting = self._parse_field_with_formatting(field_part)
            
            prefix_func = None
            suffix_func = None
            processed_prefix = ""
            processed_suffix = ""
            
            if prefix_text.startswith('$'):
                prefix_func = prefix_text[1:]
            else:
                processed_prefix = self._parse_formatted_text(prefix_text)
            
            if suffix_text.startswith('$'):
                suffix_func = suffix_text[1:]
            else:
                processed_suffix = self._parse_formatted_text(suffix_text)
            
            return FormatSection(
                field_name=field_name, 
                is_required=is_required,
                prefix=processed_prefix, 
                suffix=processed_suffix,
                field_formatting_tokens=field_formatting,
                function_name=function_name,
                prefix_function=prefix_func, 
                suffix_function=suffix_func,
                whole_section_formatting_tokens=whole_section_tokens
            )
        else:
            raise DynamicFormattingError(f"Invalid syntax: got {len(parts)} parts")
    
    def _parse_field_with_formatting(self, field_part: str) -> tuple[str, Dict[str, List]]:
        """Parse field that might have formatting at the start"""
        formatting_tokens = {}
        
        # Extract formatting tokens from the beginning
        while field_part.startswith('{'):
            found_token = False
            for token_char, formatter in TOKEN_FORMATTERS.items():
                if field_part.startswith('{' + token_char):
                    # Find the end of this token
                    end_pos = field_part.find('}')
                    if end_pos == -1:
                        break
                    
                    token_value = field_part[2:end_pos]  # Skip '{' and token_char
                    field_part = field_part[end_pos + 1:]  # Skip past '}'
                    
                    family_name = formatter.get_family_name()
                    if family_name not in formatting_tokens:
                        formatting_tokens[family_name] = []
                    
                    parsed_token = formatter.parse_token(token_value)
                    
                    # Check stacking rules BEFORE adding
                    if not formatter.self_stacking and formatting_tokens[family_name]:
                        existing_non_reset = [t for t in formatting_tokens[family_name] if str(t) != 'reset']
                        if existing_non_reset and str(parsed_token) != 'reset':
                            raise StackingError(f"Formatter '{token_char}' does not allow self-stacking")
                    
                    formatting_tokens[family_name].append(parsed_token)
                    found_token = True
                    break
            
            if not found_token:
                break
        
        return field_part, formatting_tokens
    
    def _parse_formatted_text(self, text: str) -> Union[str, List[FormattedSpan]]:
        """Parse text with inline formatting tokens"""
        if '{' not in text:
            return text
        
        spans = []
        current_span = FormattedSpan("")
        i = 0
        
        while i < len(text):
            if text[i] == '{':
                # Look for formatting tokens
                # Parse all consecutive tokens like {@italic@bold}
                formatting_tokens = {}
                token_end = text.find('}', i)
                if token_end == -1:
                    current_span.text += text[i]
                    i += 1
                    continue
                
                token_content = text[i+1:token_end]
                
                # Parse multiple consecutive tokens within {}
                token_pos = 0
                while token_pos < len(token_content):
                    found_token = False
                    for token_char, formatter in TOKEN_FORMATTERS.items():
                        if token_content[token_pos:token_pos+1] == token_char:
                            # Find the end of this specific token
                            value_start = token_pos + 1
                            value_end = value_start
                            
                            # Read until we hit another token char or end
                            while value_end < len(token_content):
                                if token_content[value_end] in TOKEN_FORMATTERS:
                                    break
                                value_end += 1
                            
                            token_value = token_content[value_start:value_end]
                            if token_value:  # Only if we found a value
                                family_name = formatter.get_family_name()
                                if family_name not in formatting_tokens:
                                    formatting_tokens[family_name] = []
                                
                                parsed_token = formatter.parse_token(token_value)
                                formatting_tokens[family_name].append(parsed_token)
                                
                                token_pos = value_end
                                found_token = True
                                break
                    
                    if not found_token:
                        token_pos += 1
                
                # Find the end of this formatted section
                section_start = token_end + 1
                section_end = text.find('{', section_start)
                if section_end == -1:
                    section_end = len(text)
                
                # Save current span if it has text
                if current_span.text:
                    spans.append(current_span)
                
                # Create formatted span
                formatted_text = text[section_start:section_end]
                spans.append(FormattedSpan(formatted_text, formatting_tokens))
                
                # Start new span
                current_span = FormattedSpan("")
                i = section_end
            else:
                current_span.text += text[i]
                i += 1
        
        # Add final span if it has content
        if current_span.text:
            spans.append(current_span)
        
        # Return simple string if no formatting
        if len(spans) == 1 and not spans[0].formatting_tokens:
            return spans[0].text
        
        return spans
    
    def _split_content(self, content: str) -> List[str]:
        parts = []
        current = ""
        i = 0
        
        while i < len(content):
            char = content[i]
            
            if char == '\\' and i + 1 < len(content) and content[i + 1] == self.delimiter:
                current += self.delimiter
                i += 2
            elif char == self.delimiter:
                parts.append(current)
                current = ""
                i += 1
            else:
                current += char
                i += 1
        
        parts.append(current)
        return parts
    
    def format(self, **data) -> str:
        result = ""
        
        for section in self.sections:
            if isinstance(section, str):
                result += section
            else:
                result += self._render_section(section, data)
        
        return result
    
    def _render_section(self, section: FormatSection, data: Dict[str, Any]) -> str:
        field_value = data.get(section.field_name)
        
        if field_value is None:
            if section.is_required:
                raise RequiredFieldError("Required field missing: " + section.field_name)
            return ""
        
        # Check conditional function
        if section.function_name:
            func = self.functions.get(section.function_name)
            if not func:
                raise FunctionNotFoundError("Function not found: " + section.function_name)
            
            if not func(field_value):
                return ""
        
        # Build whole-section formatting state as base
        base_section_state = FormattingState()
        for family_name, tokens in section.whole_section_formatting_tokens.items():
            formatter = self._get_formatter_by_family(family_name)
            base_section_state.add_tokens(family_name, tokens, formatter.self_stacking)
        
        result_parts = []
        
        # Render prefix with inline formatting support
        if section.prefix_function:
            func = self.functions.get(section.prefix_function)
            if not func:
                raise FunctionNotFoundError("Prefix function not found: " + section.prefix_function)
            prefix_text = func(field_value)
            result_parts.append(self._apply_base_formatting(prefix_text, base_section_state))
        elif section.prefix:
            prefix_rendered = self._render_formatted_spans_with_base(section.prefix, base_section_state)
            result_parts.append(prefix_rendered)
        
        # Render field with combined formatting
        field_state = base_section_state.copy()
        for family_name, tokens in section.field_formatting_tokens.items():
            formatter = self._get_formatter_by_family(family_name)
            field_state.add_tokens(family_name, tokens, formatter.self_stacking)
        
        field_rendered = self._apply_base_formatting(str(field_value), field_state)
        result_parts.append(field_rendered)
        
        # Render suffix with inline formatting support
        if section.suffix_function:
            func = self.functions.get(section.suffix_function)
            if not func:
                raise FunctionNotFoundError("Suffix function not found: " + section.suffix_function)
            suffix_text = func(field_value)
            result_parts.append(self._apply_base_formatting(suffix_text, base_section_state))
        elif section.suffix:
            suffix_rendered = self._render_formatted_spans_with_base(section.suffix, base_section_state)
            result_parts.append(suffix_rendered)
        
        return "".join(result_parts)
    
    def _render_formatted_spans_with_base(self, spans: Union[str, List[FormattedSpan]], base_state: FormattingState) -> str:
        """Render formatted spans with base formatting and inline overrides"""
        if isinstance(spans, str):
            return self._apply_base_formatting(spans, base_state)
        
        # For now, let's use a simpler approach - each span gets full formatting
        result = ""
        
        for span in spans:
            # Start with base state
            span_state = base_state.copy()
            
            # Apply span-specific formatting - REPLACE families, don't add to them
            for family_name, tokens in span.formatting_tokens.items():
                # Clear the family first, then add the new tokens
                span_state.family_states[family_name] = []
                formatter = self._get_formatter_by_family(family_name)
                
                # Handle reset specially
                if tokens and str(tokens[0]) == 'reset':
                    # Reset means this family should have NO formatting for this span
                    # Don't restore base state - just leave it empty
                    pass  # Keep family_states[family_name] = []
                else:
                    # Replace with new tokens
                    span_state.add_tokens(family_name, tokens, formatter.self_stacking)
            
            # Format this span
            formatted_span = self._apply_base_formatting(span.text, span_state)
            result += formatted_span
        
        return result
    
    def _format_span_with_state_change(self, text: str, from_state: FormattingState, to_state: FormattingState) -> str:
        """Format text with a state transition, adding only necessary format codes"""
        if not text:
            return text
        
        # Determine what formatting codes need to change
        codes_to_add = []
        
        # Check each family for changes
        for family_name in set(from_state.family_states.keys()) | set(to_state.family_states.keys()):
            from_tokens = from_state.get_family_tokens(family_name)
            to_tokens = to_state.get_family_tokens(family_name)
            
            # If tokens changed for this family, we need new codes
            if from_tokens != to_tokens:
                if to_tokens:
                    formatter = self._get_formatter_by_family(family_name)
                    family_codes = self._get_family_formatting_codes(formatter, to_tokens)
                    if family_codes:
                        codes_to_add.append(family_codes)
        
        if codes_to_add:
            return ''.join(codes_to_add) + text
        else:
            return text
    
    def _get_family_formatting_codes(self, formatter, tokens) -> str:
        """Get formatting codes for a specific family"""
        if not tokens:
            return ""
        
        # Use the formatter to get codes by applying to a marker
        temp_result = formatter.apply_formatting("###MARKER###", tokens, self.output_mode)
        if temp_result and self.output_mode == 'console':
            marker_pos = temp_result.find("###MARKER###")
            if marker_pos != -1:
                return temp_result[:marker_pos]
        
        return ""
    
    def _has_active_formatting(self, formatting_state: FormattingState) -> bool:
        """Check if state has any active (non-reset) formatting"""
        for family_name, tokens in formatting_state.family_states.items():
            active_tokens = [t for t in tokens if str(t) != 'reset']
            if active_tokens:
                return True
        return False
    
    def _apply_base_formatting(self, text: str, formatting_state: FormattingState) -> str:
        """Apply formatting to text with proper reset handling"""
        if not text:
            return text
        
        # Check if we have any active formatting (non-reset tokens)
        has_active_formatting = False
        for family_name, tokens in formatting_state.family_states.items():
            active_tokens = [t for t in tokens if str(t) != 'reset']
            if active_tokens:
                has_active_formatting = True
                break
        
        # Apply formatting codes
        if has_active_formatting:
            format_codes = self._get_formatting_codes(formatting_state)
            if format_codes and self.output_mode == 'console':
                return format_codes + text + '\033[0m'
            else:
                return text
        else:
            # No active formatting - return plain text
            return text
    
    def _get_formatting_codes(self, formatting_state: FormattingState) -> str:
        """Extract just the formatting codes from a formatting state"""
        format_codes = []
        
        for family_name, tokens in formatting_state.family_states.items():
            if tokens:
                formatter = self._get_formatter_by_family(family_name)
                # Get the formatting codes by applying to a marker and extracting
                temp_result = formatter.apply_formatting("###MARKER###", tokens, self.output_mode)
                if temp_result and self.output_mode == 'console':
                    marker_pos = temp_result.find("###MARKER###")
                    if marker_pos != -1:
                        codes = temp_result[:marker_pos]
                        if codes:
                            format_codes.append(codes)
        
        return ''.join(format_codes)
    
    def _render_formatted_spans_no_formatting(self, spans: Union[str, List[FormattedSpan]]) -> str:
        """Render formatted spans as plain text (for building complete text before formatting)"""
        if isinstance(spans, str):
            return spans
        
        result = ""
        for span in spans:
            result += span.text
        return result
    
    def _apply_section_formatting(self, text: str, formatting_state: FormattingState) -> str:
        """Apply formatting codes to text without adding resets"""
        if not text:
            return text
            
        format_codes = []
        
        # Collect formatting codes from each family
        for family_name, tokens in formatting_state.family_states.items():
            if tokens:
                formatter = self._get_formatter_by_family(family_name)
                # Get the formatting codes by applying to empty string and extracting codes
                temp_result = formatter.apply_formatting("TEMP", tokens, self.output_mode)
                if temp_result and self.output_mode == 'console':
                    # Extract the codes before "TEMP"
                    temp_pos = temp_result.find("TEMP")
                    if temp_pos != -1:
                        codes = temp_result[:temp_pos]
                        if codes:
                            format_codes.append(codes)
        
        if format_codes:
            return ''.join(format_codes) + text
        else:
            return text
    
    def _get_formatter_by_family(self, family_name: str):
        """Get formatter instance by family name"""
        for formatter in TOKEN_FORMATTERS.values():
            if formatter.get_family_name() == family_name:
                return formatter
        raise ValueError(f"No formatter found for family: {family_name}")


class DynamicLoggingFormatter(logging.Formatter):
    def __init__(self, format_string: str, delimiter: str = ';', 
                 functions: Optional[Dict[str, Callable]] = None,
                 output_mode: str = 'console'):
        super().__init__()
        self.formatter = DynamicFormatter(format_string, delimiter, functions, output_mode)
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'message': record.getMessage(),
            'levelname': record.levelname,
            'name': record.name,
            'funcName': record.funcName,
            'lineno': record.lineno,
            'asctime': self.formatTime(record),
        }
        
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_'):
                log_data[key] = value
        
        try:
            return self.formatter.format(**log_data)
        except DynamicFormattingError as e:
            return "[ERROR: " + str(e) + "] " + record.getMessage()


if __name__ == "__main__":
    # Write all output to a file for easier reading
    with open('formatting_test_output.txt', 'w') as f:
        def log(message):
            print(message)  # Still print to console
            f.write(message + '\n')  # Also write to file
            f.flush()  # Ensure immediate write
        
        log("=== Family-Based Dynamic Formatting Tests ===")
        
        # Test basic formatting with families
        log("\n1. Basic color test:")
        formatter = DynamicFormatter("{{#red;Processing ;file_count; files}}")
        result = formatter.format(file_count=5)
        log(f"Basic color: {result}")
        log(f"Basic color repr: {repr(result)}")
        
        # Test stacking within text family
        log("\n2. Text stacking test:")
        formatter = DynamicFormatter("{{@bold@italic;Status: ;message}}")
        result = formatter.format(message="OK")
        log(f"Text stacking: {result}")
        log(f"Text stacking repr: {repr(result)}")
        
        # Test cross-family formatting
        log("\n3. Cross-family test:")
        formatter = DynamicFormatter("{{#green@bold;Success: ;operation; completed}}")
        result = formatter.format(operation="backup")
        log(f"Cross-family: {result}")
        log(f"Cross-family repr: {repr(result)}")
        
        # Test field-specific formatting
        log("\n4. Field formatting test:")
        formatter = DynamicFormatter("{{#green@bold;Success: ;{@italic}operation; completed}}")
        result = formatter.format(operation="backup")
        log(f"Field formatting: {result}")
        log(f"Field formatting repr: {repr(result)}")
        
        # Test inline formatting - FIXED: use #red for color, not @red
        log("\n4b. Inline formatting test:")
        formatter = DynamicFormatter("{{#green@bold;Succ{@normal}ess: ;operation; {@default}com{@italic@bold}pleted}}")
        result = formatter.format(operation="wtf")
        log(f"Inline formatting: {result}")
        log(f"Inline formatting repr: {repr(result)}")
        
        # Debug the parsing of this complex case
        sections = formatter.sections
        for i, section in enumerate(sections):
            if hasattr(section, 'prefix') and not isinstance(section.prefix, str):
                log(f"Section {i} prefix spans:")
                for j, span in enumerate(section.prefix):
                    log(f"  Span {j}: '{span.text}' with tokens {span.formatting_tokens}")
            if hasattr(section, 'suffix') and not isinstance(section.suffix, str):
                log(f"Section {i} suffix spans:")
                for j, span in enumerate(section.suffix):
                    log(f"  Span {j}: '{span.text}' with tokens {span.formatting_tokens}")
            if hasattr(section, 'whole_section_formatting_tokens'):
                log(f"Section {i} base tokens: {section.whole_section_formatting_tokens}")
        
        # Test what @normal should do vs @bold base
        log("\nReset behavior test:")
        base_state = FormattingState()
        base_state.add_tokens('color', ['green'], True)
        base_state.add_tokens('text', ['bold'], True)
        log(f"Base state: {base_state.family_states}")
        
        # When we do @normal, what should happen?
        normal_state = base_state.copy()
        normal_state.family_states['text'] = []  # Clear text formatting
        normal_state.add_tokens('text', ['reset'], True)
        log(f"After @normal: {normal_state.family_states}")
        
        # What should the base state be for text family after @normal?
        # If section has @bold, but span does @normal, span should have no text formatting
        empty_text_state = FormattingState()
        empty_text_state.add_tokens('color', ['green'], True)
        # Don't add any text formatting - this is what @normal should result in
        test_result = formatter._apply_base_formatting("TEST", empty_text_state)
        log(f"Green only (no text formatting): {repr(test_result)}")
        
        # Test text-based inline formatting
        log("\n4c. Text inline formatting test:")
        formatter = DynamicFormatter("{{#green@bold;Succ{@italic}ess{@normal}ful: ;{@underline}operation; completed}}")
        result = formatter.format(operation="wtf")
        log(f"Text inline formatting: {result}")
        log(f"Text inline formatting repr: {repr(result)}")
        
        # Debug field formatting
        sections = formatter.sections
        for i, section in enumerate(sections):
            if hasattr(section, 'field_formatting_tokens'):
                log(f"Field formatting tokens: {section.field_formatting_tokens}")
            if hasattr(section, 'prefix') and not isinstance(section.prefix, str):
                log(f"Prefix spans: {len(section.prefix)} spans")
                for j, span in enumerate(section.prefix):
                    log(f"  Span {j}: '{span.text}' with tokens {span.formatting_tokens}")
            if hasattr(section, 'whole_section_formatting_tokens'):
                log(f"Base section tokens: {section.whole_section_formatting_tokens}")
        
        # Test what individual spans should look like
        log("\nDirect span tests:")
        # Test: base formatting should be green+bold
        base_state = FormattingState()
        from .formatters import TOKEN_FORMATTERS
        base_state.add_tokens('color', ['green'], True)
        base_state.add_tokens('text', ['bold'], True)
        
        test_result = formatter._apply_base_formatting("TEST", base_state)
        log(f"Base green+bold: {repr(test_result)}")
        
        # Test: red should override text family but keep color
        red_state = base_state.copy()
        red_state.family_states['text'] = ['red']  # Replace text family
        test_result = formatter._apply_base_formatting("TEST", red_state)
        log(f"Green+red text: {repr(test_result)}")
        
        # Test: what happens when we parse red as color instead of text
        red_color_state = base_state.copy()
        red_color_state.family_states['color'] = ['red']  # Replace color family
        test_result = formatter._apply_base_formatting("TEST", red_color_state)
        log(f"Red+bold text: {repr(test_result)}")
        
        # Test @normal reset
        log("\n5. Reset test:")
        formatter = DynamicFormatter("{{@bold;Bold ;text}} and {{@normal;normal ;text}}")
        result = formatter.format(text="content")
        log(f"Reset test: {result}")
        log(f"Reset test repr: {repr(result)}")
        
        # Test error on invalid stacking
        log("\n6. Stacking error test:")
        try:
            formatter = DynamicFormatter("{{#red#blue;This should fail}}")
            result = formatter.format()
            log(f"ERROR: Should not reach here: {result}")
        except StackingError as e:
            log(f"Expected stacking error: {e}")
        except Exception as e:
            log(f"Unexpected error: {type(e).__name__}: {e}")
            import traceback
            log(traceback.format_exc())
        
        log("All tests completed!")
        
    print(f"\nOutput also written to formatting_test_output.txt")