class Type:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "%s(%s)" %(self.__class__.__name__, str(self.value))
    def __repr__(self):
        return self.__str__()
    
class String(Type):
    def __init__(self, value):
        assert isinstance(value, str)
        Type.__init__(self, value)
    
class Float(Type):
    pass

class Integer(Type):
    pass

class Boolean(Type):
    pass

class Double(Type):
    pass

class RegisterNumber(Type):
    pass

class Constant8(Type):
    pass

class Constant16(Type):
    pass

class Null(Type):
    def __init__(self):
        Type.__init__(self, None)

class Undefined(Type):
    def __init__(self):
        Type.__init__(self, None)



class Shape:
    def __init__(self, shape_id):
        self.shape_id = shape_id