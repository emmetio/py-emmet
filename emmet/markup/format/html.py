import re
from .walk import walk, WalkState
from .utils import caret, is_inline_element, is_snippet, push_tokens, should_output_attribute
from .comment import comment_node_before, comment_node_after, CommentWalkState
from ...abbreviation import Abbreviation, AbbreviationNode, AbbreviationAttribute
from ...abbreviation.tokenizer.tokens import Field
from ...config import Config
from ...output_stream import tag_name, self_close, attr_name, is_boolean_attribute, attr_quote, is_inline
from ...list_utils import some, find_index, get_item

re_html_tag = re.compile(r'<([\w\-:]+)[\s>]')

class HTMLWalkState(WalkState):
    __slots__ = ('comment')


def html(abbr: Abbreviation, config: Config):
    state = HTMLWalkState(config)
    state.comment = CommentWalkState(config)
    walk(abbr, element, state)
    return state.out.value


def element(node: AbbreviationNode, index: int, items: list, state: HTMLWalkState, walk_next: callable):
    out = state.out
    config = state.config
    fmt = should_format(node, index, items, state)

    # Pick offset level for current node
    level = get_indent(state)
    out.level += level

    if fmt: out.push_newline(True)

    if node.name:
        name = tag_name(node.name, config)
        comment_node_before(node, state)
        out.push_string('<%s' % name)

        if node.attributes:
            for attr in node.attributes:
                if should_output_attribute(attr):
                    push_attribute(attr, state)

        if node.self_closing and not node.children and not node.value:
            out.push_string('%s>' % self_close(config))
        else:
            out.push_string('>')

            if not push_snippet(node, state, walk_next):
                if node.value:
                    inner_format = some(has_newline, node.value) or starts_with_block_tag(node.value, config)
                    if inner_format:
                        out.level += 1
                        out.push_newline(out.level)
                    push_tokens(node.value, state)
                    if inner_format:
                        out.level -= 1
                        out.push_newline(out.level)

                _next(node.children, walk_next)

                if not node.value and not node.children:
                    inner_format = config.options.get('output.formatLeafNode') or \
                        node.name in config.options.get('output.formatForce', [])
                    if inner_format:
                        out.level += 1
                        out.push_newline(out.level)
                    push_tokens(caret, state)
                    if inner_format:
                        out.level -= 1
                        out.push_newline(out.level)

            out.push_string('</%s>' % name)
            comment_node_after(node, state)
    elif not push_snippet(node, state, walk_next) and node.value:
        # A text-only node (snippet)
        push_tokens(node.value, state)
        _next(node.children, walk_next)

    if fmt and index == len(items) - 1 and state.parent:
        offset = 0 if is_snippet(state.parent) else 1
        out.push_newline(out.level - offset)

    out.level -= level


def push_attribute(attr: AbbreviationAttribute, state: WalkState):
    "Outputs given attribute’s content into output stream"
    out = state.out
    config = state.config

    if attr.name:
        name = attr_name(attr.name, config)
        l_quote = attr_quote(attr, config, True)
        r_quote = attr_quote(attr, config, False)
        value = attr.value

        if is_boolean_attribute(attr, config) and not value:
            # If attribute value is omitted and it’s a boolean value, check for
            # `compactBoolean` option: if it’s disabled, set value to attribute name
            # (XML style)
            if not config.options.get('output.compactBoolean'):
                value = [name]
        elif not value:
            value = caret

        out.push_string(' %s' % name)
        if value:
            out.push_string('=%s' % l_quote)
            push_tokens(value, state)
            out.push_string(r_quote)
        elif config.options.get('output.selfClosingStyle') != 'html':
            out.push_string('=%s%s' % (l_quote, r_quote))


def push_snippet(node: AbbreviationNode, state: WalkState, walk_next: callable):
    if node.value and node.children:
        # We have a value and child nodes. In case if value contains fields,
        # we should output children as a content of first field
        field_ix = find_index(is_field, node.value)
        if field_ix != -1:
            push_tokens(node.value[0:field_ix], state)
            line = state.out.line
            pos = field_ix + 1

            _next(node.children, walk_next)

            # If there was a line change, trim leading whitespace for better result
            if state.out.line != line and isinstance(get_item(node.value, pos), str):
                state.out.push_string(get_item(node.value, pos).lstrip())
                pos += 1

            push_tokens(node.value[pos:], state)
            return True

    return False


def should_format(node: AbbreviationNode, index: int, items: list, state: WalkState):
    "Check if given node should be formatted in its parent context"
    parent = state.parent
    config = state.config

    if not config.options.get('output.format'):
        return False

    if index == 0 and not parent:
        # Do not format very first node
        return False

    # Do not format single child of snippet
    if parent and is_snippet(parent) and len(items) == 1:
        return False

    if is_snippet(node):
        # Adjacent text-only/snippet nodes
        fmt = is_snippet(get_item(items, index - 1)) or is_snippet(get_item(items, index + 1)) or \
            some(has_newline, node.value) or \
            (some(is_field, node.value) and node.children)

        if fmt:
            return True

    if is_inline(node, config):
        # Check if inline node is the next sibling of block-level node
        if index == 0:
            # First node in parent: format if it’s followed by a block-level element
            for item in items:
                if not is_inline(item, config):
                    return True
        elif not is_inline(items[index - 1], config):
            # Node is right after block-level element
            return True

        if config.options.get('output.inlineBreak'):
            # check for adjacent inline elements before and after current element
            adjacent_inline = 1
            before = index - 1
            after = index + 1

            while before >= 0 and is_inline_element(items[before], config):
                adjacent_inline += 1
                before -= 1

            while after < len(items) and is_inline_element(items[after], config):
                adjacent_inline += 1
                after += 1

            if adjacent_inline >= config.options.get('output.inlineBreak'):
                return True

        # Edge case: inline node contains node that should receive formatting
        for i, child in enumerate(node.children):
            if should_format(child, i, node.children, state):
                return True

        return False

    return True


def get_indent(state: WalkState):
    "Returns indentation offset for given node"
    parent = state.parent

    if not parent or is_snippet(parent) or (parent.name and parent.name in state.config.options.get('output.formatSkip')):
        return 0

    return 1


def has_newline(value):
    "Check if given node value contains newlines"
    return '\r' in value or '\n' in value if isinstance(value, str) else False


def starts_with_block_tag(value: list, config: Config) -> bool:
    "Check if given node value starts with block-level tag"
    if value and isinstance(value[0], str):
        m = re_html_tag.match(value[0])

        if m and m.group(1).lower() not in config.options.get('inlineElements'):
            return True

    return False

def _next(items: list, walk_next: callable):
    for i, item in enumerate(items):
        walk_next(item, i, items)


def is_field(item):
    return isinstance(item, Field)
