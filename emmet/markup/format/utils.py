from .walk import WalkState
from ...abbreviation import AbbreviationNode, AbbreviationAttribute
from ...abbreviation.tokenizer.tokens import Field
from ...config import Config
from ...output_stream import OutputStream, is_inline

caret = [Field('', 0)]
"Default caret token"

def is_snippet(node: AbbreviationNode):
    "Check if given node is a snippet: a node without name and attributes"
    return node and not node.name and not node.attributes if node else False

def is_inline_element(node: AbbreviationNode, config: Config):
    """
    Check if given node is inline-level element, e.g. element with explicitly
    defined node name
    """
    return is_inline(node, config) if node else False

def push_tokens(tokens: list, state: WalkState):
    out = state.out
    largest_index = -1

    for t in tokens:
        if isinstance(t, str):
            out.push_string(t)
        else:
            out.push_field(state.field + t.index, t.name)
            if t.index > largest_index:
                largest_index = t.index

    if largest_index != -1:
        state.field += largest_index + 1


def split_by_lines(tokens: list):
    """
    Splits given value token by lines: returns array where each entry is a token list
    for a single line
    """
    result = []
    line = []

    for t in tokens:
        if isinstance(t, str):
            lines = t.splitlines()
            line.append(lines.pop(0) if lines else '')
            while lines:
                result.append(line)
                line = [lines.pop(0) or '']
        else:
            line.append(t)

    if line:
        result.append(line)

    return result

def should_output_attribute(attr: AbbreviationAttribute):
    # In case if attribute is implied, check if it has a defined value:
    # either non-empty value or quoted empty value
    return not attr.implied or attr.value_type != 'raw' or attr.value
