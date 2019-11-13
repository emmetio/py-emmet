from .tokenizer import tokenize
from .convert import convert, Abbreviation, AbbreviationAttribute, AbbreviationNode
from .parser import parse as parser
from ..scanner import ScannerException

def parse(abbr: str, options={}):
    try:
        tokens = tokenize(abbr) if isinstance(abbr, str) else abbr
        return convert(parser(tokens, options), options)
    except ScannerException as err:
        if isinstance(abbr, str):
            err.message += '\n%s\n%s^' % (abbr, '-' * err.pos)

        raise err
