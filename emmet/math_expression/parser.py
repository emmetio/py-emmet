from ..scanner import Scanner
from ..scanner_utils import is_white_space, is_number

class TokenType:
    Number = 'num'
    Op1 = 'op1'
    Op2 = 'op2'
    Null = 'null'


class Operator:
    Plus = '+'
    Minus = '-'
    Multiply = '*'
    Divide = '/'
    IntDivide = '\\'
    LeftParenthesis = '('
    RightParenthesis = ')'
    Dot = '.'


class ParserState:
    Primary = 1 << 0
    Operator = 1 << 1
    LParen = 1 << 2
    RParen = 1 << 3
    Sign = 1 << 4
    NullaryCall = 1 << 5


class Token:
    __slots__ = ('type', 'value', 'priority')

    def __init__(self, token_type: TokenType, value: int, priority=0):
        self.type = token_type
        self.value = value
        self.priority = priority

class MathExpressionException(Exception):
    def __init__(self, message: str, scanner: Scanner=None):
        if scanner:
            message += ' at column %d of expression' % scanner.pos
        super(MathExpressionException, self).__init__(message)
        self.message = message
        if scanner:
            self.pos = scanner.pos


nullary = Token(TokenType.Null, 0)


def parse(expr: str):
    "Parses given expression in forward direction"
    scanner = Scanner(expr) if isinstance(expr, str) else expr
    priority = 0
    expected = ParserState.Primary | ParserState.LParen | ParserState.Sign
    tokens = []

    while not scanner.eof():
        scanner.eat_while(is_white_space)
        scanner.start = scanner.pos

        if consume_number(scanner):
            if (expected & ParserState.Primary) == 0:
                raise MathExpressionException('Unexpected number', scanner)

            tokens.append(number(scanner.current()))
            expected = ParserState.Operator | ParserState.RParen
        elif is_operator(scanner.peek()):
            ch = scanner.next()
            if is_sign(ch) and (expected & ParserState.Sign):
                if is_negative_sign(ch):
                    tokens.append(op1(ch, priority))
                expected = ParserState.Primary | ParserState.LParen | ParserState.Sign
            else:
                if (expected & ParserState.Operator) == 0:
                    raise MathExpressionException('Unexpected operator', scanner)
                tokens.append(op2(ch, priority))
                expected = ParserState.Primary | ParserState.LParen | ParserState.Sign
        elif scanner.eat(Operator.LeftParenthesis):
            if (expected & ParserState.LParen) == 0:
                raise MathExpressionException('Unexpected "("', scanner)

            priority += 10
            expected = ParserState.Primary | ParserState.LParen | ParserState.Sign | ParserState.NullaryCall
        elif scanner.eat(Operator.RightParenthesis):
            priority -= 10

            if expected & ParserState.NullaryCall:
                tokens.append(nullary)
            elif (expected & ParserState.RParen) == 0:
                raise MathExpressionException('Unexpected ")"', scanner)

            expected = ParserState.Operator | ParserState.RParen | ParserState.LParen
        else:
            raise MathExpressionException('Unknown character', scanner)

    if 0 < priority >= 10:
        raise MathExpressionException('Unmatched "()"', scanner)

    result = order_tokens(tokens)

    if result is None:
        raise MathExpressionException('Parity', scanner)

    return result

def consume_number(scanner: Scanner):
    """
    Consumes number from given stream
    :return `True` if number was consumed
    """
    start = scanner.pos
    if scanner.eat(Operator.Dot) and scanner.eat_while(is_number):
        # short decimal notation: .025
        return True

    if scanner.eat_while(is_number) and (not scanner.eat(Operator.Dot) or scanner.eat_while(is_number)):
        # either integer or decimal: 10, 10.25
        return True

    scanner.pos = start
    return False


def order_tokens(tokens: list):
    """
    Orders parsed tokens (operands and operators) in given array so that they are
    laid off in order of execution
    """
    operators = []
    operands = []
    n_operators = 0

    for t in tokens:
        if t.type == TokenType.Number:
            operands.append(t)
        else:
            n_operators += 1 if t.type == TokenType.Op1 else 2

            while operators:
                if t.priority <= operators[-1].priority:
                    operands.append(operators.pop())
                else:
                    break

            operators.append(t)

    if n_operators + 1 == len(operands) + len(operators):
        operators.reverse()
        return operands + operators

    # Parity
    return None


def number(value: str, priority=0):
    "Number token factory"
    return Token(TokenType.Number, float(value), priority)


def op1(value: str, priority=0):
    "Unary operator factory"
    if value == Operator.Minus:
        priority += 2
    return Token(TokenType.Op1, value, priority)


def op2(value: str, priority=0):
    "Binary operator factory"
    if value == Operator.Multiply:
        priority += 1
    elif value == Operator.Divide or value == Operator.IntDivide:
        priority += 2

    return Token(TokenType.Op2, value, priority)


def is_sign(ch: str):
    return is_positive_sign(ch) or is_negative_sign(ch)


def is_positive_sign(ch: str):
    return ch == Operator.Plus


def is_negative_sign(ch: str):
    return ch == Operator.Minus


def is_operator(ch: str):
    return ch in (Operator.Plus, Operator.Minus, Operator.Multiply, Operator.Divide, Operator.IntDivide)
