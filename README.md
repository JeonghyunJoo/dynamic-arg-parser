# Why do we need 'Dynamic Argument Parser'?
In the early stage of experiment design,  
 - hyper-parameters for the experiment are adopted or deprecated dynamically.
 - similar experiments which differ in only a small set of hyper-parameters are performed frequently to see the effect of each hyper parameter.

Those call for the efficient way of **adopting arguments flexibly** and **keeping arguments** used by experiments **in a reusable way**.  
dynamic-argu-parser aims to meet those goals.

# What can I do with 'Dynamic Argument Parser'?
All examples here explicitly pass the string which simulates command-line arguments. But it can also implicitly accept a program argument string as in the standard 'argparse' module.  

1. You can parse command-line arguments without specifying anything

```python
from argumentparser import DynamicArgumentParser

cmd_args = "--model resnet18 --optimizer adam --lr 0.1"
# If the parser is 'argparse.ArgumentParser', then it requires a detailed specification like:
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

2. You can save the configuration easily in a yaml-formatted file
* Or convert it to python dictionary
```python
from argumentparser import DynamicArgumentParser
cmd_args = "--model resnet18 --optimizer adam --lr 0.1"

dynamicparser = DynamicArgumentParser()
args = dynamicparser.parse_argument(args = cmd_args.split())

args.toyaml("save_file_path.yaml") #Save to the file
print( args.toyaml() ) #If any path is not given, it just returns the yaml-style string
print( args.todict() ) #or dict(args) also works
```
 Result:
```
>> lr: 0.1
>> model: resnet18
>> optimizer: adam
>> {'lr': 0.1, 'model': 'resnet18', 'optimizer': 'adam'}
```

3. You can load arguments from the file.  
* If an argument with the same name is given as command-line arguments too, then command-line arguments will overwrite the argument value given from the file.  
* Therefore, it allows you load base hyper-parameters from the previous experiement that you want to compare with and adjust only specific arguments.
```python
from argumentparser import DynamicArgumentParser
cmd_args = "--conf save_file_path.yaml --lr 0.5"

#'--conf' is used as the argument specifying the configuration file path
args = dynamicparser.parse_argument(args = cmd_args.split(), cfgfile_arg = 'conf')

print( args.toyaml() )
args.toyaml("new_experiment_config.yaml") #Save new arguments
```
Result: ('lr' has changed from 0.1 to 0.5)
```
conf: save_file_path.yaml
lr: 0.5
model: resnet18
optimizer: adam
```

4. You can use a hierachical argument
* hierachical arguments can be easily referenced in the code using dot notation.
```python
from argumentparser import DynamicArgumentParser
from argumentparser import DynamicArgumentParser
cmd_args = "--discriminator.type MLP --discriminator.layers 3 --generator.type CNN --generator.layers 4 --optimi.lr 0.01 --optim.type sgd"

args = dynamicparser.parse_argument(args = cmd_args.split())

print("optim.lr:", args.optim.lr) #Attributed access with dot notation
print("\n<yaml style >")
print(args.toyaml()) #yaml style looks like this
```
Result:
```
optim.lr: 0.01

<yaml style >
discriminator:
  layers: 3
  type: MLP
generator:
  layers: 4
  type: CNN
optim:
  lr: 0.01
  type: sgd
```
5. Trim unreferenced arguments
* 'AugmentedNamespace' implemented in this repo monitors member access.
* You can cut unreferrenced arguments
Example) In this example, 'optim.betas' is not used
```python
from argumentparser import DynamicArgumentParser
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
args.toyaml("save_cleaned_arguments.yaml")
```
Result:
```
... Model load: resnet18
... Optimizer load: sgd 0.001

Before trim: {'conf': 'old_config.yaml', 'model': 'resnet18', 'optim': {'betas': [0.99, 0.999], 'lr': 0.001, 'name': 'sgd'}}

After trim: {'model': 'resnet18', 'optim': {'lr': 0.001, 'name': 'sgd'}}
```