from .tokenizer import tokenize, tokens
from .parser import parser, CSSProperty, CSSValue, FunctionCall
from ..scanner import ScannerException

def parse(abbr: str, options={}):
    "Parses given abbreviation into property set"
    try:
        tokens = tokenize(abbr, options.get('value', False)) if isinstance(abbr, str) else abbr
        return parser(tokens, options)
    except ScannerException as err:
        if isinstance(abbr, str):
            err.message += '\n%s\n%s^' % (abbr, '-' * err.pos)

        raise err
