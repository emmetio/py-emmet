from .walk import WalkState
from .utils import push_tokens
from .template import template
from ...abbreviation import AbbreviationNode
from ...config import Config


class CommentWalkState(WalkState):
    __slots__ = ('enabled', 'trigger', 'before', 'after')

    def __init__(self, config: Config):
        super(CommentWalkState, self).__init__(config)
        options = config.options
        before = options.get('comment.before')
        after = options.get('comment.after')

        self.enabled = options.get('comment.enabled')
        self.trigger = options.get('comment.trigger')
        self.before = template(before) if before else None
        self.after = template(after) if after else None


def comment_node_before(node: AbbreviationNode, state):
    "Adds comment prefix for given node, if required"
    if should_comment(node, state) and state.comment.before:
        output(node, state.comment.before, state)


def comment_node_after(node: AbbreviationNode, state):
    "Adds comment suffix for given node, if required"
    if should_comment(node, state) and state.comment.after:
        output(node, state.comment.after, state)


def should_comment(node: AbbreviationNode, state):
    "Check if given node should be commented"
    comment = state.comment

    if not comment.enabled or not comment.trigger or not node.name or not node.attributes:
        return False

    for attr in node.attributes:
        if attr.name and attr.name in comment.trigger:
            return True

    return False


def output(node: AbbreviationNode, tokens: list, state: WalkState):
    "Pushes given template tokens into output stream"
    attrs = {}
    out = state.out

    # Collect attributes payload
    for attr in node.attributes:
        if attr.name and attr.value:
            attrs[attr.name.upper()] = attr.value

    # Output parsed tokens
    for token in tokens:
        if isinstance(token, str):
            out.push_string(token)
        elif token.name in attrs:
            out.push_string(token.before)
            push_tokens(attrs[token.name], state)
            out.push_string(token.after)
