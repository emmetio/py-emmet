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
        if scanner.eof():
            scanner.start = scanner.pos - 1
        else:
            scanner.start = scanner.pos
            scanner.pos += 1

        return True

    return False
