from ..html_matcher import scan, attributes, ScannerOptions, ElementType, AttributeToken
from .utils import push_range, SelectItemModel, token_list

class ContextTag:
    __slots__ = ('name', 'type', 'start', 'end', 'attributes')

    def __init__(self, name: str, elem_type: ElementType, start: int, end: int, attrs: list=None):
        self.name = name
        self.type = elem_type
        self.start = start
        self.end = end
        self.attributes = attrs

    def to_json(self):
        "Returns JSON representation of current object"
        result = {
            'name': self.name,
            'type': self.type,
            'start': self.start,
            'end': self.end
        }

        if self.attributes:
            result['attributes'] = [attr.to_json() for attr in self.attributes]

        return result


def get_open_tag(code: str, pos: int) -> ContextTag:
    """
    Check if there’s open or self-closing tag under given `pos` location in source code.
    If found, returns its name, range in source and parsed attributes
    """
    opt = ScannerOptions()
    tag = []
    tag.append(None)

    # Find open or self-closing tag, closest to given position
    def scan_callback(name: str, elem_type: ElementType, start: int, end: int):
        if start < pos < end:
            tag[0] = ContextTag(name, elem_type, start, end)
            if elem_type in (ElementType.Open, ElementType.SelfClose):
                tag[0].attributes = shift_attribute_ranges(attributes(code[start:end], name), start)

            return False
        if end > pos:
            return False

    scan(code, scan_callback, opt.special)

    return tag[0]


def select_item_html(code: str, pos: int, is_prev=False, options: dict=None) -> SelectItemModel:
    "Returns list of ranges for Select Next/Previous Item action"
    if is_prev:
        return select_previous_item(code, pos, options)
    return select_next_item(code, pos, options)


def select_next_item(code: str, pos: int, options: dict=None) -> SelectItemModel:
    "Returns list of ranges for Select Next Item action"
    opt = ScannerOptions(options)
    result = []
    result.append(None)

    # Find open or self-closing tag, closest to given position
    def scan_callback(name, elem_type, start, end):
        if elem_type in (ElementType.Open, ElementType.SelfClose) and end > pos:
            # Found open or self-closing tag
            result[0] = get_tag_selection_model(code, name, start, end)
            return False
    scan(code, scan_callback, opt.special)
    return result[0]


def select_previous_item(code: str, pos: int, options: dict=None) -> SelectItemModel:
    "Returns list of ranges for Select Previous Item action"
    opt = ScannerOptions(options)
    last = {
        'name': '',
        'type': None,
        'start': -1,
        'end': -1
    }

    # We should find the closest open or self-closing tag left to given `pos`.
    def scan_callback(name: str, elem_type: ElementType, start: int, end: int):
        if start >= pos:
            return False

        if elem_type in (ElementType.Open, ElementType.SelfClose):
            # Found open or self-closing tag
            last['name'] = name
            last['type'] = elem_type
            last['start'] = start
            last['end'] = end

    scan(code, scan_callback, opt.special)

    if last['type'] is not None:
        return get_tag_selection_model(code, last['name'], last['start'], last['end'])


def get_tag_selection_model(code: str, name: str, start: int, end: int) -> SelectItemModel:
    """
    Parses open or self-closing tag in `start:end` range of `code` and returns its
    model for selecting items
    :param code Document source code
    :param name Name of matched tag
    """
    # Add tag name range
    ranges = [(start + 1, start + 1 + len(name))]

    # Parse and add attributes ranges
    tag_src = code[start:end]
    for attr in attributes(tag_src, name):
        if attr.value is not None:
            # Attribute with value
            push_range(ranges, (start + attr.name_start, start + attr.value_end))

            # Add (unquoted) value range
            val = value_range(attr)
            if val[0] != val[1]:
                push_range(ranges, (start + val[0], start + val[1]))

                if attr.name == 'class':
                    # For class names, split value into space-separated tokens
                    for token in token_list(tag_src[val[0]:val[1]], start + val[0]):
                        push_range(ranges, token)
        else:
            # Attribute without value (boolean)
            push_range(ranges, (start + attr.name_start, start + attr.name_end))

    return SelectItemModel(start, end, ranges)


def value_range(attr: AttributeToken) -> tuple:
    "Returns value range of given attribute. Value range is unquoted."
    value = attr.value
    ch = value[0]
    last_ch = value[-1]
    if ch == '"' or ch == '\'':
        return (
            attr.value_start + 1,
            attr.value_end - (1 if last_ch == ch else 0)
        )

    if ch == '{' and last_ch == '}':
        return (
            attr.value_start + 1,
            attr.value_end - 1
        )

    return (attr.value_start, attr.value_end)

def shift_attribute_ranges(attrs: list, offset: int):
    for attr in attrs:
        attr.name_start += offset
        attr.name_end += offset
        if attr.value is not None:
            attr.value_start += offset
            attr.value_end += offset
    return attrs
