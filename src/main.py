'''
Created on Jul 20, 2010

@author: dannygoodman
'''

import struct


class Tag:
  def __init__(self, parent=None, contents=""):
    self.children = []
    self.contents = contents
    self.parent = parent
  def addChild(tag):
    self.children.append(tag)
    tag.parent = self
    
class Program(Tag):
  def __init__(self):
    Tag.__init__(self, parent=None, contents="")

class SWF:
    tag_type_to_string = {
        0 : "End",
        1 : "Show Frame",
        2 : "DefineShape",
        4 : "PlaceObject",
        5 : "Remove Object",
        9 : "Set Background Color",
        12 : "DoAction",
        20 : "DefineBitsLossless",
        22 : "DefineShape2",
        24 : "Protect",
        32 : "DefineShape3",
        36 : "DefineBitsLossless2",
        37 : "DefineEditText",
        39 : "DefineSprite",
        48 : "DefineFont",
        56 : "ExportAssets",
        59 : "DoInitAction",
        60 : "DefineVideoStream",
        70 : "PlaceObject3",
        88 : "DefineFontName"
    }
    
    action_code_to_name = {
        28 : 'action_get_variable',
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
        startPos = self.byte_pos
        (action_code, action_length) = self.read_action_header()
        expected_length = 1
        if action_length > 0:
            if action_code in self.action_code_to_name:
                action_name = self.action_code_to_name[action_code]
                print "Action %d: %s" %(action_code, action_name)
                getattr(self, "read_%s" %action_name).__call__(action_length)
            else:
                print "Unhandled action code: %d" %action_code
                action = self.read_ui(action_length)
            expected_length = action_length + 3
        else:
            print "Action code %d of length 0" %action_code
        bytesRead = self.byte_pos - startPos
        assert bytesRead == expected_length, "Wrong number of action bytes: expected %d, read %d" %(expected_length, bytesRead)
        return expected_length
    
    def read_actions(self):
        next_byte = self.next_unsigned_bytes_little_endian(1)
        total_len = 0
        while next_byte != 0:
            total_len += self.read_action()
            next_byte = self.next_unsigned_bytes_little_endian(1)
            
        self.step_bytes(1)            
        total_len += 1
        return total_len

    def read_action_constant_pool(self, length):
        count = self.read_ui(2)
        print "%d strings:" %count
        for i in range(count):
            print "%d: %s" %(i+1, self.read_string())
    
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
        while bytesRead < length:
            stackElt = None
            type = self.read_ui(1)
            if type == 0:
                stackElt = self.read_string()
                print "ActionPush string: %s" %stackElt
            elif type == 1:
                print "skipping 4-byte float"
                self.step_bytes(4)
            elif type == 2:
                print "ActionPush null"
            elif type == 3:
                print "ActionPush undefined"
            elif type == 4:
                stackElt = self.read_ui(1)
                print "ActionPush RegisterNumber: %d" %stackElt
            elif type == 5:
                stackElt = self.read_ui(1)
                print "ActionPush Boolean: %d" %stackElt
            elif type == 6:
                print "Skipping 8-byte double"
                self.step_bytes(8)
            elif type == 7:
                stackElt = self.read_ui(4)
                print "ActionPush Integer: %d" %stackElt
            elif type == 8:
                stackElt = self.read_ui(1)
                print "ActionPush 1-byte Constant: %d" %stackElt
            elif type == 9:
                stackElt = self.read_ui(2)
                print "ActionPush 2-byte Constant: %d" %stackElt
            else:
                raise Exception("Unknown type %d" %type)
            self.action_stack.append(stackElt)
            bytesRead = self.byte_pos - startPos
        assert bytesRead == length, "Error in action push: expected %d bytes, read %d" %(length, bytesRead)

        
    def read_action_store_register(self, length):
        registerIndex = self.read_ui(1) - 1
        stackElt = self.action_stack[-1]
        print "Storing '%s' in register index '%d'" %(str(stackElt), registerIndex)
        self.action_registers[registerIndex] = stackElt

    def read_tag(self):
        short_header = self.read_ui(2)
        tag_type = short_header / 2**6
        tag_length = short_header % 2**6
        if tag_length == 63:
            tag_length = self.read_si(4)
          
          
            
        startPos = self.byte_pos
        if tag_type in (60,):
            print "VIDEO TAG detected: %d" %tag_type
            self.read_video_stream_tag_body()
        elif tag_type == 12:
            print "DoAction (%d)" %tag_type
            self.read_actions()
        elif tag_type == 59:
            print "DoInitAction for Sprite ID %d" %self.read_ui(2)
            self.read_actions()
        else:
            if tag_type in self.tag_type_to_string:
                print self.tag_type_to_string[tag_type]
            else:
                print "Unhandled tag code: %d" % tag_type
            self.step_bytes(tag_length)
        bytesRead = self.byte_pos - startPos 
        assert tag_length == bytesRead, "Tag length mismatch: expected %d bytes, read %d" %(tag_length, bytesRead)
        
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
    swf.read_tag()
print "Read %d bytes" %len(swf.file_contents)
print "Byte pos is %d" %swf.byte_pos
#import pdb; pdb.set_trace()

print "done"