"""Conditional token handler for StringSmith."""

from typing import Any, Optional
from .base import BaseTokenHandler
from ..exceptions import StringSmithError
from ..core import SectionParts
import inspect
class ConditionalTokenHandler(BaseTokenHandler):
    """
    Handles conditional tokens (?function_name) that show/hide sections.
    
    Conditional tokens call user-defined functions with field values and show
    the section only if the function returns a truthy value.
    
    Examples:
        >>> def is_error(level):
        ...     return level.lower() == 'error'
        >>> handler = ConditionalTokenHandler('?', {'is_error': is_error})
        >>> # Template: {{?is_error;[ERROR] ;level}}
        >>> # Shows "[ERROR] " prefix only when level is 'error'
    """

    RESET_ANSI = ''  # Conditional tokens don't produce ANSI escape codes
    
    def _apply_sectional_formatting(self, token_value: str, field_value: Any, text: tuple[str, str, str]) -> Optional[tuple]:
        """Apply conditional logic to section visibility."""
        if token_value in self.functions: # the token's value is a call to one of the custom functions
            if field_value is None: # no field provided - this is a bake pass
                return None
            else:
                token_value = self._call_function(token_value, field_value)
        else:
            raise StringSmithError(f"Error applying function '{token_value}'")
        return text if token_value else ('', '', '')
    

    def apply_inline_formatting(self, parts: SectionParts, field_value: Any = None) -> bool:
        if field_value is None: # Baking phase
            return False
        
        def apply_inline_formatting_to_part(p:str) -> bool:
            found = []

            for start, end, token_value in self.find_token(parts[p]):
                if token_value in self.functions:
                    obj = {
                        'show': self._call_function(token_value, field_value),
                        'start': start,
                        'end': end
                    }
                    found.append(obj)
                elif self._is_reset_token(token_value):
                    obj = {
                        'show': True,
                        'start': start,
                        'end': end
                    }
                    found.append(obj)
                else:
                    raise StringSmithError(f"Error applying function '{token_value}'")
            
            if not len(found):
                return True
            last_index = len(found) - 1
            show_field = found[last_index]['show']
            result = parts[p][found[last_index]['end']:] if show_field else ''
            for i in range(last_index - 1, -1, -1):
                if found[i]['show']:
                    result = parts[p][found[i]['end']:found[i+1]['start']] + result
            parts[p] = parts[p][:found[0]['start']] + result

            return show_field

        for p in ['prefix', 'suffix']:
            apply_inline_formatting_to_part(p)
        return apply_inline_formatting_to_part('field')

    '''def apply_inline_formatting(self, parts: SectionParts, field_value: Any = None) -> bool:
        if field_value is None: # Baking phase
            return False

        def apply_inline_formatting_to_part(p:str) -> bool:
            nonlocal parts
            funcs = {}
            do_reset = lambda: True

            for start, end, token_value in self.find_token(parts[p]):
                if token_value in funcs:
                    funcs[token_value]['end'] = max(end, funcs[token_value]['end'])
                elif token_value in self.functions:
                    func = self.functions[token_value]
                    funcs[token_value] = {
                        'func': func,
                        'needs_field_value': len(inspect.signature(func).parameters) != 0,
                        'end': end
                    }
                elif self._is_reset_token(token_value):
                    funcs[token_value] = {
                        'func': do_reset,
                        'needs_field_value': False,
                        'end': end
                    }
                else:
                    raise StringSmithError(f"Error applying function '{token_value}'")
            
            parts[p], show_field = self._replace_dynamic_tokens(parts[p], funcs, field_value)
            return show_field

        for p in ['prefix', 'suffix']:
            apply_inline_formatting_to_part(p)
        show_field = apply_inline_formatting_to_part('field')
        return show_field
    
    def _replace_dynamic_tokens(self, part: str, func_tokens: dict, field_value: Any) -> tuple[str, bool]:
        
        # this doesn't work. it updates part as it goes through the loop, so it'll cut out later resets and then not see
        
        last_do_show = True, -1
        for token, func in func_tokens.items():
            print(part)
            parts_list = part.split(self._get_token_bracket(token))
            bools = [(func['func'](field_value) if func['needs_field_value'] else func['func'](), func['end']) for _ in range(len(parts_list) - 1)]
            print(f'{token}|||||||{bools}')
            result = parts_list[0]
            for i, do_show in enumerate(bools):
                print(do_show)
                if do_show[1] > last_do_show[1]:
                    last_do_show = do_show
                if do_show[0]:
                    result += parts_list[i + 1]
            part = result
            
        return part, last_do_show[0]
    
    def finalize(self, section: TemplateSection, field_value: Any) -> bool:
        """Process conditional markers and show/hide content accordingly."""
        for part in section.get_parts():
            part.content = self._finalize(part, field_value)
        return True
    
    def _finalize(self, template_part: TemplatePart, field_value: Any) -> str:
        template_part = template_part.copy()
        pieces = template_part.content.split('\uE000')
        result = pieces.pop(0)
        inline_formatting = template_part.get_inline_formatting_of_type(self._token)
        if len(pieces) != len(inline_formatting):
            raise StringSmithError(f"Error finalizing text_segment '{template_part.content}': Mismatch between formatting length and number of conditional ANSI markers")
        for i, v in enumerate(pieces):
            token_value = inline_formatting[i].value
            if self._is_reset_token(token_value):
                result += v
            elif token_value not in self.functions:
                raise StringSmithError(f"Error applying function '{token_value}'")
            else:
                # Show piece only if function returns truthy value
                result += v if self._call_function(token_value, field_value) else ''
        return result'''
    
    def get_replacement_text(self, token_value: str, field_value: str = None) -> str:
        return ''