from ..scanner import Scanner
from ..scanner_utils import is_quote, is_space

class ScanState:
    __slots__ = ('start', 'end', 'property_delimiter', 'property_start',
        'property_end', 'expression')

    def __init__(self):
        self.start = -1
        "Start location of currently consumed token"

        self.end = -1
        "End location of currently consumed token"

        self.property_delimiter = -1
        "Location of possible property delimiter"

        self.property_start = -1
        "Location of possible property start"

        self.property_end = -1
        "Location of possible property end"

        self.expression = 0
        "In expression context"

    def reset(self):
        self.start = self.end = self.property_start = self.property_end = self.property_delimiter = -1



class TokenType:
    Selector = 'selector'
    PropertyName = 'propertyName'
    PropertyValue = 'propertyValue'
    BlockEnd = 'blockEnd'


class Chars:
    LeftCurly = '{'
    RightCurly = '}'
    Asterisk = '*'
    Slash = '/'
    Colon = ':'
    Semicolon = ';'
    Backslash = '\\'
    LeftRound = '('
    RightRound = ')'
    LF = '\n'
    CR = '\r'

def scan(source: str, callback: callable):
    """
    Performs fast scan of given stylesheet (CSS, LESS, SCSS) source code and runs
    callback for each token and its range found. The goal of this parser is to quickly
    determine document structure: selector, property, value and block end.
    It doesn’t provide detailed info about CSS atoms like compound selectors,
    operators, quoted string etc. to reduce memory allocations: this data can be
    parsed later on demand.
    """
    scanner = Scanner(source)
    state = ScanState()
    block_end = False

    def notify(token_type: TokenType, delimiter: int=None, start: int=None, end: int=None):
        if delimiter is None: delimiter = scanner.start
        if start is None: start = state.start
        if end is None: end = state.end
        return callback(token_type, start, end, delimiter) is False

    while not scanner.eof():
        if comment(scanner) or whitespace(scanner):
            continue

        scanner.start = scanner.pos
        block_end = scanner.eat(Chars.RightCurly)
        if block_end or scanner.eat(Chars.Semicolon):
            # Block or property end
            if state.property_start != -1:
                # We have pending property
                if notify(TokenType.PropertyName, state.property_delimiter, state.property_start, state.property_end):
                    return

                if state.start == -1:
                    # Explicit property value state: emit empty value
                    state.start = state.end = scanner.start

                if notify(TokenType.PropertyValue):
                    return
            elif state.start != -1 and notify(TokenType.PropertyName):
                # Flush consumed token
                return

            if block_end:
                state.start = scanner.start
                state.end = scanner.pos

                if notify(TokenType.BlockEnd):
                    return

            state.reset()
        elif scanner.eat(Chars.LeftCurly):
            # Block start
            if state.start == -1 and state.property_start == -1:
                # No consumed selector, emit empty value as selector start
                state.start = state.end = scanner.pos

            if state.property_start != -1:
                # Now we know that value that looks like property name-value pair
                # was actually a selector
                state.start = state.property_start

            if notify(TokenType.Selector):
                return
            state.reset()
        elif scanner.eat(Chars.Colon) and not is_known_selector_colon(scanner, state):
            # Colon could be one of the following:
            # — property delimiter: `foo: bar`, must be in block context
            # — variable delimiter: `$foo: bar`, could be anywhere
            # — pseudo-selector: `a:hover`, could be anywhere (for LESS and SCSS)
            # — media query expression: `min-width: 100px`, must be inside expression context
            # Since I can’t easily detect `:` meaning for sure, we’ll update state
            # to accumulate possible property name-value pair or selector
            if state.property_start == -1:
                state.property_start = state.start
            state.property_end = state.end
            state.property_delimiter = scanner.pos - 1
            state.start = state.end = -1
        else:
            if state.start == -1:
                state.start = scanner.pos

            if scanner.eat(Chars.LeftRound):
                state.expression += 1
            elif scanner.eat(Chars.RightRound):
                state.expression -= 1
            elif not literal(scanner):
                scanner.pos += 1

            state.end = scanner.pos

    if state.property_start != -1:
        # Pending property name
        if notify(TokenType.PropertyName, state.property_delimiter, state.property_start, state.property_end):
            return

    if state.start != -1:
        # There’s pending token in state
        notify(TokenType.PropertyValue if state.property_start != -1 else TokenType.PropertyName, -1)


def whitespace(scanner: Scanner):
    return scanner.eat_while(is_space)


def comment(scanner: Scanner):
    """
    Consumes CSS comments from scanner: `/*  * /`
    It’s possible that comment may not have closing part
    """
    start = scanner.pos
    if scanner.eat(Chars.Slash) and scanner.eat(Chars.Asterisk):
        scanner.start = start
        while not scanner.eof():
            if scanner.eat(Chars.Asterisk):
                if scanner.eat(Chars.Slash):
                    return True
                continue
            scanner.pos += 1
        return True
    else:
        scanner.pos = start

    return False


def literal(scanner: Scanner):
    ch = scanner.peek()
    if is_quote(ch):
        scanner.start = scanner.pos
        scanner.pos += 1
        while not scanner.eof():
            if scanner.eat(ch) or scanner.eat(Chars.LF) or scanner.eat(Chars.CR):
                break

            # Skip escape character, if any
            scanner.eat(Chars.Backslash)
            scanner.pos += 1

        # Do not throw if string is incomplete
        return True


def is_known_selector_colon(scanner: Scanner, state: ScanState):
    "Check if current state is a known selector context for `:` delimiter"
    # Either inside expression like `(min-width: 10px)` or pseudo-element `::before`
    return state.expression or scanner.eat_while(Chars.Colon)
