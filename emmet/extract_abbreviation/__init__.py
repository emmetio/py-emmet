import re
from .reader import BackwardScanner
from .is_html import is_html as is_at_html_tag, is_quote
from .brackets import Brackets, BRACE_PAIRS
from ..scanner_utils import is_alpha, is_number

class ExtractedAbbreviation:
    __slots__ = ('abbreviation', 'location', 'start', 'end')

    def __init__(self, abbreviation: str, location: int, start: int, end: int):
        self.abbreviation = abbreviation
        "Extracted abbreviation"

        self.location = location
        "Location of abbreviation in input string"

        self.start = start
        "Start location of matched abbreviation, including prefix"

        self.end = end
        "End location of extracted abbreviation"

    def __eq__(self, other):
        if isinstance(other, ExtractedAbbreviation):
            return self.abbreviation == other.abbreviation and \
                self.location == other.location and \
                self.start == other.start and \
                self.end == other.end

        raise NotImplementedError

    def __repr__(self):
        return repr({
            'abbreviation': self.abbreviation,
            'location': self.location,
            'start': self.start,
            'end': self.end,
        })

SPECIAL_CHARS = '#.*:$-_!@%^+>/'

def extract_abbreviation(line: str, pos: int=None, options={}) -> ExtractedAbbreviation:
    """
    Extracts abbreviation from given line of source code.
    Options:

    Parser options:

    lookAhead: bool
    Allow parser to look ahead of `pos` index for searching of missing
    abbreviation parts. Most editors automatically inserts closing braces for
    `[`, `{` and `(`, which will most likely be right after current caret position.
    So in order to properly expand abbreviation, user must explicitly move
    caret right after auto-inserted braces. With this option enabled, parser
    will search for closing braces right after `pos`. Default is `true`

    type: 'markup' | 'stylesheet'
    Type of context syntax of expanded abbreviation.
    In 'stylesheet' syntax, brackets `[]` and `{}` are not supported thus
    not extracted.

    prefix: str
    A string that should precede abbreviation in order to make it successfully
    extracted. If given, the abbreviation will be extracted from the nearest
    `prefix` occurrence.
    """
    if pos is None:
        pos = len(line)
    opt = create_options(options)
    # make sure `pos` is within line range
    pos = min(len(line), max(0, pos))

    if opt.get('lookAhead'):
        pos = offset_past_auto_closed(line, pos, opt)

    start = get_start_offset(line, pos, opt.get('prefix', ''))
    if start == -1:
        return None

    scanner = BackwardScanner(line, start)
    scanner.pos = pos
    stack = []

    while not scanner.sol():
        ch = scanner.peek()

        if Brackets.CurlyR in stack:
            if ch == Brackets.CurlyR:
                stack.append(ch)
                scanner.pos -= 1
                continue

            if ch != Brackets.CurlyL:
                scanner.pos -= 1
                continue

        if is_close_brace(ch, opt.get('type')):
            stack.append(ch)
        elif is_open_brace(ch, opt.get('type')):
            if not stack or stack.pop() != BRACE_PAIRS[ch]:
                # unexpected brace
                break
        elif Brackets.SquareR in stack or Brackets.CurlyR in stack:
            # respect all characters inside attribute sets or text nodes
            scanner.pos -= 1
            continue
        elif is_at_html_tag(scanner) or not is_abbreviation(ch):
            break

        scanner.pos -= 1

    if not stack and scanner.pos != pos:
        # Found something, remove some invalid symbols from the
        # beginning and return abbreviation
        abbreviation = re.sub(r'^[*+>^]+', '', line[scanner.pos:pos])
        prefix = opt.get('prefix', '')
        start = start - len(prefix) if prefix else pos - len(abbreviation)
        return ExtractedAbbreviation(abbreviation, pos - len(abbreviation), start, pos)


def offset_past_auto_closed(line: str, pos: int, options: dict):
    """
    Returns new `line` index which is right after characters beyond `pos` that
    editor will likely automatically close, e.g. }, ], and quotes
    """
    # closing quote is allowed only as a next character
    if pos < len(line) and is_quote(line[pos]): pos += 1

    # offset pointer until non-autoclosed character is found
    while pos < len(line) and is_close_brace(line[pos], options.get('type')):
        pos += 1

    return pos


def get_start_offset(line: str, pos: int, prefix: str):
    """
    Returns start offset (left limit) in `line` where we should stop looking for
    abbreviation: it’s nearest to `pos` location of `prefix` token
    """
    if not prefix: return 0

    scanner = BackwardScanner(line)
    scanner.pos = pos

    while not scanner.sol():
        if consume_pair(scanner, Brackets.SquareR, Brackets.SquareL) or consume_pair(scanner, Brackets.CurlyR, Brackets.CurlyL):
            continue

        result = scanner.pos
        if consume_list(scanner, prefix):
            return result

        scanner.pos -= 1

    return -1


def consume_pair(scanner: BackwardScanner, close_ch: str, open_ch: str):
    "Consumes full character pair, if possible"
    start = scanner.pos
    if scanner.consume(close_ch):
        while not scanner.sol():
            if scanner.consume(open_ch):
                return True

            scanner.pos -= 1

    scanner.pos = start
    return False


def consume_list(scanner: BackwardScanner, arr: list):
    "Consumes all character codes from given list, right-to-left, if possible"
    start = scanner.pos
    consumed = False
    i = len(arr) - 1

    while i >= 0 and not scanner.sol():
        if not scanner.consume(arr[i]):
            break
        consumed = i == 0
        i -= 1

    if not consumed:
        scanner.pos = start

    return consumed


def is_abbreviation(ch: str):
    return is_alpha(ch) or is_number(ch) or ch in SPECIAL_CHARS


def is_open_brace(ch: str, syntax: str):
    return ch == Brackets.RoundL or (syntax == 'markup' and ch in (Brackets.SquareL, Brackets.CurlyL))


def is_close_brace(ch: str, syntax: str):
    return ch == Brackets.RoundR or (syntax == 'markup' and ch in (Brackets.SquareR, Brackets.CurlyR))


def create_options(opt=None):
    options = {
        'type': 'markup',
        'lookAhead': True,
        'prefix': '',
    }

    if opt:
        options.update(opt)
    return options
