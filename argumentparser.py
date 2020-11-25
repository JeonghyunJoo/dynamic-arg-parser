'''
Created on Nov 13, 2020

@author: jhjoo
'''
import yaml
import sys

def bool_converter(s):
    if isinstance(s, str):
        s = s.lower()
        if s == 'true':
            return True
        elif s == 'false':
            return False
        else:
            raise ValueError
    elif isinstance(s, bool):
        return s
    elif isinstance(s, int):
        return s != 0
    else:
        raise ValueError

#Check a type consistency b/w two types, typ1 and typ2
#If their types disagree but one type can cover the other, then return the more general type among them.
#If their types are contradictory, then raise exception
def type_consistency(typ1, typ2):
    if typ1 == typ2:
        return typ1

    terminal_typ1 = typ1.replace('list_', '') if typ1.startswith('list') else typ1
    terminal_typ2 = typ2.replace('list_', '') if typ2.startswith('list') else typ2

    if terminal_typ1 == terminal_typ2:
        #this case happens, only when two types have the same terminal type but one is a list type and the other is not
        return 'list_' + terminal_typ1

    #relationship
    #String <- float, int, bool
    #Float <- int
    #int <- bool
    num = {'str' : 3, 'float' : 2, 'int' : 1, 'bool' : 0}

    M = max(num[terminal_typ1], num[terminal_typ2])
    m = min(num[terminal_typ1], num[terminal_typ2])

    if M == 3:
        unified_terminal_typ = 'str'
    elif M == 2 and m == 1:
        unified_terminal_typ = 'float'
    elif M == 1 and m == 0:
        unified_terminal_typ = 'int'
    else:
        raise Exception()

    if typ1.startswith('list') or typ2.startswith('list'):
        return 'list_' + unified_terminal_typ
    return unified_terminal_typ
        
class DynamicArgumentParser():
    converters = {
        'list_int' : int,
        'int' : int,
        'list_float' : float,
        'float' : float,
        'list_bool' : bool_converter,
        'bool' : bool_converter,
        'list_str' : str,
        'str' : str
    }
    
    @classmethod
    def _convert(cls, v):
        if isinstance(v, list):
            result_list = []
            unified_terminal_typ = None
            
            for e in v:
                e, typ = DynamicArgumentParser._convert(e)
                
                unified_terminal_typ = type_consistency(unified_terminal_typ, typ) if unified_terminal_typ else typ
                    
                result_list.append(e)
            
            return result_list, 'list_' + unified_terminal_typ
        
        if isinstance(v, bool):
            return v, 'bool'
        if isinstance(v, int):
            return v, 'int'
        elif isinstance(v, float):
            return v, 'float'
        elif isinstance(v, str):
            #inspired by 'https://github.com/bruth/strconv'
        
            for typ in ['int', 'float', 'bool']:
                try:
                    converter = cls.converters[typ]
                    v = converter(v)
                    return v, typ
                except ValueError:
                    pass
            return v, 'str'
        else:
            raise Exception("Can not handle the conversion of the type {}".format(type(v)))

    def __init__(self, staticparser = None, check_type_consistency = True):
        # - check_type_consistency : Check whether a data type is matched for the same argument
        super(DynamicArgumentParser, self).__init__()
        
        self.staticparser = staticparser
        self.arg_dict = {} # Key: arg name, Value: (arg value #converted python data, arg type #string, terminal type)
        self.check_type_consistency = check_type_consistency
    
    @classmethod
    def dict_to_arg_dict(cls, dic, arg_dict = {}, prefix = []):
        for k, v in dic.items():
            if v is None:
                continue
            if isinstance(v, dict):
                argname = '.'.join(prefix + [k])
                arg_dict[argname] = ({}, 'dict')
                cls.dict_to_arg_dict(v, arg_dict, prefix = prefix + [k])
            else:
                argname = '.'.join(prefix + [k])
                
                _v, typ = cls._convert(v)
                
                arg_dict[argname] = (v, typ)
        
        return arg_dict
    
    
    def update(self, add_dict, overwrite = True):
        # - overwrite:
        # If true, self.arg_dict has a priority over add_dict when a duplicate key occurs
#         if not overwrite:
#             filtered = filter(lambda item: item[0] not in self.arg_dict, add_dict.items())
#         else:
#             filtered = add_dict.items()
    
        for arg, v in add_dict.items():
            if arg in self.arg_dict:
                value = self.arg_dict[arg][0]
                typ = self.arg_dict[arg][1]
                if self.check_type_consistency:
                    typ1 = self.arg_dict[arg][1]
                    typ2 = v[1]
                    try:
                        typ = type_consistency(typ1, typ2)
                    except KeyError:
                        #it happens when one type is 'dict' and the other type is 'dictionary'
                        msg = "Type Consistency check Error\n"\
                               "If you want to overwrite the argument value anyway, then set 'check_type_consistency = Fasle'\n"\
                               "Error Caused by:\n"
                        if typ2 == 'dict':
                            msg += "{} can not be extended, because the terminal value {value} is already assigned".format(arg)
                        elif typ1 == 'dict':
                            msg += "The terminal value {} can not be assigned to {}, because it has its children".format(v[0], arg)
                        raise Exception(msg)
                    except Exception:
                        msg = "Type Consistency check Error\n"\
                               "If you want to overwrite the argument value anyway, then set 'check_type_consistency = Fasle'\n"\
                               "Error Caused by:\n"
                        raise Exception("Contradictory types {} and {} for {}".format(typ1,  typ2, arg))
                        
                if overwrite:
                    value = v[0]
                    #elf.arg_dict[arg] = v
                
                self.arg_dict[arg] = (value, typ)
            else:
                self.arg_dict[arg] = v
        
#        for arg, v in filtered:
#            self.arg_dict[arg] = v
    
    #add_mode:
    # - 'o' : Overwrite if a new value is given for the existing argument
    # - 'a' : Add values only for new values
    # - 'n' : Remove an old parsing result
    def parse_config_file(self, file, add_mode = ['o', 'a', 'n'][0]):
        if add_mode == 'n':
            self.arg_dict = {}
            
        with open(file, 'r') as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
        
        arg_dict = DynamicArgumentParser.dict_to_arg_dict(cfg, arg_dict = {})
        
        self.update(arg_dict, add_mode == 'o')
        
    
    def static_parse_cmd_args(self, args = None, add_mode = ['o', 'a', 'n'][0]):
        if add_mode == 'n':
            self.arg_dict = {}
        
        if args is None:
            args = sys.argv[1:]
        
        if self.staticparser is not None:
            static_args, args = self.staticparser.parse_known_args(args)
            arg_dict = DynamicArgumentParser.dict_to_arg_dict(static_args.__dict__, arg_dict = {})
            self.update(arg_dict, add_mode == 'o')
        
        return args
            
    
    def dynamic_parse_cmd_args(self, args = None, add_mode = ['o', 'a', 'n'][0]):
        if add_mode == 'n':
            self.arg_dict = {}
        
        if args is None:
            args = sys.argv[1:]
        
        arg_dict = {}
        argvalue = []
        argname = None
        for arg in args + ["-"]: #Append a dummy argument to make the logic simple
            if arg.startswith(("-", "--")):
                if argname is not None:
                    v = None
                    typ = None
                    if len(argvalue) == 0:
                        v, typ = True, 'bool'
                    elif len(argvalue) == 1:
                        v, typ = self._convert(argvalue[0])
                    elif len(argvalue) > 1:
                        v, typ = self._convert(argvalue)
                        
                    lastindex = 0
                    while True:
                        lastindex = argname.find('.', lastindex)
                        if lastindex == -1:
                            break
                        arg_dict[ argname[:lastindex] ] = ({}, 'dict')
                        lastindex = lastindex + 1

                    arg_dict[argname] = (v, typ)
                argname = arg.lstrip('-')
                argvalue = []
            else:
                argvalue.append(arg)
        
        self.update(arg_dict, add_mode == 'o')

    def parse_argument(self, args = None, cfgfile_arg = ''):
        if args is None:
            args = sys.argv[1:]
        
        #renew old parsing results and parse command line arguments with a static parser 
        args_yet_to_be_parsed = self.static_parse_cmd_args(args, add_mode = 'n')
        
        #handle arguments unrecognized by the static parser
        self.dynamic_parse_cmd_args(args_yet_to_be_parsed, add_mode = 'a')
        
        if cfgfile_arg != '' and cfgfile_arg in self.arg_dict:
            cfg_filepath = self.arg_dict.get(cfgfile_arg)[0]
            
            #Load arguments from the configuration file
            self.parse_config_file(cfg_filepath, 'a') #'a' is No-Overwrite mode. CMD-line args has a priority
       
        def convert_2_recursive_dict(arg_dict):
            root_dir = {}
            for k in sorted(arg_dict.keys()):
                v, _ = arg_dict[k] #Drop type information
                key_chain = k.split('.')
                
                def get_parent_dict(keys, parent):
                    if len(keys) == 1:
                        return parent
                    else:
                        return get_parent_dict(keys[1:], parent[keys[0]])
                
                p_dict = get_parent_dict(key_chain, root_dir)
                p_dict[key_chain[-1]] = {} if isinstance(v, dict) else v
            
            return root_dir
        
        rdict = convert_2_recursive_dict(self.arg_dict)
        
        #args_namespace = argdict_to_namespace(self.arg_dict)
        
        args_tree = Node(rdict)
        args_tree.activate(True)
        
        return args_tree#args_namespace
    
class Node():
    def __init__(self, arg_dict, p = None, activate = False):
        super(Node, self).__init__()
        
        self._mem_parent = p
        self._mem_children = {}
        
        self._mem_activate = activate
        self._mem_arg_dict = {} #key: arg name , value: {value: arg value, ref_count: ref count}
         
        self._mem_absorbing_node = NoneLike(self)
        self._mem_key_chain_buffer = []
        
        self._mem_build(arg_dict)
    
    #def asdict(self):
    def todict(self, include_ref_count = False):
        root_dir = {}
        for k,v in self._mem_arg_dict.items():
            if include_ref_count:
                root_dir[k] = (v['value'], v['ref_count'])
            else:
                root_dir[k] = v['value']
        
        for k,v in self._mem_children.items():
            root_dir[k] = v.todict(include_ref_count)
        
        return root_dir
    
    def activate(self, v = True):
        self._mem_activate = v
        for c in self._mem_children.values():
            c.activate(v)
    
    def trim(self, min_ref_count = 1):
        del_keys = []
        for k,v in self._mem_arg_dict.items():
            if v['ref_count'] < min_ref_count:
                del_keys.append(k)
        
        for k in del_keys:
            del self._mem_arg_dict[k]
        
        del_keys = []
        for k, c in self._mem_children.items():
            if c.trim(min_ref_count) is None:
                del_keys.append(k)
        
        for k in del_keys:
            del self._mem_children[k]
        
        if len(self._mem_arg_dict) + len(self._mem_children) == 0:
            return None
        else:
            return self
        
        
    
    def _mem_build(self, arg_dict):
        for k,v in arg_dict.items():
            setattr(self, k, v)   
    
    def __setattr__(self, key, value):
        if key.startswith('_mem_'):
            super().__setattr__(key, value)
        else:
            if isinstance(value, dict):
                self._mem_children[key] = Node(value, self, activate = self._mem_activate) 
            else: #terminal type
                if key in self._mem_arg_dict:
                    self._mem_arg_dict[key]['value'] = value
                else:
                    self._mem_arg_dict[key] = {'value': value, 'ref_count' : 0}
                self._mem_stack_ref_count(key)
#                setattr(self._mem_arg_namespace, key, value)
    
    def __getattr__(self, key):
        if key in self._mem_children:
            return self._mem_children[key]
        elif key in self._mem_arg_dict:
            self._mem_stack_ref_count(key)
            return self._mem_arg_dict[key]['value']#getattr(self._mem_arg_namespace, key)            
        else:
            self._mem_reset_key_chain_buffer()
            self._mem_append_key_chain_buffer(key)
            return self._mem_absorbing_node
    
    def _mem_stack_ref_count(self, key):
        additional_ref_count = 1 if self._mem_activate else 0
        
        self._mem_arg_dict[key]['ref_count'] = self._mem_arg_dict[key]['ref_count'] + additional_ref_count 

    def _mem_reset_key_chain_buffer(self):
        self._mem_key_chain_buffer = []
    
    def _mem_append_key_chain_buffer(self, key):
        self._mem_key_chain_buffer.append(key)
        
class NoneLike():
    #Member = ['_momp']
    def __init__(self, p):
        super(NoneLike, self).__init__()
        self._mem_p = p
    
    def __bool__(self):
        return False
    
    def __str__(self):
        return "None"
    
    def __eq__(self, other):
        return (other is None) or isinstance(other, NoneLike)
    
    def __getattr__(self, key):
        self._mem_p._mem_append_key_chain_buffer(key)
        return self
    
    def __setattr__(self, key, value):
        if key.startswith('_mem_'):
            super().__setattr__(key, value)
        else:
            root_dict = {}
            ptr = root_dict
            for k in self._mem_p._mem_key_chain_buffer[1:]:
                ptr[k] = {}
                ptr = ptr[k]
                
            ptr[key] = value
            root_key = self._mem_p._mem_key_chain_buffer[0]
            
            setattr(self._mem_p, root_key, root_dict)
        

def print_config(args, path = None):
    if path == None:
        print(yaml.dump(args.todict(), sort_keys=True))
    else:
        with open(path, 'w') as f:
            yaml.dump(args.todict(), f, sort_keys=True)
