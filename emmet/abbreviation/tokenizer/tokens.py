class Token:
    def __init__(self, start: int=None, end: int=None):
        self.start = start
        self.end = end

    @property
    def type(self):
        "Type of current token"
        return self.__class__.__name__

class Repeater(Token):
    def __init__(self, count: int, value: int, implicit: bool=False, *args):
        super(Repeater, self).__init__(*args)
        self.count = count
        self.value = value
        self.implicit = implicit

class RepeaterNumber(Token):
    def __init__(self, size: int, reverse: bool, base: int=0, parent: int=0, *args):
        super(RepeaterNumber, self).__init__(*args)

class RepeaterPlaceholder(Token):
    def __init__(self, value: str=None, *args):
        super(RepeaterPlaceholder, self).__init__(*args)
        self.value = value

class Field(Token):
    def __init__(self, name: str, index: int=None, *args):
        super(Field, self).__init__(*args)
        self.index = index
        self.name = name

class Operator(Token):
    def __init__(self, operator: str, *args):
        super(Operator, self).__init__(*args)
        self.operator = operator

class Bracket(Token):
    def __init__(self, is_open: bool, context: str, *args):
        super(Bracket, self).__init__(*args)
        self.open = is_open
        self.context = context

class Quote(Token):
    def __init__(self, single: bool, *args):
        super(Quote, self).__init__(*args)
        self.single = single

class Literal(Token):
    def __init__(self, value: str, *args):
        super(Literal, self).__init__(*args)
        self.value = value

class WhiteSpace(Token): pass
