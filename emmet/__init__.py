from .config import Config
from .markup import parse as markup_abbreviation, \
    stringify as stringify_markup, \
    abbreviation as parse_markup_abbreviation, \
    Abbreviation, AbbreviationNode, AbbreviationAttribute
from .stylesheet import parse as stylesheet_abbreviation, \
    stringify as stringify_stylesheet, \
    abbreviation as parse_stylesheet_abbreviation, \
    convert_snippets as parse_stylesheet_snippets
from .extract_abbreviation import extract_abbreviation as extract
from .scanner import ScannerException


def expand(abbr: str, config: dict={}, global_config: dict={}) -> str:
    "Expands given abbreviation into code snippet"
    if isinstance(config, Config):
        resolved_config = config
    else:
        resolved_config = Config(config, global_config)
    if resolved_config.type == 'stylesheet':
        return expand_stylesheet(abbr, resolved_config)

    return expand_markup(abbr, resolved_config)


def expand_markup(abbr: str, config: Config) -> str:
    """
    Expands given *markup* abbreviation (e.g. regular Emmet abbreviation that
    produces structured output like HTML) and outputs it according to options
    provided in config
    """
    return stringify_markup(markup_abbreviation(abbr, config), config)


def expand_stylesheet(abbr: str, config: Config):
    """
    Expands given *stylesheet* abbreviation (a special Emmet abbreviation designed for
    stylesheet languages like CSS, SASS etc.) and outputs it according to options
    provided in config
    """
    return stringify_stylesheet(stylesheet_abbreviation(abbr, config), config)
