from ..abbreviation import parse, Abbreviation, AbbreviationNode, AbbreviationAttribute
from ..config import Config
from .utils import walk, find_deepest

def resolve_snippets(abbr: Abbreviation, config: Config):
    """
    Finds matching snippet from `registry` and resolves it into a parsed abbreviation.
    Resolved node is then updated or replaced with matched abbreviation tree.

    A HTML registry basically contains aliases to another Emmet abbreviations,
    e.g. a predefined set of name, attributes and so on, possibly a complex
    abbreviation with multiple elements. So we have to get snippet, parse it
    and recursively resolve it.
    """
    stack = []
    is_reversed = config.options.get('output.reverseAttributes', False)

    def resolve(child: AbbreviationNode):
        snippet = config.snippets.get(child.name) if child.name else None
        # A snippet in stack means circular reference.
        # It can be either a user error or a perfectly valid snippet like
        # "img": "img[src alt]/", e.g. an element with predefined shape.
        # In any case, simply stop parsing and keep element as is
        if not snippet or snippet in stack:
            return None

        snippet_abbr = parse(snippet, config)
        stack.append(snippet)
        walk_resolve(snippet_abbr, resolve, config)
        stack.pop()

        # Add attributes from current node into every top-level node of parsed abbreviation
        for top_node in snippet_abbr.children:
            if child.attributes:
                from_attr = top_node.attributes or []
                to_attr = child.attributes or []
                if is_reversed:
                    top_node.attributes = to_attr + from_attr
                else:
                    top_node.attributes = from_attr + to_attr
            merge(child, top_node)

        return snippet_abbr

    walk_resolve(abbr, resolve, config)
    return abbr


def walk_resolve(node: AbbreviationNode, resolve: callable, config: Config) -> list:
    children = []

    for child in node.children:
        resolved = resolve(child)

        if resolved:
            children += resolved.children

            deepest = find_deepest(resolved)
            if isinstance(deepest[1], AbbreviationNode):
                deepest[1].children += walk_resolve(child, resolve, config)
        else:
            children.append(child)
            child.children = walk_resolve(child, resolve, config)

    node.children = children
    return children


def merge(from_node: AbbreviationNode, to_node: AbbreviationNode):
    if from_node.self_closing:
        to_node.self_closing = True

    if from_node.value is not None:
        to_node.value = from_node.value

    if from_node.repeat:
        to_node.repeat = from_node.repeat
