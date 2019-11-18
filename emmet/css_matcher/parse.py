from ..scanner import Scanner
from ..scanner_utils import is_space
from .scan import literal, Chars

# NB: no `Minus` operator, it must be handled differently
operators = '+/*,'

def split_value(value: str, offset=0):
    "Splits given CSS value into token list"
    start = -1
    expression = 0
    pos = 0
    result = []
    scanner = Scanner(value)

    while not scanner.eof():
        pos = scanner.pos
        if scanner.eat(is_space) or scanner.eat(is_operator) or is_minus_operator(scanner):
            # Use space as value delimiter but only if not in expression context,
            # e.g. `1 2` are distinct values but `(1 2)` not
            if not expression and start != -1:
                result.append((offset + start, offset + pos))
                start = -1
            scanner.eat_while(is_space)
        else:
            if start == -1:
                start = scanner.pos

            if scanner.eat(Chars.LeftRound):
                expression += 1
            elif scanner.eat(Chars.RightRound):
                expression -= 1
            elif not literal(scanner):
                scanner.pos += 1

    if start != -1 and start != scanner.pos:
        result.append((offset + start, offset + scanner.pos))

    return result


def is_operator(ch: str):
    "Check if given character is an operator"
    return ch in operators


def is_minus_operator(scanner: Scanner):
    "Check if current scanner state is at minus operator"
    # Minus operator is tricky since CSS supports dashes in keyword names like
    # `no-repeat`
    start = scanner.pos
    if scanner.eat('-') and scanner.eat(is_space):
        return True

    scanner.pos = start
    return False
