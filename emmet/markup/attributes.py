from ..config import Config
from ..abbreviation import AbbreviationNode, AbbreviationAttribute

def merge_attributes(node: AbbreviationNode, config: Config):
    """
    Merges attributes in current node: de-duplicates attributes with the same name
    and merges class names
    """
    if not node.attributes:
        return

    attributes = []
    lookup = {}

    for attr in node.attributes:
        if attr.name:
            attr_name = attr.name
            if attr_name in lookup:
                prev = lookup[attr_name]
                if attr_name == 'class':
                    prev.value = merge_value(prev.value, attr.value, ' ')
                else:
                    merge_declarations(prev, attr, config)
            else:
                # Create new attribute instance so we can safely modify it later
                lookup[attr_name] = attr.copy()
                attributes.append(lookup[attr_name])
        else:
            attributes.append(attr)

    node.attributes = attributes

def merge_value(prev_value: list=None, next_value: list=None, glue: str=''):
    "Merges two token lists into single list. Adjacent strings are merged together"
    if prev_value is not None and next_value is not None:
        if prev_value and glue:
            append(prev_value, glue)

        for t in next_value:
            append(prev_value, t)

        return prev_value

    result = prev_value or next_value
    return result and result[:]

def merge_declarations(dest: AbbreviationAttribute, src: AbbreviationAttribute, config: Config):
    "Merges data from `src` attribute into `dest` and returns it"
    dest.name = src.name

    if not config.options.get('output.reverseAttributes'):
        dest.value = src.value

    # Keep high-priority properties
    if not dest.implied: dest.implied = src.implied
    if not dest.boolean: dest.boolean = src.boolean

    if dest.value_type != 'expression':
        dest.value_type = src.value_type

    return dest

def append(tokens: list, value: str):
    if tokens and isinstance(tokens[-1], str) and isinstance(value, str):
        tokens[-1] += value
    else:
        tokens.append(value)
