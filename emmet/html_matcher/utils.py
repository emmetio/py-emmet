from ..scanner import Scanner
from ..scanner_utils import is_space, is_quote, is_alpha, is_number, eat_pair

class ElementType:
    Open = 1
    Close = 2
    SelfClose = 3

class Chars:
    Dash = '-'
    Dot = '.'
    Slash = '/'
    Colon = ':'
    LeftAngle = '<'
    RightAngle = '>'
    LeftRound = '('
    RightRound = ')'
    LeftSquare = '['
    RightSquare = ']'
    LeftCurly = '{'
    RightCurly = '}'
    Underscore = '_'
    Equals = '='
    Asterisk = '*'
    Hash = '#'

scan_opt = { 'throws': False }
default_special = {
    'style': None,
    'script': ['', 'text/javascript', 'application/x-javascript', 'javascript', 'typescript', 'ts', 'coffee', 'coffeescript']
}
default_empty = ['img', 'meta', 'link', 'br', 'base', 'hr', 'area', 'wbr', 'col', 'embed', 'input', 'param', 'source', 'track']

class ScannerOptions:
    __slots__ = ('xml', 'special', 'empty')

    def __init__(self, options: dict=None):
        if options is None:
            options = {}
        self.xml = options.get('xml', False)
        """
        Parses given source as XML document. It alters how should-be-empty
        elements are treated: for example, in XML mode parser will try to locate
        closing pair for `<br>` tag
        """

        self.special = options.get('special', default_special)
        """
        List of tags that should have special parsing rules, e.g. should not parse
        inner content and skip to closing tag. Key is a tag name that should be
        considered special and value is either empty (always mark element as special)
        or list of `type` attribute values, which, if present with one of this value,
        make element special
        """

        self.empty = options.get('empty', default_empty)
        """
        List of elements that should be treated as empty (e.g. without closing tag)
        in non-XML syntax
        """


def consume_array(scanner: Scanner, codes: list):
    "Consumes array of character codes from given scanner"
    start = scanner.pos

    for ch in codes:
        if not scanner.eat(ch):
            scanner.pos = start
            return False

    scanner.start = start
    return True


def consume_section(scanner: Scanner, prefix: list, suffix: list, allow_unclosed=False):
    """
    Consumes section from given string which starts with `open` character codes
    and ends with `close` character codes
    :return `true` if section was consumed
    """
    start = scanner.pos
    if consume_array(scanner, prefix):
        # consumed `<!--`, read next until we find ending part or reach the end of input
        while not scanner.eof():
            if consume_array(scanner, suffix):
                scanner.start = start
                return True

            scanner.pos += 1

        # unclosed section is allowed
        if allow_unclosed:
            scanner.start = start
            return True

        scanner.pos = start
        return False

    # unable to find section, revert to initial position
    scanner.pos = start
    return False


def name_start_char(ch: str):
    # Limited XML spec: https://www.w3.org/TR/xml/#NT-NameStartChar
    o = ord(ch) if ch else 0
    return is_alpha(ch) or \
        ch == Chars.Colon or \
        ch == Chars.Underscore or \
        0xC0  <= o <= 0xD6  or \
        0xD8  <= o <= 0xF6  or \
        0xF8  <= o <= 0x2FF or \
        0x370 <= o <= 0x37D or \
        0x37F <= o <= 0x1FFF


def name_char(ch: str):
    "Check if given character can be used in a tag or attribute name"
    # Limited XML spec: https://www.w3.org/TR/xml/#NT-NameChar
    o = ord(ch) if ch else 0
    return name_start_char(ch) or \
        ch == Chars.Dash or \
        ch == Chars.Dot or \
        is_number(ch) or \
        o == 0xB7 or \
        0x0300 <= o <= 0x036F


def ident(scanner: Scanner):
    "Consumes identifier from given scanner"
    start = scanner.pos
    if scanner.eat(name_start_char):
        scanner.eat_while(name_char)
        scanner.start = start
        return True

    return False


def is_terminator(ch: str):
    "Check if given code is tag terminator"
    return ch == Chars.RightAngle or ch == Chars.Slash


def is_unquoted(ch: str):
    "Check if given character code is valid unquoted value"
    return ch and not is_quote(ch) and not is_space(ch) and not is_terminator(ch)

def consume_paired(scanner: Scanner):
    """
    Consumes paired tokens (like `[` and `]`) with respect of nesting and embedded
    quoted values
    :return `true` if paired token was consumed
    """
    global scan_opt
    return eat_pair(scanner, Chars.LeftAngle, Chars.RightAngle, scan_opt) or \
        eat_pair(scanner, Chars.LeftRound, Chars.RightRound, scan_opt) or \
        eat_pair(scanner, Chars.LeftSquare, Chars.RightSquare, scan_opt) or \
        eat_pair(scanner, Chars.LeftCurly, Chars.RightCurly, scan_opt)


def get_unquoted_value(value: str):
    "Returns unquoted value of given string"
    # Trim quotes
    if value and is_quote(value[0]):
        value = value[1:]

    if is_quote(value[-1]):
        value = value[0:-1]

    return value
