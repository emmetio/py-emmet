from .tokenizer import tokens


operators = {
    'child': '>',
    'class': '.',
    'climb': '^',
    'id': '#',
    'equal': '=',
    'close': '/',
    'sibling': '+'
}


def stringify(token: tokens.Token, state):
    visitor = globals().get(token.type)
    if not visitor:
        raise Exception('Unknown token %s' % token.type)

    return visitor(token, state)


def Literal(token: tokens.Literal, state):
    return token.value


def Quote(token: tokens.Quote, state):
    return '\'' if token.single else '"'


def Bracket(token: tokens.Bracket, state):
    if token.context == 'attribute':
        return '[' if token.open else ']'
    if token.context == 'expression':
        return '{' if token.open else '}'
    return '(' if token.open else '}'


def Operator(token: tokens.Operator, state):
    global operators
    return operators.get(token.operator)


def Field(token: tokens.Field, state):
    if token.index is not None:
        # It’s a field: by default, return TextMate-compatible field
        fmt = '${%d:%s}' if token.name else '${%s}'
        return fmt % (token.index, token.name)

    if token.name:
        # It’s a variable
        return state.get_variable(token.name)

    return ''


def RepeaterPlaceholder(token: tokens.RepeaterPlaceholder, state):
    # Find closest implicit repeater
    repeater = None
    repeater_list = state.repeaters[:]
    repeater_list.reverse()

    for r in repeater_list:
        if r.implicit:
            repeater = r
            break

    state.inserted = True
    return state.get_text(repeater.value) if repeater else None


def RepeaterNumber(token: tokens.RepeaterNumber, state):
    value = 1
    last_ix = len(state.repeaters) - 1

    if last_ix >= 0:
        repeater = state.repeaters[-1]
        if token.reverse:
            value = token.base + repeater.count - repeater.value - 1
        else:
            value = token.base + repeater.value

        if token.parent:
            parent_ix = max(0, last_ix - token.parent)
            if parent_ix != last_ix:
                value += repeater.count * state.repeaters[parent_ix].value

    result = str(value)
    prefix = '0' * max(0, token.size - len(result))

    return prefix + result


def WhiteSpace(token, state):
    return ' '
