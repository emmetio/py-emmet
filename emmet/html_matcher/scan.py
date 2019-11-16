from ..scanner import Scanner
from ..scanner_utils import is_space, eat_quoted
from .utils import ElementType, Chars, consume_array, is_terminator, consume_section, ident
from .attributes import attributes, attribute_name, attribute_value, get_attribute_value

cdata_open = '<![CDATA['
cdata_close = ']]>'
comment_open = '<!--'
comment_close = '-->'
pi_start = '<?'
pi_end = '?>'

def scan(source: str, callback: callable, special: dict=None):
    """
    Performs fast scan of given source code: for each tag found it invokes callback
    with tag name, its type (open, close, self-close) and range in original source.
    Unlike regular scanner, fast scanner doesn’t provide info about attributes to
    reduce object allocations hence increase performance.
    If `callback` returns `false`, scanner stops parsing.
    :param special List of “special” HTML tags which should be ignored. Most likely
    it’s a "script" and "style" tags.
    """
    scanner = Scanner(source)
    found = False

    while not scanner.eof():
        if cdata(scanner) or comment(scanner) or processing_instruction(scanner):
            continue

        start = scanner.pos
        if scanner.eat(Chars.LeftAngle):
            # Maybe a tag name?
            elem_type = ElementType.Close if scanner.eat(Chars.Slash) else ElementType.Open
            name_start = scanner.pos

            if ident(scanner):
                # Consumed tag name
                name_end = scanner.pos
                if elem_type != ElementType.Close:
                    skip_attributes(scanner)
                    scanner.eat_while(is_space)
                    if scanner.eat(Chars.Slash):
                        elem_type = ElementType.SelfClose

                if scanner.eat(Chars.RightAngle):
                    # Tag properly closed
                    name = scanner.substring(name_start, name_end)
                    if callback(name, elem_type, start, scanner.pos) is False:
                        break

                    if elem_type == ElementType.Open and special and is_special(special, name, source, start, scanner.pos):
                        # Found opening tag of special element: we should skip
                        # scanner contents until we find closing tag
                        found = False
                        while not scanner.eof():
                            if consume_closing(scanner, name):
                                found = True
                                break

                            scanner.pos += 1

                        if found and callback(name, ElementType.Close, scanner.start, scanner.pos) is False:
                            break
        else:
            scanner.pos += 1


def skip_attributes(scanner: Scanner):
    "Skips attributes in current tag context"
    while not scanner.eof():
        scanner.eat_while(is_space)
        if attribute_name(scanner):
            if scanner.eat(Chars.Equals):
                attribute_value(scanner)
        elif is_terminator(scanner.peek()):
            break
        else:
            scanner.pos += 1

def consume_closing(scanner: Scanner, name: str):
    "Consumes closing tag with given name from scanner"
    start = scanner.pos
    if scanner.eat(Chars.LeftAngle) and \
        scanner.eat(Chars.Slash) and \
        consume_array(scanner, name) and \
        scanner.eat(Chars.RightAngle):
        scanner.start = start
        return True

    scanner.pos = start
    return False


def cdata(scanner: Scanner):
    "Consumes CDATA from given scanner"
    global cdata_open, cdata_close
    return consume_section(scanner, cdata_open, cdata_close, True)


def comment(scanner: Scanner):
    "Consumes comments from given scanner"
    global comment_open, comment_close
    return consume_section(scanner, comment_open, comment_close, True)


def processing_instruction(scanner: Scanner):
    "Consumes processing instruction from given scanner"
    global pi_start, pi_end
    if consume_array(scanner, pi_start):
        while not scanner.eof():
            if consume_array(scanner, pi_end):
                break

            if not eat_quoted(scanner): scanner.pos += 1

        return True

    return False


def is_special(special: dict, name: str, source: str, start: int, end: int):
    "Check if given tag name should be considered as special"
    if name in special:
        type_values = special[name]
        if not isinstance(type_values, list):
            return True

        attrs = attributes(source[start + len(name) + 1:end - 1])
        value = get_attribute_value(attrs, 'type') or ''
        return value in type_values

    return False
