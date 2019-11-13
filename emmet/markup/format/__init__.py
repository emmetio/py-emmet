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
        'booleanValue': 'true'
    })


def pug(abbr: Abbreviation, config: Config):
    return indent_format(abbr, config, {
        'beforeAttribute': '(',
        'afterAttribute': ')',
        'glueAttribute': ', ',
        'beforeTextLine': '| '
    })


def slim(abbr: Abbreviation, config: Config):
    return indent_format(abbr, config, {
        'beforeAttribute': ' ',
        'glueAttribute': ' ',
        'beforeTextLine': '| '
    })

