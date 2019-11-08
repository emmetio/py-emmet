class Scanner:
    __slots__ = ('string', 'pos', 'start', 'end')

    def __init__(self, source: str, start=0, end=None):
        self.string = source
        self.pos = self.start = start
        self.end = len(source) if end is None else end

    def eof(self):
        "Returns true only if the stream is at the end of the file."
        return self.pos >= self.end

    def limit(self, start=0, end: int=None):
        """
        Creates a new stream instance which is limited to given `start` and `end`
        range. E.g. its `eof()` method will look at `end` property, not actual
        stream end
        """
        return Scanner(self.string, start, end)

    def peek(self):
        "Returns the next character in the stream without advancing it."
        return self.string[self.pos] if self.pos < self.end else ''

    def next(self):
        """
        Returns the next character in the stream and advances it.
        Returns `None` when no more characters left
        """
        if self.pos < self.end:
            ch = self.string[self.pos]
            self.pos += 1
            return ch

    def eat(self, match):
        """
        `match` can be a character or a function that takes a character
        and returns a boolean. If the next character in the stream 'matches'
        the given argument, it is consumed and returned.
        Otherwise, `False` is returned.
        """
        ch = self.peek()
        ok = match(ch) if callable(match) else match == ch
        if ok:
            self.pos += 1

        return ok

    def eat_while(self, match):
        """
        Repeatedly calls `eat` with the given argument, until it
        fails. Returns `True` if any characters were eaten.
        """
        start = self.pos
        while self.pos < self.end and self.eat(match):
            pass
        return self.pos != start

    def back_up(self, n: int = 1):
        """
        Backs up the stream n characters. Backing it up further than the
        start of the current token will cause things to break, so be careful.
        """
        self.pos -= n

    def current(self):
        "Get the string between the start of the current token and the current stream position."
        return self.substring(self.start, self.pos)

    def substring(self, start: int, end: int = None):
        "Returns substring for given range"
        if end is None:
            end = self.end
        return self.string[start:end]

    def error(self, message: str, pos: int = None):
        "Creates error object with current stream state"
        if pos is None:
            pos = self.pos
        return ScannerException("%s at %d" % (message, pos + 1), pos, self.string)


class ScannerException(Exception):
    def __init__(self, message: str, pos: int, source: str):
        super(ScannerException, self).__init__()
        self.message = message
        self.string = source
        self.pos = pos
