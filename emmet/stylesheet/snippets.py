import re
import collections
from ..css_abbreviation import parse, tokens, CSSValue, FunctionCall


re_property = re.compile(r'^([a-z-]+)(?:\s*:\s*([^\n\r;]+?);*)?$')
opt = {'value': True}


class CSSSnippetType:
    Raw = 'Raw'
    Property = 'Property'


class CSSSnippetRaw:
    __slots__ = ('type', 'key', 'value')

    def __init__(self, key: str, value: str):
        self.type = CSSSnippetType.Raw
        self.key = key
        self.value = value


class CSSSnippetProperty:
    __slots__ = ('type', 'key', 'value', 'property', 'keywords', 'dependencies')

    def __init__(self, key: str, prop: str, value: list, keywords: dict):
        self.type = CSSSnippetType.Property
        self.key = key
        self.property = prop
        self.value = value
        self.keywords = keywords
        self.dependencies = []


def create_snippet(key: str, value: str):
    "Creates structure for holding resolved CSS snippet"
    # A snippet could be a raw text snippet (e.g. arbitrary text string) or a
    # CSS property with possible values separated by `|`.
    # In latter case, we have to parse snippet as CSS abbreviation
    m = re_property.match(value)
    if m:
        keywords = collections.OrderedDict()
        parsed = [parse_value(v) for v in m.group(2).split('|')] if m.group(2) else []

        for item in parsed:
            for css_val in item:
                collect_keywords(css_val, keywords)

        return CSSSnippetProperty(key, m.group(1), parsed, keywords)

    return CSSSnippetRaw(key, value)


def nest(snippets: list):
    """
    Nests more specific CSS properties into shorthand ones, e.g.
    `background-position-x` -> `background-position` -> `background`
    """
    snippets = snippets[:]
    snippets.sort(key=lambda x: x.key)
    stack = []

    # For sorted list of CSS properties, create dependency graph where each
    # shorthand property contains its more specific one, e.g.
    # background -> background-position -> background-position-x
    for cur in filter(is_property, snippets):
        # Check if current property belongs to one from parent stack.
        # Since `snippets` array is sorted, items are perfectly aligned
        # from shorthands to more specific variants
        while stack:
            prev = stack[-1]

            if cur.property.startswith(prev.property) and \
                len(cur.property) > len(prev.property) and \
                cur.property[len(prev.property)] == '-':
                prev.dependencies.append(cur)
                stack.append(cur)
                break

            stack.pop()

        if not stack:
            stack.append(cur)

    return snippets


def parse_value(value: str):
    global opt
    return parse(value.strip(), opt)[0].value


def is_property(snippet):
    return isinstance(snippet, CSSSnippetProperty)


def collect_keywords(css_val: CSSValue, dest: dict):
    for v in css_val.value:
        if isinstance(v, tokens.Literal):
            dest[v.value] = v
        elif isinstance(v, FunctionCall):
            dest[v.name] = v
        elif isinstance(v, tokens.Field):
            # Create literal from field, if available
            value = v.name.strip()
            if value:
                dest[value] = tokens.Literal(value)
