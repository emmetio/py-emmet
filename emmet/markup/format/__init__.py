from .html import html
from .indent_format import indent_format
from ...abbreviation import Abbreviation
from ...config import Config


def haml(abbr: Abbreviation, config: Config):
    return indent_format(abbr, config, {
        'beforeName': '%',
        'beforeAttribute': '(',
        'afterAttribute': ')',
        'glueAttribute': ' ',
        'afterTextLine': ' |',
        'booleanValue': 'true',
        'selfClose': '/'
    })


def pug(abbr: Abbreviation, config: Config):
    return indent_format(abbr, config, {
        'beforeAttribute': '(',
        'afterAttribute': ')',
        'glueAttribute': ', ',
        'beforeTextLine': '| ',
        'selfClose': '/' if config.options.get('output.selfClosingStyle') == 'xml' else ''
    })


def slim(abbr: Abbreviation, config: Config):
    return indent_format(abbr, config, {
        'beforeAttribute': ' ',
        'glueAttribute': ' ',
        'beforeTextLine': '| ',
        'selfClose': '/'
    })

