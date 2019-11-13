from ...abbreviation import AbbreviationNode, AbbreviationAttribute

def jsx(node: AbbreviationNode):
    """
    JSX transformer: replaces `class` and `for` attributes with `className` and
    `htmlFor` attributes respectively
    """
    if node.attributes:
        for attr in node.attributes:
            rename(attr)

def rename(attr: AbbreviationAttribute):
    if attr.name == 'class':
        attr.name = 'className'
    elif attr.name == 'for':
        attr.name = 'htmlFor'
