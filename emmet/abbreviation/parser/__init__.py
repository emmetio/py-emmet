from ...token_scanner import TokenScanner, TokenScannerException
from ..tokenizer import tokens

class TokenAttribute:
    __slots__ = ('name', 'value', 'expression')

    def __init__(self, name: list=None, value: list=None, expression: bool=False):
        self.name = name
        self.value = value
        self.expression = expression


class TokenElement:
    __slots__ = ('type', 'name', 'attributes', 'value', 'repeat', 'self_close', 'elements')

    def __init__(self):
        self.type = 'TokenElement'
        self.name = None
        self.attributes = None
        self.value = None
        self.repeat = None
        self.self_close = False
        self.elements = []


class TokenGroup:
    __slots__ = ('type', 'elements', 'repeat')

    def __init__(self):
        self.type = 'TokenGroup'
        self.elements = []
        self.repeat = None


def parse(abbr: list, options: dict={}):
    scanner = TokenScanner(abbr)
    result = statements(scanner, options)
    if scanner.readable():
        raise scanner.error('Unexpected character')

    return result


def statements(scanner: TokenScanner, options: dict):
    result = TokenGroup()
    ctx = result
    node = None
    stack = []

    while scanner.readable():
        node = element(scanner, options) or group(scanner, options)
        if node:
            ctx.elements.append(node)
            if scanner.consume(is_child_operator):
                stack.append(ctx)
                ctx = node
            elif scanner.consume(is_sibling_operator):
                continue
            elif is_climb_operator(scanner.peek()):
                while scanner.consume(is_climb_operator):
                    if len(stack): ctx = stack.pop()
        else:
            break

    return result


def group(scanner: TokenScanner, options: dict):
    "Consumes group from given scanner"
    if scanner.consume(is_group_start):
        result = statements(scanner, options)
        token = scanner.next()
        if is_bracket(token, 'group', False):
            result.repeat = repeater(scanner)
        return result


def element(scanner: TokenScanner, options: dict):
    "Consumes single element from given scanner"
    attr = None
    elem = TokenElement()

    if element_name(scanner, options):
        elem.name = scanner.slice()

    while scanner.readable():
        scanner.start = scanner.pos
        if not elem.repeat and not is_empty(elem) and scanner.consume(is_repeater):
            elem.repeat = scanner.tokens[scanner.pos - 1]
        elif elem.value is None and text(scanner):
            elem.value = get_text(scanner)
        else:
            attr = short_attribute(scanner, 'id', options) or short_attribute(scanner, 'class', options) or attribute_set(scanner)
            if attr is not None:
                if not isinstance(attr, list):
                    attr = [attr]
                if elem.attributes is None:
                    elem.attributes = attr[:]
                else:
                    elem.attributes += attr
            else:
                if not is_empty(elem) and scanner.consume(is_close_operator):
                    elem.self_close = True
                    if not elem.repeat and scanner.consume(is_repeater):
                        elem.repeat = scanner.tokens[scanner.pos - 1]
                break

    return elem if not is_empty(elem) else None


def attribute_set(scanner: TokenScanner):
    "Consumes attribute set from given scanner"
    if scanner.consume(is_attribute_set_start):
        attributes = []
        attr = None

        while scanner.readable():
            attr = attribute(scanner)
            if attr:
                attributes.append(attr)
            elif scanner.consume(is_attribute_set_end):
                break
            elif not scanner.consume(is_white_space):
                raise scanner.error('Unexpected "%s" token' % scanner.peek().type)

        return attributes


def short_attribute(scanner: TokenScanner, attr_type: str, options: dict):
    "Consumes attribute shorthand (class or id) from given scanner"
    if is_operator(scanner.peek(), attr_type):
        scanner.pos += 1
        attr = TokenAttribute([create_literal(attr_type)])

        # Consume expression after shorthand start for React-like components
        if options.get('jsx') and text(scanner):
            attr.value = get_text(scanner)
            attr.expression = True
        else:
            attr.value = scanner.slice() if literal(scanner) else None

        return attr


def attribute(scanner: TokenScanner):
    if quoted(scanner):
        # Consumed quoted value: it’s a value for default attribute
        return TokenAttribute(value=scanner.slice())

    if literal(scanner, True):
        name = scanner.slice()
        value = None
        if scanner.consume(is_equals) and (quoted(scanner) or literal(scanner, True)):
            value = scanner.slice()
        return TokenAttribute(name, value)


def repeater(scanner: TokenScanner):
    if is_repeater(scanner.peek()):
        return scanner.next()


def quoted(scanner: TokenScanner):
    "Consumes quoted value from given scanner, if possible"
    start = scanner.pos
    quote = scanner.peek()
    if is_quote(quote):
        scanner.pos += 1
        while scanner.readable():
            if is_quote(scanner.next(), quote.single):
                scanner.start = start
                return True

        raise scanner.error('Unclosed quote', quote)

    return False


def literal(scanner: TokenScanner, allow_brackets=False):
    "Consumes literal (unquoted value) from given scanner"
    start = scanner.pos
    brackets = {
        'attribute': 0,
        'expression': 0,
        'group': 0
    }

    while scanner.readable():
        token = scanner.peek()
        if brackets['expression']:
            # If we’re inside expression, we should consume all content in it
            if is_bracket(token, 'expression'):
                brackets[token.context] += 1 if token.open else -1
        elif is_quote(token) or is_operator(token) or is_white_space(token) or is_repeater(token):
            break
        elif is_bracket(token):
            if not allow_brackets: break

            if token.open:
                brackets[token.context] += 1
            elif not brackets[token.context]:
                # Stop if found unmatched closing brace: it must be handled
                # by parent consumer
                break
            else:
                brackets[token.context] -= 1

        scanner.pos += 1

    if start != scanner.pos:
        scanner.start = start
        return True

    return False


def element_name(scanner: TokenScanner, options: dict):
    "Consumes element name from given scanner"
    start = scanner.pos

    if options.get('jsx') and scanner.consume(is_capitalized_literal):
        # Check for edge case: consume immediate capitalized class names
        # for React-like components, e.g. `Foo.Bar.Baz`
        while scanner.readable():
            pos = scanner.pos
            if not scanner.consume(is_class_name_operator) or not scanner.consume(is_capitalized_literal):
                scanner.pos = pos
                break

    while scanner.readable() and scanner.consume(is_element_name):
        pass

    if scanner.pos != start:
        scanner.start = start
        return True

    return False


def text(scanner: TokenScanner):
    "Consumes text value from given scanner"
    start = scanner.pos
    if scanner.consume(is_text_start):
        brackets = 0
        while scanner.readable():
            token = scanner.next()
            if is_bracket(token, 'expression'):
                if token.open:
                    brackets += 1
                elif not brackets:
                    break
                else:
                    brackets -= 1

        scanner.start = start
        return True

    return False


def get_text(scanner: TokenScanner):
    start = scanner.start
    end = scanner.pos
    if is_bracket(scanner.tokens[start], 'expression', True):
        start += 1

    if is_bracket(scanner.tokens[end - 1], 'expression', False):
        end -= 1

    return scanner.slice(start, end)


def is_bracket(token: tokens.Bracket, context: str=None, is_open=None):
    return isinstance(token, tokens.Bracket) and \
        (context is None or token.context == context) and \
        (is_open is None or token.open == is_open)


def is_operator(token: tokens.Operator, op_type: str=None):
    return isinstance(token, tokens.Operator) and (not op_type or token.operator == op_type)


def is_quote(token: tokens.Quote, is_single=None):
    return isinstance(token, tokens.Quote) and (is_single is None or token.single == is_single)


def is_white_space(token: tokens.WhiteSpace):
    return isinstance(token, tokens.WhiteSpace)


def is_equals(token: tokens.Operator):
    return is_operator(token, 'equal')


def is_repeater(token: tokens.Repeater):
    return isinstance(token, tokens.Repeater)


def is_literal(token: tokens.Literal):
    return isinstance(token, tokens.Literal)


def is_capitalized_literal(token: tokens.Literal):
    if is_literal(token):
        return 'A' <= token.value[0] <= 'Z'

    return False


def is_element_name(token: tokens.Literal):
    return is_literal(token) or isinstance(token, tokens.RepeaterNumber) or isinstance(token, tokens.RepeaterPlaceholder)


def is_class_name_operator(token: tokens.Operator):
    return is_operator(token, 'class')


def is_attribute_set_start(token: tokens.Bracket):
    return is_bracket(token, 'attribute', True)


def is_attribute_set_end(token: tokens.Bracket):
    return is_bracket(token, 'attribute', False)


def is_text_start(token: tokens.Bracket):
    return is_bracket(token, 'expression', True)


def is_group_start(token: tokens.Bracket):
    return is_bracket(token, 'group', True)


def create_literal(value: str):
    return tokens.Literal(value)


def is_empty(elem: TokenElement):
    return elem.name is None and elem.value is None and elem.attributes is None


def is_child_operator(token: tokens.Operator):
    return is_operator(token, 'child')


def is_sibling_operator(token: tokens.Operator):
    return is_operator(token, 'sibling')


def is_climb_operator(token: tokens.Operator):
    return is_operator(token, 'climb')


def is_close_operator(token: tokens.Operator):
    return is_operator(token, 'close')
