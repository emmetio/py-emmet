from ...scanner import Scanner
from ...scanner_utils import is_quote, is_space, is_number, is_alpha, is_alpha_numeric_word
from .utils import Chars, escaped
from . import tokens

OPERATOR_TYPES = dict([
    (Chars.Child, 'child'),
    (Chars.Sibling, 'sibling'),
    (Chars.Climb, 'climb'),
    (Chars.Dot, 'class'),
    (Chars.Hash, 'id'),
    (Chars.Slash, 'close'),
    (Chars.Equals, 'equal')
])


def tokenize(source: str):
    scanner = Scanner(source)
    result = []
    ctx = {
        'group': 0,
        'attribute': 0,
        'expression': 0,
        'quote': None
    }

    while not scanner.eof():
        ch = scanner.peek()
        token = field(scanner, ctx) or \
            repeater_placeholder(scanner) or \
            repeater_number(scanner) or \
            repeater(scanner) or \
            white_space(scanner) or \
            literal(scanner, ctx) or \
            operator(scanner) or \
            quote(scanner) or \
            bracket(scanner)

        if token:
            result.append(token)
            if token.type == 'Quote':
                ctx['quote'] = None if ch == ctx['quote'] else ch
            elif token.type == 'Bracket':
                ctx[token.context] += 1 if token.open else -1
        else:
            raise scanner.error('Unexpected character')

    return result


def literal(scanner: Scanner, ctx: dict):
    "Consumes literal from given scanner"
    start = scanner.pos
    value = []

    while not scanner.eof():
        if escaped(scanner):
            value.append(scanner.current())
            continue

        ch = scanner.peek()

        if ch == '/' and not ctx['quote'] and not ctx['expression'] and not ctx['attribute']:
            # Special case for `/` character between numbers in class names
            prev = scanner.string[scanner.pos - 1] if scanner.pos > 0 else ''
            next = scanner.string[scanner.pos + 1] if scanner.pos < scanner.end - 1 else ''
            if prev.isdigit() and next.isdigit():
                value.append(scanner.next())
                continue

        if ch == ctx['quote'] or ch == Chars.Dollar or is_allowed_operator(ch, ctx):
            # 1. Found matching quote
            # 2. The `$` character has special meaning in every context
            # 3. Depending on context, some characters should be treated as operators
            break

        if ctx['expression']:
            if ch == Chars.CurlyBracketOpen:
                # Handle nested curly braces inside expressions, e.g. `span{{foo}}`
                ctx['expression'] += 1
            elif ch == Chars.CurlyBracketClose:
                if ctx['expression'] == 1:
                    break;
                ctx['expression'] -= 1

        if not ctx['quote'] and not ctx['expression']:
            # Consuming element name
            if not ctx['attribute'] and not is_element_name(ch):
                break

            if is_allowed_space(ch, ctx) or \
               is_allowed_repeater(ch, ctx) or \
               is_quote(ch) or \
               bracket_type(ch):
                # Stop for characters not allowed in unquoted literal
                break

        value.append(scanner.next())

    if start != scanner.pos:
        scanner.start = start
        return tokens.Literal(''.join(value), start, scanner.pos)


def white_space(scanner: Scanner):
    "Consumes white space characters as string literal from given scanner"
    start = scanner.pos
    if scanner.eat_while(is_space):
        return tokens.WhiteSpace(start, scanner.pos)


def quote(scanner: Scanner):
    "Consumes quote from given scanner"
    ch = scanner.peek()
    if is_quote(ch):
        return tokens.Quote(ch == Chars.SingleQuote, inc_pos(scanner), scanner.pos)


def bracket(scanner: Scanner):
    "Consumes bracket from given scanner"
    ch = scanner.peek()
    context = bracket_type(ch)
    if context:
        return tokens.Bracket(is_open_bracket(ch), context, inc_pos(scanner), scanner.pos)


def operator(scanner: Scanner):
    "Consumes operator from given scanner"
    op = operator_type(scanner.peek())
    if op:
        return tokens.Operator(op, inc_pos(scanner), scanner.pos)


def repeater(scanner: Scanner):
    "Consumes node repeat token from current scanner position and returns its parsed value"
    start = scanner.pos
    if scanner.eat(Chars.Asterisk):
        scanner.start = scanner.pos
        count = 1
        implicit = False

        if scanner.eat_while(is_number):
            count = int(scanner.current())
        else:
            implicit = True

        return tokens.Repeater(count, 0, implicit, start, scanner.pos)


def repeater_placeholder(scanner: Scanner):
    "Consumes repeater placeholder `$#` from given scanner"
    start = scanner.pos
    if scanner.eat(Chars.Dollar) and scanner.eat(Chars.Hash):
        return tokens.RepeaterPlaceholder(None, start, scanner.pos)

    scanner.pos = start


def repeater_number(scanner: Scanner):
    "Consumes numbering token like `$` from given scanner state"
    start = scanner.pos
    if scanner.eat_while(Chars.Dollar):
        size = scanner.pos - start
        reverse = False
        base = 1
        parent = 0

        if scanner.eat(Chars.At):
            # Consume numbering modifiers
            while scanner.eat(Chars.Climb):
                parent += 1

            reverse = scanner.eat(Chars.Dash)
            scanner.start = scanner.pos
            if scanner.eat_while(is_number):
                base = int(scanner.current())

        scanner.start = start
        return tokens.RepeaterNumber(size, reverse, base, parent, start, scanner.pos)


def field(scanner: Scanner, ctx: dict):
    start = scanner.pos
    # Fields are allowed inside expressions and attributes
    if (ctx['expression'] or ctx['attribute']) and scanner.eat(Chars.Dollar) and scanner.eat(Chars.CurlyBracketOpen):
        scanner.start = scanner.pos
        index = None
        name = ''

        if scanner.eat_while(is_number):
            # It’s a field
            index = int(scanner.current())
            if scanner.eat(Chars.Colon):
                name = consume_placeholder(scanner)
        elif is_alpha(scanner.peek()):
            # It’s a variable
            name = consume_placeholder(scanner)

        if scanner.eat(Chars.CurlyBracketClose):
            return tokens.Field(name, index, start, scanner.pos)

        raise scanner.error('Expecting }')


    # If we reached here then there’s no valid field here, revert
    # back to starting position
    scanner.pos = start


def consume_placeholder(scanner: Scanner):
    "Consumes a placeholder: value right after `:` in field. Could be empty"
    stack = []
    scanner.start = scanner.pos

    while not scanner.eof():
        if scanner.eat(Chars.CurlyBracketOpen):
            stack.append(scanner.pos)
        elif scanner.eat(Chars.CurlyBracketClose):
            if not len(stack):
                scanner.pos -= 1
                break
            stack.pop()
        else:
            scanner.pos += 1

    if len(stack):
        scanner.pos = stack.pop()
        raise scanner.error('Expecting }')

    return scanner.current()


def is_allowed_operator(ch: str, ctx: dict):
    "Check if given character code is an operator and it’s allowed in current context"
    op = operator_type(ch)
    if not op or ctx['quote'] or ctx['expression']:
        # No operators inside quoted values or expressions
        return False

    # Inside attributes, only `equals` is allowed
    return not ctx['attribute'] or op == 'equal'


def is_allowed_space(ch: str, ctx: dict):
    """
    Check if given character is a space character and is allowed to be consumed
    as a space token in current context
    """
    return is_space(ch) and not ctx['expression']


def is_allowed_repeater(ch: str, ctx: dict):
    "Check if given character can be consumed as repeater in current context"
    return ch == Chars.Asterisk and not ctx['attribute'] and not ctx['expression']


def bracket_type(ch: str):
    "If given character is a bracket, returns it’s type"
    if ch in (Chars.RoundBracketOpen, Chars.RoundBracketClose):
        return 'group'

    if ch in (Chars.SquareBracketOpen, Chars.SquareBracketClose):
        return 'attribute'

    if ch in (Chars.CurlyBracketOpen, Chars.CurlyBracketClose):
        return 'expression'

def operator_type(ch: int):
    "If given character is an operator, returns it’s type"
    global OPERATOR_TYPES
    return OPERATOR_TYPES.get(ch)


def is_open_bracket(ch: str):
    "Check if given character is an open bracket"
    return ch in (Chars.CurlyBracketOpen, Chars.SquareBracketOpen, Chars.RoundBracketOpen)

def is_element_name(ch: str):
    "Check if given character is allowed in element name"
    return is_alpha_numeric_word(ch) or ch in (Chars.Dash, Chars.Colon, Chars.Excl)

def inc_pos(scanner: Scanner):
    pos = scanner.pos
    scanner.pos += 1
    return pos
