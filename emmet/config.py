from .snippets import markup_snippets, stylesheet_snippets, xsl_snippets, pug_snippets, variables

DEFAULT_SYNTAXES = { 'markup': 'html', 'stylesheet': 'css' }
"Default syntaxes for abbreviation types"

SYNTAXES = {
    'markup': ['html', 'xml', 'xsl', 'jsx', 'js', 'pug', 'slim', 'haml'],
    'stylesheet': ['css', 'sass', 'scss', 'less', 'sss', 'stylus']
}
"List of all known syntaxes"

DEFAULT_OPTIONS = {
    'inlineElements': [
        'a', 'abbr', 'acronym', 'applet', 'b', 'basefont', 'bdo',
        'big', 'br', 'button', 'cite', 'code', 'del', 'dfn', 'em', 'font', 'i',
        'iframe', 'img', 'input', 'ins', 'kbd', 'label', 'map', 'object', 'q',
        's', 'samp', 'select', 'small', 'span', 'strike', 'strong', 'sub', 'sup',
        'textarea', 'tt', 'u', 'var'
    ],
    'output.indent': '\t',
    'output.baseIndent': '',
    'output.newline': '\n',
    'output.tagCase': '',
    'output.attributeCase': '',
    'output.attributeQuotes': 'double',
    'output.format': True,
    'output.formatLeafNode': False,
    'output.formatSkip': ['html'],
    'output.formatForce': ['body'],
    'output.inlineBreak': 3,
    'output.compactBoolean': False,
    'output.booleanAttributes': [
        'contenteditable', 'seamless', 'async', 'autofocus',
        'autoplay', 'checked', 'controls', 'defer', 'disabled', 'formnovalidate',
        'hidden', 'ismap', 'loop', 'multiple', 'muted', 'novalidate', 'readonly',
        'required', 'reversed', 'selected', 'typemustmatch'
    ],
    'output.reverseAttributes': False,
    'output.selfClosingStyle': 'html',
    'output.field': lambda index, placeholder, **kwargs: placeholder,
    'output.text': lambda text, **kwargs: text,

    'markup.href': True,

    'comment.enabled': False,
    'comment.trigger': ['id', 'class'],
    'comment.before': '',
    'comment.after': '\n<!-- /[#ID][.CLASS] -->',

    'bem.enabled': False,
    'bem.element': '__',
    'bem.modifier': '_',

    'jsx.enabled': False,

    'stylesheet.keywords': ['auto', 'inherit', 'unset'],
    'stylesheet.unitless': ['z-index', 'line-height', 'opacity', 'font-weight', 'zoom', 'flex', 'flex-grow', 'flex-shrink'],
    'stylesheet.shortHex': True,
    'stylesheet.between': ': ',
    'stylesheet.after': ';',
    'stylesheet.intUnit': 'px',
    'stylesheet.floatUnit': 'em',
    'stylesheet.unitAliases': { 'e': 'em', 'p': '%', 'x': 'ex', 'r': 'rem' },
    'stylesheet.json': False,
    'stylesheet.jsonDoubleQuotes': False,
    'stylesheet.fuzzySearchMinScore': 0,
    'stylesheet.skipUnmatched': True,
}

DEFAULT_CONFIG = {
    'type': 'markup',
    'syntax': 'html',
    'variables': variables,
    'snippets': {},
    'options': DEFAULT_OPTIONS
}

SYNTAX_CONFIG = {
    'markup': {
        'snippets': markup_snippets,
    },
    'xhtml': {
        'options': {
            'output.selfClosingStyle': 'xhtml'
        }
    },
    'xml': {
        'options': {
            'output.selfClosingStyle': 'xml'
        }
    },
    'xsl': {
        'snippets': xsl_snippets,
        'options': {
            'output.selfClosingStyle': 'xml'
        }
    },
    'jsx': {
        'options': {
            'jsx.enabled': True
        }
    },
    'pug': {
        'snippets': pug_snippets
    },

    'stylesheet': {
        'snippets': stylesheet_snippets
    },

    'sass': {
        'options': {
            'stylesheet.after': ''
        }
    },
    'stylus': {
        'options': {
            'stylesheet.between': ' ',
            'stylesheet.after': '',
        }
    }
}

class Config:
    __slots__ = ('type', 'syntax', 'variables', 'snippets', 'options', 'user_config', 'context', 'cache')

    def __init__(self, user_config={}, global_config={}):
        syntax_type = user_config.get('type', 'markup')
        syntax = user_config.get('syntax', DEFAULT_SYNTAXES.get(syntax_type, 'html'))

        self.type = syntax_type
        self.syntax = syntax
        self.user_config = user_config
        self.context = user_config.get('context')
        self.variables = merged_data(syntax_type, syntax, 'variables', user_config, global_config)
        self.snippets = merged_data(syntax_type, syntax, 'snippets', user_config, global_config)
        self.options = merged_data(syntax_type, syntax, 'options', user_config, global_config)
        self.cache = user_config.get('cache')

    def get(self, key: str):
        if key in dir(self):
            return self.__getattribute__(key)

        if key in self.user_config:
            return self.user_config.get(key)

        return None


def merged_data(syntax_type: str, syntax: str, key: str, user_config: dict, global_config: dict={}):
    empty = {}
    type_defaults = SYNTAX_CONFIG.get(syntax_type, empty)
    type_override = global_config.get(syntax_type, empty)
    syntax_defaults = SYNTAX_CONFIG.get(syntax, empty)
    syntax_override = global_config.get(syntax, empty)

    result = {}
    result.update(DEFAULT_CONFIG.get(key, empty))
    if key in type_defaults: result.update(type_defaults[key])
    if key in syntax_defaults: result.update(syntax_defaults[key])
    if key in type_override: result.update(type_override[key])
    if key in syntax_override: result.update(syntax_override[key])
    result.update(user_config.get(key, empty))

    return result
