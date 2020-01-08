import re

from .walk import walk, WalkState
from .utils import push_tokens, caret, split_by_lines, is_snippet, should_output_attribute
from ...abbreviation import Abbreviation, AbbreviationNode, AbbreviationAttribute
from ...abbreviation.tokenizer.tokens import Field
from ...config import Config
from ...output_stream import attr_name, attr_quote, is_boolean_attribute


__doc__ =  "Utility methods for working with indent-based markup languages like HAML, Slim, Pug etc."


class IndentWalkState(WalkState):
    __slots__ = ('options')


def indent_format(abbr: Abbreviation, config: Config, options={}):
    state = IndentWalkState(config)
    state.options = options
    walk(abbr, element, state)
    return state.out.value


def element(node: AbbreviationNode, index: int, items: list, state: IndentWalkState, walk_next: callable):
    out = state.out
    options = state.options
    primary, secondary = collect_attributes(node)

    # Pick offset level for current node
    level = 1 if state.parent else 0
    out.level += level

    # Do not indent top-level elements
    if should_format(node, index, items, state):
        out.push_newline(True)

    if node.name and (node.name != 'div' or not primary):
        s = '%s%s%s' % (options.get('beforeName', ''), node.name, options.get('afterName', ''))
        out.push_string(s)

    push_primary_attributes(primary, state)
    push_secondary_attributes(list(filter(should_output_attribute, secondary)), state)

    if node.self_closing and not node.value and not node.children:
        if state.options['selfClose']:
            out.push_string(state.options['selfClose'])
    else:
        push_value(node, state)
        for index, child in enumerate(node.children):
            walk_next(child, index, node.children)

    out.level -= level


def collect_attributes(node: AbbreviationNode):
    """
    From given node, collects all attributes as `primary` (id, class) and
    `secondary` (all the rest) lists. In most indent-based syntaxes, primary attribute
    has special syntax
    """
    primary = []
    secondary = []

    if node.attributes:
        for attr in node.attributes:
            if is_primary_attribute(attr):
                primary.append(attr)
            else:
                secondary.append(attr)

    return (primary, secondary)


def push_primary_attributes(attrs: list, state: WalkState):
    "Outputs given attributes as primary into output stream"
    for attr in attrs:
        if attr.value is not None:
            if attr.name == 'class':
                state.out.push_string('.')
                # All whitespace characters must be replaced with dots in class names
                tokens = [re.sub(r'\s+', '.', t) if isinstance(t, str) else t for t in attr.value]
                push_tokens(tokens, state)
            else:
                # ID attribute
                state.out.push_string('#')
                push_tokens(attr.value, state)


def push_secondary_attributes(attrs: list, state: IndentWalkState):
    if attrs:
        out = state.out
        config = state.config
        options = state.options

        before = options.get('beforeAttribute')
        after = options.get('afterAttribute')
        glue = options.get('glueAttribute')

        if before: out.push_string(before)

        for i, attr in enumerate(attrs):
            out.push_string(attr_name(attr.name or '', config))
            if is_boolean_attribute(attr, config) and not attr.value:
                if not config.options.get('output.compactBoolean') and options.get('booleanValue'):
                    out.push_string('=%s' % options.get('booleanValue'))
            else:
                out.push_string('=%s' % attr_quote(attr, config, True))
                push_tokens(attr.value or caret, state)
                out.push_string(attr_quote(attr, config))

            if i != len(attrs) - 1 and glue:
                out.push_string(glue)

        if after: out.push_string(after)


def push_value(node: AbbreviationNode, state: IndentWalkState):
    # We should either output value or add caret but for leaf nodes only (no children)
    if not node.value and node.children:
        return

    value = node.value or caret
    lines = split_by_lines(value)
    out = state.out
    options = state.options

    if len(lines) == 1:
        if node.name or node.attributes:
            out.push(' ')
        push_tokens(value, state)
    else:
        # We should format multi-line value with terminating `|` character
        # and same line length
        line_lengths = []
        max_length = 0
        before = options.get('beforeTextLine')
        after = options.get('afterTextLine')

        # Calculate lengths of all lines and max line length
        for line in lines:
            l = value_length(line)
            line_lengths.append(l)
            if l > max_length:
                max_length = l

        # Output each line, padded to max length
        out.level += 1
        for i, line in enumerate(lines):
            out.push_newline(True)
            if before:
                out.push(before)
            push_tokens(line, state)
            if after:
                out.push(' ' * (max_length - line_lengths[i]))
                out.push(after)

        out.level -= 1

def is_primary_attribute(attr: AbbreviationAttribute):
    return attr.name == 'class' or attr.name == 'id'


def value_length(tokens: list):
    "Calculates string length from given tokens"
    l = 0

    for token in tokens:
        l += len(token) if isinstance(token, str) else len(token.name)

    return l

def should_format(node: AbbreviationNode, index: int, items: list, state: WalkState):
    # Do not format first top-level element or snippets
    if not state.parent and index == 0:
        return False

    return not is_snippet(node)
