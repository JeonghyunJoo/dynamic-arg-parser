#!/usr/bin/env python
# coding: utf-8

# # Import

# In[1]:


from dynamicargparse import DynamicArgumentParser


# # Standard argparse can be applied directly

# In[2]:


cmd_args = "--model resnet18 --optimizer adam --lr 0.1"

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, required=True)
parser.add_argument("--optimizer", type=str, default="sgd")
parser.add_argument("--lr", type=float, default=0.01)
parser.add_argument("--batchsize", type=int, default=128)

dynamicparser = DynamicArgumentParser(staticparser = parser)
dargs = dynamicparser.parse_argument(args = cmd_args.split())

print("\nParsing result with the dynamic parser")
print("dargs.model:", dargs.model)
print("dargs.optimizer:", dargs.optimizer)
print("dargs.lr:", dargs.lr)
print("dargs.batchsize:", dargs.batchsize)


# # Handling arguments unrecognized by argparse 

# In[3]:


cmd_args = "--model resnet18 --optimizer adam --lr 0.1 --unrecognized hello"

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, required=True)
parser.add_argument("--optimizer", type=str, default="sgd")
parser.add_argument("--lr", type=float, default=0.01)
parser.add_argument("--batchsize", type=int, default=128)

dynamicparser = DynamicArgumentParser(staticparser = parser)
args = dynamicparser.parse_argument(args = cmd_args.split())
print("args.model:", args.model)
print("args.optimizer:", args.optimizer)
print("args.lr:", args.lr)
print("args.batchsize:", args.batchsize)
print("args.unrecognized:", args.unrecognized)


# # various argument types are supported

# In[4]:


cmd_args = "--arg1 abc --arg2 100 --arg3 5e-3 --arg4 5 10 -arg5 --arg6 False"

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split())
print("args.arg1:", args.arg1, type(args.arg1))
print("args.arg2:", args.arg2, type(args.arg2))
print("args.arg3:", args.arg3, type(args.arg3))
print("args.arg4:", args.arg4, type(args.arg4))
print("args.arg5:", args.arg5, type(args.arg5))
print("args.arg6:", args.arg6, type(args.arg6))


# # Hierarchical argument

# In[5]:


cmd_args = "--log.save_path a/b/e --log.level info --checkpoint.save_path a/b/d --checkpoint.save_frequency 50"

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split())
print("args.log.save_path:", args.log.save_path)
print("args.log.level:", args.log.level)
print("args.checkpoint.save_path:", args.checkpoint.save_path)
print("args.checkpoint.save_frequency:", args.checkpoint.save_frequency)


# # Loading arguments from a configuration file

# In[6]:


cmd_args = "--conf example.yaml"

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split(), cfgfile_arg = 'conf')

print("args.model:", args.model)
print("args.dataset:", args.dataset)
print("args.optimizer.name:", args.optimizer.name)
print("args.optimizer.lr:", args.optimizer.lr)
print("args.optimizer.betas:", args.optimizer.betas)


# # Save configuration as a yaml-formatted file

# In[7]:


cmd_args = "--conf example.yaml"

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split(), cfgfile_arg = 'conf')

config_save_path = "save_config.yaml"
args.toyaml(config_save_path)

#if path is not given, then 'toyaml()' just returns the yaml string
print( args.toyaml() )


# # Conveying arguments through both sources 

# In[8]:


#command line arguments have a precedence over arguments from the file
cmd_args = "--conf example.yaml --optimizer.name sgd --optimizer.lr 0.1"

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split(), cfgfile_arg = 'conf')

print(args.todict())


# # Triming unreferenced arguments

# In[9]:


cmd_args = "--conf example.yaml --optimizer.name sgd --optimizer.lr 0.1"

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split(), cfgfile_arg = 'conf')

print("Before trim\n", args.todict())

print("\n... Create dataset instance:", args.dataset)
print("... Create model instance:", args.model)
print("... Create optimizer instance:", args.optimizer.name, args.optimizer.lr)
print("optimizer.betas is never used")

args.trim()
print("\nAfter trim\n", args.todict())


# # Checking whether an argument is given or not
# # Adding new arguments dynamically

# In[10]:


cmd_args = "--a 1"

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split())

print("Arguments:", dict(args))

#Warning: Argument must be compared with None by equality operators (==, !=) not by identity operators (is, is not)
if args.a != None:
    print("argument a: ", args.a)
else:
    print("argument a is not given")

if args.c != None:
    print("argument c: ", args.c)
else:
    print("argument c is not given")

#Though it prints its value as 'None', as said, it is not truly None. Therefore 'args.this.does_not.cause.any.error is None' would result in False
print("argument even.this.does_not.cause.attribute.error: ",  args.even.this.does_not.cause.attribute.error)
print("argument even.this.does_not.cause.attribute.error is None: ",  args.even.this.does_not.cause.attribute.error is None)
print("argument even.this.does_not.cause.attribute.error == None: ",  args.even.this.does_not.cause.attribute.error == None)

args.even.this.does_not.cause.attribute.error = 'yes'
print("Arguments:", args.todict())


# In[11]:


cmd_args = "--a=1,2,3"
dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split())
print("Arguments:", args.todict())


# In[20]:


from dynamicargparse import DynamicArgumentParser
cmd_args = "--a 1"

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split())

#Warning: Argument must be compared with None by equality operators (==, !=) not by identity operators (is, is not)
if args.a != None:
    print("argument a: ", args.a)
else:
    print("argument a is not given")

if args.c != None:
    print("argument c: ", args.c)
else:
    print("argument c is not given")

print("c == None", args.c == None)
print("c is None", args.c is None)

