from .css import snippets as raw_stylesheet_snippets
from .html import snippets as raw_markup_snippets
from .xsl import snippets as raw_xsl_snippets
from .pug import snippets as raw_pug_snippets
from .variables import variables

def parse_snippets(snippets: dict):
    """
    Parses raw snippets definitions with possibly multiple keys into a plan
    snippet map
    """
    result = {}
    for k in snippets.keys():
        for name in k.split('|'):
            result[name] = snippets[k]

    return result

# Parse raw snippets which may contains multiple entries in key into one-to-one dict
markup_snippets = parse_snippets(raw_markup_snippets)
stylesheet_snippets = parse_snippets(raw_stylesheet_snippets)
xsl_snippets = parse_snippets(raw_xsl_snippets)
pug_snippets = parse_snippets(raw_pug_snippets)
