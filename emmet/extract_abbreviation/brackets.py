class Brackets:
    SquareL = '['
    SquareR = ']'
    RoundL = '('
    RoundR = ')'
    CurlyL = '{'
    CurlyR = '}'

BRACE_PAIRS = dict([
    (Brackets.SquareL, Brackets.SquareR),
    (Brackets.RoundL, Brackets.RoundR),
    (Brackets.CurlyL, Brackets.CurlyR),
])
