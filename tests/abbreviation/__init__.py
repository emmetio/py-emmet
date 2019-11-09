import sys

sys.path.append('../../')

from emmet.abbreviation.convert import Abbreviation, AbbreviationNode, AbbreviationAttribute
from emmet.abbreviation.tokenizer import tokens

def stringify_node(abbr: Abbreviation):
    return ''.join(map(elem, abbr.children))

def elem(node: AbbreviationNode):
    name = node.name or '?'
    attributes = ''.join(map(lambda attr: ' %s' % attribute(attr), node.attributes or []))
    value = stringify_value(node.value) if node.value else ''
    repeat = '*%d@%d' % (node.repeat.count, node.repeat.value) if node.repeat else ''

    if node.self_closing and not node.value and not node.children:
        return '<{name}{repeat}{attributes} />'.format_map(locals())

    children = ''.join(map(elem, node.children))
    return '<{name}{repeat}{attributes}>{value}{children}</{name}>'.format_map(locals())

def attribute(attr: AbbreviationAttribute):
    name = attr.name or '?'
    value = '"%s"' % stringify_value(attr.value) if attr.value else None
    return '%s=%s' % (name, value) if value is not None else name

def stringify_value(items: list):
    return ''.join(map(lambda tok: field(tok) if isinstance(tok, tokens.Field) else tok, items))

def field(fld: tokens.Field):
    if fld.name:
        return '${%d:%s}' % (fld.index, fld.name)
    else:
        return '${%d}' % fld.index


## Stringify abbreviation AST
