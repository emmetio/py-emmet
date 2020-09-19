import re
from .parser import TokenGroup, TokenElement, TokenAttribute, is_quote, is_bracket
from .tokenizer import tokens
from .stringify import stringify

re_url = re.compile(r'(https?:|ftp:|file:)?\/\/|(www|ftp)\.')
re_email = re.compile(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,5}$')

class ConvertState:
    __slots__ = ('inserted', 'text', 'repeat_guard', 'repeaters', 'variables',
                 '_text_inserted', 'clean_text')

    def __init__(self, text: str = None, variables={}, max_repeat=None):
        self.inserted = False
        self.text = text

        if isinstance(text, list):
            self.clean_text = [l for l in text if l.strip()]
        else:
            self.clean_text = text

        self.repeat_guard = max_repeat if max_repeat is not None else 1000000
        self.variables = variables
        self.repeaters = []
        self._text_inserted = False

    def get_text(self, pos: int):
        self._text_inserted = True
        if isinstance(self.text, list):
            if pos is not None and pos >= 0 and pos < len(self.clean_text):
                return self.clean_text[pos].strip()

            value = self.text[pos] if pos is not None else '\n'.join(self.text)
        else:
            value = self.text or ''
        return value

    def get_variable(self, name: str):
        return self.variables.get(name) if self.variables else name


class Abbreviation:
    __slots__ = ('type', 'children')

    def __init__(self):
        self.type = 'Abbreviation'
        self.children = []

class AbbreviationNode:
    __slots__ = ('type', 'name', 'value', 'repeat', 'attributes', 'children', 'self_closing')

    def __init__(self, node: TokenElement, state: ConvertState):
        self.type = 'AbbreviationNode'
        self.name = stringify_name(node.name, state) if node.name else None
        self.value = stringify_value(node.value, state) if node.value else None
        self.attributes = None
        self.children = []
        self.repeat = clone_repeater(node.repeat) if node.repeat else None
        self.self_closing = node.self_close
        "Indicates current element is self-closing, e.g. should not contain closing pair"


class AbbreviationAttribute:
    __slots__ = ('name', 'value', 'value_type', 'boolean', 'implied')

    def __init__(self, name: str, value: list, value_type='raw', boolean=False, implied=False):
        self.name = name
        self.value = value
        self.value_type = value_type
        "Indicates type of value stored in `.value` property"

        self.boolean = boolean
        "Attribute is boolean (e.g.name equals value)"

        self.implied = implied
        "Attribute is implied (e.g.must be outputted only if contains non-null value)"

    def copy(self):
        return AbbreviationAttribute(self.name, self.value, self.value_type, self.boolean, self.implied)


def convert(abbr: TokenGroup, params={}):
    "Converts given token-based abbreviation into simplified and unrolled node-based abbreviation"
    text = params.get('text')
    options = params.get('options') or {}
    state = ConvertState(text, params.get('variables'), params.get('max_repeat'))
    result = Abbreviation()
    result.children = convert_group(abbr, state)

    if text is not None and not state._text_inserted:
        # Text given but no implicitly repeated elements: insert it into deepest child
        deepest = deepest_node(result.children[-1])
        if deepest:
            tx = '\n'.join(text).strip() if isinstance(text, list) else text.strip() or ''
            insert_text(deepest, tx)
            if deepest.name == 'a' and options.get('markup.href'):
                # Automatically update value of `<a>` element if inserting URL or email
                insert_href(deepest, tx)


    return result


def convert_statement(node: TokenElement, state: ConvertState):
    result = []

    if node.repeat:
        # Node is repeated: we should create copies of given node
        # and supply context token with actual repeater state
        original = node.repeat
        repeat = clone_repeater(node.repeat)

        if repeat.implicit and isinstance(state.text, list):
            repeat.count = len(state.clean_text)
        else:
            repeat.count = repeat.count or 1

        state.repeaters.append(repeat)
        i = 0

        while i < repeat.count:
            repeat.value = i
            node.repeat = repeat
            items = convert_group(node, state) if is_group(node) else convert_element(node, state)

            if repeat.implicit and not state.inserted:
                # It’s an implicit repeater but no repeater placeholders found inside,
                # we should insert text into deepest node
                target = items[-1]
                deepest = deepest_node(target) if target else None
                if deepest:
                    insert_text(deepest, state.get_text(repeat.value))

            result += items

            # We should output at least one repeated item even if it’s reached
            # repeat limit
            state.repeat_guard -= 1
            if state.repeat_guard <= 0: break

            i += 1

        state.repeaters.pop()
        node.repeat = original

        if repeat.implicit: state.inserted = True
    else:
        result += convert_group(node, state) if is_group(node) else convert_element(node, state)

    return result


def convert_element(node: TokenElement, state: ConvertState):
    elem = AbbreviationNode(node, state)
    result = [elem]

    for child in node.elements:
        elem.children += convert_statement(child, state)

    if node.attributes:
        elem.attributes = [convert_attribute(attr, state) for attr in node.attributes]

    # In case if current node is a text-only snippet without fields, we should
    # put all children as siblings
    if not elem.name and elem.attributes is None and elem.value and not some(elem.value, is_field):
        result += elem.children
        elem.children = []

    return result


def convert_group(node: TokenGroup, state: ConvertState):
    result = []
    for child in node.elements:
        result += convert_statement(child, state)

    if node.repeat:
        result = attach_repeater(result, node.repeat)

    return result


def convert_attribute(node: TokenAttribute, state: ConvertState):
    attr = create_attribute(node, state)

    if node.value:
        tokens = node.value[:]

        if is_quote(tokens[0]):
            # It’s a quoted value: remove quotes from output but mark attribute
            # value as quoted
            quote = tokens.pop(0)

            if len(tokens) and tokens[-1].type == quote.type:
                tokens.pop()

            attr.value_type = 'singleQuote' if quote.single else 'doubleQuote'
        elif is_bracket(tokens[0], 'expression', True):
            # Value is expression: remove brackets but mark value type
            attr.value_type = 'expression'
            tokens.pop(0)

            if tokens and is_bracket(tokens[-1], 'expression', False):
                tokens.pop()

        attr.value = stringify_value(tokens, state)

    return attr


def create_attribute(node: TokenAttribute, state: ConvertState):
    name = stringify_name(node.name, state) if node.name else None
    value_type = 'expression' if node.expression else 'raw'
    boolean = False
    implied = False
    if name:
        if name[-1] == '.':
            boolean = True
            name = name[0:-1]
        if name[0] == '!':
            implied = True
            name = name[1:]
    return AbbreviationAttribute(name, None, value_type, boolean, implied)

def stringify_name(tokens: list, state: ConvertState):
    "Converts given token list to string"
    return ''.join([stringify(token, state) for token in tokens])


def stringify_value(token_list: list, state: ConvertState):
    "Converts given token list to value list"
    result = []
    accum = []

    for token in token_list:
        if is_field(token):
            # We should keep original fields in output since some editors has their
            # own syntax for field or doesn’t support fields at all so we should
            # capture actual field location in output stream
            if accum:
                result.append(''.join(accum))
                accum = []

            result.append(token)
        else:
            accum.append(stringify(token, state))


    if accum:
        result.append(''.join(accum))

    return result


def is_group(node):
    return isinstance(node, TokenGroup)


def is_field(token):
    return isinstance(token, tokens.Field) and token.index is not None


def deepest_node(node: AbbreviationNode):
    return deepest_node(node.children[-1]) if node.children else node


def insert_text(node: AbbreviationNode, text: str):
    if node.value:
        last_token = node.value[-1]
        if isinstance(last_token, str):
            node.value[-1] += text
        else:
            node.value.append(text)
    else:
        node.value = [text]


def insert_href(node: AbbreviationNode, text: str):
    href = None
    if re_url.match(text):
        href = text
        if not re.match(r'\w+:', href) and not href.startswith('//'):
            href = 'http://%s' % href
    elif re_email.match(text):
        href = 'mailto:%s' % text

    if href:
        href_attr = None
        if node.attributes:
            for attr in node.attributes:
                if attr.name == 'href':
                    href_attr = attr
                    break

        if not href_attr:
            node.attributes = [AbbreviationAttribute('href', href)]
        elif not href_attr.value:
            href_attr.value = href


def attach_repeater(items: list, repeater: tokens.Repeater):
    for item in items:
        if not item.repeat:
            item.repeat = clone_repeater(repeater)

    return items


def clone_repeater(repeater: tokens.Repeater):
    return tokens.Repeater(repeater.count, repeater.value, repeater.implicit)

def some(items: list, fn: callable):
    for item in items:
        if fn(item): return True
    return False
