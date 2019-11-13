from ..abbreviation import Abbreviation, AbbreviationNode

def walk(node: AbbreviationNode, fn: callable, state=None):
    """
    Walks over each child node of given markup abbreviation AST node (not including
    given one) and invokes `fn` on each node.
    The `fn` callback accepts context node, list of ancestor nodes and optional
    state object
    """
    ancestors = [node]
    def callback(ctx: AbbreviationNode):
        fn(ctx, ancestors, state)
        ancestors.append(ctx)
        for child in ctx.children:
            callback(child)
        ancestors.pop()

    for child in node.children:
        callback(child)

def find_deepest(node: AbbreviationNode):
    "Finds node which is the deepest for in current node or node itself."
    parent = None
    while node.children:
        parent = node
        node = node.children[-1]

    return (parent, node)
