from ..abbreviation import parse, AbbreviationNode, AbbreviationAttribute
from ..config import Config
from .utils import walk, find_deepest

def resolve_snippets(node: AbbreviationNode, parent_ancestors: list, parent_config: Config):
    """
    Finds matching snippet from `registry` and resolves it into a parsed abbreviation.
    Resolved node is then updated or replaced with matched abbreviation tree.

    A HTML registry basically contains aliases to another Emmet abbreviations,
    e.g. a predefined set of name, attributes and so on, possibly a complex
    abbreviation with multiple elements. So we have to get snippet, parse it
    and recursively resolve it.
    """
    stack = []
    def resolve(child: AbbreviationNode, ancestors: list, config: Config):
        snippet = config.snippets.get(child.name) if child.name else None
        # A snippet in stack means circular reference.
        # It can be either a user error or a perfectly valid snippet like
        # "img": "img[src alt]/", e.g. an element with predefined shape.
        # In any case, simply stop parsing and keep element as is
        if not snippet or snippet in stack:
            return

        abbr = parse(snippet, config)
        stack.append(snippet)
        walk(abbr, resolve, config)
        stack.pop()

        # Move current node contents into new tree
        deepest_node = find_deepest(abbr)[1]
        if isinstance(deepest_node, AbbreviationNode):
            merge(deepest_node, child)
            deepest_node.children = deepest_node.children + child.children

        # Add attributes from current node into every top-level node of parsed abbreviation
        if child.attributes:
            for top_node in abbr.children:
                from_attr = top_node.attributes or []
                to_attr = child.attributes or []
                if config.options.get('output.reverseAttributes'):
                    top_node.attributes = to_attr + from_attr
                else:
                    top_node.attributes = from_attr + to_attr

        # Replace original child with contents of parsed snippet
        parent = ancestors[-1]
        ix = parent.children.index(child)
        parent.children[ix:ix + 1] = abbr.children

    resolve(node, parent_ancestors, parent_config)

def merge(from_node: AbbreviationNode, to_node: AbbreviationNode):
    to_node.name = from_node.name

    if from_node.self_closing:
        to_node.self_closing = True

    if from_node.value is not None:
        to_node.value = from_node.value

    if from_node.repeat:
        to_node.repeat = from_node.repeat
