class BackwardScanner:
    __slots__ = ('text', 'start', 'pos')

    def __init__(self, text: str, start=0):
        self.text = text
        "Text to scan"

        self.start = start
        "Left bound till given text must be scanned"

        self.pos = len(text)
        "Current scanner position"

    def sol(self):
        "Check if given scanner position is at start of scanned text"
        return self.pos == self.start

    def peek(self, offset=0):
        "“Peeks” character code an current scanner location without advancing it"
        pos = self.pos - 1 + offset
        return self.text[pos] if 0 <= pos < len(self.text) else ''

    def previous(self):
        "Returns current character code and moves character location one symbol back"
        if not self.sol():
            self.pos -= 1
            return self.text[self.pos]

    def consume(self, match: callable):
        "Consumes current character code if it matches given `match` code or function"
        if self.sol():
            return False

        ok = match(self.peek()) if callable(match) else match == self.peek()
        if ok: self.pos -= 1

        return bool(ok)

    def consume_while(self, match: callable):
        start = self.pos
        while self.consume(match): pass
        return self.pos < start
