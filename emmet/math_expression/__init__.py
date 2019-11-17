from math import floor
from .parser import parse, TokenType, Operator, Token, MathExpressionException
from .extract import extract

ops1 = {
    Operator.Minus: lambda num: -num
}

ops2 = {
    Operator.Plus: lambda a, b: a + b,
    Operator.Minus: lambda a, b: a - b,
    Operator.Multiply: lambda a, b: a * b,
    Operator.Divide: lambda a, b: a / b,
    Operator.IntDivide: lambda a, b: floor(a / b)
}

def evaluate(expr: str):
    if not isinstance(expr, (list, tuple)):
        expr = parse(expr)

    if not expr:
        return None

    n_stack = []

    for token in expr:
        if token.type == TokenType.Number:
            n_stack.append(token.value)
        elif token.type == TokenType.Op2:
            n2 = n_stack.pop()
            n1 = n_stack.pop()
            f = ops2[token.value]
            n_stack.append(f(n1, n2))
        elif token.type == TokenType.Op1:
            n1 = n_stack.pop()
            f = ops1[token.value]
            n_stack.append(f(n1))
        else:
            raise Exception('Invalid expression')

    if len(n_stack) > 1:
        raise Exception('Invalid Expression (parity)')

    return n_stack[0]
