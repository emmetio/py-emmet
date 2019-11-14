from .config import Config
from .abbreviation.convert import AbbreviationAttribute, AbbreviationNode

class OutputStream:
    __slots__ = ('options', '_value', 'level', 'offset', 'line', 'column')

    def __init__(self, options={}, level=0):
        self._value = []
        self.options = options
        self.level = level
        self.offset = 0
        self.line = 0
        self.column = 0

    @property
    def value(self):
        return ''.join(self._value)

    def _push(self, text: str):
        "Pushes raw string into output stream without any processing"
        l = len(text)
        self._value.append(text)
        self.offset += l
        self.column += l

    def push(self, text: str):
        "Pushes plain string into output stream without newline processing"
        process_text = self.options.get('output.text')
        self._push(process_text(text, offset=self.offset, line=self.line, column=self.column))

    def push_string(self, value: str):
        "Pushes given string with possible newline formatting into output"
        # If given value contains newlines, we should push content line-by-line and
        # use `push_newline()` to maintain proper line/column state
        first = True

        for line in value.splitlines():
            if not first: self.push_newline(True)
            first = False
            self.push(line)

    def push_newline(self, indent=None):
        "Pushes new line into given output stream"
        base_indent = self.options.get('output.baseIndent')
        newline = self.options.get('output.newline')
        self.push('%s%s' % (newline, base_indent))
        self.line += 1
        self.column = len(base_indent)
        if indent:
            self.push_indent(self.level if indent is True else indent)

    def push_indent(self, size=None):
        "Adds indentation of `size` to current output stream"

        if size is None: size = self.level
        indent = self.options.get('output.indent')
        self.push(indent * max(size, 0))

    def push_field(self, index: int, placeholder: str=''):
        field = self.options.get('output.field')
        # NB: use `_push` instead of `push` to skip text processing
        self._push(field(index, placeholder, offset=self.offset, line=self.line, column=self.column))


def tag_name(name: str, config: Config):
    "Returns given tag name formatted according to given config"
    return str_case(name, config.options.get('output.tagCase'))


def attr_name(name: str, config: Config):
    "Returns given attribute name formatted according to given config"
    return str_case(name, config.options.get('output.attributeCase'))


def attr_quote(attr: AbbreviationAttribute, config: Config, is_open: bool=None):
    "Returns character for quoting value of given attribute"
    if attr.value_type == 'expression':
        return '{' if is_open else '}'

    return '\'' if config.options.get('output.attributeQuotes') == 'single' else '"'


def is_boolean_attribute(attr: AbbreviationAttribute, config: Config):
    "Check if given attribute is boolean"
    if attr.boolean:
        return True

    name = (attr.name or '').lower()
    return name in config.options.get('output.booleanAttributes', [])

def self_close(config: Config):
    "Returns a token for self-closing tag, depending on current options"
    style = config.options.get('output.selfClosingStyle')
    if style == 'xhtml': return ' /'
    if style == 'xml': return '/'
    return ''

def is_inline(node: AbbreviationNode, config: Config):
    if isinstance(node, str):
        return node.lower() in config.options.get('inlineElements', [])

    # inline node is a node either with inline-level name or text-only node
    return is_inline(node.name, config) if node.name else bool(node.value and not node.attributes)

def str_case(text: str, case_type: str):
    if case_type:
        return text.upper() if case_type == 'upper' else text.lower()

    return text

