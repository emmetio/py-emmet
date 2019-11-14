import re
from ...abbreviation import AbbreviationNode
from ...config import Config
from ...list_utils import get_item

class BEMData:
    __slots__ = ('class_names', 'block')

    def __init__(self, class_names: list, block: str=None):
        self.class_names = class_names
        self.block = block

re_element = re.compile(r'^(-+)([a-z0-9]+[a-z0-9-]*)', re.I)
re_modifier = re.compile(r'^(_+)([a-z0-9]+[a-z0-9-_]*)', re.I)

def block_candidates1(class_name: str):
    return re.match(r'^[a-z]-', class_name, re.I)

def block_candidates2(class_name: str):
    return re.match(r'^[a-z]', class_name, re.I)

def bem(node: AbbreviationNode, ancestors: list, config: Config):
    lookup = {}
    expand_class_names(node, lookup)
    expand_short_notation(node, ancestors, config, lookup)

def expand_class_names(node: AbbreviationNode, lookup: dict):
    """
    Expands existing class names in BEM notation in given `node`.
    For example, if node contains `b__el_mod` class name, this method ensures
    that element contains `b__el` class as well
    """
    data = get_bem_data(node, lookup)
    class_names = []

    for cl in data.class_names:
        # remove all modifiers and element prefixes from class name to get a base element name
        ix = cl.find('_')
        if ix > 0 and cl[0] != '-':
            class_names.append(cl[0:ix])
            class_names.append(cl[ix:])
        else:
            class_names.append(cl)

    if class_names:
        data.class_names = unique(class_names)
        data.block = find_block_name(data.class_names)
        update_class(node, ' '.join(data.class_names))


def expand_short_notation(node: AbbreviationNode, ancestors: list, config: Config, lookup: dict):
    data = get_bem_data(node, lookup)
    class_names = []
    options = config.options
    path = ancestors[1:] + [node]

    for cl in data.class_names:
        prefix = ''
        original_class = cl

        # parse element definition (could be only one)
        m = re_element.match(cl)
        if m:
            prefix = ''.join((get_block_name(path, len(m.group(1)), config.context) + options.get('bem.element') + m.group(2)))
            class_names.append(prefix)
            cl = cl[len(m.group(0)):]

        # parse modifiers definitions
        m = re_modifier.match(cl)
        if m:
            if not prefix:
                prefix = get_block_name(path, len(m.group(1)))
                class_names.append(prefix)

            class_names.append(''.join( (prefix, options.get('bem.modifier'), m.group(2)) ))
            cl = cl[len(m.group(0)):]

        if cl == original_class:
            # class name wasn’t modified: it’s not a BEM-specific class,
            # add it as-is into output
            class_names.append(original_class)

    arr_class_names = unique(class_names)
    if arr_class_names:
        update_class(node, ' '.join(arr_class_names))


def get_bem_data(node: AbbreviationNode, lookup: dict):
    "Returns BEM data from given abbreviation node"
    if node not in lookup:
        class_value = ''
        if node.attributes:
            for attr in node.attributes:
                if attr.name == 'class' and attr.value:
                    class_value = stringify_value(attr.value)
                    break

        lookup[node] = parse_bem(class_value)

    return lookup[node]


def get_bem_data_from_context(context: dict):
    # XXX dict is unhashable, can’t use lookup. Just re-parse on each request
    attrs = context.get('attributes', {})
    return parse_bem(attrs.get('class', ''))


def parse_bem(class_value=''):
    "Parses BEM data from given class name"
    class_names = class_value.split() if class_value else []
    return BEMData(class_names, find_block_name(class_names))


def get_block_name(ancestors: list, depth=0, context: dict=None, lookup={}):
    """
    Returns block name for given `node` by `prefix`, which tells the depth of
    of parent node lookup
    """
    max_parent_ix = 0
    parent_ix = max(len(ancestors) - depth, max_parent_ix)
    while max_parent_ix <= parent_ix:
        parent = get_item(ancestors, parent_ix)
        if parent:
            data = get_bem_data(parent, lookup)
            if data.block:
                return data.block
        parent_ix -= 1

    if context is not None:
        data = get_bem_data_from_context(context)
        if data.block:
            return data.block

    return ''


def find_block_name(class_names: list):
    return find(class_names, block_candidates1) or find(class_names, block_candidates2) or None


def find(class_names: list, fn: callable):
    for cl in class_names:
        if re_element.match(cl) or re_modifier.match(cl):
            break

        if fn(cl): return cl


def update_class(node: AbbreviationNode, value: str):
    for attr in node.attributes:
        if attr.name == 'class':
            attr.value = [value]
            break


def stringify_value(value: list):
    return ''.join([t if isinstance(t, str) else t.name for t in value])

def unique(items: list):
    seen = set()
    return [x for x in items if x not in seen and not seen.add(x)]
