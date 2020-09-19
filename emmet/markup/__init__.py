from ..config import Config
from ..abbreviation import parse as abbreviation, Abbreviation, AbbreviationNode, AbbreviationAttribute
from .attributes import merge_attributes as attributes
from .snippets import resolve_snippets as snippets
from .implicit_tag import implicit_tag
from .lorem import lorem
from .addon.jsx import jsx
from .addon.xsl import xsl
from .addon.bem import bem
from .format import html, haml, slim, pug
from .utils import walk

FORMATTERS = {
    'html': html,
    'haml': haml,
    'slim': slim,
    'pug': pug
}

def parse(abbr: str, config: Config):
    """
    Parses given Emmet abbreviation into a final abbreviation tree with all
    required transformations applied
    """

    text = config.get('text')
    if isinstance(abbr, str):
        abbr = abbreviation(abbr, {
            'text': text,
            'variables': config.variables,
            'options': config.options,
            'max_repeat': config.get('maxRepeat') or config.get('max_repeat'),
            'jsx': bool(config.options.get('jsx.enabled'))
        })

    # Run abbreviation resolve in two passes:
    # 1. Map each node to snippets, which are abbreviations as well. A single snippet
    # may produce multiple nodes
    # 2. Transform every resolved node
    # In case if config contains text, temporary remove it from config
    if text:
        config.user_config['text'] = None

    snippets(abbr, config)
    walk(abbr, transform, config)
    config.user_config['text'] = text
    return abbr

def stringify(abbr: Abbreviation, config: Config):
    "Converts given abbreviation to string according to provided `config`"
    global FORMATTERS
    formatter = FORMATTERS.get(config.syntax, html)
    return formatter(abbr, config)


def transform(node: AbbreviationNode, ancestors: list, config: Config):
    "Modifies given node and prepares it for output"
    implicit_tag(node, ancestors, config)
    attributes(node, config)
    lorem(node, ancestors, config)

    if config.syntax == 'xsl':
        xsl(node)

    if config.options.get('jsx.enabled'):
        jsx(node)

    if config.options.get('bem.enabled'):
        bem(node, ancestors, config)
