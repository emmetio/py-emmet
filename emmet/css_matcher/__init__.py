from .scan import scan, TokenType
from ..scanner_utils import is_space
from .parse import split_value

class MatchResult:
    __slots__ = ('type', 'start', 'end', 'body_start', 'body_end')

    def __init__(self, match_type: str, start: int, end: int, body_start: int=None, body_end: int=None):
        self.type = match_type
        self.start = start
        self.end = end
        self.body_start = body_start
        self.body_end = body_end

    def to_json(self):
        return {
            'type': self.type,
            'start': self.start,
            'end': self.end,
            'body_start': self.body_start,
            'body_end': self.body_end
        }

class InwardRange:
    __slots__ = ('start', 'end', 'delimiter', 'first_child')

    def __init__(self, start: int, end: int, delimiter: int):
        self.start = start
        self.end = end
        self.delimiter = delimiter
        self.first_child = None


def match(source: str, pos: int) -> MatchResult:
    pool = []
    stack = []
    result = [None]
    pending_property = []
    pending_property.append(None) # get rid of pyLint rant

    def release_pending():
        if pending_property[0]:
            release_range(pool, pending_property[0])
            pending_property[0] = None

    def scan_callback(token_type: str, start: int, end: int, delimiter: int):
        if token_type == TokenType.Selector:
            release_pending()
            stack.append(alloc_range(pool, start, end, delimiter))
        elif token_type == TokenType.BlockEnd:
            release_pending()
            parent = stack and stack.pop()
            if parent and parent[0] < pos < end:
                result[0] = MatchResult('selector', parent[0], end, parent[2] + 1, start)
                return False
        elif token_type == TokenType.PropertyName:
            release_pending()
            pending_property[0] = alloc_range(pool, start, end, delimiter)
        elif token_type == TokenType.PropertyValue:
            pending = pending_property[0]
            if pending and pending[0] < pos < end:
                result[0] = MatchResult('property', pending[0], delimiter + 1, start, end)
                return False
            release_pending()


    scan(source, scan_callback)
    return result[0]


def balanced_outward(source: str, pos: int) -> list:
    """
    Returns balanced CSS model: a list of all ranges that could possibly match
    given location when moving in outward direction
    """
    pool = []
    stack = []
    result = []
    prop = []
    prop.append(None) # Get rid of pyLint rant

    def scan_callback(token_type: str, start: int, end: int, delimiter: int):
        if token_type == TokenType.Selector:
            stack.append(alloc_range(pool, start, end, delimiter))
        elif token_type == TokenType.BlockEnd:
            left = stack and stack.pop()
            if left and left[0] < pos < end:
                # Matching section found
                inner = inner_range(source, left[2] + 1, start)
                if inner:
                    push(result, inner)
                push(result, (left[0], end))
            if left:
                release_range(pool, left)
            if not stack:
                return False
        elif token_type == TokenType.PropertyName:
            if prop[0]:
                release_range(pool, prop[0])

            prop[0] = alloc_range(pool, start, end, delimiter)
        elif token_type == TokenType.PropertyValue:
            p = prop[0]
            if p and p[0] < pos < max(delimiter, end):
                # Push full token and value range
                push(result, (start, end))
                push(result, (p[0], delimiter + 1 if delimiter != -1 else end))

        if token_type != TokenType.PropertyName and prop[0]:
            release_range(pool, prop[0])
            prop[0] = None

    scan(source, scan_callback)
    return result


def balanced_inward(source: str, pos: int) -> list:
    """
    Returns balanced CSS selectors: a list of all ranges that could possibly match
    given location when moving in inward direction
    """
    # Collecting ranges for inward balancing is a bit trickier: we have to store
    # first child of every matched selector until we find the one that matches given
    # location
    pool = []
    stack = []
    result = []
    pending_property = []
    pending_property.append(None)

    def alloc(start: int, end: int, delimiter: int):
        if pool:
            r = pool.pop()
            r.start = start
            r.end = end
            r.delimiter = delimiter
            return r

        return InwardRange(start, end, delimiter)

    def release(r: InwardRange):
        r.first_child = None
        pool.append(r)

    def release_pending():
        if pending_property[0]:
            release(pending_property[0])
            pending_property[0] = None

    def push_child(start: int, end: int, delimiter: int):
        """
        Pushes given inward range as a first child of current selector only if it’s
        not set yet
        """
        parent = stack and stack[-1]
        if parent and not parent.first_child:
            parent.first_child = alloc(start, end, delimiter)

    def scan_callback(token_type: str, start: int, end: int, delimiter: int):
        if token_type == TokenType.BlockEnd:
            release_pending()

            r = stack and stack.pop()
            if not r:
                # Some sort of lone closing brace, ignore it
                return

            if r.start <= pos <= end:
                # Matching selector found: add it and its inner range into result
                inner = inner_range(source, r.delimiter + 1, start)
                push(result, (r.start, end))
                if inner:
                    push(result, inner)

                while r.first_child:
                    child = r.first_child

                    inner = inner_range(source, child.delimiter + 1, child.end - 1)
                    push(result, (child.start, child.end))
                    if inner:
                        push(result, inner)
                    r = child

                return False
            else:
                parent = stack and stack[-1]
                if parent and not parent.first_child:
                    # No first child in parent node: store current selector
                    r.end = end
                    parent.first_child = r
                else:
                    release(r)
        elif token_type == TokenType.PropertyName:
            release_pending()
            pending_property[0] = alloc(start, end, delimiter)
            push_child(start, end, delimiter)
        elif token_type == TokenType.PropertyValue:
            if pending_property[0]:
                p = pending_property[0]
                if p.start <= pos <= end:
                    # Direct hit into property, no need to look further
                    push(result, (p.start, delimiter + 1))
                    push(result, (start, end))
                    release_pending()
                    return False

                parent = stack and stack[-1]
                if parent and parent.first_child and parent.first_child.start == p.start:
                    # First child is an expected property name, update its range
                    # to include property value
                    parent.first_child.end = delimiter + 1 if delimiter != -1 else end

                release_pending()
        else:
            # Selector start
            stack.append(alloc(start, end, delimiter))
            release_pending()

    scan(source, scan_callback)
    return result


def inner_range(source: str, start: int, end: int):
    """
    Returns inner range for given selector bounds: narrows it to first non-empty
    region. If resulting region is empty, returns `None`
    """
    while start < end and is_space(source[start]):
        start += 1

    while end and end > start and is_space(source[end - 1]):
        end -= 1

    return (start, end) if start != end else None

def alloc_range(pool: list, start: int, end: int, delimiter: int):
    if pool:
        r = pool.pop()
        r[0] = start
        r[1] = end
        r[2] = delimiter
        return r

    return [start, end, delimiter]

def release_range(pool: list, r: list):
    if r:
        pool.append(r)


def push(ranges: list, r: list):
    prev = ranges and ranges[-1]
    if (not prev or prev[0] != r[0] or prev[1] != r[1]) and r[0] != r[1]:
        ranges.append(r)
