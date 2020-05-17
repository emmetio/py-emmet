class Chars:
    CurlyBracketOpen = '{'
    CurlyBracketClose = '}'
    Escape = '\\'
    Equals = '='
    SquareBracketOpen = '['
    SquareBracketClose = ']'
    Asterisk = '*'
    Hash = '#'
    Dollar = '$'
    Dash = '-'
    Dot = '.'
    Slash = '/'
    Colon = ':'
    Excl = '!'
    At = '@'
    Underscore = '_'
    RoundBracketOpen = '('
    RoundBracketClose = ')'
    Sibling = '+'
    Child = '>'
    Climb = '^'
    SingleQuote = "'"
    DoubleQuote = '"'

def escaped(scanner):
    if scanner.eat(Chars.Escape):
        scanner.start = scanner.pos
        if not scanner.eof():
            scanner.pos += 1

        return True

    return False
