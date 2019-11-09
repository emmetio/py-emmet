from emmet.abbreviation.parser import parse as parser
from emmet.abbreviation.tokenizer import tokenize

def parse(abbr: str, options={}):
    return parser(tokenize(abbr), options)

print(parse('ul.nav[title="foo"]'))
