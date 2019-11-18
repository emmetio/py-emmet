from ..scanner_utils import is_space, is_number
from .parser import Operator, is_sign, is_operator

class BackwardScanner:
    __slots__ = ('text', 'pos')

    def __init__(self, text: str, pos=0):
        self.text = text
        self.pos = pos

    def prev(self):
        return self.text[self.pos - 1] if self.pos else ''

    def cur(self):
        return self.text[self.pos] if self.pos < len(self.text) else ''


def extract(text: str, pos=None, options: dict=None) -> tuple:
    """
    Extracts math expression from given text at specified position.
    Expression is extracted in backward direction.

    Options:
    :lookAhead bool
    Allow capturing extra expression characters right after start position.
    Useful for extracting expressions from text editor source which inserts
    paired characters like `(` and `)` to properly extract expression past
    caret position

    :whitespace: bool
    Allow whitespace in extracted expressions
    """
    if pos is None:
        pos = len(text)

    opt = { 'lookAhead': True, 'whitespace': True }
    if options: opt.update(options)

    scanner = BackwardScanner(text, pos)

    if opt['lookAhead'] and scanner.cur() == Operator.RightParenthesis:
        # Basically, we should consume right parenthesis only with optional whitespace
        scanner.pos += 1
        l = len(text)
        while scanner.pos < l:
            ch = scanner.cur()
            if ch != Operator.RightParenthesis and not (opt['whitespace'] and is_space(ch)):
                break
            scanner.pos += 1

    end = scanner.pos
    braces = 0
    while scanner.pos >= 0:
        if number(scanner):
            continue

        ch = scanner.prev()
        if ch == Operator.RightParenthesis:
            braces += 1
        elif ch == Operator.LeftParenthesis:
            if not braces:
                break
            braces -= 1
        elif not ((opt['whitespace'] and is_space(ch)) or is_sign(ch) or is_operator(ch)):
            break

        scanner.pos -= 1

    if scanner.pos != end and not braces:
        # Trim whitespace
        while is_space(scanner.cur()):
            scanner.pos += 1

        return (scanner.pos, end)


def number(scanner: BackwardScanner):
    if is_number(scanner.prev()):
        scanner.pos -= 1
        dot = False

        while scanner.pos >= 0:
            ch = scanner.prev()
            if ch == '.':
                if dot:
                    # Decimal delimiter already consumed, abort
                    break
                dot = True
            elif not is_number(ch):
                break
            scanner.pos -= 1

        return True

    return False
