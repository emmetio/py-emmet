from .tokenizer import tokens
from .tokenizer.tokens import OperatorType
from ..token_scanner import TokenScanner

class FunctionCall:
    __slots__ = ('type', 'name', 'arguments')

    def __init__(self, name: str, arguments: list):
        self.type = 'FunctionCall'
        self.name = name
        self.arguments = arguments

class CSSValue:
    __slots__ = ('type', 'value')

    def __init__(self, value: list):
        self.type = 'CSSValue'
        self.value = value


class CSSProperty:
    __slots__ = ('name', 'value', 'important', 'snippet')

    def __init__(self, name: str, value: list, important=False):
        self.name = name
        self.value = value
        self.important = important
        self.snippet = None
        "Snippet matched with current property"

def parser(token_list: list, options={}):
    scanner = TokenScanner(token_list)
    result = []

    while scanner.readable():
        prop = consume_property(scanner, options)
        if prop:
            result.append(prop)
        elif not scanner.consume(is_sibling_operator):
            raise scanner.error('Unexpected token')

    return result

def consume_property(scanner: TokenScanner, options={}):
    "Consumes single CSS property"
    name = None
    important = False
    value_fragment = None
    value = []
    token = scanner.peek()
    value_mode = bool(options.get('value', False))

    if not value_mode and is_literal(token) and not is_function_start(scanner):
        scanner.pos += 1
        name = token.value
        # Consume any following value delimiter after property name
        scanner.consume(is_value_delimiter)

    # Skip whitespace right after property name, if any
    if value_mode:
        scanner.consume(is_white_space)

    while scanner.readable():
        if scanner.consume(is_important):
            important = True
        else:
            value_fragment = consume_value(scanner, value_mode)
            if value_fragment:
                value.append(value_fragment)
            elif not scanner.consume(is_fragment_delimiter):
                break

    if name or value or important:
        return CSSProperty(name, value, important)

def consume_value(scanner: TokenScanner, in_argument=False):
    "Consumes single value fragment, e.g. all value tokens before comma"
    result = []
    token = None
    args = None

    while scanner.readable():
        token = scanner.peek()
        if is_value(token):
            scanner.pos += 1
            args = consume_arguments(scanner) if is_literal(token) else None

            if args is not None:
                result.append(FunctionCall(token.value, args))
            else:
                result.append(token)
        elif is_value_delimiter(token) or (in_argument and is_white_space(token)):
            scanner.pos += 1
        else:
            break

    return CSSValue(result) if result else None

def consume_arguments(scanner: TokenScanner):
    start = scanner.pos
    if scanner.consume(is_open_bracket):
        args = []
        value = None

        while scanner.readable() and not scanner.consume(is_close_bracket):
            value = consume_value(scanner, True)
            if value:
                args.append(value)
            elif not scanner.consume(is_white_space) and not scanner.consume(is_argument_delimiter):
                raise scanner.error('Unexpected token')

        scanner.start = start
        return args

def is_literal(token: tokens.Token):
    return isinstance(token, tokens.Literal)


def is_bracket(token: tokens.Token, is_open=None):
    return isinstance(token, tokens.Bracket) and (is_open is None or token.open == is_open)


def is_open_bracket(token: tokens.Token):
    return is_bracket(token, True)


def is_close_bracket(token: tokens.Token):
    return is_bracket(token, False)


def is_white_space(token: tokens.Token):
    return isinstance(token, tokens.WhiteSpace)


def is_operator(token: tokens.Token, operator: OperatorType=None):
    return isinstance(token, tokens.Operator) and (not operator or token.operator == operator)


def is_sibling_operator(token: tokens.Token):
    return is_operator(token, OperatorType.Sibling)


def is_argument_delimiter(token: tokens.Token):
    return is_operator(token, OperatorType.ArgumentDelimiter)


def is_fragment_delimiter(token: tokens.Token):
    return is_argument_delimiter(token)

def is_important(token: tokens.Token):
    return is_operator(token, OperatorType.Important)


def is_value(token: tokens.Token):
    return isinstance(token, tokens.StringValue) or \
        isinstance(token, tokens.ColorValue) or \
        isinstance(token, tokens.NumberValue) or \
        isinstance(token, tokens.Literal) or \
        isinstance(token, tokens.Field)


def is_value_delimiter(token: tokens.Token):
    return is_operator(token, OperatorType.PropertyDelimiter) or \
        is_operator(token, OperatorType.ValueDelimiter)


def is_function_start(scanner: TokenScanner):
    max_ix = len(scanner.tokens) - 1
    if scanner.pos < max_ix:
        t1 = scanner.tokens[scanner.pos]
        t2 = scanner.tokens[scanner.pos + 1]
        return t1 and t2 and is_literal(t1) and isinstance(t2, tokens.Bracket)
