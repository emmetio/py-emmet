import re
from ..css_abbreviation.tokenizer.tokens import ColorValue

def color(token: ColorValue, short_hex=False):
    if not token.r and not token.g and not token.b and not token.a:
        return 'transparent'
    if token.a == 1:
        return as_hex(token, short_hex)

    return as_rgb(token)

def as_hex(token: ColorValue, short=False):
    """
    Output given color as hex value
    :param short Produce short value (e.g. #fff instead of #ffffff), if possible
    """
    if short and is_short_hex(token.r) and is_short_hex(token.g) and is_short_hex(token.b):
        fn = to_short_hex
    else:
        fn = to_hex

    return '#%s%s%s' % (fn(token.r), fn(token.g), fn(token.b))

def as_rgb(token: ColorValue):
    values = [str(token.r), str(token.g), str(token.b)]
    prefix = 'rgb'
    if token.a != 1:
        prefix = 'rgba'
        values.append(frac(token.a, 8))

    return '%s(%s)' % (prefix, ', '.join(values))

def frac(num: int, digits=4):
    str_num = ('%.' + str(digits) + 'f') % num
    return re.sub(r'\.?0+$', '', str_num)

def is_short_hex(num: int):
    return not (num % 17)

def to_short_hex(num: int):
    return format(num >> 4, 'x')

def to_hex(num: int):
    return format(num, 'x').ljust(2, '0')
