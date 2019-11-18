from ..css_matcher import scan, split_value, TokenType
from .utils import push_range, SelectItemModel

class CSSSection:
    __slots__ = ('start', 'end', 'body_start', 'body_end', 'properties')

    def __init__(self, start: int, end: int, body_start: int, body_end: int, properties: list=None):
        self.start = start
        self.end = end
        self.body_start = body_start
        self.body_end = body_end
        self.properties = properties

    def to_json(self):
        result = {
            'start': self.start,
            'end': self.end,
            'body_start': self.body_start,
            'body_end': self.body_end
        }

        if self.properties:
            result['properties'] = [prop.to_json() for prop in self.properties]

        return result


class CSSProperty:
    __slots__ = ('name', 'value', 'value_tokens', 'before', 'after')

    def __init__(self, code: str, name: list, before: int, start: int, end: int, delimiter: int, offset=0):
        self.name = (offset + name[0], offset + name[1])
        self.value = (offset + start, offset + end)
        self.value_tokens = split_value(code[start:end], offset + start)
        self.before = before
        self.after = offset + delimiter + 1

    def to_json(self):
        return {
            'name': self.name,
            'value': self.value,
            'value_tokens': self.value_tokens,
            'before': self.before,
            'after': self.after
        }


class ParseState:
    __slots__ = ('type', 'start', 'end', 'value_start', 'value_end', 'value_delimiter')

    def __init__(self):
        self.type = None
        self.start = -1
        self.end = -1
        self.value_start = -1
        self.value_end = -1
        self.value_delimiter = -1


def get_css_section(code: str, pos: int, properties=False) -> CSSSection:
    """
    Returns context CSS section for given location in source code
    :param properties Parse inner properties
    """
    stack = []
    pool = []
    result = []
    result.append(None) # Skip pylint warnings

    def scan_callback(token_type: str, start: int, end: int, delimiter: int):
        if start > pos and not stack:
            return False

        if token_type == TokenType.Selector:
            stack.append(alloc_range(pool, start, end, delimiter))
        elif token_type == TokenType.BlockEnd:
            sel = stack and stack.pop()
            if sel and sel[0] <= pos <= end:
                result[0] = CSSSection(sel[0], end, sel[2] + 1, start)
                return False
            release_range(pool, sel)


    scan(code, scan_callback)
    section = result[0]

    if section and properties:
        section.properties = parse_properties(code, section.body_start, section.body_end)

    return section


def select_item_css(code: str, pos: int, is_prev=False) -> SelectItemModel:
    "Returns list of ranges for Select Next/Previous CSS Item  action"
    if is_prev:
        return select_previous_item(code, pos)
    return select_next_item(code, pos)


def select_next_item(code: str, pos: int) -> SelectItemModel:
    "Returns regions for selecting next item in CSS"
    result = []
    result.append(None)
    pending_property = []
    pending_property.append(None)

    def scan_callback(token_type: str, start: int, end: int, delimiter: int):
        if start < pos:
            return

        if token_type == TokenType.Selector:
            result[0] = SelectItemModel(start, end, [(start, end)])
            return False
        elif token_type == TokenType.PropertyName:
            pending_property[0] = (start, end, delimiter)
        elif token_type == TokenType.PropertyValue:
            section = SelectItemModel(start, delimiter + 1 if delimiter != -1 else end, [])
            result[0] = section

            if pending_property[0]:
                # Full property range
                prop = pending_property[0]
                section.start = prop[0]
                push_range(section.ranges, (prop[0], section.end))


            # Full value range
            push_range(section.ranges, (start, end))

            # Value fragments
            for r in split_value(code[start:end]):
                push_range(section.ranges, (r[0] + start, r[1] + start))

            return False
        elif pending_property[0]:
            prop = pending_property[0]
            result[0] = SelectItemModel(prop[0], prop[1], [(prop[0], prop[1])])
            return False

    scan(code, scan_callback)
    return result[0]


def select_previous_item(code: str, pos: int) -> SelectItemModel:
    "Returns regions for selecting previous item in CSS"
    state = ParseState()

    def scan_callback(token_type, start, end, delimiter):
        # Accumulate context until we reach given position
        if start >= pos and token_type != TokenType.PropertyValue:
            return False

        if token_type in (TokenType.Selector, TokenType.PropertyName):
            state.start = start
            state.end = end
            state.type = token_type
            state.value_start = state.value_end = state.value_delimiter = -1
        elif token_type == TokenType.PropertyValue:
            state.value_start = start
            state.value_end = end
            state.value_delimiter = delimiter

    scan(code, scan_callback)

    if state.type == TokenType.Selector:
        return SelectItemModel(state.start, state.end, [(state.start, state.end)])

    if state.type == TokenType.PropertyName:
        result = SelectItemModel(state.start, state.end, [])

        if state.value_start != -1:
            result.end = state.value_delimiter + 1 if state.value_delimiter != -1 else state.value_end
            # Full property range
            push_range(result.ranges, (state.start, result.end))

            # Full value range
            push_range(result.ranges, (state.value_start, state.value_end))

            # Value fragments
            for r in split_value(code[state.value_start:state.value_end]):
                push_range(result.ranges, (r[0] + state.value_start, r[1] + state.value_start))
        else:
            push_range(result.ranges, (state.start, state.end))

        return result


class ParsePropertiesState:
    __slots__ = ('pending_name', 'nested', 'before')

    def __init__(self, before: int):
        self.pending_name = None
        self.nested = 0
        self.before= before

def parse_properties(code: str, parse_from=0, parse_to=None) -> list:
    """
    Parses properties in `from:to` fragment of `code`. Note that `from:to` must
    point to CSS section content, e.g. *inside* `{` and `}` (or top-level code context),
    all properties found in nested sections will be ignored
    """
    if parse_to is None:
        parse_to = len(code)

    fragment = code[parse_from:parse_to]
    result = []
    pool = []
    state = ParsePropertiesState(parse_from)

    def scan_callback(token_type, start: int, end: int, delimiter: int):
        if token_type == TokenType.Selector:
            state.nested += 1
        elif token_type == TokenType.BlockEnd:
            state.nested -= 1
            state.before = parse_from + end
        elif not state.nested:
            if token_type == TokenType.PropertyName:
                if state.pending_name:
                    # Create property with empty value
                    value_pos = state.pending_name[2]
                    result.append(
                        CSSProperty(fragment, state.pending_name, state.before,
                                    value_pos, value_pos, value_pos,
                                    parse_from))
                    release_range(pool, state.pending_name)
                    state.before = parse_from + start
                state.pending_name = alloc_range(pool, start, end, delimiter)
            elif token_type == TokenType.PropertyValue:
                if state.pending_name:
                    result.append(
                        CSSProperty(fragment, state.pending_name, state.before,
                                    start, end, delimiter, parse_from))
                    release_range(pool, state.pending_name)
                    state.pending_name = None
                state.before = parse_from + delimiter + 1

    scan(fragment, scan_callback)
    return result


def alloc_range(pool: list, start: int, end: int, delimiter: int) -> list:
    "Allocates new token range from pool"
    if pool:
        rng = pool.pop()
        rng[0] = start
        rng[1] = end
        rng[2] = delimiter
        return rng

    return [start, end, delimiter]


def release_range(pool: list, rng: list):
    "Releases given token range and pushes it back into the pool"
    if rng:
        pool.append(rng)
