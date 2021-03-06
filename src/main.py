'''
Created on Jul 20, 2010

@author: dannygoodman
'''

import struct

from flash_types import *
from flash_tags import *


unhandled_codes = {}
class SWF:
    tag_type_to_string = {
        0 : "End",
        1 : "ShowFrame",
        2 : "DefineShape",
        4 : "PlaceObject",
        5 : "RemoveObject",
        7 : "DefineButton",
        9 : "SetBackgroundColor",
        12 : "DoAction",
        20 : "DefineBitsLossless",
        22 : "DefineShape2",
        24 : "Protect",
        26 : "PlaceObject2",
        28 : "RemoveObject2",
        32 : "DefineShape3",
        36 : "DefineBitsLossless2",
        37 : "DefineEditText",
        39 : "DefineSprite",
        43 : "FrameLabel",
        48 : "DefineFont",
        56 : "ExportAssets",
        59 : "DoInitAction",
        60 : "DefineVideoStream",
        70 : "PlaceObject3",
        88 : "DefineFontName"
    }
    
    simple_define_character_tags = {
        37 : "DefineEditText",
        48 : "DefineFont",
        88 : "DefineFontName"
    }
    
    tag_type_to_is_executable = {
        0 : False,
        # 1 : "ShowFrame",
        # 2 : "DefineShape",
        # 4 : "PlaceObject",
        # 5 : "RemoveObject",
        9 : False,
        # 12 : "DoAction",
        # 20 : "DefineBitsLossless",
        # 22 : "DefineShape2",
        24 : False,
        # 26 : "PlaceObject2",
        # 32 : "DefineShape3",
        36 : False,
        37 : False,
        # 39 : "DefineSprite",
        43 : False,
        48 : False,
        56 : False,
        # 59 : "DoInitAction",
        # 60 : "DefineVideoStream",
        # 70 : "PlaceObject3",
        88 : False,
        -1 : True
    }
    
    # tag_name_to_class = {}
    # for tag_name in tag_type_to_string.values():
    #     tag_class_name = tag_name+"Tag"
    #     if tag_class_name in globals():
    #         continue
    #     
    
    action_code_to_name = {
        0 : 'action_null?',
        7 : 'action_stop',
        11 : 'action_subtract',
        12 : 'action_multiply',
        13 : 'action_divide',
        18 : 'action_not',
        23 : 'action_pop',
        28 : 'action_get_variable',
        29 : 'action_set_variable',
        43 : 'action_cast_op',
        44 : 'action_implements_op',
        51 : 'action_ascii_to_char',
        52 : 'action_get_time',
        58 : 'action_delete',
        60 : 'action_define_local',
        61 : 'action_call_function',
        62 : 'action_return',
        63 : 'action_modulo',
        64 : 'action_new_object',
        66 : 'action_init_array',
        67 : 'action_init_object',
        68 : 'action_type_of',
        71 : 'action_add2',
        72 : 'action_less2',
        73 : 'action_equals2',
        74 : 'action_to_number',
        75 : 'action_to_string',
        76 : 'action_push_duplicate',
        78 : 'action_get_member',
        79 : 'action_set_member',
        80 : 'action_increment',
        81 : 'action_decrement',
        82 : 'action_call_method',
        83 : 'action_new_method',
        84 : 'action_instance_of',
        85 : 'action_enumerate2',
        96 : 'action_bit_and',
        100 : 'action_bit_rshift',
        102 : 'action_strict_equals',
        103 : 'action_greater',
        105 : 'action_extends',
        135 : 'action_store_register',
        136 : 'action_constant_pool',
        142 : 'action_define_function2',
        150 : 'action_push',
        153 : 'action_jump',
        155 : 'action_define_function',
        157 : 'action_if'
    }
    
    def __init__(self, filename):
        self.file_contents = open(filename, 'rb').read()
        self.byte_pos = 0
        self.bit_pos = 0
        
        self.action_registers = [None for i in range(256)]
        self.action_stack = []
        
        self.characters = {}
        
        self.position_stack = []
        self.program = Program()
        
    def __len__(self):
        return len(self.file_contents)
        
    def read_header(self):
        self.step_bytes(3)
        version = self.read_ui(1)
        file_length = self.read_ui(4)
        print "File type: %s" %self.file_contents[:3]
        print "swf version: %d" %version
        print "file length: %d" %file_length
        (xmin, xmax, ymin, ymax) = self.read_rect()
        print "frame size: %d x %d" %(xmax/20, ymax/20)        
        frame_rate = self.read_ui(2)
        num_frames = self.read_ui(2)
        print "frame rate: %d" %(frame_rate / 256)
        print "frame count: %d" %num_frames
        print "[end header]\n"
    
    def read_action(self):
        action_tag = ActionTag()
        startPos = self.byte_pos
        (action_code, action_length) = self.read_action_header()
        
        assert action_code in self.action_code_to_name, "Unhandled action code: %d" %action_code
        action_name = self.action_code_to_name[action_code]
        action_tag.name = action_name

        expected_length = 1        
        if action_length > 0:
            tag_contents = getattr(self, "read_%s" %action_name).__call__(action_length)
            action_tag.update_contents(tag_contents)

            expected_length = action_length + 3
        else:
            if action_code not in self.action_code_to_name:
                unhandled_codes[action_code] = True        
        action_tag.update_contents({'action_code': action_code})
        
        bytesRead = self.byte_pos - startPos
        assert bytesRead == expected_length, "Wrong number of action bytes: expected %d, read %d" %(expected_length, bytesRead)
        action_tag.length = expected_length
        return action_tag
    
    def read_actions(self):
        do_action_tag = DoActionTag()
        next_byte = self.next_unsigned_bytes_little_endian(1)
        total_len = 0
        while next_byte != 0:
            action_tag = self.read_action()
            do_action_tag.addChild(action_tag)
            total_len += action_tag.length
            next_byte = self.next_unsigned_bytes_little_endian(1)
            
        self.step_bytes(1)            
        total_len += 1
        # return total_len
        return do_action_tag

    def read_action_constant_pool(self, length):
        count = self.read_ui(2)
        string_constants = []
        for i in range(count):
            string_constants.append(self.read_string())
        return {'string_constants' : string_constants}
    
    def read_action_define_function(self, length):
        startPos = self.byte_pos
        functionName = self.read_string()
        numParams = self.read_ui(2)
        params = []
        for i in range(numParams):
            params.append(self.read_string())
        codeSize = self.read_ui(2)
        print "function %s(%s) has %d bytes of code" %(functionName, ', '.join(params), codeSize)
        assert self.byte_pos-startPos == length, "Define function mismatch"
    
    def read_action_define_function2(self, length):
        startPos = self.byte_pos
        functionName = self.read_string()
        numParams = self.read_ui(2)
        registerCount = self.read_ui(1)
        self.step_bytes(2) # flags
        params = []
        for i in range(numParams):
            register = self.read_ui(1)
            params.append(self.read_string())
        codeSize = self.read_ui(2)
        print "function2 %s(%s) has %d bytes of code" %(functionName, ', '.join(params), codeSize)
        assert self.byte_pos-startPos == length, "Define function mismatch"
    
    def read_action_get_variable(self):
        print "Action get variable"
    
    def read_action_header(self):
        action_code = self.read_ui(1)
        length = 0
        if action_code >= 128:
            length = self.read_ui(2)
        return (action_code, length)
    
    def read_action_if(self, length):
        branchOffset = self.read_si(2)
        condition = self.action_stack.pop()
        print "ActionIf has condition number '%s' and branch offset '%d'" %(str(condition), branchOffset)
        if condition:
            print "Stepping %d bytes and reading action" %branchOffset
            self.positionPush()
            self.step_bytes(branchOffset)
            self.read_action()
            self.positionPop()
            
    def read_action_jump(self, length):
        offset = self.read_si(2)
        print "Jump to offset: %d" %offset
    
    def read_action_push(self, length):
        startPos = self.byte_pos
        bytesRead = self.byte_pos - startPos
        values = []
        while bytesRead < length:
            stackElt = None
            value = None
            type = self.read_ui(1)
            if type == 0:
                stackElt = self.read_string()
                value = String(stackElt)
            elif type == 1:
                stackElt = self.read_float()
                value = Float(stackElt)
            elif type == 2:
                value = Null()
            elif type == 3:
                value = Undefined()
            elif type == 4:
                stackElt = self.read_ui(1)
                value = RegisterNumber(stackElt)
            elif type == 5:
                stackElt = self.read_ui(1)
                value = Boolean(stackElt)
            elif type == 6:
                stackElt = self.read_double()
                value = Double(stackElt)
            elif type == 7:
                stackElt = self.read_ui(4)
                value = Integer(stackElt)
            elif type == 8:
                stackElt = self.read_ui(1)
                value = Constant8(stackElt)
            elif type == 9:
                stackElt = self.read_ui(2)
                value = Constant16(stackElt)
            else:
                raise Exception("Unknown type %d" %type)
            self.action_stack.append(stackElt)
            values.append(value)
            bytesRead = self.byte_pos - startPos
        assert bytesRead == length, "Error in action push: expected %d bytes, read %d" %(length, bytesRead)
        return {'values' : values}

    def read_action_store_register(self, length):
        return {'register_number': self.read_ui(1)}

    def read_tag(self, debug=False):
        tag = None
        
        short_header = self.read_ui(2)
        tag_type = short_header / 2**6
        tag_length = short_header % 2**6
        if tag_length == 63:
            tag_length = self.read_si(4)
            
        if debug:
            print "Tag type %d, length %d" %(tag_type, tag_length)
            
        startPos = self.byte_pos
        if tag_type in (60,):
            print "VIDEO TAG detected: %d" %tag_type
            tag = self.read_video_stream_tag_body()
        elif tag_type == 12:
            print "DoAction (%d)" %tag_type
            tag = self.read_actions()
        elif tag_type == 59:
            sprite_id = self.read_ui(2)
            print "DoInitAction for Sprite ID %d" %sprite_id
            tag = DoInitActionTag.fromDoActionTag( sprite_id, self.read_actions() )
        elif tag_type in (2, 22, 32):
            tag = self.read_define_shape(tag_length)
        elif tag_type == 39:
            tag = self.read_define_sprite(tag_length)
        elif tag_type == 1:
            tag = self.read_show_frame(tag_length)
        elif tag_type == 26:
            tag = self.read_place_object2(tag_length)
        elif tag_type == 28:
            tag = self.read_remove_object2(tag_length)
        elif tag_type in self.simple_define_character_tags:
            tag = self.read_simple_define_character_tag(tag_length, tag_type)
        else:
            if tag_type in self.tag_type_to_string:
                tag_name = self.tag_type_to_string[tag_type]
                if tag_type in self.tag_type_to_is_executable and not self.tag_type_to_is_executable[tag_type]:
                    tag = NonExecutingTag(name=tag_name)
                else:
                    tag = Tag(name=tag_name)
            else:
                assert False, "Unhandled tag code: %d" % tag_type
            self.step_bytes(tag_length)
        bytesRead = self.byte_pos - startPos 
        assert tag_length == bytesRead, "Tag length mismatch: expected %d bytes, read %d" %(tag_length, bytesRead)
        return tag
        
        
        
    def read_control_tags_for_character(self, character_tag, tags_length):
        end_pos = swf.byte_pos + tags_length
        while self.byte_pos < end_pos:
            character_tag.addChild(self.read_tag())
                    
    def read_define_shape(self, tag_length):
        before_pos = self.byte_pos
        shape_id = self.read_ui(2)
        shape_bounds = self.read_rect()
        self.step_bytes( tag_length + before_pos - self.byte_pos )
        return DefineShape(shape_id, contents={'shape_bounds': shape_bounds})
       
    def read_define_sprite(self, tag_length):
        before_pos = self.byte_pos
        sprite_id = self.read_ui(2)
        frame_count = self.read_ui(2)
        # self.step_bytes( tag_length + before_pos - self.byte_pos )
        sprite = DefineSprite(sprite_id, contents={'frame_count': frame_count})
        self.read_control_tags_for_character(sprite, tag_length + before_pos - self.byte_pos)
        assert self.byte_pos == before_pos+tag_length, "Final position %d, should be %d" %(self.byte_pos, before_pos+tag_length)
        return sprite
        
    def read_place_object2(self, tag_length):
        before_pos = self.byte_pos
        
        self.read_ub(6)
        has_character = self.read_ub(1)
        self.seek_byte_start()
        
        depth = self.read_ui(2)
        character_id = None
        if has_character:
            character_id = self.read_ui(2)
            
        self.step_bytes( tag_length + before_pos - self.byte_pos )
        return PlaceObject2(depth, contents={'character_id': character_id})
        
    def read_remove_object2(self, tag_length):
        depth = self.read_ui(2)
        return RemoveObject2(depth)
      
    def read_simple_define_character_tag(self, tag_length, tag_type):
        before_pos = self.byte_pos
        character_id = self.read_ui(2)
        self.step_bytes( tag_length + before_pos - self.byte_pos )
        return globals()[self.simple_define_character_tags[tag_type]](character_id)
      
    def read_show_frame(self, tag_length):
        self.step_bytes( tag_length )
        return ShowFrame()
      
    def read_video_stream_tag_body(self):
        character_id = self.read_ui(2)
        num_frames = self.read_ui(2)
        width = self.read_ui(2)
        height = self.read_ui(2)

        self.read_ui(1)

        codec_id = self.read_ui(1)
        print "character id: %d" %character_id
        print "num frames: %d" %num_frames
        print "dimensions: %d x %d" %(width, height)
        print "codec: %d" %codec_id
        
        contents = {
          'num_frames' : num_frames,
          'width' : width,
          'height' : height,
          'codec_id' : codec_id
        }
        return VideoStreamTag(character_id, contents = contents)

        
        
    def read_rect(self):
        Nbits = self.read_ub(5)
        xmin = self.read_sb(Nbits)
        xmax = self.read_sb(Nbits)
        ymin = self.read_sb(Nbits)
        ymax = self.read_sb(Nbits)
        self.seek_byte_start()
        return (xmin, xmax, ymin, ymax)
    def read_sb(self, num_bits):
        sb = self.next_signed_bits(num_bits)
        self.step_bits(num_bits)
        return sb
    def read_si(self, num_bytes):
        si = self.next_signed_bytes(num_bytes)
        self.step_bytes(num_bytes)
        return si
    def read_string(self):
        string = ''
        next_byte = self.read_ui(1)
        while next_byte != 0:
            string += chr(next_byte)
            next_byte = self.read_ui(1)
        return string
    def read_ub(self, num_bits):
        ub = self.next_unsigned_bits(num_bits)
        self.step_bits(num_bits)
        return ub
    def read_ui(self, num_bytes):
        ui = self.next_unsigned_bytes_little_endian(num_bytes)
        self.step_bytes(num_bytes)
        return ui
    def read_string_bytes(self, num_bytes):
        string_bytes = self.file_contents[self.byte_pos:self.byte_pos+num_bytes]
        self.step_bytes(num_bytes)
        return string_bytes
    def read_float(self):
        return struct.unpack('<f', self.read_string_bytes(4))
    def read_double(self):
        return struct.unpack('<d', self.read_string_bytes(8))
            
    def next_bit_string(self, num_bits):
        end_bit_pos = self.bit_pos + num_bits
        num_bytes = 1 + (end_bit_pos)/8
        raw_int = self.next_unsigned_bytes_big_endian(num_bytes)
        raw_int += 256 ** num_bytes
        return (bin(raw_int).split('b')[1]+'x')[self.bit_pos+1:end_bit_pos+1]
    def next_signed_bits(self, num_bits):
        bit_string = self.next_bit_string(num_bits)
        sign_bit = bit_string[0]
        if sign_bit == '0':
            return int(bit_string[1:], 2)
        elif sign_bit == '1':
            return -(int(self.complement_bit_string(bit_string[1:]), 2) + 1)
        else:
            raise ValueError("Bad bit string '%s'" %bit_string)
    def next_signed_bytes(self, num_bytes):
        val = self.next_unsigned_bytes_little_endian(num_bytes)
        if val >= 256 ** num_bytes / 2:
            val -= 256 ** num_bytes
        return val
    def next_unsigned_bits(self, num_bits):
        return int(self.next_bit_string(num_bits), 2)
    def next_unsigned_bytes_big_endian(self, num_bytes):
        int = 0
        for i in range(num_bytes):
            int = 256*int + ord(self.file_contents[self.byte_pos + i])
        return int
    def next_unsigned_bytes_little_endian(self, num_bytes):
        int = 0
        for i in range(num_bytes):
            int += 256**i * ord(self.file_contents[self.byte_pos + i])
        return int
    
    def positionPop(self):
        self.byte_pos, self.bit_pos = self.position_stack.pop()
    def positionPush(self):
        self.position_stack.append([self.byte_pos, self.bit_pos])
    
    def seek_byte_start(self):
        if self.bit_pos > 0:
            self.bit_pos = 0
            self.byte_pos += 1
    
    def step_bits(self, num_bits):
        self.bit_pos += num_bits
        self.byte_pos += self.bit_pos / 8
        self.bit_pos = self.bit_pos % 8
    def step_bytes(self, num_bytes):
        self.byte_pos += num_bytes

    def complement_bit_string(self, bit_str):
        complemented_string = ''
        for bit in bit_str:
            complemented_string += self.complement_bit(bit)
        return bit
    def complement_bit(self, bit):
        if bit == '0':
            return '1'
        elif bit == '1':
            return '0'
        else:
            raise ValueError("Invalid bit '%s'" %bit)

swf = SWF('/Users/dannygoodman/Desktop/SideIdeas/Coding/Web/video/flash/example_decompressed.swf')

#swf.file_contents = struct.pack('BB', 255, 255)
#swf.bit_pos = 4
#print swf.next_signed_bits(9)
#print swf.next_unsigned_bits(9)

swf.read_header()
while swf.byte_pos < len(swf):
    swf.program.addChild(swf.read_tag())
print "Read %d bytes" %len(swf.file_contents)
print "Byte pos is %d" %swf.byte_pos
#import pdb; pdb.set_trace()

# print "Program has %d child tags" %len(swf.program.children)
# print str(swf.program)

unhandled_codes = unhandled_codes.keys()
unhandled_codes.sort()
for code in unhandled_codes:
    print "%d: %s" %(code, hex(code))

swf.program.execute()

print "done"
print "TODO:"
print "DefineSprite: sub tags"