import sys

sys.path.append('../../')
from emmet.abbreviation.tokenizer import tokens
from emmet.abbreviation.parser import TokenAttribute, TokenElement, TokenGroup

operator_map = {
    'id': '#',
    'class': '.',
    'equal': '=',
    'child': '>',
    'climb': '^',
    'sibling': '+',
    'close': '/'
}

def Repeater(token: tokens.Repeater):
    return '*%s' % ('' if token.implicit else token.count,)

def RepeaterNumber(token: tokens.RepeaterNumber):
    return '$' * token.size

def RepeaterPlaceholder(node):
    return '$#'

def Field(node: tokens.Field):
    name = node.name
    index = str(node.index) if node.index is not None else ''
    sep = ':' if index and name else ''
    return '${%s%s%s}' % (index, sep, name)

def Operator(node: tokens.Operator):
    global operator_map
    return operator_map[node.operator]

def Bracket(node: tokens.Bracket):
    if node.context == 'attribute':
        return '[' if node.open else ']'

    if node.context == 'expression':
        return '{' if node.open else '}'

    if node.context == 'group':
        return '(' if node.open else ')'

    return '?'

def Quote(node: tokens.Quote):
    return '\'' if node.single else '"'

def Literal(node: tokens.Literal):
    return node.value

def WhiteSpace(node):
    return ' '

def statement(node: TokenGroup):
    if isinstance(node, TokenGroup):
        r = string(node.repeat) if node.repeat else ''
        return '(%s)%s' % (content(node), r)

    return element(node)

def element(node: TokenElement):
    name = token_list(node.name) if node.name else '?'
    repeat = string(node.repeat) if node.repeat else ''
    attributes = ' '.join(map(attribute, node.attributes)) if node.attributes else ''
    if attributes: attributes = ' ' + attributes
    if node.self_close and not node.elements:
        return '<{name}{repeat}{attributes} />'.format_map(locals())

    value = token_list(node.value) + content(node)
    return '<{name}{repeat}{attributes}>{value}</{name}>'.format_map(locals())

def attribute(attr: TokenAttribute):
    name = token_list(attr.name) or '?'
    if attr.value:
        return '%s=%s' % (name, token_list(attr.value))
    return name

def token_list(tokens: list):
    return ''.join(map(string, tokens)) if tokens else ''

def string(token: tokens.Token):
    visitor = globals().get(token.type)
    if callable(visitor):
        return visitor(token)

    raise Exception('Unknown token "%s"' % token.type)

def content(node: tokens.Token):
    return ''.join(map(statement, node.elements))

def stringify(abbr: TokenGroup):
    return content(abbr)
