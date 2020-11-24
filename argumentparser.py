'''
Created on Nov 13, 2020

@author: jhjoo
'''
import argparse
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
            raise Exception(f"Can not handle the conversion of the type {type(v)}")

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
                        msg = f"Type Consistency check Error\n"\
                               "If you want to overwrite the argument value anyway, then set 'check_type_consistency = Fasle'\n"\
                               "Error Caused by:\n"
                        if typ2 == 'dict':
                            msg += f"{arg} can not be extended, because the terminal value {value} is already assigned"
                        elif typ1 == 'dict':
                            msg += f"The terminal value {v[0]} can not be assigned to {arg}, because it has its children"
                        raise Exception(msg)
                    except Exception:
                        msg = f"Type Consistency check Error\n"\
                               "If you want to overwrite the argument value anyway, then set 'check_type_consistency = Fasle'\n"\
                               "Error Caused by:\n"
                        raise Exception(f"Contradictory types {typ1} and {typ2} for {arg}")
                        
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
            args = _sys.argv[1:]
        
        if self.staticparser is not None:
            static_args, args = self.staticparser.parse_known_args(args)
            arg_dict = DynamicArgumentParser.dict_to_arg_dict(static_args.__dict__, arg_dict = {})
            self.update(arg_dict, add_mode == 'o')
        
        return args
            
    
    def dynamic_parse_cmd_args(self, args = None, add_mode = ['o', 'a', 'n'][0]):
        if add_mode == 'n':
            self.arg_dict = {}
        
        if args is None:
            args = _sys.argv[1:]
        
        arg_dict = {}
        
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
            args = _sys.argv[1:]
        
        #renew old parsing results and parse command line arguments with a static parser 
        args_yet_to_be_parsed = self.static_parse_cmd_args(args, add_mode = 'n')
        
        #handle arguments unrecognized by the static parser
        self.dynamic_parse_cmd_args(args_yet_to_be_parsed, add_mode = 'a')
        
        if cfgfile_arg is not '' and cfgfile_arg in self.arg_dict:
            cfg_filepath = self.arg_dict.get(cfgfile_arg)
            
            if os.path.exists(cfg_filePath):
                #Load arguments from the configuration file
                self.parse_config_file(cfg_filepath, 'a') #'a' is No-Overwrite mode. CMD-line args has a priority
    
        args_namespace = argdict_to_namespace(self.arg_dict)
    
        return args_namespace
    
from types import SimpleNamespace

class Namespace(SimpleNamespace):
    def __init__(self):
        super(Namespace, self).__init__()
        
    def __getattr__(self, key):
        try:
            value = getattr(super, key)
            return value
        except AttributeError:
            return NoneLike()
##        if key in self:
#        return getattr(self, key)
#        return NoneLike()

class NoneLike():
    def __init__(self):
        super(NoneLike, self).__init__()
    
    def __bool__(self):
        return False
    
    def __str__(self):
        return "None"
    
    def __eq__(self, other):
        return (other is None) or isinstance(other, NoneLike)
    
    
    def __getattr__(self, key):
        return NoneLike()

def add_value_to_namespace(key, value, basenamespace):
    if len(key) == 1:
        key = key[0]
        setattr(basenamespace, key, value)
        return
    add_value_to_namespace(key[1:], value, getattr(basenamespace, key[0]))
    
def argdict_to_namespace(arg_dict):
    #arg_dict := {argname: (argvalue, type)}
    root = Namespace()
    for k in sorted(arg_dict.keys()):
        value, typ = arg_dict[k]
        keys = k.split('.')
        if isinstance(value, dict):
            add_value_to_namespace(keys, Namespace(), root)    
        else:
            add_value_to_namespace(keys, value, root)    
    #from arg_dict
    return root

def namespace_to_dict(namespace):
    dic = {}
    for k, v in vars(namespace).items():
        if isinstance(v, Namespace):
            dic[k] = namespace_to_dict(v)
        else:
            dic[k] = v
    return dic
    

class Wrapper():
    def __init__(self, instance):
        super(Wrapper, self).__init__()
        self.instance_ = instance
    
    def __getattr__(self, key):
        return getattr(self.instance_, key, NoneLike())
    
    def __str__(self):
        return str(self.instance_)

def print_config(cfg, path = None):
    if path == None:
        print(yaml.dump(namespace_to_dict(cfg), sort_keys=True))
    else:
        with open(path, 'w') as f:
            yaml.dump(namespace_to_dict(cfg), f, sort_keys=True)

#def save_config(path, cfg):
    

# def parse_argument(staticparser = None, cfg_file_argname = None, cmd_line_args = None):
#     cfg_filepath = None
#     
#     rem_cmd_line_args = cmd_line_args
#     if cfg_file_argname is not None:
#         #the configuration file path parser
#         cfg_filepath_parser = argparse.ArgumentParser()
#         cfg_filepath_parser.add_argument("-"+cfg_file_argname, "--"+cfg_file_argname, type=str, required = True)
#         cfg_filepath_args, rem_cmd_line_args = cfg_filepath_parser.parse_known_args(cmd_line_args)
#         #Read the configuration file path
#         cfg_filepath = cfg_filepath_args.__dict__.get(cfg_file_argname)
#     
#     #Create a parser instance
#     simpleparser = DynamicArgumentParser(staticparser)
#     
#     #Parse command-line arguments
#     simpleparser.parse_cmd_line_args(rem_cmd_line_args)
#     
#     if cfg_filepath is not None:
#         #Load arguments from the configuration file
#         simpleparser.parse_config_file(cfg_filepath, 'a') #'a' is No-Overwrite mode. CMD-line args has a priority
#     
#     print(simpleparser.arg_dict)
#     def build_dynamic_parser(arg_dict, converters):
#         #converters: dictionary of (key: type string, value: converter function)
#         parser = jsonargparse.ArgumentParser()
#  
#         for arg, (v, typ) in arg_dict.items():
#             converter = converters.get(typ, None)
#  
#             if v is None:
#                 parser.add_argument('-'+arg, '--'+arg, dest=arg, action = 'store_true')
#             elif isinstance(v, list):
#                 parser.add_argument('-'+arg, '--'+arg, type=converter, nargs='+') 
#             else:
#                 parser.add_argument('-'+arg, '--'+arg, type=converter) 
#  
#         return parser
#     
#     dynamic_parser = build_dynamic_parser(simpleparser.arg_dict, DynamicArgumentParser.converters)
#     if cfg_filepath is not None:
#         dynamic_parser.add_argument("-"+cfg_file_argname, "--"+cfg_file_argname, action=jsonargparse.ActionConfigFile)
#     
#     args = dynamic_parser.parse_args(cmd_line_args)
# 
#     
#     def wrapup_namespace(instance, wrapper):
#         import types
#         if isinstance(instance, types.SimpleNamespace):
#             dic = instance.__dict__
#             for k in dic.keys():
#                 #dic[k] = dic[k]
#                 dic[k] = wrapup_namespace(dic[k], wrapper)
#             return wrapper(instance)#wrapper(instance)
#         return instance
# 
#     args = wrapup_namespace(args, Wrapper)
#     
#     return args