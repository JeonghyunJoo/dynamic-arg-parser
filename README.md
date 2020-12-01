# Why do I need 'Dynamic Argument Parser'?
In the early stage of experiment design,  
 - hyper-parameters for the experiment are adopted or deprecated dynamically.
 - similar experiments which differ in only a small set of hyper-parameters are performed frequently to see the effect of each hyper parameter.

Those call for the efficient way of **adopting arguments flexibly** and **keeping arguments** used by experiments **in a reusable way**.  
dynamic-argu-parser aims to meet those goals.

# Installation
```
pip install dynamicargparse
```
### Import
```python
from dynamicargparse import DynamicArgumentParser
#Create an instance
dynamicparser = DynamicArgumentParser()

#Or create an instance by extending a static parser
import argparse
staticparser = argparse.ArgumentParser()
dynamicparser = DynamicArgumentParser(staticparser = staticparser)
```
### methods
```python
args = dynamicparser.parse_argument() #Parse arguments
args = dynamicparser.parse_argument(config_args = "conf") #Parse arguments. This will load arguments from the file_path given by '--conf file_path'
args.toyaml("save.yaml") #Save arguments as a yaml file
arg_dict = args.todict() #Convert into the python dictionary

```

# What can I do with 'Dynamic Argument Parser'?
All examples here explicitly pass the string which simulates command-line arguments. But it can also implicitly accept a program argument string as in the standard 'argparse' module.  

### 1. You can parse command-line arguments without specifying anything

```python
from dynamicargparse import DynamicArgumentParser

cmd_args = "--model resnet18 --optimizer adam --lr 0.1"
# If the parser was 'argparse.ArgumentParser', then it requires a detailed specification like:
# parser.add_argument("--model", type=str)
# parser.add_argument("--optimizer", type=str)
# parser.add_argument("--lr", type=float)

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split())
print("args.model:", args.model, type(args.model))
print("args.optimizer:", args.optimizer, type(args.optimizer))
print("args.lr:", args.lr, type(args.lr))
```

 Result:
```
>> model: resnet18 <class 'str'>
>> optimizer: adam <class 'str'>
>> lr: 0.1 <class 'float'>
```
### 2. You can easily extend the 'argparse.ArgumentParser' module
```python
from dynamicargparse import DynamicArgumentParser
import argparse

cmd_args = "--model resnet18 --optimizer adam --lr 0.1 --new_argu new"

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str)
parser.add_argument("--optimizer", type=str)
parser.add_argument("--lr", type=float)

dynamicparser = DynamicArgumentParser(staticparser = parser)
args = dynamicparser.parse_argument(args = cmd_args.split())
print("args.model:", args.model)
print("args.optimizer:", args.optimizer)
print("args.lr:", args.lr)
print("args.new_argu:", args.new_argu)
```
Result:
```
>> args.model: resnet18
>> args.optimizer: adam
>> args.lr: 0.1
>> args.new_argu: new
```

### 3. You can save the configuration easily in a yaml-formatted file
* Or convert it to python dictionary
```python
from dynamicargparse import DynamicArgumentParser
cmd_args = "--model resnet18 --optimizer adam --lr 0.1"

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split())

args.toyaml("save_file_path.yaml") #Save to the file
print( "<yaml style>\n", args.toyaml() ) #If any path is not given, it just returns the yaml-style string
print( "Dictionary:", args.todict() ) #or dict(args) also works
```
 Result:
```
>> <yaml style>
>> lr: 0.1
>> model: resnet18
>> optimizer: adam
>> Dictionary: {'lr': 0.1, 'model': 'resnet18', 'optimizer': 'adam'}
```

### 4. You can load arguments from the file.  
* If an argument with the same name is given as command-line arguments too, then command-line arguments will overwrite the argument value given from the file.  
* Therefore, it allows you **load base hyper-parameters** from the previous experiement that you want to compare with and **adjust only specific arguments.**
```python
from dynamicargparse import DynamicArgumentParser
cmd_args = "--conf save_file_path.yaml --lr 0.5"

#'--conf' is used as the argument specifying the configuration file path
args = dynamicparser.parse_argument(args = cmd_args.split(), cfgfile_arg = 'conf')

print( args.toyaml() )
args.toyaml("new_experiment_config.yaml") #Save new arguments
```
Result: ('lr' has changed from 0.1 to 0.5)
```
>> conf: save_file_path.yaml
>> lr: 0.5
>> model: resnet18
>> optimizer: adam
```

### 5. You can use a hierachical argument
* hierachical arguments can be easily referenced in the code using dot notation.
```python
from dynamicargparse import DynamicArgumentParser
from dynamicargparse import DynamicArgumentParser
cmd_args = "--discriminator.type MLP --discriminator.layers 3 --generator.type CNN --generator.layers 4 --optimi.lr 0.01 --optim.type sgd"

args = dynamicparser.parse_argument(args = cmd_args.split())

print("optim.lr:", args.optim.lr) #Attributed access with dot notation
print("\n<yaml style >")
print(args.toyaml()) #yaml style looks like this
```
Result:
```
>> optim.lr: 0.01

>> <yaml style >
>> discriminator:
>>   layers: 3
>>   type: MLP
>> generator:
>>   layers: 4
>>   type: CNN
>> optim:
>>   lr: 0.01
>>   type: sgd
```
### 6. Trim unreferenced arguments
* 'AugmentedNamespace' implemented in this repo monitors member access.
* You can cut unreferrenced arguments
Example) In this example, 'optim.betas' is not used
```python
from dynamicargparse import DynamicArgumentParser
cmd_args = "--conf old_config.yaml --optim.name sgd"

# > old_config.yaml
# > model: resnet18
# > optim:
# >    name: adam
# >    lr: 0.001
# >    betas:
# >      - 0.99
# >      - 0.999

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split(), cfgfile_arg = 'conf')

print("... Model load:", args.model)
print("... Optimizer load:", args.optim.name, args.optim.lr)

print("\nBefore trim:", args.todict() )
args.trim()
print("\nAfter trim:", args.todict() )
args.toyaml("save_clean_arguments.yaml")
```
Result:
```
>> ... Model load: resnet18
>> ... Optimizer load: sgd 0.001

>> Before trim: {'conf': 'old_config.yaml', 'model': 'resnet18', 'optim': {'betas': [0.99, 0.999], 'lr': 0.001, 'name': 'sgd'}}

>> After trim: {'model': 'resnet18', 'optim': {'lr': 0.001, 'name': 'sgd'}}
```
### 7. How to check whether a specific argument is given or not?
* The namespace returns 'Nonelike' object for the invalid access
* You can check by an equality test with None (Caution: not identity test as 'Nonelike' object is not truly None)
```python
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
```
Result:
```
>> argument a:  1
>> argument c is not given
>> c == None True
>> c is None False
```
#### You can find some more examples in the example folder: a notebook file 'Example.ipynb', a python file 'Example.py'

# What is the parsing rule used by 'Dynamic Argument Parser'?
#### 1. Space splits each element
* e.g.) `'--abc 1 2,3 4'` ==> `['--abc', '1', '2,3', '4']`
#### 2. An argument name is assumed to begin with '-' or '--' and values which appear between two argument names are assigned to the former argument
* e.g.) `'--abc 1 2 --c'` ==> `abc <= [1, 2]`
#### 3. If no argument value is given to a argument, the argument is treated like a binary flag value, especially 'True' is assigned
* e.g.) `'--a --b 1'` ==> `a <= True, b <= 1`
#### 4. Data type is implictly Inferrenced.
* 3.g.) `'--a 0.1 --b a --c 1 --d 1e-5'` ==> `a <= 0.1 (float), b <= a (str), c <= 1 (int), d <= 0.00001 (float)`

# Final remarks
Dynamic parsing is convenient to work with. But it is vulnerable to error, especially typo. Therefore, once your program is stabilized, it is recommended to move to the static parser which can give nice help messages and strict type/typo checking.   
If you feel interests, I recommend to visit this repo 'https://github.com/omni-us/jsonargparse' too. Thier parser is less flexible but has more features and complete.  
Any error report or suggestions are welcomed. Thanks. 
