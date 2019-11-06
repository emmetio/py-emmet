class Token:
    @property
    def type(self):
        return self.__class__.__name__

class Repeater(Token): pass
class Another(Token): pass

a = Repeater()
b = Another()
print(a.type)
print(b.type)
