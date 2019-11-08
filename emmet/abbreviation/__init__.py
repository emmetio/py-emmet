from .tokenizer import tokenize
from .convert import convert
from .parser import parse
from ..scanner import ScannerException

def parse_abbreviation(abbr: str, options={}):
    try:
        tokens = tokenize(abbr) if isinstance(abbr, str) else abbr
        return convert(parse(tokens, options), options)
    except ScannerException as err:
        if isinstance(abbr, str):
            err.message += '\n%s\n%s^' % (abbr, '-' * err.pos)

        raise err
