from .utils import ScannerOptions, ElementType
from .scan import scan
from .attributes import attributes, AttributeToken

class MatchedTag:
    __slots__ = ('name', 'attributes', 'open', 'close')

    def __init__(self, name: str, attrs: list, open_range: tuple, close_range: tuple=None):
        self.name = name
        "Name of matched tag"

        self.attributes = attrs
        "List of tag attributes"

        self.open = open_range
        "Range of opening tag"

        self.close = close_range
        "Range of closing tag. If absent, tag is self-closing"


class Tag:
    __slots__ = ('name', 'start', 'end')

    def __init__(self, name: str, start: int, end: int):
        self.name = name
        self.start = start
        self.end = end


class InwardTag:
    __slots__ = ('name', 'ranges', 'first_child')

    def __init__(self, name: str, ranges: list, first_child=None):
        self.name = name
        self.ranges = ranges
        self.first_child = first_child


class BalancedTag:
    __slots__ = ('name', 'open', 'close')

    def __init__(self, name: str, open_range: tuple, close_range: tuple=None):
        self.name = name
        "Name of matched tag"

        self.open = open_range
        "Range of opening tag"

        self.close = close_range
        "Range of closing tag. If absent, tag is self-closing"

    def to_json(self):
        json = {
            'name': self.name,
            'open': list(self.open)
        }
        if self.close:
            json['close'] = list(self.close)

        return json


def match(source: str, pos: int, opt: dict=None) -> MatchedTag:
    "Finds matched tag for given `pos` location in XML/HTML `source`"
    # Since we expect large input document, we’ll use pooling technique
    # for storing tag data to reduce memory pressure and improve performance
    pool = []
    stack = []
    options = ScannerOptions(opt)
    result = [None]

    def scan_callback(name: str, elem_type: ElementType, start: int, end: int):
        if elem_type == ElementType.Open and is_self_close(name, options):
            # Found empty element in HTML mode, mark is as self-closing
            elem_type = ElementType.SelfClose

        if elem_type == ElementType.Open:
            # Allocate tag object from pool
            stack.append(alloc_tag(pool, name, start, end))
        elif elem_type == ElementType.SelfClose:
            if start < pos < end:
                # Matched given self-closing tag
                result[0] = MatchedTag(name, get_attributes(source, start, end, name), (start, end))
                return False
        else:
            tag = stack and stack[-1]
            if tag and tag.name == name:
                # Matching closing tag found
                if tag.start < pos < end:
                    result[0] = MatchedTag(name, get_attributes(source, tag.start, tag.end, name), (tag.start, tag.end), (start, end))
                    return False

                if stack:
                    # Release tag object for further re-use
                    release_tag(pool, stack.pop())

    scan(source, scan_callback, options.special)
    return result[0]


def balanced_outward(source: str, pos: int, opt: dict=None) -> list:
    """
    Returns balanced tag model: a list of all XML/HTML tags that could possibly match
    given location when moving in outward direction
    """
    pool = []
    stack = []
    options = ScannerOptions(opt)
    result = []

    def scan_callback(name: str, elem_type: ElementType, start: int, end: int):
        if elem_type == ElementType.Close:
            tag = stack and stack[-1]
            if tag and tag.name == name:
                # XXX check for invalid tag names?
                # Matching closing tag found, check if matched pair is a candidate
                # for outward balancing
                if tag.start < pos < end:
                    result.append(BalancedTag(name, (tag.start, tag.end), (start, end)))
                # Release tag object for further re-use
                release_tag(pool, stack.pop())
        elif elem_type == ElementType.SelfClose or is_self_close(name, options):
            if start < pos < end:
                # Matched self-closed tag
                result.append(BalancedTag(name, (start, end)))
        else:
            stack.append(alloc_tag(pool, name, start, end))

    scan(source, scan_callback, options.special)
    return result


def balanced_inward(source: str, pos: int, opt: dict=None) -> list:
    """
    Returns balanced tag model: a list of all XML/HTML tags that could possibly match
    given location when moving in inward direction
    """
    # Collecting tags for inward balancing is a bit trickier: we have to store
    # first child of every matched tag until we find the one that matches given
    # location
    pool = []
    stack = []
    options = ScannerOptions(opt)
    result = []

    def alloc(name: str, start: int, end: int):
        if pool:
            tag = pool.pop()
            tag.name = name
            tag.ranges.append(start)
            tag.ranges.append(end)
            return tag

        return InwardTag(name, [start, end])

    def release(tag: InwardTag):
        tag.ranges.clear()
        tag.first_child = None
        pool.append(tag)

    def scan_callback(name: str, elem_type: ElementType, start: int, end: int):
        if elem_type == ElementType.Close:
            if not stack:
                # Some sort of lone closing tag, ignore it
                return

            tag = stack[-1]
            if tag.name == name:
                # XXX check for invalid tag names?
                # Matching closing tag found, check if matched pair is a candidate
                # for outward balancing
                if tag.ranges[0] <= pos <= end:
                    result.append(BalancedTag(name, (tag.ranges[0], tag.ranges[1]), (start, end)))

                    while tag.first_child:
                        child = tag.first_child
                        res = BalancedTag(child.name, (child.ranges[0], child.ranges[1]))
                        if len(child.ranges) > 2:
                            res.close = (child.ranges[2], child.ranges[3])
                        result.append(res)
                        release(tag)
                        tag = child

                    return False
                else:
                    stack.pop()
                    parent = stack and stack[-1]
                    if parent and not parent.first_child:
                        # No first child in parent node: store current tag
                        tag.ranges.append(start)
                        tag.ranges.append(end)
                        parent.first_child = tag
                    else:
                        release(tag)
        elif elem_type == ElementType.SelfClose or is_self_close(name, options):
            if start < pos < end:
                # Matched self-closed tag, no need to look further
                result.append(BalancedTag(name, (start, end)))
                return False

            parent = stack and stack[-1]
            if parent and not parent.first_child:
                parent.first_child = alloc(name, start, end)
        else:
            stack.append(alloc(name, start, end))

    scan(source, scan_callback, options.special)
    return result


def alloc_tag(pool: list, name: str, start: int, end: int):
    if pool:
        tag = pool.pop()
        tag.name = name
        tag.start = start
        tag.end = end
        return tag
    return Tag(name, start, end)

def release_tag(pool: list, tag: Tag):
    if tag:
        pool.append(tag)


def get_attributes(source: str, start: int, end: int, name: str=None):
    "Returns parsed attributes from given source"
    attrs = attributes(source[start:end], name)
    for attr in attrs:
        attr.name_start += start
        attr.name_end += start
        if attr.value is not None:
            attr.value_start += start
            attr.value_end += start

    return attrs


def is_self_close(name: str, options: ScannerOptions):
    "Check if given tag is self-close for current parsing context"
    return not options.xml and name in options.empty
