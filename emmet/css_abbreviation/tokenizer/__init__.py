from . import tokens
from .tokens import Chars, OperatorType
from ...scanner import Scanner
from ...scanner_utils import is_number, is_alpha, is_alpha_word, is_alpha_numeric_word, is_quote, is_space

OPERATOR_MAP = dict([
    (Chars.Sibling, OperatorType.Sibling),
    (Chars.Excl, OperatorType.Important),
    (Chars.Comma, OperatorType.ArgumentDelimiter),
    (Chars.Colon, OperatorType.PropertyDelimiter),
    (Chars.Dash, OperatorType.ValueDelimiter)
])

def tokenize(abbr: str, is_value=False):
    brackets = 0
    scanner = Scanner(abbr)
    result = []

    while not scanner.eof():
        token = field(scanner) or \
            number_value(scanner) or \
            color_value(scanner) or \
            string_value(scanner) or \
            bracket(scanner) or \
            operator(scanner) or \
            white_space(scanner) or \
            literal(scanner, brackets == 0 and not is_value) or \
            None

        if not token:
            raise scanner.error('Unexpected character')

        if isinstance(token, tokens.Bracket):
            if not brackets and token.open:
                merge_tokens(scanner, result)

            brackets += 1 if token.open else -1
            if brackets < 0:
                raise scanner.error('Unexpected bracket', token.start)

        result.append(token)

        # Forcibly consume next operator after unit-less numeric value or color:
        # next dash `-` must be used as value delimiter
        if should_consume_dash_after(token):
            token = operator(scanner)
            if token: result.append(token)

    return result

def field(scanner: Scanner):
    start = scanner.pos
    if scanner.eat(Chars.Dollar) and scanner.eat(Chars.CurlyBracketOpen):
        scanner.start = scanner.pos
        name = ''
        index = None

        if scanner.eat_while(is_number):
            # It’s a field
            index = int(scanner.current())
            name = consume_placeholder(scanner) if scanner.eat(Chars.Colon) else ''
        elif is_alpha(scanner.peek()):
            # It’s a variable
            name = consume_placeholder(scanner)

        if scanner.eat(Chars.CurlyBracketClose):
            return tokens.Field(name, index, start, scanner.pos)

        raise scanner.error('Expecting }')

    # If we reached here then there’s no valid field here, revert
    # back to starting position
    scanner.pos = start

def consume_placeholder(stream: Scanner):
    "Consumes a placeholder: value right after `:` in field. Could be empty"
    stack = []
    stream.start = stream.pos

    while not stream.eof():
        if stream.eat(Chars.CurlyBracketOpen):
            stack.append(stream.pos)
        elif stream.eat(Chars.CurlyBracketClose):
            if not stack:
                stream.pos -= 1
                break
            stack.pop()
        else:
            stream.pos += 1

    if stack:
        stream.pos = stack.pop()
        raise stream.error('Expecting }')

    return stream.current()

def literal(scanner: Scanner, short=False):
    """
    Consumes literal from given scanner
    :param short Use short notation for consuming value.
    The difference between “short” and “full” notation is that first one uses
    alpha characters only and used for extracting keywords from abbreviation,
    while “full” notation also supports numbers and dashes
    """
    start = scanner.pos

    if scanner.eat(is_ident_prefix):
        # SCSS or LESS variable
        # NB a bit dirty hack: if abbreviation starts with identifier prefix,
        # consume alpha characters only to allow embedded variables
        scanner.eat_while(is_keyword if start else is_literal)
    elif scanner.eat(is_alpha_word):
        scanner.eat_while(is_literal if short else is_keyword)
    else:
        # Allow dots only at the beginning of literal
        scanner.eat(Chars.Dot)
        scanner.eat_while(is_literal)

    if start != scanner.pos:
        scanner.start = start
        return create_literal(scanner)

def create_literal(scanner: Scanner, start=None, end=None):
    if start is None: start = scanner.start
    if end is None: end = scanner.pos
    return tokens.Literal(scanner.substring(start, end), start, end)

def number_value(scanner: Scanner):
    """
    Consumes numeric CSS value (number with optional unit) from current stream,
    if possible
    """
    start = scanner.pos
    if consume_number(scanner):
        scanner.start = start
        raw_value = scanner.current()
        value = float(raw_value)

        # eat unit, which can be a % or alpha word
        scanner.start = scanner.pos
        scanner.eat(Chars.Percent) or scanner.eat_while(is_alpha_word)
        return tokens.NumberValue(value, raw_value, scanner.current(), start, scanner.pos)

def string_value(scanner: Scanner):
    "Consumes quoted string value from given scanner"
    ch = scanner.peek()
    start = scanner.pos
    finished = False

    if is_quote(ch):
        scanner.pos += 1
        while not scanner.eof():
            # Do not throw error on malformed string
            if scanner.eat(ch):
                finished = True
                break
            else:
                scanner.pos += 1

        scanner.start = start
        value_start = start + 1
        value_end = scanner.pos - (1 if finished else 0)
        return tokens.StringValue(
            scanner.substring(value_start, value_end),
            'single' if ch == Chars.SingleQuote else 'double',
            start, scanner.pos)

def color_value(scanner: Scanner):
    "Consumes a color token from given scanner"
    # supported color variations:
    # #abc   → #aabbccc
    # #0     → #000000
    # #fff.5 → rgba(255, 255, 255, 0.5)
    # #t     → transparent

    start = scanner.pos
    if scanner.eat(Chars.Hash):
        value_start = scanner.pos
        color = ''
        alpha = ''
        if scanner.eat_while(is_hex):
            color = scanner.substring(value_start, scanner.pos)
            alpha = color_alpha(scanner)
        elif scanner.eat(Chars.Transparent):
            color = '0'
            alpha = color_alpha(scanner) or '0'
        else:
            alpha = color_alpha(scanner)

        if color or alpha or scanner.eof():
            r, g, b, a = parse_color(color, alpha)
            return tokens.ColorValue(r, g, b, a, scanner.substring(start + 1, scanner.pos), start, scanner.pos)
        else:
            # Consumed `#` but no actual value: invalid color value, treat it as literal
            return create_literal(scanner, start)

    scanner.pos = start

def color_alpha(scanner: Scanner):
    "Consumes alpha value of color: `.1`"
    start = scanner.pos
    if scanner.eat(Chars.Dot):
        scanner.start = start
        if scanner.eat_while(is_number):
            return scanner.current()
        return '1'

    return ''

def white_space(scanner: Scanner):
    "Consumes white space characters as string literal from given scanner"
    start = scanner.pos
    if scanner.eat_while(is_space):
        return tokens.WhiteSpace(start, scanner.pos)

def bracket(scanner: Scanner):
    "Consumes bracket from given scanner"
    ch = scanner.peek()
    if is_bracket(ch):
        start = scanner.pos
        scanner.pos += 1
        return tokens.Bracket(ch == Chars.RoundBracketOpen, start, scanner.pos)

def operator(scanner: Scanner):
    global OPERATOR_MAP
    op = OPERATOR_MAP.get(scanner.peek())
    if op:
        start = scanner.pos
        scanner.pos += 1
        return tokens.Operator(op, start, scanner.pos)

def consume_number(stream: Scanner):
    """
    Eats number value from given stream.
    Returns `True` if number was consumed
    """
    start = stream.pos
    stream.eat(Chars.Dash)
    after_negative = stream.pos

    has_decimal = stream.eat_while(is_number)

    prev_pos = stream.pos
    if stream.eat(Chars.Dot):
        # It’s perfectly valid to have numbers like `1.`, which enforces
        # value to float unit type
        has_float = stream.eat_while(is_number)
        if not has_decimal and not has_float:
            # Lone dot
            stream.pos = prev_pos

    # Edge case: consumed dash only: not a number, bail-out
    if stream.pos == after_negative:
        stream.pos = start

    return stream.pos != start

def is_ident_prefix(ch: str):
    return ch == Chars.At or ch == Chars.Dollar

def is_hex(ch: str):
    "Check if given code is a hex value (/0-9a-f/)"
    return is_number(ch) or 'A' <= ch <= 'F' or 'a' <= ch <= 'f'

def is_keyword(ch: str):
    return is_alpha_numeric_word(ch) or ch == Chars.Dash

def is_bracket(ch: str):
    return ch in (Chars.RoundBracketOpen, Chars.RoundBracketClose)

def is_literal(ch: str):
    return is_alpha_word(ch) or ch == Chars.Percent

def parse_color(value: str, alpha=None):
    r = '0'
    g = '0'
    b = '0'
    a = float(alpha) if alpha is not None and alpha != '' else 1

    if value == 't':
        a = 0
    else:
        l = len(value)
        if l == 0:
            pass
        elif l == 1:
            r = g = b = value + value
        elif l == 2:
            r = g = b = value
        elif l == 3:
            r = value[0] * 2
            g = value[1] * 2
            b = value[2] * 2
        else:
            value = value.rjust(6, '0')
            r = value[0:2]
            g = value[2:4]
            b = value[4:6]

    return (int(r, 16), int(g, 16), int(b, 16), a)


def should_consume_dash_after(token: tokens.Token):
    """
    Check if scanner reader must consume dash after given token.
    Used in cases where user must explicitly separate numeric values
    """
    return isinstance(token, tokens.ColorValue) or (isinstance(token, tokens.NumberValue) and not token.unit)


def merge_tokens(scanner: Scanner, token_list: list):
    """
    Merges last adjacent tokens into a single literal.
    This function is used to overcome edge case when function name was parsed
    as a list of separate tokens. For example, a `scale3d()` value will be
    parsed as literal and number tokens (`scale` and `3d`) which is a perfectly
    valid abbreviation but undesired result. This function will detect last adjacent
    literal and number values and combine them into single literal
    """
    start = 0
    end = 0

    while token_list:
        token = token_list[-1]
        if isinstance(token, tokens.Literal) or isinstance(token, tokens.NumberValue):
            start = token.start
            if not end: end = token.end
            token_list.pop()
        else:
            break

    if start != end:
        token_list.append(create_literal(scanner, start, end))
