import re
from ..css_abbreviation import parse as abbreviation, tokens, CSSValue, CSSProperty, FunctionCall
from ..config import Config
from ..list_utils import some, get_item
from .snippets import create_snippet, nest, CSSSnippetProperty, CSSSnippetRaw, CSSSnippetType
from .score import calculate_score
from .color import color
from .format import stringify
from .scope import CSSAbbreviationScope

gradient_name = 'lg'


def parse(abbr: str, config: Config):
    """
    Parses given Emmet abbreviation into a final abbreviation tree with all
    required transformations applied
    """
    snippets = config.cache.get('stylesheet_snippets') if config.cache is not None else None

    if snippets is None:
        snippets = convert_snippets(config.snippets)
        if config.cache is not None:
            config.cache['stylesheet_snippets'] = snippets

    if isinstance(abbr, str):
        abbr = abbreviation(abbr, { 'value': is_value_scope(config) })

    filtered_snippets = get_snippets_for_scope(snippets, config)

    for node in abbr:
        resolve_node(node, filtered_snippets, config)

    return abbr


def convert_snippets(snippets: dict):
    "Converts given raw snippets into internal snippets representation"
    result = [create_snippet(k, v) for (k, v) in snippets.items()]
    return nest(result)


def resolve_node(node: CSSProperty, snippets: list, config: Config):
    """
    Resolves given node: finds matched CSS snippets using fuzzy match and resolves
    keyword aliases from node value
    """
    if not resolve_gradient(node, config):
        score = config.options.get('stylesheet.fuzzySearchMinScore', 0)
        if is_value_scope(config):
            # Resolve as value of given CSS property
            prop_name = config.context.get('name', '')
            snippet = None
            for s in snippets:
                if isinstance(s, CSSSnippetProperty) and s.property == prop_name:
                    snippet = s
                    break
            resolve_value_keywords(node, config, snippet, score)
            node.snippet = snippet
        elif node.name:
            snippet = find_best_match(node.name, snippets, score, True)
            node.snippet = snippet

            if snippet:
                if isinstance(snippet, CSSSnippetProperty):
                    resolve_as_property(node, snippet, config)
                else:
                    resolve_as_snippet(node, snippet)

    if node.name or config.context:
        # Resolve numeric values for CSS properties only
        resolve_numeric_value(node, config)

    return node


def resolve_gradient(node: CSSProperty, config: Config):
    "Resolves CSS gradient shortcut from given property, if possible"
    global gradient_name
    gradient_fn = None
    css_val = node.value[0] if len(node.value) == 1 else None

    if css_val is not None and len(css_val.value) == 1:
        v = css_val.value[0]
        if isinstance(v, FunctionCall) and v.name == gradient_name:
            gradient_fn = v

    if gradient_fn or node.name == gradient_name:
        gradient_value = gradient_fn.arguments if gradient_fn else [CSSValue([tokens.Field('', 0)])]
        gradient_fn = FunctionCall('linear-gradient', gradient_value)

        if not config.context:
            node.name = 'background-image'
        node.value = [CSSValue([gradient_fn])]
        node.snippet = True

        return True

    return False


def resolve_as_property(node: CSSProperty, snippet: CSSSnippetProperty, config: Config):
    "Resolves given parsed abbreviation node as CSS property"

    abbr = node.name

    # Check for unmatched part of abbreviation
    # For example, in `dib` abbreviation the matched part is `d` and `ib` should
    # be considered as inline value. If unmatched fragment exists, we should check
    # if it matches actual value of snippet. If either explicit value is specified
    # or unmatched fragment did not resolve to to a keyword, we should consider
    # matched snippet as invalid
    inline_value = get_unmatched_part(abbr, snippet.key)
    node.name = snippet.property

    if inline_value:
        if node.value:
            # Already have value: unmatched part indicates matched snippet is invalid
            return node

        kw = resolve_keyword(inline_value, config, snippet)
        if not kw:
            if config.options.get('stylesheet.skipUnmatched'):
                node.snippet = None
            return node

        node.value.append(CSSValue([kw]))

    if node.value:
        # Replace keyword alias from current abbreviation node with matched keyword
        resolve_value_keywords(node, config, snippet)
    elif snippet.value:
        default_value = snippet.value[0]

        # https://github.com/emmetio/emmet/issues/558
        # We should auto-select inserted value only if there’s multiple value
        # choice
        if len(snippet.value) == 1 or some(has_field, default_value):
            node.value = default_value
        else:
            node.value = list(map(lambda n: wrap_with_field(n, config), default_value))

    return node


def resolve_value_keywords(node: CSSProperty, config: Config, snippet: CSSSnippetProperty=None, minScore: int=0):
    for css_val in node.value:
        value = []

        for token in css_val.value:
            if isinstance(token, tokens.Literal):
                value.append(resolve_keyword(token.value, config, snippet, minScore) or token)
            elif isinstance(token, FunctionCall):
                # For function calls, we should find matching function call
                # and merge arguments
                match = resolve_keyword(token.name, config, snippet, minScore)
                if match and isinstance(match, FunctionCall):
                    value.append(FunctionCall(match.name, token.arguments + match.arguments[len(token.arguments):]))
                else:
                    value.append(token)
            else:
                value.append(token)

        css_val.value = value

def resolve_as_snippet(node: CSSProperty, snippet: CSSSnippetRaw):
    # When resolving snippets, we have to do the following:
    # 1. Replace field placeholders with actual field tokens.
    # 2. If input values given, put them instead of fields
    offset = 0
    input_value = get_item(node.value, 0)
    output_value = []

    for m in re.finditer(r'\$\{(\d+)(:[^}]+)?\}', snippet.value):
        if offset != m.start():
            output_value.append(tokens.Literal(snippet.value[offset:m.start()]))
        offset = m.end()
        if input_value and input_value.value:
            output_value.append(input_value.value.pop(0))
        else:
            output_value.append(tokens.Field(m.group(2)[1:] if m.group(2) else '', int(m.group(1))))

    tail = snippet.value[offset:]
    if tail:
        output_value.append(tokens.Literal(tail))

    node.name = None
    node.value = [CSSValue(output_value)]
    return node


def find_best_match(abbr: str, items: list, min_score=0, partial_match=False):
    """
    Finds best matching item from `items` array
    :param abbr  Abbreviation to match
    :param items List of items for match
    :param minScore The minimum score the best matched item should have to be a valid match.
    """
    max_score = 0
    matched_item = None

    for item in items:
        score = calculate_score(abbr, get_scoring_part(item), partial_match)

        if score == 1:
            # direct hit, no need to look further
            return item

        if score and score >= max_score:
            max_score = score
            matched_item = item

    return matched_item if max_score >= min_score else None


def get_scoring_part(item):
    return item if isinstance(item, str) else item.key


def get_unmatched_part(abbr: str, text: str):
    """
    Returns a part of `abbr` that wasn’t directly matched against `str`.
    For example, if abbreviation `poas` is matched against `position`,
    the unmatched part will be `as` since `a` wasn’t found in string stream
    """
    last_pos = 0
    for i, ch in enumerate(abbr):
        last_pos = text.find(ch, last_pos)
        if last_pos == -1:
            return abbr[i:]
        last_pos += 1

    return ''


def resolve_keyword(kw: str, config: Config, snippet: CSSSnippetProperty=None, min_score=0):
    """
    Resolves given keyword shorthand into matched snippet keyword or global keyword,
    if possible
    """
    if snippet:
        ref = find_best_match(kw, snippet.keywords.keys(), min_score)
        if ref:
            return snippet.keywords[ref]

        for dep in snippet.dependencies:
            ref = find_best_match(kw, dep.keywords.keys(), min_score)
            if ref:
                return dep.keywords[ref]

    ref = find_best_match(kw, config.options.get('stylesheet.keywords', []), min_score)
    if ref:
        return tokens.Literal(ref)

    return None


def resolve_numeric_value(node: CSSProperty, config: Config):
    "Resolves numeric values in given abbreviation node"
    aliases = config.options.get('stylesheet.unitAliases', {})
    unitless = config.options.get('stylesheet.unitless', [])

    for v in node.value:
        for t in v.value:
            if isinstance(t, tokens.NumberValue):
                if t.unit:
                    t.unit = aliases.get(t.unit, t.unit)
                elif t.value != 0 and node.name not in unitless:
                    opt_name = 'stylesheet.floatUnit' if '.' in t.raw_value else 'stylesheet.intUnit'
                    t.unit = config.options.get(opt_name, '')


def has_field(value: CSSValue):
    "Check if given value contains fields"
    for v in value.value:
        if isinstance(v, tokens.Field) or (isinstance(v, FunctionCall) and some(has_field, v.arguments)):
            return True

    return False


class WrapState:
    __slots__ = ('index',)

    def __init__(self, index=1):
        self.index = index

    def inc(self):
        index = self.index
        self.index += 1
        return index

def wrap_with_field(node: CSSValue, config: Config, state: WrapState=None):
    if state is None: state = WrapState()
    value = []

    for v in node.value:
        if isinstance(v, tokens.ColorValue):
            color_val = color(v, config.options.get('stylesheet.shortHex'))
            value.append(tokens.Field(color_val, state.inc()))
        elif isinstance(v, tokens.Literal):
            value.append(tokens.Field(v.value, state.inc()))
        elif isinstance(v, tokens.NumberValue):
            value.append(tokens.Field(''.join((v.value, v.unit)), state.inc()))
        elif isinstance(v, tokens.StringValue):
            q = '\'' if v.quote == 'single' else '"'
            value.append(tokens.Field(''.join((q, v.value, q)), state.inc()))
        elif isinstance(v, FunctionCall):
            value.append(tokens.Field(v.name, state.inc()))
            value.append(tokens.Literal('('))

            max_i = len(v.arguments) - 1
            for i, arg in enumerate(v.arguments):
                value += wrap_with_field(arg, config, state).value
                if i != max_i:
                    value.append(tokens.Literal(', '))

            value.append(tokens.Literal(')'))
        else:
            value.append(v)

    return CSSValue(value)

def is_value_scope(config: Config):
    "Check if abbreviation should be expanded in CSS value context"
    if config.context:
        return config.context['name'] == CSSAbbreviationScope.Value or not config.context['name'].startswith('@@')

    return False


def get_snippets_for_scope(snippets: list, config: Config):
    "Returns snippets for given scope"

    if config.context:
        if config.context['name'] == CSSAbbreviationScope.Section:
            return [s for s in snippets if s.type == CSSSnippetType.Raw]


        if config.context['name'] == CSSAbbreviationScope.Property:
            return [s for s in snippets if s.type == CSSSnippetType.Property]

    return snippets
