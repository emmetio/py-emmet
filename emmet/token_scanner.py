class TokenScanner:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.start = 0
        self.pos = 0
        self.size = len(tokens)

    def peek(self):
        return self.tokens[self.pos] if self.readable() else None

    def next(self):
        t = self.peek()
        self.pos += 1
        return t

    def slice(self, start: int=None, end: int=None):
        if start is None: start = self.start
        if end is None: end = self.pos
        return self.tokens[start:end]

    def readable(self):
        return self.pos < self.size

    def consume(self, test: callable):
        token = self.peek()
        if token and test(token):
            self.pos += 1
            return True

        return False

    def consume_while(self, test: callable):
        start = self.pos
        while self.consume(test):
            pass
        return self.pos != start

    def error(self, message: str, token=None):
        if token is None:
            token = self.peek()
        pos = None
        if token and token.start is not None:
            pos = token.start
            message += ' at %d' % pos
        return TokenScannerException(message, pos)

class TokenScannerException(Exception):
    def __init__(self, message: str, pos: int):
        super(TokenScannerException, self).__init__(message)
        self.message = message
        self.pos = pos
