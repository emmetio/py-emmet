from ..scanner_utils import is_space


class SelectItemModel:
    __slots__ = ('start', 'end', 'ranges')

    def __init__(self, start: int, end: int, ranges: list=None):
        self.start = start
        self.end = end
        self.ranges = ranges

    def to_json(self):
        return {
            'start': self.start,
            'end': self.end,
            'ranges': self.ranges
        }


def push_range(ranges: list, rng: list):
    prev = ranges and ranges[-1]
    if rng and rng[0] != rng[1] and (not prev or prev[0] != rng[0] or prev[1] != rng[1]):
        ranges.append(rng)


def token_list(value: str, offset=0):
    "Returns ranges of tokens in given value. Tokens are space-separated words."
    ranges = []
    l = len(value)
    pos = 0
    start = 0
    end = 0

    while pos < l:
        end = pos
        ch = value[pos]
        pos += 1
        if is_space(ch):
            if start != end:
                ranges.append((offset + start, offset + end))

            while pos < l and is_space(value[pos]):
                pos += 1

            start = pos

    if start != pos:
        ranges.append((offset + start, offset + pos))

    return ranges
