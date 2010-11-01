import copy
import heapq

from flash_types import *

class Tag:
    def __init__(self, contents=None, length=-1, name="", parent=None):
        self.children = []
        self.contents = contents
        self.length = length
        self.name = name if name else self.__class__.__name__
        self.parent = parent
    def __str__(self, indent=0):
        self_str = "%s%s: %s" %("  " * indent, self.name, str(self.contents))
        for child_tag in self.children:
            self_str += "\n%s" %child_tag.__str__(indent = indent+1)
        return self_str
    def addChild(self, tag):
        self.children.append(tag)
        tag.parent = self
    def execute(self):
        raise NotImplementedError("execute not defined for tag: %s" %self.__str__())
    def program(self):
        return self.parent.program()
    def update_contents(self, contents):
        if not contents:
            return
        if self.contents and isinstance(self.contents, dict):
            self.contents.update(contents)
        else:
            self.contents = contents

class NonExecutingTag(Tag):
    def execute(self):
        print "Skipping execution of tag: %s" %self.__str__()


    
class Program(Tag):
    def __init__(self, *args, **kwargs):
        self.characters = {}
        self.display_list = DisplayList()
        Tag.__init__(self, *args, **kwargs)
    def addCharacter(self, character):
        self.characters[character.character_id] = character
    def addToDisplayList(self, display_list_character):
        self.display_list.add(display_list_character)
    def execute(self):
        for child_tag in self.children:
            child_tag.execute()
    def getCharacter(self, character_id):
        return self.characters[character_id]
    def program(self):
        return self
    


class ActionTag(Tag):
    def __init__(self, **kwargs):
        if 'contents' not in kwargs:
            kwargs['contents'] = {}
        Tag.__init__(self, **kwargs)
    def runAction(self):
        raise NotImplementedError("runAction not defined for action tag: %s" %self.__str__())

class DefineCharacter(Tag):
    def __init__(self, character_id, **kwargs):
        Tag.__init__(self, **kwargs)
        self.update_contents({'character_id': character_id})
    def _build_character(self, character_id):
        return globals()[self.character_type](character_id)
    def execute(self):
        character_id = self.contents['character_id']
        print "Adding %s with id %d" %(self.character_type, character_id)
        self.program().addCharacter(self._build_character(character_id))
        for child in self.children:
            child.execute()

class DefineShape(DefineCharacter):
    character_type = "Shape"

class DefineSprite(DefineCharacter):
    character_type = "Sprite"

class DepthTag(Tag):
    def __init__(self, depth, *args, **kwargs):
        self.depth = depth
        Tag.__init__(self, *args, **kwargs)
        
class DoActionTag(ActionTag):
    """
    DoAction instructs Flash Player to perform a list of actions when the current frame is
    complete. The actions are performed when the ShowFrame tag is encountered, regardless of
    where in the frame the DoAction tag appears.
    
    Starting with SWF 9, if the ActionScript3 field of the FileAttributes tag is 1, the contents of
    the DoAction tag will be ignored.
    """
    def execute(self):
        print "Adding %d actions to next ShowFrame" %len(self.children)
        self.program().display_list.addActions(self.children)
    
class DoInitActionTag(DoActionTag):
    # TODO: doinit should execute in tag appearance order, not depth order
    """
    The DoInitAction tag is similar to the DoAction tag: it defines a series of bytecodes to be
    executed. However, the actions defined with DoInitAction are executed earlier than the usual
    DoAction actions, and are executed only once.
    
    In some situations, actions must be executed before the ActionScript representation of the first
    instance of a particular sprite is created. The most common such action is calling
    Object.registerClass to associate an ActionScript class with a sprite. Such a call is generally
    found within the #initclip pragma in the ActionScript language. DoInitAction is used to
    implement the #initclip pragma.
    
    A DoInitAction tag specifies a particular sprite to which its actions apply. A single frame can
    contain multiple DoInitAction tags; their actions are executed in the order in which the tags
    appear. However, the SWF file can contain only one DoInitAction tag for any particular
    sprite.
    
    The specified actions are executed immediately before the normal actions of the frame in
    which the DoInitAction tag appears. This only occurs the first time that this frame is
    encountered; playback reaches the same frame again later, actions provided in DoInitAction
    are skipped.
    """
    @classmethod
    def fromDoActionTag(klass, sprite_id, do_action_tag):
        do_init_action_tag = klass()
        for attr,value in do_action_tag.__dict__.items():
            do_init_action_tag.__dict__[attr] = copy.copy(value)
        do_init_action_tag.contents['sprite_id'] = sprite_id
        do_init_action_tag.name = klass.__name__
        return do_init_action_tag
    def execute(self):
        print "Attaching DoInit to sprite %d" %self.sprite_id()
        self.program().getCharacter(self.sprite_id()).setAction(self)
    def sprite_id(self):
        return self.contents['sprite_id']

class PlaceObject(DepthTag):
    """
    The PlaceObject tag adds a character to the display list. The CharacterId identifies the
    character to be added. The Depth field specifies the stacking order of the character. The
    Matrix field species the position, scale, and rotation of the character. If the size of the
    PlaceObject tag exceeds the end of the transformation matrix, it is assumed that a
    ColorTransform field is appended to the record. The ColorTransform field specifies a color
    effect (such as transparency) that is applied to the character. The same character can be added
    more than once to the display list with a different depth and transformation matrix.
    """
    def character(self):
        if 'character_id' not in self.contents or not self.contents['character_id']:
            return None
        character_id = self.contents['character_id']
        return self.program().characters[character_id]
    def execute(self):
        character = self.character()
        if character:
            self.program().addToDisplayList(character.displayListCharacter(self.depth))
            print "Placing character at depth %d: %s" %(self.depth, str(character))
        else:
            print "Skipping PlaceObject since no character specified"
        
class PlaceObject2(PlaceObject):
    pass
    
class RemoveObject2(DepthTag):
    def execute(self):
        print "Removing object of depth %d from display" %self.depth
        self.program().display_list.remove(self.depth)
        
class ShowFrame(Tag):
    """
    The ShowFrame tag instructs Flash Player to display the contents of the display list. The file is
    paused for the duration of a single frame.
    
    The minimum file format version is SWF 1.
    """
    def execute(self):
        print "ShowFrame with %d characters and %d actions" %(len(self.program().display_list), len(self.program().display_list.pending_actions))
        for character in sorted(self.program().display_list):
            print "\tRendering character %s" %str(character)
            character.display()
        self.program().display_list.runActions()

class VideoStreamTag(DefineCharacter):
    character_type = "VideoStream"