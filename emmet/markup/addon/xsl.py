from ...abbreviation import AbbreviationNode, AbbreviationAttribute

def xsl(node: AbbreviationNode):
    "XSL transformer: removes `select` attributes from certain nodes that contain children"
    if matches_name(node.name) and node.attributes and (node.children or node.value):
        node.attributes = filter(is_allowed, node.attributes)

def is_allowed(attr: AbbreviationAttribute):
    return attr.name != 'select'

def matches_name(name: str):
    return name == 'xsl:variable' or name == 'xsl:with-param'

