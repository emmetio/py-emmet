from ..abbreviation import AbbreviationNode
from ..config import Config
from ..output_stream import is_inline

ELEMENT_MAP = {
    'p': 'span',
    'ul': 'li',
    'ol': 'li',
    'table': 'tr',
    'tr': 'td',
    'tbody': 'tr',
    'thead': 'tr',
    'tfoot': 'tr',
    'colgroup': 'col',
    'select': 'option',
    'optgroup': 'option',
    'audio': 'source',
    'video': 'source',
    'object': 'param',
    'map': 'area'
}

def implicit_tag(node: AbbreviationNode, ancestors: list, config: Config):
    if not node.name and node.attributes:
        resolve_implicit_tag(node, ancestors, config)


def resolve_implicit_tag(node: AbbreviationNode, ancestors: list, config: Config):
    global ELEMENT_MAP
    parent = get_parent_element(ancestors)
    context_name = config.get('context').get('name', '') if config.get('context') else ''
    parent_name = lowercase(parent.name if parent else context_name)
    node.name = ELEMENT_MAP.get(parent_name, 'span' if is_inline(parent_name, config) else 'div')


def lowercase(text: str=None):
    return (text or '').lower()

def get_parent_element(ancestors: list):
    "Returns closest element node from given ancestors list"
    i = len(ancestors) - 1
    while i >= 0:
        elem = ancestors[i]
        if isinstance(elem, AbbreviationNode):
            return elem
        i -= 1
