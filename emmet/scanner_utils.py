nbsp = chr(160)

def is_number(ch: str):
    "Check if given code is a number"
    return ch.isdecimal()

def is_alpha(ch: str):
    "Check if given character code is alpha code (letter through A to Z)"
    return 'a' <= ch <= 'z' or 'A' <= ch <= 'Z'

def is_alpha_numeric(ch: str):
    "Check if given character code is alpha-numeric (letter through A to Z or number)"
    return is_number(ch) or is_alpha(ch)

def is_alpha_numeric_word(ch: str):
    return is_number(ch) or is_alpha_word(ch)

def is_alpha_word(ch: str):
    return ch == '_' or is_alpha(ch)

def is_white_space(ch: str):
    "Check if given character code is a white-space character: a space character without line breaks"
    return ch == ' ' or ch == '\t' or ch == nbsp

def is_space(ch: str):
    "Check if given character code is a space character"
    return is_white_space(ch) or ch == '\n' or ch == '\r'

def is_quote(ch: str):
    "Check if given character code is a quote character"
    return ch == '"' or ch == "'"

def eat_quoted(scanner, options={}):
    """
    Consumes 'single' or "double"-quoted string from given string, if possible
    Returns `True` if quoted string was consumed. The contents of quoted string
    will be available as `scanner.current()`
    """
    options = create_options(options)
    start = scanner.pos
    quote = scanner.peek()

    if scanner.eat(is_quote):
        while not scanner.eof():
            if scanner.eat(quote):
                scanner.start = start
                return True
            scanner.eat(options['escape'])
            scanner.pos += 1

        # If we’re here then stream wasn’t properly consumed.
        # Revert stream and decide what to do
        scanner.pos = start

        if options['throws']:
            raise scanner.error('Unable to consume quoted string')

    return False

def eat_pair(scanner, open_ch: str, close_ch: str, options={}):
    options = create_options(options)
    start = scanner.pos

    if scanner.eat(open_ch):
        stack = 1

        while not scanner.eof():
            if eat_quoted(scanner, options): continue

            ch = scanner.next()
            if ch == open_ch:
                stack += 1
            elif ch == close_ch:
                stack -= 1
                if not stack:
                    scanner.start = start
                    return True
            elif ch == options['escape']:
                scanner.pos += 1

        # If we’re here then paired character can’t be consumed
        scanner.pos = start

        if options['throws']:
            raise scanner.error('Unable to find matching pair for %s' % open_ch)

    return False

def create_options(opt={}):
    options = {
        'escape': '\\',
        'throws': False
    }

    options.update(opt)
    return options
