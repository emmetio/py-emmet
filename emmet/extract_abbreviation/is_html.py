from .reader import BackwardScanner
from .brackets import Brackets, BRACE_PAIRS
from ..scanner_utils import is_alpha, is_number, is_quote

class Chars:
    Tab = '\t'
    Space = ' '
    Dash = '-'
    Slash = '/'
    Colon = ':'
    Equals = '='
    AngleLeft = '<'
    AngleRight = '>'


def is_html(scanner: BackwardScanner):
    "Check if given reader’s current position points at the end of HTML tag"
    start = scanner.pos

    if not scanner.consume(Chars.AngleRight):
        return False

    ok = False
    scanner.consume(Chars.Slash) # possibly self-closed element

    while not scanner.sol():
        scanner.consume_while(is_white_space)

        if consume_ident(scanner):
            # ate identifier: could be a tag name, boolean attribute or unquoted
            # attribute value
            if scanner.consume(Chars.Slash):
                # either closing tag or invalid tag
                ok = scanner.consume(Chars.AngleLeft)
                break
            elif scanner.consume(Chars.AngleLeft):
                # opening tag
                ok = True
                break
            elif scanner.consume(is_white_space):
                # boolean attribute
                continue
            elif scanner.consume(Chars.Equals):
                # simple unquoted value or invalid attribute
                if consume_ident(scanner): continue
                break
            elif consume_attribute_with_unquoted_value(scanner):
                # identifier was a part of unquoted value
                ok = True
                break

            # invalid tag
            break

        if consume_attribute(scanner):
            continue

        break

    scanner.pos = start
    return ok


def consume_attribute(scanner: BackwardScanner):
    """
    Consumes HTML attribute from given string.
    Returns `True` if attribute was consumed.
    """
    return consume_attribute_with_quoted_value(scanner) or \
        consume_attribute_with_unquoted_value(scanner)


def consume_attribute_with_quoted_value(scanner: BackwardScanner):
    start = scanner.pos
    if consume_quoted(scanner) and scanner.consume(Chars.Equals) and consume_ident(scanner):
        return True

    scanner.pos = start
    return False


def consume_attribute_with_unquoted_value(scanner: BackwardScanner):
    start = scanner.pos
    stack = []

    while not scanner.sol():
        ch = scanner.peek()
        if is_close_bracket(ch):
            stack.append(ch)
        elif is_open_bracket(ch):
            if not stack or stack.pop() != BRACE_PAIRS[ch]:
                # Unexpected open bracket
                break
        elif not is_unquoted_value(ch):
            break
        scanner.pos -= 1


    if start != scanner.pos and scanner.consume(Chars.Equals) and consume_ident(scanner):
        return True

    scanner.pos = start
    return False


def consume_ident(scanner: BackwardScanner):
    "Consumes HTML identifier from stream"
    return scanner.consume_while(is_ident)


def consume_quoted(scanner: BackwardScanner):
    start = scanner.pos
    quote = scanner.previous()

    if is_quote(quote):
        while not scanner.sol():
            if scanner.previous() == quote and scanner.peek() != '\\':
                return True

    scanner.pos = start
    return False


def is_ident(ch: str):
    "Check if given character code belongs to HTML identifier"
    return ch == Chars.Colon or ch == Chars.Dash or is_alpha(ch) or is_number(ch)


def is_white_space(ch: str):
    "Check if given code is a whitespace"
    return ch == Chars.Space or ch == Chars.Tab


def is_unquoted_value(ch: str):
    "Check if given code may belong to unquoted attribute value"
    return ch and ch != Chars.Equals and not is_white_space(ch) and not is_quote(ch)


def is_open_bracket(ch: int):
    return ch in (Brackets.CurlyL, Brackets.RoundL, Brackets.SquareL)


def is_close_bracket(ch: int):
    return ch in (Brackets.CurlyR, Brackets.RoundR, Brackets.SquareR)
