"""
Template parsing engine for StringSmith conditional formatting.

This module handles the core parsing logic that converts template strings into
structured AST objects for efficient runtime evaluation. The parser recognizes
template sections ({{...}}), inline formatting tokens, escape sequences, and
custom delimiters.
"""

import re
from typing import List, Optional, Dict, Tuple, Iterator, Union


from ..exceptions import StringSmithError
from ..tokens import SORTED_TOKENS
from . import TemplateSection, SectionParts

class TemplateParser:
    """
    Parses template strings into structured AST representations for efficient evaluation.
    
    TemplateParser converts StringSmith template strings into TemplateSection objects
    that can be efficiently evaluated with runtime data. The parser handles the full
    complexity of StringSmith template syntax including formatting tokens, escape
    sequences, and custom delimiters.
    
    Args:
        delimiter (str, optional): Character(s) separating components within template
                                 sections. Defaults to ';'.
        escape_char (str, optional): Character(s) for escape sequences. Defaults to '\\'.
        
    Examples:
        >>> parser = TemplateParser()
        >>> sections = parser.parse_template("{{Hello ;name;}}")
        
        >>> parser = TemplateParser(delimiter='|')
        >>> sections = parser.parse_template("{{Hello|name|!}}")
    """
    
    _instance = None
    
    def __new__(cls, delimiter=';', escape_char='\\'):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, delimiter=';', escape_char='\\'):
        if not self._initialized:
            self.delimiter = delimiter
            self.escape_char = escape_char

            # Pre-compile regex patterns for efficient parsing
            self.section_pattern = re.compile(r'\{\{(.*?)\}\}')
            self._initialized = True

    @property
    def delimiter(self):
        return self._delimiter

    @delimiter.setter
    def delimiter(self, value):
        self._delimiter = value

    @property
    def escape_char(self):
        return self._escape_char

    @escape_char.setter
    def escape_char(self, value):
        self._escape_char = value
        
        # Inline formatting pattern with escape handling
        escaped_tokens = [re.escape(token) for token in SORTED_TOKENS]
        token_pattern = '|'.join(escaped_tokens)
        esc = re.escape(value)  # "\\" becomes "\\\\"
        self.inline_pattern = re.compile(f'(?<!{esc})(?:{esc}{esc})*\\{{({token_pattern})([^}}]*)\\}}')

    def create_token_regex(self, *tokens: str) -> re.Pattern:
        """
        Create a compiled regex pattern that matches {token...} sequences for specified tokens.
        
        Builds an optimized regex that finds brace sequences starting with any of the
        provided token prefixes. The regex uses alternation with longest-first matching
        to handle overlapping token prefixes correctly.
        
        Args:
            *tokens: Variable number of token prefix strings to match (e.g., '#', '@', '?', '$')
            
        Returns:
            re.Pattern: Compiled regex that matches {token_content} where token_content
                    starts with any of the provided token prefixes
                    
        Examples:
            >>> pattern = create_token_regex('#', '@', '?')
            >>> # Matches: {#red}, {@bold}, {?show_errors}, etc.
            >>> # Doesn't match: {$literal}, {unknown}, etc.
            
            >>> pattern = create_token_regex('?')  
            >>> # Matches only: {?function_name}
            
            >>> for match in pattern.finditer("text {#red}colored{@bold}bold text"):
            ...     print(match.groups())
            ('red', '#')
            ('bold', '@')
        
        Pattern Details:
            - Uses non-greedy matching (.*?) to handle nested braces correctly
            - Sorts tokens by length (longest first) to prevent partial matches
            - Uses capturing groups to extract both content and token type
            - Handles empty token list gracefully (returns pattern that matches nothing)
            
        Performance:
            - Compiled regex is much faster than multiple sequential searches
            - Single pass through text finds all relevant tokens
            - Longest-first ordering prevents incorrect partial matches
        """
        if not tokens:
            # Return pattern that matches nothing if no tokens provided
            return re.compile(r'(?!)')
        
        # Sort tokens by length (longest first) to prevent partial matches
        # Example: if tokens are ['#', '##'], we want '##' to match before '#'
        sorted_tokens = sorted(tokens, key=len, reverse=True)
        
        # Escape special regex characters in token prefixes
        escaped_tokens = [re.escape(token) for token in sorted_tokens]
        
        # Create alternation pattern: (#|@|\?) 
        token_alternation = '|'.join(escaped_tokens)
        
        # Full pattern: \{(content_starting_with_token)\}
        # Capturing groups: (content, token_type)
        # (?=...) is a positive lookahead to capture which token matched
        pattern = rf'\{{(({token_alternation})(.*?))\}}'
        
        return re.compile(pattern)
    
    def split_tokens(
        self,
        text: str,
        token: Union[str, List[str], re.Pattern]
    ) -> List[Union[str, Tuple[str, str]]]:
        """
        Split `text` on tokenized sections, keeping prefix/content info.

        Args:
            text: The string to split.
            token: Single token string, list of token strings, or precompiled regex.

        Returns:
            List of segments: plain strings or tuples (token_prefix, token_content)
        """
        # Determine regex pattern
        if isinstance(token, re.Pattern):
            pattern = token
        else:
            # Normalize to list
            tokens = [token] if isinstance(token, str) else token
            pattern = self.create_token_regex(*tokens)

        result = []
        last_end = 0

        for match in pattern.finditer(text):
            start, end = match.start(), match.end()
            groups = match.groups()

            # Expecting groups: full_content, token_prefix, token_content
            if len(groups) >= 3:
                full_content, token_prefix, token_content = groups
            else:
                full_content = groups[0]
                token_prefix = ''
                token_content = full_content

            # Append text before the token
            if start > last_end:
                result.append(text[last_end:start])

            # Append token as tuple
            result.append((token_prefix, token_content))
            last_end = end

        # Append remaining text
        if last_end < len(text):
            result.append(text[last_end:])

        return result
    
    def find_token(self, text: str, token: Union[str, re.Pattern] = None) -> Iterator[Tuple[int, int, str]]:
        """
        Find unescaped {token ...} sequences in text using string token or pre-compiled regex.
        
        Args:
            text: Text to search for tokens
            token: Either a string token prefix (e.g., '#') or a pre-compiled regex pattern
                If string: creates regex using create_token_regex() 
                If Pattern: uses the provided regex directly
                If None: uses self.get_token() for backward compatibility
        
        Yields:
            Tuple[int, int, str, str]: (start_index, end_index, token_content, token_prefix)
            
        Examples:
            # Single token string
            for start, end, content in self.find_token(text, '#'):
                # Finds {#red}, {#blue}, etc.
                
            # Pre-compiled pattern for multiple tokens
            pattern = create_token_regex('#', '@', '?')
            for start, end, content in self.find_token(text, pattern):
                # Finds {#red}, {@bold}, {?show}, etc. in single pass
        """
        escape_len = len(self._escape_char)
        def is_unescaped(pos: int) -> bool:
            count = 0
            i = pos - escape_len
            while i >= 0 and text[i:i+escape_len] == self._escape_char:
                count += 1
                i -= escape_len
            return count % 2 == 0
        
        # Determine pattern based on token parameter type
        pattern = token if isinstance(token, re.Pattern) else self.create_token_regex(token)
        
        # Common logic for all pattern types
        for match in pattern.finditer(text):
            start, end = match.start(), match.end()
            groups = match.groups()
            
            # Extract token content (after the prefix)
            if len(groups) >= 3:
                full_content, token_prefix, token_content = groups
            else:
                # Fallback for simpler patterns or single-token case
                full_content = groups[0]
                token_content = full_content

            # Check if unescaped and yield
            if is_unescaped(start) and is_unescaped(end - 1):
                yield start, end, token_content, token_prefix

    def parse_template(self, template: str) -> List[TemplateSection]:
        sections = []
        i = 0
        
        while i < len(template):
            # Look for opening {{
            start = template.find('{{', i)
            if start == -1:
                # Add remaining literal text
                if i < len(template):
                    text_content = self._unescape_text(template[i:])
                    if text_content:
                        sections.append(self._create_text_section(text_content))
                break
            
            # Add literal text before section
            if start > i:
                text_content = self._unescape_text(template[i:start])
                if text_content:
                    sections.append(self._create_text_section(text_content))
            
            # Find matching }}
            end = self._find_matching_close_brace(template, start + 2)
            if end == -1:
                raise StringSmithError(f"Unclosed section starting at position {start}")
            
            # Extract and parse section content
            section_content = template[start + 2:end]
            section = self._parse_section(section_content)
            sections.append(section)
            
            i = end + 2
        
        return sections
    
    def _is_position_unescaped(self, text: str, pos: int) -> bool:
        """Check if position is unescaped using the same logic as find_token."""
        escape_len = len(self._escape_char)
        if pos < escape_len:
            return True
        
        count = 0
        i = pos - escape_len
        while i >= 0 and text[i:i + escape_len] == self._escape_char:
            count += 1
            i -= escape_len
        return count % 2 == 0

    def _find_matching_close_brace(self, template: str, start_pos: int) -> int:
        """
        Find matching }} for a {{ section, handling nested tokens and escape sequences.
        
        Properly handles {token} constructs inside sections by skipping over them
        during brace counting. Respects escape sequences to avoid matching escaped braces.
        Essential for parsing complex nested template structures correctly.
        
        Args:
            template: Full template string
            start_pos: Position after opening {{ to start search
            
        Returns:
            Position of matching }} or -1 if not found
            
        Raises:
            StringSmithError: If no matching }} found (handled by caller)
        """
        section_brace_count = 1
        i = start_pos
        
        while i < len(template) - 1:
            # Check for single { - start of a token
            if template[i] == '{' and template[i+1] != '{':
                if self._is_position_unescaped(template, i):
                    # Find the closing } for this token
                    token_end = template.find('}', i + 1)
                    if token_end != -1:
                        i = token_end + 1  # Skip past the token entirely
                        continue
            
            # Check for {{
            elif template[i:i+2] == '{{':
                if self._is_position_unescaped(template, i):
                    section_brace_count += 1
                i += 2
            
            # Check for }}
            elif template[i:i+2] == '}}':
                if self._is_position_unescaped(template, i):
                    section_brace_count -= 1
                    if section_brace_count == 0:
                        return i
                i += 2
            else:
                i += 1
        
        return -1
    
    def _create_text_section(self, text: str) -> TemplateSection:
        """Create a TemplateSection for literal text (no variables)."""
        return TemplateSection(
            is_mandatory=False,
            section_formatting=[],
            field_name=None,  # None indicates literal text
            parts=SectionParts(text, '', None),
            live_tokens=[]
        )
    
    def _split_unescaped(self, content: str) -> List[str]:
        """Split content on delimiter characters that are not escaped."""
        # Match: (even number of escape chars)(delimiter)
        # (?<!\\) ensures we're not in the middle of escape sequence
        # (\\\\)* matches zero or more pairs of escapes (even count)
        esc = re.escape(self._escape_char)
        delim = re.escape(self._delimiter)
        pattern = f"(?<!{esc})(?:{esc}{esc})*{delim}"
        
        return re.split(pattern, content)

    def split_by_substrings(self, text: str, substrings: List[str]) -> Dict[str, List[str]]:
        """Split text by multiple substrings, tracking which delimiter was used."""
        # Sort by length (longest first) to avoid partial matches
        sorted_subs = sorted(substrings, key=len, reverse=True)
        
        # Create regex pattern with capturing groups
        escaped_subs = [re.escape(sub) for sub in sorted_subs]
        pattern = f"({'|'.join(escaped_subs)})"
        
        # Split while keeping delimiters
        parts = re.split(pattern, text)
        
        # Organize into dictionary
        result = {sub: [] for sub in substrings}
        current_key = None
        
        for part in parts:
            if part in substrings:
                current_key = part
            elif current_key is not None and part:  # Skip empty parts
                result[current_key].append(part)
        
        return result
    
    def _extract_starting_token(self, text: str) -> Tuple[Optional[str], str]:
        """Extract starting token and return (token, remaining_text)."""
        if text:
            # Sort by length descending to match longest tokens first
            for token in SORTED_TOKENS:
                if text.startswith(token):
                    remaining = text[len(token):]
                    return token, remaining
        
        return None, text
    
    def _parse_section(self, content: str) -> TemplateSection:
        """Parse the content of a single {{}} section."""
        is_mandatory, content = self._extract_mandatory_marker(content)
        section_tokens, parts = self._extract_formatting_tokens(content)
        prefix, field, suffix = self._split_into_parts(parts)
        
        field = self._extract_field_name(field)
        return TemplateSection(
                is_mandatory=is_mandatory,
                section_formatting=section_tokens,
                field_name=field[0], # field name used as identifier
                parts=SectionParts(prefix, field[1], suffix),  # the rest of the field part (formatting) left in text
                live_tokens=[]
            )
    
    def _extract_field_name(self, field_text: str) -> Tuple[str, str]:
        """
        Extract field name from field part, separating tokens from literal field name.
        
        Ensures formatting tokens appear before literal text by validating token positions.
        This maintains consistent parsing rules and prevents ambiguous field definitions.
        
        Args:
            field_text: Raw field part text potentially containing tokens and field name
            
        Returns:
            Tuple of (field_name, remaining_tokens) where field_name is the literal
            identifier and remaining_tokens contains any formatting for the field itself
            
        Raises:
            StringSmithError: If tokens appear after literal text (invalid format)
        """
        result = field_text
        
        escaped_tokens = [re.escape(token) for token in SORTED_TOKENS]
        token_pattern = '|'.join(escaped_tokens)
        valid_token_pattern = f'^\\{{({token_pattern})[^}}]*\\}}'
        
        tokens = ''

        # Remove all leading valid tokens
        while True:
            match = re.match(valid_token_pattern, result)
            if not match:
                break
            tokens = result[:match.end()]
            result = result[match.end():]
        
        # Search for valid tokens anywhere in remaining text (no ^ anchor)
        search_pattern = f'\\{{({token_pattern})[^}}]*\\}}'
        if re.search(search_pattern, result):
            raise StringSmithError(
                f"Invalid field format: '{field_text}'. "
                f"All valid formatting tokens must precede all literal text."
            )
        
        return result.strip(), tokens
    
    def _extract_mandatory_marker(self, content: str) -> tuple[bool, str]:
        """Extract mandatory marker and return cleaned content."""
        if content.startswith('!'):
            return True, content[1:]
        return False, content
    
    def _extract_formatting_tokens(self, content: str) -> tuple[Dict[str, List[str]], List[str]]:
        """Extract formatting tokens from the beginning of section content."""
        parts = self._split_unescaped(content)
        
        if not parts:
            return {}, []
        
        first_token, _ = self._extract_starting_token(parts[0])
        if first_token:
            format_part = parts.pop(0)
            section_tokens = self.split_by_substrings(format_part, SORTED_TOKENS)
            return section_tokens, parts
        
        return {}, parts
    
    def _split_into_parts(self, parts: List[str]) -> tuple[str, str, str]:
        """Split remaining parts into prefix, field, and suffix."""
        prefix = ''
        field = ''
        suffix = ''

        match len(parts):
            case 0: 
                pass
            case 1: 
                field = parts[0]
            case 2: 
                prefix, field = parts
            case 3: 
                prefix, field, suffix = parts
            case _: 
                section_repr = f"{{{{{self._delimiter.join(parts)}}}}}"
                raise StringSmithError(f"Too many parts in section: {section_repr}")

        return prefix, field, suffix

    def unescape_part(self, part: str) -> str:
        """Remove escape sequences from text part."""
        if not part:
            return part
        
        result = ""
        i = 0
        while i < len(part):
            char = part[i]
            if char == self._escape_char and i + 1 < len(part):
                # Escaped character - add next character literally
                result += part[i + 1]
                i += 2
            else:
                # Regular character
                result += char
                i += 1
        
        return result
    
    def _unescape_text(self, text: str) -> str:
        """Remove escape sequences from literal text."""
        return self.unescape_part(text)