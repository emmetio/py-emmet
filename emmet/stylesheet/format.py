import re
from ..css_abbreviation.parser import CSSValue, CSSProperty, FunctionCall
from ..css_abbreviation.tokenizer import tokens
from ..output_stream import OutputStream
from ..config import Config
from .color import color, frac
from .scope import CSSAbbreviationScope


def stringify(abbr: list, config: Config):
    out = OutputStream(config.options)
    fmt = config.options.get('output.format')

    if config.options.get('stylesheet.skipUnmatched'):
        # Filter out unmatched snippets
        abbr = [node for node in abbr if node.snippet is not None or node.important]

    for i, prop in enumerate(abbr):
        if fmt and i != 0:
            out.push_newline(True)
        css_property(prop, out, config)

    return out.value

def css_property(node: CSSProperty, out: OutputStream, config: Config):
    "Outputs given abbreviation node into output stream"
    is_json = config.options.get('stylesheet.json')

    if node.name:
        # It’s a CSS property
        name = to_camel_case(node.name) if is_json else node.name
        out.push_string(name + config.options.get('stylesheet.between'))

        if node.value:
            css_property_value(node, out, config)
        else:
            out.push_field(0, '')

        if is_json:
            # For CSS-in-JS, always finalize property with comma
            # NB: seems like `important` is not available in CSS-in-JS syntaxes
            out.push(',')
        else:
            output_important(node, out, True)
            out.push(config.options.get('stylesheet.after'))
    else:
        # It’s a regular snippet, output plain tokens without any additional formatting
        for css_val in node.value:
            for v in css_val.value:
                output_token(v, out, config)
        output_important(node, out, len(node.value) > 0)


def css_property_value(node: CSSProperty, out: OutputStream, config: Config):
    is_json = config.options.get('stylesheet.json')
    num = get_single_numeric(node) if is_json else None

    if num and (not num.unit or num.unit == 'px'):
        # For CSS-in-JS, if property contains single numeric value, output it
        # as JS number
        out.push(frac(num.value))
    else:
        quote = get_quote(config)
        if is_json: out.push(quote)
        for i, v in enumerate(node.value):
            if i != 0:
                out.push(', ')
            output_value(v, out, config)
        if is_json: out.push(quote)


def output_important(node: CSSProperty, out: OutputStream, separator=False):
    if node.important:
        if separator: out.push(' ')
        out.push('!important')


def output_value(value: CSSValue, out: OutputStream, config: Config):
    prev_end = -1
    for i, token in enumerate(value.value):
        # Handle edge case: a field is written close to previous token like this: `foo${bar}`.
        # We should not add delimiter here

        if i != 0 and (not isinstance(token, tokens.Field) or token.start != prev_end):
            out.push(' ')

        output_token(token, out, config)
        prev_end = token.end if hasattr(token, 'end') else -1

def output_token(token, out: OutputStream, config: Config):
    if isinstance(token, tokens.ColorValue):
        out.push(color(token, config.options.get('stylesheet.shortHex')))
    elif isinstance(token, tokens.Literal):
        out.push_string(token.value)
    elif isinstance(token, tokens.NumberValue):
        out.push_string(frac(token.value, 4) + token.unit)
    elif isinstance(token, tokens.StringValue):
        quote = '"' if token.quote == 'double' else '\''
        out.push_string(''.join((quote, token.value, quote)))
    elif isinstance(token, tokens.Field):
        out.push_field(token.index, token.name)
    elif isinstance(token, FunctionCall):
        out.push(token.name + '(')
        for i, arg in enumerate(token.arguments):
            if i: out.push(', ')
            output_value(arg, out, config)
        out.push(')')


def get_single_numeric(node: CSSProperty):
    "If value of given property is a single numeric value, returns this token"
    if len(node.value) == 1:
        css_val = node.value[0]
        if len(css_val.value) == 1 and isinstance(css_val.value[0], tokens.NumberValue):
            return css_val.value[0]


def to_camel_case(text: str):
    "Converts kebab-case string to camelCase"
    return re.sub(r'\-(\w)', lambda m: m.group(1).upper(), text)

def get_quote(config: Config):
    return '"' if config.options.get('stylesheet.jsonDoubleQuotes') else '\''
