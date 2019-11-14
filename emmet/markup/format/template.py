class TemplatePlaceholder:
    __slots__ = ('before', 'after', 'name')

    def __init__(self, before: str, after: str, name: str):
        self.before = before
        self.after = after
        self.name = name


class TokenScanner:
    __slots__ = ('text', 'pos')

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def peek(self, pos: int=None):
        if pos is None: pos = self.pos
        return self.text[pos] if pos < len(self.text) else ''


def template(text: str):
    """
    Splits given string into template tokens.
    Template is a string which contains placeholders which are uppercase names
    between `[` and `]`, for example: `[PLACEHOLDER]`.
    Unlike other templates, a placeholder may contain extra characters before and
    after name: `[%PLACEHOLDER.]`. If data for `PLACEHOLDER` is defined, it will
    be outputted with with these extra character, otherwise will be completely omitted.
    """
    tokens = []
    scanner = TokenScanner(text)
    offset = scanner.pos
    pos = scanner.pos

    while scanner.pos < len(scanner.text):
        pos = scanner.pos
        placeholder = consume_placeholder(scanner)
        if placeholder:
            if offset != scanner.pos:
                tokens.append(text[offset:pos])
            tokens.append(placeholder)
            offset = scanner.pos
        else:
            scanner.pos += 1

    if offset != scanner.pos:
        tokens.append(text[offset:])

    return tokens

def consume_placeholder(scanner: TokenScanner):
    if scanner.peek() == '[':
        scanner.pos += 1
        start = scanner.pos
        name_pos = start
        after_pos = start
        stack = 1

        while scanner.pos < len(scanner.text):
            ch = scanner.peek()
            if is_token_start(ch):
                name_pos = scanner.pos
                while is_token(scanner.peek()):
                    scanner.pos += 1
                after_pos = scanner.pos
            else:
                if ch == '[':
                    stack += 1
                elif ch == ']':
                    stack -= 1
                    if stack == 0:
                        pos = scanner.pos
                        scanner.pos += 1
                        return TemplatePlaceholder(
                            scanner.text[start:name_pos],
                            scanner.text[after_pos:pos],
                            scanner.text[name_pos:after_pos])

                scanner.pos += 1


def is_token_start(ch: str):
    return 'A' <= ch <= 'Z'


def is_token(ch: str):
    return is_token_start(ch) or ch == '_' or ch == '-' or '0' <= ch <= '9'
