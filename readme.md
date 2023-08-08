# SnakeRun #

Launch python scripts with dependencies and python version handled

*Requires pyenv installed to handle python versions*


## How to use ##

Inside your python script specify requirements in a PEP-722 style format.

eg:
```python
# Script Dependencies:
#     prefab_classes>=0.9.3
#     requests
```

Optionally specify python version with a non-standard `# x-requires-python: >=3.10`.

Run with `python snakerun.py myscript.py`

## Logic ##

If an environment matching the exact text of the dependencies exists in the 
SnakeRun cache, that environment will be used.

Otherwise if python version and dependencies are given, the script will use
the newest python version installed that matches the requirement to create
a virtualenv with the listed dependencies.

If only a python version is given, if the version running `snakerun.py` 
satisfies the requirement the script will run in that version. Otherwise
it will attempt to find the newest python installed that satisfies the 
requirement and use that.

If only dependencies are given, the version of python running `snakerun.py`
will be used to create the environment.

If no python version or dependencies are given, the version of python
running `snakerun.py` will launch the script.


## Performance considerations ##

Much like prefab_classes this goes to some lengths to keep the start time
as low as possible (for python). Ideally the only overhead in the optimal 
case is the time it takes to parse the dependency format and find the 
cached environment.

This leads to avoiding some otherwise useful stdlib modules as importing
them takes as long as launching python from scratch.
