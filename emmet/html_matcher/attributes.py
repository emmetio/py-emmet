from ..scanner import Scanner
from ..scanner_utils import eat_quoted, is_space
from .utils import Chars, ident, consume_paired, scan_opt, is_unquoted, get_unquoted_value


class AttributeToken:
    __slots__ = ('name', 'value', 'name_start', 'name_end', 'value_start', 'value_end')

    def __init__(self, name: str, name_start: int, name_end: int, value: str=None, value_start: int=None, value_end: int=None):
        self.name = name
        self.name_start = name_start
        self.name_end = name_end
        self.value = value
        self.value_start = value_start
        self.value_end = value_end

    def to_json(self):
        json = {
            'name': self.name,
            'name_start': self.name_start,
            'name_end': self.name_end
        }

        if self.value is not None:
            json['value'] = self.value
            json['value_start'] = self.value_start
            json['value_end'] = self.value_end

        return json


def attributes(src: str, name: str=None):
    """
    Parses given string as list of HTML attributes.
    :param src A fragment to parse. If `name` argument is provided, it must be an
    opening tag (`<a foo="bar">`), otherwise it should be a fragment between element
    name and tag closing angle (`foo="bar"`)
    :param name Tag name
    """
    result = []
    start = 0
    end = len(src)
    if name:
        start = len(name) + 1
        end -= 2 if src.endswith('/>') else 1

    scanner = Scanner(src, start, end)

    while not scanner.eof():
        scanner.eat_while(is_space)
        if attribute_name(scanner):
            token = AttributeToken(scanner.current(), scanner.start, scanner.pos)

            if scanner.eat(Chars.Equals) and attribute_value(scanner):
                token.value = scanner.current()
                token.value_start = scanner.start
                token.value_end = scanner.pos

            result.append(token)
        else:
            # Do not break on invalid attributes: we are not validating parser
            scanner.pos += 1

    return result


def attribute_name(scanner: Scanner):
    "Consumes attribute name from given scanner context"
    start = scanner.pos
    if scanner.eat(Chars.Asterisk) or scanner.eat(Chars.Hash):
        # Angular-style directives: `<section *ngIf="showSection">`, `<video #movieplayer ...>`
        ident(scanner)
        scanner.start = start
        return True

    # Attribute name could be a regular name or expression:
    # React-style – `<div {...props}>`
    # Angular-style – `<div [ng-for]>` or `<div *ng-for>`
    return consume_paired(scanner) or ident(scanner)

def attribute_value(scanner: Scanner):
    "Consumes attribute value"
    # Supported attribute values are quoted, React-like expressions (`{foo}`)
    # or unquoted literals
    return eat_quoted(scanner, scan_opt) or consume_paired(scanner) or unquoted(scanner)


def get_attribute_value(attrs: list, name: str):
    "Returns clean (unquoted) value of `name` attribute"
    for attr in attrs:
        if attr.name == name:
            return attr.value and get_unquoted_value(attr.value)


def unquoted(scanner: Scanner):
    "Consumes unquoted value"
    start = scanner.pos
    if scanner.eat_while(is_unquoted):
        scanner.start = start
        return True

    return False
