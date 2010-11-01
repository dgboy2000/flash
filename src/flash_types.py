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



class Character:
    def __init__(self, character_id):
        self.action = None
        self.character_id = character_id
    def __getattr__(self, attr_name):
        if attr_name == self.id_field():
            return self.character_id
        raise AttributeError("'%s' object has no attribute '%s'" %(self.__class__.__name__, attr_name))
    def __str__(self):
        return "%s(character_id=%d)" %(self.__class__.__name__, self.character_id)
    def displayListCharacter(self, depth):
        return DisplayListCharacter(self, depth)
    def id_field(self):
        return "%s_id" %self.__class__.__name__.lower()
    def set_action(self, action):
        self.action = action

class Shape(Character):
    pass
        
class Sprite(Character):
    pass
    
class VideoStream(Character):
    pass
    
    
    
class DisplayList:
    def __init__(self):
        self.depth_to_characters = {}
        self.pending_actions = []
    def __iter__(self):
        return self.depth_to_characters.values().__iter__()
    def __len__(self):
        return self.depth_to_characters.__len__()
    def add(self, display_list_character):
        self.depth_to_characters[display_list_character.depth] = display_list_character
    def addActions(self, actions):
        self.pending_actions.extend(actions)
    def remove(self, depth):
        self.depth_to_characters[depth].hide()
        del self.depth_to_characters[depth]
    def runActions(self):
        for action in self.pending_actions:
            action.runAction()
        self.pending_actions = []
                
class DisplayListCharacter():
    def __init__(self, character, depth):
        self.character = character
        self.depth = depth
        self.is_showing = False
    def __cmp__(self, other):
        return self.depth.__cmp__(other.depth)
    def __str__(self):
        return "%s(character=%s, depth=%d)" %(self.__class__.__name__, str(self.character), self.depth)
    def display(self):
        if self.character.action and not self.is_showing:
            self.character.action.runActions()
        self.is_showing = True
    def hide(self):
        self.is_showing = False
            
            
    
    
    