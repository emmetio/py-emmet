from ...abbreviation import AbbreviationNode, AbbreviationAttribute
from ..utils import find

def label(node: AbbreviationNode):
    if node.name == 'label':
        input = find(node, lambda n: n.name == 'input' or n.name == 'textarea')
        if input:
            # Remove empty `for` attribute
            if node.attributes:
                node.attributes = [attr for attr in node.attributes if not (attr.name == 'for' and is_empty_attribute(attr))]

            # Remove empty `id` attribute
            if input.attributes:
                input.attributes = [attr for attr in input.attributes if not (attr.name == 'id' and is_empty_attribute(attr))]


def is_empty_attribute(attr: AbbreviationAttribute):
    if not attr.value:
        return True


    if len(attr.value) == 1:
        token = attr.value[0]
        if token and not isinstance(token, str) and not token.name:
            # Attribute contains field
            return True

    return False


