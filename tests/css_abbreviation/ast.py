import sys
sys.path.append('../../')

from emmet.css_abbreviation.parser import CSSProperty, CSSValue, FunctionCall
from emmet.css_abbreviation.tokenizer import tokens

def stringify(prop: CSSProperty):
    name = prop.name or '?'
    value = ', '.join(map(stringify_value, prop.value))
    important = ' !important' if prop.important else ''
    return '{name}: {value}{important};'.format_map(locals())


def stringify_value(value: CSSValue):
    return ' '.join(map(stringify_token, value.value))


def stringify_token(token):
    if isinstance(token, tokens.ColorValue):
        if not token.r and not token.g and not token.b and not token.a:
            return 'transparent'

        if token.a == 1:
            return '#%s%s%s' % (to_hex(token.r), to_hex(token.g), to_hex(token.b))

        return 'rgba(%d, %d, %d, %s)' % (token.r, token.g, token.b, to_float(token.a))
    elif isinstance(token, tokens.NumberValue):
        return '%s%s' % (to_float(token.value), token.unit)
    elif isinstance(token, tokens.StringValue):
        return '"%s"' % token.value
    elif isinstance(token, tokens.Literal):
        return token.value
    elif isinstance(token, FunctionCall):
        args = ', '.join(map(stringify_value, token.arguments))
        return '%s(%s)' % (token.name, args)

    raise Exception('Unexpected token')


def to_hex(num: int):
    return hex(num)[2:].ljust(2, '0')

def to_float(num: float):
    s = '%.2f' % num
    return s.rstrip('0').rstrip('.')
