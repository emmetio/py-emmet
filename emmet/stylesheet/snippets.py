import re

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

re_property = re.compile(r'^([a-z-]+)(?:\s*:\s*([^\n\r;]+?);*)?$')
opt = { 'value': True }

def create_snippet(key: str, value: str):
    "Creates structure for holding resolved CSS snippet"
    # A snippet could be a raw text snippet (e.g. arbitrary text string) or a
    # CSS property with possible values separated by `|`.
    # In latter case, we have to parse snippet as CSS abbreviation
    m = re_property.match(value)
    if m:
        keywords = {}
        parsed = [parse_value(v) for v in m[2].split('|')] if m[2] else []

        for item in parsed:
            for css_val in item:
                collect_keywords(css_val, keywords)

        return CSSSnippetProperty(key, m[1], parsed, keywords)

    return CSSSnippetRaw(key, value)
