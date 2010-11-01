import copy

from flash_types import *

class ActionDoer:
    ignorable_actions = {
        # 0 : 'action_null?',
        7 : 'action_stop',
        # 11 : 'action_subtract',
        # 12 : 'action_multiply',
        # 13 : 'action_divide',
        # 18 : 'action_not',
        # 23 : 'action_pop',
        # 28 : 'action_get_variable',
        # 29 : 'action_set_variable',
        # 43 : 'action_cast_op',
        # 44 : 'action_implements_op',
        # 51 : 'action_ascii_to_char',
        # 52 : 'action_get_time',
        # 58 : 'action_delete',
        # 60 : 'action_define_local',
        # 61 : 'action_call_function',
        # 62 : 'action_return',
        # 63 : 'action_modulo',
        # 64 : 'action_new_object',
        # 66 : 'action_init_array',
        # 67 : 'action_init_object',
        # 68 : 'action_type_of',
        # 71 : 'action_add2',
        # 72 : 'action_less2',
        # 73 : 'action_equals2',
        # 74 : 'action_to_number',
        # 75 : 'action_to_string',
        # 76 : 'action_push_duplicate',
        # 78 : 'action_get_member',
        # 79 : 'action_set_member',
        # 80 : 'action_increment',
        # 81 : 'action_decrement',
        # 82 : 'action_call_method',
        # 83 : 'action_new_method',
        # 84 : 'action_instance_of',
        # 85 : 'action_enumerate2',
        # 96 : 'action_bit_and',
        # 100 : 'action_bit_rshift',
        # 102 : 'action_strict_equals',
        # 103 : 'action_greater',
        # 105 : 'action_extends',
        # 135 : 'action_store_register',
        # 136 : 'action_constant_pool',
        # 142 : 'action_define_function2',
        # 150 : 'action_push',
        # 153 : 'action_jump',
        # 155 : 'action_define_function',
        # 157 : 'action_if',
        -1 : 'null'
    }
    def __init__(self):
        self.constant_pool = []
        self.registers = [None]*4
        self.stack = []
    def do(self, action):
        if action.action_code() in self.ignorable_actions:
            print "Ignoring action %s" %str(action)
        elif action.action_code() == 18:
            value = self.stack.pop()
            not_value = Boolean(value)
            print "Pushing not(%s) = %s" %(str(value), str(not_value))
            self.stack.append(not_value)
        elif action.action_code() == 23:
            print "Popping value from stack"
            self.stack.pop()
        elif action.action_code() == 28:
            variable_name = self.stack.pop()
            variable = None
            if isinstance(variable_name, Constant):
                # TODO: is this the right thing to do?  const isn't nec a name
                variable = self.constant_pool[variable_name.value]
            else:
                raise Exception("Getting variable '%s'" %variable_name)
            print "Pushing variable %s: %s" %(str(variable_name), str(variable))
            self.stack.append(variable)
        elif action.action_code() == 78:
            member_name = self.stack.pop()
            obj = self.stack.pop()
            value = None
            if isinstance(member_name, Constant):
                # TODO: is this the right thing to do?  doesn't use obj
                value = self.constant_pool[member_name.value]
            else:
                raise Exception("Get member %s, %s" %(str(member_name), str(obj)))
            print "Get member: pushing %s.%s = %s" %(str(obj), str(member_name), str(value))
            self.stack.append(value)
        elif action.action_code() == 135:
            stack_elt = self.stack[-1]
            print "Storing '%s' in register %d" %(str(stack_elt), action.register_number)
            self.registers[action.register_number] = stack_elt
        elif action.action_code() == 136:
            self.constant_pool = copy.copy(action.contents['string_constants'])
            print "Set constant pool to: %s" %str(self.constant_pool)
        elif action.action_code() == 150:
            self.stack.extend(action.contents['values'])
            print "Pushed onto the stack: %s" %str(action.contents['values'])
        else:
            raise NotImplementedError("do(action) not defined for action tag: %s" %action.__str__())
        
        
        
        
        