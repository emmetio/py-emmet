from ...abbreviation import Abbreviation, AbbreviationNode
from ...config import Config
from ...output_stream import OutputStream


class WalkState:
    __slots__ = ('current', 'parent', 'ancestors', 'config', 'out', 'field')

    def __init__(self, config: Config):
        self.current = None
        "Context node"

        self.parent = None
        "Immediate parent of currently iterated method"

        self.ancestors = []
        "List of all ancestors of context node"

        self.config = config
        "Current output config"

        self.out = OutputStream(config.options)
        "Output stream"

        self.field = 1
        "Current field index, used to output field marks for editor tabstops"

def walk(abbr: Abbreviation, visitor: callable, state: WalkState):
    def callback(ctx: AbbreviationNode, index: int, items: list):
        parent = state.parent
        current = state.current

        state.parent = current
        state.current = ctx
        visitor(ctx, index, items, state, walk_next)
        state.current = current
        state.parent = parent

    def walk_next(node, index, items):
        state.ancestors.append(state.current)
        callback(node, index, items)
        state.ancestors.pop()

    for index, child in enumerate(abbr.children):
        callback(child, index, abbr.children)
